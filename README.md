# C2 Proxy Chain System

Hệ thống C2 (Command and Control) Proxy Chain với kiến trúc modular, hỗ trợ HTTP/SOCKS5 proxy và quản lý bot agents.

## 🏗️ Kiến trúc hệ thống

```
C2 Server (Entry Point)
    ↓
Bot Agents (Exit Nodes)
    ↓
Target Servers
```

## 📁 Cấu trúc thư mục

```
C2/
├── core/                    # Core components
│   ├── protocol/           # Communication protocol
│   ├── server/            # C2 server logic
│   ├── client/            # Bot agent logic
│   └── utils/             # Utilities
├── features/              # Feature modules
│   ├── monitoring/        # Health checks & web dashboard
│   ├── proxy/            # Proxy features
│   └── management/       # Management tools
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/            # End-to-end tests
├── scripts/             # Utility scripts
├── config/              # Configuration files
├── docs/               # Documentation
├── main_c2.py          # C2 server entry point
├── main_bot.py         # Bot agent entry point
└── run_tests.py        # Test runner
```

## 🚀 Quick Start

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Tạo TLS certificates (optional)

```bash
# Tạo self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### 3. Chạy C2 Server

```bash
# Sử dụng entry point
python3 main_c2.py --host 0.0.0.0 --bot-port 4443 --http-port 8080 --socks-port 1080

# Hoặc chạy trực tiếp
python3 core/server/c2_server.py --host 0.0.0.0 --bot-port 4443 --http-port 8080 --socks-port 1080
```

### 4. Chạy Bot Agent

```bash
# Sử dụng entry point
python3 main_bot.py --c2-host 127.0.0.1 --c2-port 4443 --token your_token --bot-id bot_1

# Hoặc chạy trực tiếp
python3 core/client/bot_agent.py --c2-host 127.0.0.1 --c2-port 4443 --token your_token --bot-id bot_1
```

## ⚙️ Configuration

### Config file (config/config.json)

```json
{
  "server": {
    "host": "0.0.0.0",
    "bot_port": 4443,
    "http_port": 8080,
    "socks_port": 1080,
    "api_port": 5001
  },
  "bot": {
    "token": "your_secure_token_here",
    "max_bots": 100,
    "max_connections_per_bot": 10
  },
  "tls": {
    "enabled": false,
    "certfile": "cert.pem",
    "keyfile": "key.pem"
  }
}
```

### Command line overrides

```bash
# Override specific settings
python3 main_c2.py --host 192.168.1.100 --bot-port 5555 --http-port 9090
```

## 🔧 Features

### Core Features
- **HTTP/SOCKS5 Proxy**: Hỗ trợ cả HTTP và SOCKS5 proxy
- **Bot Management**: Quản lý và load balancing bot agents
- **TLS Encryption**: Mã hóa kết nối C2-Bot (optional)
- **Health Monitoring**: Theo dõi trạng thái bot và hệ thống
- **Web Dashboard**: Giao diện web để quản lý

### Advanced Features
- **Connection Limits**: Giới hạn số bot và kết nối
- **Graceful Shutdown**: Tắt hệ thống an toàn
- **Health Check API**: Endpoints cho monitoring systems
- **Modular Architecture**: Kiến trúc modular dễ mở rộng

## 🧪 Testing

### Chạy tất cả tests

```bash
python3 run_tests.py
```

### Chạy tests theo loại

```bash
# Unit tests
python3 run_tests.py --unit

# Integration tests
python3 run_tests.py --integration

# End-to-end tests
python3 run_tests.py --e2e
```

### Test individual components

```bash
# Test protocol
python3 -m pytest tests/unit/test_protocol.py -v

# Test C2-Bot integration
python3 -m pytest tests/integration/test_c2_bot_integration.py -v
```

## 📊 Monitoring

### Health Check Endpoints

```bash
# Basic health
curl http://localhost:5001/health

# Detailed status
curl http://localhost:5001/health/detailed

# Readiness check
curl http://localhost:5001/health/ready

# Liveness check
curl http://localhost:5001/health/live
```

### Web Dashboard

Truy cập: `http://localhost:5001/dashboard`

## 🔒 Security

### Authentication
- Bot agents sử dụng token để xác thực
- C2 server validate token trước khi accept connection

### TLS/SSL
- Hỗ trợ TLS encryption cho C2-Bot communication
- Self-signed certificates hoặc CA-signed certificates

### Connection Limits
- Giới hạn số bot tối đa
- Giới hạn số kết nối per bot
- Prevent DoS attacks

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - Chi tiết kiến trúc hệ thống
- [API Reference](docs/API.md) - Tài liệu API endpoints
- [Configuration](docs/CONFIG.md) - Hướng dẫn cấu hình
- [Monitoring](docs/MONITORING.md) - Hướng dẫn monitoring

## 🛠️ Development

### Project Setup

```bash
# Clone repository
git clone <repository-url>
cd C2

# Install dependencies
pip install -r requirements.txt

# Run setup script
python3 setup.py
```

### Code Structure

- **`core/`**: Core components (protocol, server, client, utils)
- **`features/`**: Feature modules (monitoring, proxy, management)
- **`tests/`**: Test suite (unit, integration, e2e)
- **`scripts/`**: Utility scripts
- **`config/`**: Configuration files

### Adding New Features

1. Tạo module trong `features/`
2. Viết tests trong `tests/`
3. Update documentation
4. Test integration

## 🚨 Troubleshooting

### Common Issues

1. **Import errors**: Đảm bảo chạy từ project root hoặc sử dụng entry points
2. **Connection refused**: Kiểm tra firewall và port availability
3. **TLS errors**: Kiểm tra certificate files và permissions
4. **Bot not connecting**: Kiểm tra token và network connectivity

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 main_c2.py --host 0.0.0.0 --bot-port 4443
```

## 📄 License

[License information]

## 🤝 Contributing

[Contributing guidelines]

## 📞 Support

[Support information]