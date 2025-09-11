# C2 Proxy Chain System

Hệ thống C2 (Command & Control) proxy chain với kiến trúc asyncio, hỗ trợ HTTP/SOCKS5 proxy và quản lý bot agents qua giao diện web.

## 🚀 Tính năng

- **Async C2 Server**: Xử lý đồng thời nhiều kết nối bot và client
- **HTTP/SOCKS5 Proxy**: Hỗ trợ cả HTTP CONNECT và SOCKS5 proxy
- **Bot Management**: Quản lý bot agents với load balancing
- **Web Dashboard**: Giao diện web real-time để giám sát và điều khiển
- **TLS Encryption**: Mã hóa kết nối C2-Bot (tùy chọn)
- **Config File**: Cấu hình tập trung qua file JSON
- **Framed Protocol**: Giao thức tin cậy cho C2-Bot communication

## 📁 Cấu trúc thư mục

```
C2/
├── c2_server.py          # C2 server chính
├── bot_agent.py          # Bot agent
├── protocol.py           # Framed communication protocol
├── config.json           # File cấu hình chính
├── config_template.json  # Template cấu hình
├── templates/
│   └── dashboard.html    # Web UI template
├── static/
│   └── dashboard.js      # Web UI JavaScript
└── README.md
```

## ⚙️ Cài đặt

### Yêu cầu hệ thống
- Python 3.10+
- Không phụ thuộc bên thứ ba (chỉ dùng stdlib)
- TLS là tùy chọn nhưng nên bật khi production

### Cài đặt nhanh
```bash
git clone <repository>
cd C2
cp config_template.json config.json
# Chỉnh sửa config.json theo nhu cầu
```

## 🔧 Cấu hình

### 1. Tạo Bot Token
```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))  # ~64 ký tự an toàn
PY
```

### 2. Cấu hình Server (config.json)
```json
{
  "server": {
    "host": "0.0.0.0",
    "bot_port": 4443,
    "http_port": 8080,
    "socks_port": 1080,
    "api_port": 5001
  },
  "security": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "tls": {
      "enabled": false,
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
  }
}
```

### 3. (Tùy chọn) Tạo chứng chỉ TLS
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes \
  -subj "/CN=localhost"
```

Sau đó cập nhật `config.json`:
```json
{
  "security": {
    "tls": {
      "enabled": true,
      "cert_file": "cert.pem",
      "key_file": "key.pem"
    }
  }
}
```

## 🚀 Chạy hệ thống

### 1. Chạy C2 Server
```bash
# Sử dụng config file (khuyến nghị)
python3 c2_server.py

# Hoặc chỉ định config file khác
python3 c2_server.py --config my_config.json

# Override một số thông số từ command line
python3 c2_server.py --host 192.168.1.100 --bot-port 4444 --tls-enabled
```

### 🔄 Graceful Shutdown
Hệ thống hỗ trợ graceful shutdown với signal handling:

```bash
# Shutdown bằng Ctrl+C
python3 c2_server.py
# Nhấn Ctrl+C để shutdown gracefully

# Shutdown bằng signal
kill -TERM <pid>  # Linux/macOS
taskkill /PID <pid> /T  # Windows

# Test graceful shutdown
python3 test_graceful_shutdown.py

# Test connection limits
python3 test_connection_limits.py
```

**Tính năng Graceful Shutdown:**
- ✅ **Signal handling**: SIGINT, SIGTERM, SIGBREAK
- ✅ **Resource cleanup**: Đóng tất cả connections và servers
- ✅ **Bot disconnection**: Thông báo và đóng bot connections
- ✅ **Task cancellation**: Cancel tất cả async tasks
- ✅ **Logging**: Log quá trình shutdown

### 2. Chạy Bot Agent
```bash
# Bot cơ bản
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN>

# Bot với TLS
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN> --tls

# Bot với config file
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN> --config bot_config.json
```

### 3. Chạy nhiều Bot
```bash
# Bot 1
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN> --bot-id bot_1

# Bot 2
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN> --bot-id bot_2

# Bot 3
python3 bot_agent.py --c2-host <IP_C2> --c2-port 4443 --token <BOT_TOKEN> --bot-id bot_3
```

## 🌐 Web Dashboard

Truy cập Web UI tại: `http://<IP_C2>:5001/`

### Tính năng Web UI:
- **Trạng thái server**: Host, ports, số lượng bots
- **Quản lý bots**: Xem danh sách, chọn bot ưu tiên
- **Theo dõi kết nối**: Kết nối đang hoạt động real-time
- **Cập nhật tự động**: Refresh mỗi 2 giây

### API Endpoints:
- `GET /api/status` - Trạng thái tổng quan
- `GET /api/bots` - Danh sách bots
- `GET /api/connections` - Kết nối đang hoạt động
- `POST /api/select_bot` - Chọn bot ưu tiên
- `POST /api/clear_preferred_bot` - Bỏ ưu tiên bot

