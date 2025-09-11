# Configuration Guide

Hướng dẫn cấu hình C2 Proxy Chain System.

## 📋 Overview

Hệ thống sử dụng file cấu hình JSON để quản lý các settings. Có thể override bằng command line arguments.

## ⚙️ Configuration File

### Location

```
config/config.json
```

### Template

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
  },
  "logging": {
    "level": "INFO",
    "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
  },
  "timeouts": {
    "connection_timeout": 30,
    "heartbeat_interval": 30,
    "heartbeat_timeout": 60
  },
  "limits": {
    "buffer_size": 4096,
    "max_request_size": 1048576
  }
}
```

## 🔧 Configuration Sections

### Server Configuration

```json
{
  "server": {
    "host": "0.0.0.0",        // Server bind address
    "bot_port": 4443,         // Port for bot connections
    "http_port": 8080,        // HTTP proxy port
    "socks_port": 1080,       // SOCKS5 proxy port
    "api_port": 5001          // API/Web dashboard port
  }
}
```

**Options:**
- `host`: IP address to bind server (0.0.0.0 for all interfaces)
- `bot_port`: Port for bot agents to connect
- `http_port`: Port for HTTP proxy clients
- `socks_port`: Port for SOCKS5 proxy clients
- `api_port`: Port for API and web dashboard

### Bot Configuration

```json
{
  "bot": {
    "token": "your_secure_token_here",
    "max_bots": 100,
    "max_connections_per_bot": 10
  }
}
```

**Options:**
- `token`: Authentication token for bot agents
- `max_bots`: Maximum number of bots allowed
- `max_connections_per_bot`: Maximum connections per bot

### TLS Configuration

```json
{
  "tls": {
    "enabled": false,
    "certfile": "cert.pem",
    "keyfile": "key.pem"
  }
}
```

**Options:**
- `enabled`: Enable TLS encryption
- `certfile`: Path to TLS certificate file
- `keyfile`: Path to TLS private key file

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
  }
}
```

**Options:**
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `format`: Log message format

### Timeouts Configuration

```json
{
  "timeouts": {
    "connection_timeout": 30,
    "heartbeat_interval": 30,
    "heartbeat_timeout": 60
  }
}
```

**Options:**
- `connection_timeout`: Connection timeout in seconds
- `heartbeat_interval`: Heartbeat interval in seconds
- `heartbeat_timeout`: Heartbeat timeout in seconds

### Limits Configuration

```json
{
  "limits": {
    "buffer_size": 4096,
    "max_request_size": 1048576
  }
}
```

**Options:**
- `buffer_size`: Buffer size for data transfer
- `max_request_size`: Maximum request size in bytes

## 🚀 Command Line Overrides

### C2 Server

```bash
python3 main_c2.py [options]

Options:
  --config CONFIG       Config file path
  --host HOST           Override host
  --bot-port BOT_PORT   Override bot port
  --http-port HTTP_PORT Override HTTP port
  --socks-port SOCKS_PORT Override SOCKS port
  --api-port API_PORT   Override API port
  --bot-token BOT_TOKEN Override bot token
  --tls-enabled         Enable TLS
  --certfile CERTFILE   TLS certificate file
  --keyfile KEYFILE     TLS key file
```

**Examples:**
```bash
# Override specific settings
python3 main_c2.py --host 192.168.1.100 --bot-port 5555

# Use custom config file
python3 main_c2.py --config /path/to/custom.json

# Enable TLS
python3 main_c2.py --tls-enabled --certfile cert.pem --keyfile key.pem
```

### Bot Agent

```bash
python3 main_bot.py [options]

Options:
  --c2-host C2_HOST     C2 server host
  --c2-port C2_PORT     C2 server port
  --token TOKEN         Bot authentication token
  --bot-id BOT_ID       Bot ID (auto-generated if not provided)
  --config CONFIG       Config file path
  --tls                 Enable TLS connection
```

**Examples:**
```bash
# Basic connection
python3 main_bot.py --c2-host 127.0.0.1 --c2-port 4443 --token your_token

# With custom bot ID
python3 main_bot.py --c2-host 127.0.0.1 --c2-port 4443 --token your_token --bot-id my_bot

# With TLS
python3 main_bot.py --c2-host 127.0.0.1 --c2-port 4443 --token your_token --tls
```

