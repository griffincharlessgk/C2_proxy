# API Reference

Tài liệu API endpoints cho C2 Proxy Chain System.

## 📋 Overview

C2 Server cung cấp các API endpoints để:
- Health monitoring
- Bot management
- System statistics
- Configuration management

## 🔗 Base URL

```
http://localhost:5001
```

## 🏥 Health Check Endpoints

### GET /health

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-11T11:30:00Z",
  "uptime": "2h 15m 30s"
}
```

**Status Codes:**
- `200` - Healthy
- `503` - Unhealthy

### GET /health/detailed

Detailed health information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-11T11:30:00Z",
  "uptime": "2h 15m 30s",
  "bots": {
    "total": 3,
    "connected": 2,
    "disconnected": 1
  },
  "connections": {
    "total": 15,
    "active": 12,
    "max_per_bot": 10
  },
  "limits": {
    "max_bots": 100,
    "max_connections_per_bot": 10
  }
}
```

### GET /health/ready

Readiness check for Kubernetes/load balancers.

**Response:**
```json
{
  "ready": true,
  "reason": "All systems operational"
}
```

**Status Codes:**
- `200` - Ready
- `503` - Not ready

### GET /health/live

Liveness check for Kubernetes/load balancers.

**Response:**
```json
{
  "alive": true,
  "timestamp": "2025-09-11T11:30:00Z"
}
```

**Status Codes:**
- `200` - Alive
- `503` - Not alive

## 🤖 Bot Management Endpoints

### GET /api/bots

List all connected bots.

**Response:**
```json
{
  "bots": [
    {
      "id": "bot_1",
      "status": "connected",
      "connected_at": "2025-09-11T09:15:00Z",
      "last_heartbeat": "2025-09-11T11:29:45Z",
      "connections": 5,
      "max_connections": 10
    },
    {
      "id": "bot_2",
      "status": "connected",
      "connected_at": "2025-09-11T09:20:00Z",
      "last_heartbeat": "2025-09-11T11:29:50Z",
      "connections": 3,
      "max_connections": 10
    }
  ]
}
```

### GET /api/bots/{bot_id}

Get specific bot information.

**Parameters:**
- `bot_id` (string): Bot identifier

**Response:**
```json
{
  "id": "bot_1",
  "status": "connected",
  "connected_at": "2025-09-11T09:15:00Z",
  "last_heartbeat": "2025-09-11T11:29:45Z",
  "connections": 5,
  "max_connections": 10,
  "client_info": {
    "remote_addr": "192.168.1.100",
    "user_agent": "BotAgent/1.0"
  }
}
```

**Status Codes:**
- `200` - Bot found
- `404` - Bot not found

### POST /api/bots/{bot_id}/disconnect

Disconnect a specific bot.

**Parameters:**
- `bot_id` (string): Bot identifier

**Response:**
```json
{
  "success": true,
  "message": "Bot bot_1 disconnected"
}
```

**Status Codes:**
- `200` - Bot disconnected
- `404` - Bot not found

## 📊 Statistics Endpoints

### GET /api/stats

Get system statistics.

**Response:**
```json
{
  "system": {
    "uptime": "2h 15m 30s",
    "start_time": "2025-09-11T09:15:00Z",
    "version": "1.0.0"
  },
  "bots": {
    "total": 3,
    "connected": 2,
    "disconnected": 1
  },
  "connections": {
    "total": 15,
    "active": 12,
    "max_per_bot": 10
  },
  "proxy": {
    "http_requests": 1250,
    "socks_requests": 890,
    "total_requests": 2140
  }
}
```

### GET /api/stats/connections

Get connection statistics.

**Response:**
```json
{
  "total_connections": 15,
  "active_connections": 12,
  "connections_by_bot": {
    "bot_1": 5,
    "bot_2": 3,
    "bot_3": 4
  },
  "connection_history": {
    "last_hour": 45,
    "last_day": 1200
  }
}
```

## ⚙️ Configuration Endpoints

### GET /api/config

Get current configuration.

**Response:**
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
    "max_bots": 100,
    "max_connections_per_bot": 10
  },
  "tls": {
    "enabled": false
  }
}
```

### POST /api/config/reload

Reload configuration from file.

**Response:**
```json
{
  "success": true,
  "message": "Configuration reloaded successfully"
}
```

## 🔧 System Endpoints

### POST /api/system/shutdown

Gracefully shutdown the system.

**Response:**
```json
{
  "success": true,
  "message": "Shutdown initiated"
}
```

### GET /api/system/status

Get system status.

**Response:**
```json
{
  "status": "running",
  "uptime": "2h 15m 30s",
  "memory_usage": "45.2MB",
  "cpu_usage": "12.5%"
}
```

## 📝 Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "timestamp": "2025-09-11T11:30:00Z"
}
```

**Common Error Codes:**
- `INVALID_REQUEST` - Invalid request parameters
- `BOT_NOT_FOUND` - Bot not found
- `CONNECTION_LIMIT_EXCEEDED` - Connection limit exceeded
- `SYSTEM_ERROR` - Internal system error

## 🔐 Authentication

Currently, API endpoints do not require authentication. In production, consider implementing:
- API key authentication
- JWT tokens
- IP whitelisting

## 📊 Rate Limiting

API endpoints are not rate-limited by default. Consider implementing rate limiting for production use.

## 🧪 Testing

### Using curl

```bash
# Health check
curl http://localhost:5001/health

# Detailed health
curl http://localhost:5001/health/detailed

# List bots
curl http://localhost:5001/api/bots

# Get bot info
curl http://localhost:5001/api/bots/bot_1

# System stats
curl http://localhost:5001/api/stats
```

### Using Python

```python
import requests

# Health check
response = requests.get('http://localhost:5001/health')
print(response.json())

# List bots
response = requests.get('http://localhost:5001/api/bots')
print(response.json())
```

## 📈 Monitoring Integration

### Prometheus

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'c2-server'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboard

Import dashboard JSON for C2 server metrics visualization.

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: c2-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app: c2-server
  template:
    metadata:
      labels:
        app: c2-server
    spec:
      containers:
      - name: c2-server
        image: c2-server:latest
        ports:
        - containerPort: 5001
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5
```