**Health Check Endpoints**:
- `GET /health` - Health check cơ bản (200/503)
- `GET /health/detailed` - Health check chi tiết
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe

## 🔧 Sử dụng Proxy

### HTTP Proxy
```bash
# Cấu hình trình duyệt hoặc ứng dụng
HTTP Proxy: <IP_C2>:8080

# Test với curl
curl --proxy <IP_C2>:8080 https://httpbin.org/ip
```

### SOCKS5 Proxy
```bash
# Cấu hình ứng dụng hỗ trợ SOCKS5
SOCKS5 Proxy: <IP_C2>:1080

# Test với curl
curl --socks5 <IP_C2>:1080 https://httpbin.org/ip
```

## 📊 Cách hoạt động

### 1. Kiến trúc tổng quan
```
Client → C2 Server → Bot Agent → Internet
```

### 2. Framed Protocol
- **CMD**: Lệnh điều khiển
- **DATA**: Dữ liệu payload
- **RESP**: Phản hồi
- **END**: Kết thúc kết nối
- **ERR**: Lỗi
- **PING/PONG**: Heartbeat

### 3. Load Balancing
- **Round-robin**: Phân phối đều giữa các bots
- **Preferred bot**: Chọn bot ưu tiên
- **Fallback**: Tự động chuyển sang bot khác nếu bot ưu tiên offline

### 4. Multiplexing
- Mỗi bot có thể xử lý nhiều kết nối đồng thời
- Sử dụng `request_id` để phân biệt các kết nối
- Persistent tunnel giữa C2 và Bot

## 🔒 Bảo mật

### 1. Authentication
- Bot token bắt buộc để kết nối C2
- Token được gửi trong frame AUTH đầu tiên

### 2. TLS Encryption
- Mã hóa kết nối C2-Bot (tùy chọn)
- Sử dụng chứng chỉ tự ký hoặc CA-signed
- Bảo vệ khỏi man-in-the-middle attacks

### 3. Connection Limits
- **Max Bots**: Giới hạn số lượng bots có thể kết nối
- **Max Connections per Bot**: Giới hạn số kết nối mỗi bot có thể xử lý
- **Automatic Rejection**: Tự động từ chối khi vượt quá giới hạn
- **Resource Protection**: Bảo vệ khỏi DoS attacks và resource exhaustion

### 4. Rate Limiting
- Timeout cho kết nối không hoạt động
- Heartbeat để phát hiện dead connections
- Connection tracking và cleanup

## 📊 Monitoring & Health Checks

### Health Check Client
```bash
# Basic health check
python3 simple_health_check.py

# All endpoints
python3 simple_health_check.py --all

# Different formats
python3 simple_health_check.py --format nagios
python3 simple_health_check.py --format prometheus
python3 simple_health_check.py --format json

# Test health check functionality
python3 test_health_check.py
```

### Monitoring Integration
- **Nagios/Icinga**: Use `--format nagios` for service checks
- **Prometheus**: Use `--format prometheus` for metrics collection
- **Kubernetes**: Use `/health/ready` and `/health/live` endpoints
- **Docker**: Use health check in Dockerfile
- **Custom**: Use JSON format for custom monitoring

### Health Status Levels
- **🟢 Healthy**: All systems operational
- **🟡 Warning**: Approaching limits or some issues
- **🔴 Degraded**: No bots connected or critical issues

### Example Health Response
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "uptime_human": "2h 30m 15s",
  "bots": {
    "total": 3,
    "max": 100,
    "overloaded": 0
  },
  "connections": {
    "total": 15,
    "max_per_bot": 50
  }
}
```

Xem `monitoring_examples.md` để biết thêm chi tiết về integration với các monitoring systems.

## 🛠️ Troubleshooting

### 1. Bot không kết nối được
```bash
# Kiểm tra C2 server đang chạy
netstat -tlnp | grep 4443

# Kiểm tra firewall
ufw status
iptables -L

# Kiểm tra log
tail -f logs/c2.log
```

### 2. Proxy không hoạt động
```bash
# Kiểm tra có bot nào online không
curl http://<IP_C2>:5001/api/bots

# Kiểm tra kết nối đang hoạt động
curl http://<IP_C2>:5001/api/connections
```

### 3. TLS errors
```bash
# Kiểm tra chứng chỉ
openssl x509 -in cert.pem -text -noout

# Test kết nối TLS
openssl s_client -connect <IP_C2>:4443
```

### 4. Debug logging
```bash
# Tăng mức log
export PYTHONASYNCIODEBUG=1
python3 c2_server.py --config config.json
```

## 📝 Lưu ý

- **Production**: Luôn sử dụng TLS và token mạnh
- **Firewall**: Mở các port cần thiết (4443, 8080, 1080, 5001)
- **Monitoring**: Theo dõi log và sử dụng Web Dashboard
- **Backup**: Backup config file và TLS certificates
- **Updates**: Cập nhật thường xuyên để có security patches

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.