## 🔐 Security Configuration

### Token Generation

```bash
# Generate secure token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### TLS Certificate Generation

```bash
# Self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# With specific subject
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

### Firewall Configuration

```bash
# Allow bot port
sudo ufw allow 4443

# Allow proxy ports
sudo ufw allow 8080
sudo ufw allow 1080

# Allow API port
sudo ufw allow 5001
```

## 🌍 Environment Variables

### C2 Server

```bash
export C2_HOST=0.0.0.0
export C2_BOT_PORT=4443
export C2_HTTP_PORT=8080
export C2_SOCKS_PORT=1080
export C2_API_PORT=5001
export C2_BOT_TOKEN=your_token_here
export C2_TLS_ENABLED=false
export C2_CERTFILE=cert.pem
export C2_KEYFILE=key.pem
```

### Bot Agent

```bash
export BOT_C2_HOST=127.0.0.1
export BOT_C2_PORT=4443
export BOT_TOKEN=your_token_here
export BOT_ID=my_bot
export BOT_TLS_ENABLED=false
```

## 📊 Monitoring Configuration

### Health Check Endpoints

```json
{
  "monitoring": {
    "health_check_interval": 30,
    "health_check_timeout": 5,
    "enable_detailed_health": true
  }
}
```

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    "file": "/var/log/c2-server.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## 🔄 Configuration Reload

### API Reload

```bash
# Reload configuration via API
curl -X POST http://localhost:5001/api/config/reload
```

### Signal Reload

```bash
# Send SIGHUP to reload config
kill -HUP <pid>
```

## 🧪 Configuration Testing

### Validate Configuration

```bash
# Test configuration file
python3 -c "
import json
with open('config/config.json', 'r') as f:
    config = json.load(f)
    print('Configuration is valid')
"
```

### Test Connection

```bash
# Test C2 server startup
python3 main_c2.py --config config/config.json --dry-run

# Test bot connection
python3 main_bot.py --c2-host 127.0.0.1 --c2-port 4443 --token test_token --test-connection
```

## 📝 Configuration Examples

### Development

```json
{
  "server": {
    "host": "127.0.0.1",
    "bot_port": 4443,
    "http_port": 8080,
    "socks_port": 1080,
    "api_port": 5001
  },
  "bot": {
    "token": "dev_token_123",
    "max_bots": 10,
    "max_connections_per_bot": 5
  },
  "tls": {
    "enabled": false
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

### Production

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
    "token": "prod_secure_token_here",
    "max_bots": 1000,
    "max_connections_per_bot": 50
  },
  "tls": {
    "enabled": true,
    "certfile": "/etc/ssl/certs/c2-server.crt",
    "keyfile": "/etc/ssl/private/c2-server.key"
  },
  "logging": {
    "level": "INFO",
    "file": "/var/log/c2-server.log"
  }
}
```

### High Security

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
    "token": "ultra_secure_token_here",
    "max_bots": 100,
    "max_connections_per_bot": 10
  },
  "tls": {
    "enabled": true,
    "certfile": "/etc/ssl/certs/c2-server.crt",
    "keyfile": "/etc/ssl/private/c2-server.key"
  },
  "security": {
    "ip_whitelist": ["192.168.1.0/24", "10.0.0.0/8"],
    "rate_limit": {
      "enabled": true,
      "requests_per_minute": 100
    }
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/c2-server.log",
    "audit_log": "/var/log/c2-audit.log"
  }
}
```

## 🚨 Troubleshooting

### Common Configuration Issues

1. **Port conflicts**: Check if ports are already in use
2. **Permission errors**: Ensure proper file permissions
3. **Invalid JSON**: Validate JSON syntax
4. **Missing files**: Check file paths and existence

### Debug Configuration

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 main_c2.py --config config/config.json

# Test specific configuration
python3 -c "
from core.utils.config import load_config, validate_config
config = load_config('config/config.json')
validate_config(config)
print('Configuration loaded successfully')
"
```
