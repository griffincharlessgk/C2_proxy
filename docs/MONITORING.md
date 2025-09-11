# Monitoring Guide

Hướng dẫn monitoring và health checks cho C2 Proxy Chain System.

## 📊 Overview

Hệ thống cung cấp các endpoints và tools để monitor:
- Health status
- Bot connections
- System performance
- Connection statistics
- Error rates

## 🏥 Health Check Endpoints

### Basic Health Check

```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-11T11:30:00Z",
  "uptime": "2h 15m 30s"
}
```

### Detailed Health Check

```bash
curl http://localhost:5001/health/detailed
```

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

### Readiness Check

```bash
curl http://localhost:5001/health/ready
```

**Response:**
```json
{
  "ready": true,
  "reason": "All systems operational"
}
```

### Liveness Check

```bash
curl http://localhost:5001/health/live
```

**Response:**
```json
{
  "alive": true,
  "timestamp": "2025-09-11T11:30:00Z"
}
```

## 📈 System Statistics

### Get System Stats

```bash
curl http://localhost:5001/api/stats
```

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

### Get Connection Stats

```bash
curl http://localhost:5001/api/stats/connections
```

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

## 🤖 Bot Management

### List All Bots

```bash
curl http://localhost:5001/api/bots
```

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

### Get Bot Details

```bash
curl http://localhost:5001/api/bots/bot_1
```

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

## 🌐 Web Dashboard

### Access Dashboard

Truy cập: `http://localhost:5001/dashboard`

**Features:**
- Real-time bot status
- Connection statistics
- System health
- Configuration overview
- Logs viewer

### Dashboard API

```bash
# Get dashboard data
curl http://localhost:5001/api/dashboard

# Get real-time updates
curl http://localhost:5001/api/dashboard/stream
```

## 🔧 Monitoring Scripts

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

C2_HOST="localhost"
C2_PORT="5001"

# Basic health check
echo "Checking C2 server health..."
curl -s "http://${C2_HOST}:${C2_PORT}/health" | jq '.'

# Detailed health check
echo "Getting detailed health info..."
curl -s "http://${C2_HOST}:${C2_PORT}/health/detailed" | jq '.'

# Bot status
echo "Checking bot status..."
curl -s "http://${C2_HOST}:${C2_PORT}/api/bots" | jq '.bots[] | {id, status, connections}'
```

### System Stats Script

```bash
#!/bin/bash
# system_stats.sh

C2_HOST="localhost"
C2_PORT="5001"

echo "=== C2 Server Statistics ==="
curl -s "http://${C2_HOST}:${C2_PORT}/api/stats" | jq '.'

echo "=== Connection Statistics ==="
curl -s "http://${C2_HOST}:${C2_PORT}/api/stats/connections" | jq '.'

echo "=== Bot Status ==="
curl -s "http://${C2_HOST}:${C2_PORT}/api/bots" | jq '.bots[] | {id, status, connections, last_heartbeat}'
```

## 📊 Prometheus Integration

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'c2-server'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "C2 Server Monitoring",
    "panels": [
      {
        "title": "Bot Status",
        "type": "stat",
        "targets": [
          {
            "expr": "c2_bots_connected",
            "legendFormat": "Connected Bots"
          }
        ]
      },
      {
        "title": "Connection Count",
        "type": "graph",
        "targets": [
          {
            "expr": "c2_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

## 🐳 Docker Monitoring

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  c2-server:
    image: c2-server:latest
    ports:
      - "5001:5001"
      - "8080:8080"
      - "1080:1080"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Kubernetes Monitoring

```yaml
# k8s-monitoring.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: c2-monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'c2-server'
        static_configs:
          - targets: ['c2-server:5001']
        metrics_path: '/metrics'
        scrape_interval: 30s

---
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

## 📝 Log Monitoring

### Log Files

```bash
# C2 server logs
tail -f /var/log/c2-server.log

# Bot agent logs
tail -f /var/log/bot-agent.log

# System logs
journalctl -u c2-server -f
```

### Log Analysis

```bash
# Count errors
grep "ERROR" /var/log/c2-server.log | wc -l

# Find connection issues
grep "connection" /var/log/c2-server.log | grep "ERROR"

# Monitor bot connections
grep "bot.*connected" /var/log/c2-server.log
```

## 🚨 Alerting

### Alert Rules

```yaml
# alert-rules.yml
groups:
  - name: c2-server
    rules:
      - alert: C2ServerDown
        expr: up{job="c2-server"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "C2 Server is down"
          description: "C2 Server has been down for more than 1 minute"

      - alert: HighConnectionCount
        expr: c2_connections_active > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High connection count"
          description: "Connection count is {{ $value }}, which is above 80"

      - alert: BotDisconnected
        expr: c2_bots_connected < 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "No bots connected"
          description: "No bots are currently connected to the C2 server"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@example.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/api/alerts'
        send_resolved: true
```

## 🔍 Troubleshooting

### Common Issues

1. **Health check fails**: Check if server is running and accessible
2. **Bot not connecting**: Verify token and network connectivity
3. **High connection count**: Check for connection leaks
4. **Dashboard not loading**: Verify API endpoints are working

### Debug Commands

```bash
# Check server status
curl -v http://localhost:5001/health

# Check bot connections
curl -s http://localhost:5001/api/bots | jq '.'

# Check system resources
curl -s http://localhost:5001/api/system/status | jq '.'

# Test connectivity
telnet localhost 5001
```

### Performance Monitoring

```bash
# Monitor CPU usage
top -p $(pgrep -f "python.*main_c2.py")

# Monitor memory usage
ps aux | grep "python.*main_c2.py"

# Monitor network connections
netstat -tulpn | grep :5001
ss -tulpn | grep :5001
```

## 📊 Metrics Collection

### Custom Metrics

```python
# Example custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Bot metrics
bots_connected = Gauge('c2_bots_connected', 'Number of connected bots')
bots_total = Gauge('c2_bots_total', 'Total number of bots')

# Connection metrics
connections_active = Gauge('c2_connections_active', 'Active connections')
connections_total = Counter('c2_connections_total', 'Total connections')

# Request metrics
requests_total = Counter('c2_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('c2_request_duration_seconds', 'Request duration')
```

### Metrics Endpoint

```bash
# Get Prometheus metrics
curl http://localhost:5001/metrics
```

## 🎯 Best Practices

### Monitoring Setup

1. **Set up health checks** for all components
2. **Configure alerts** for critical issues
3. **Monitor resource usage** (CPU, memory, network)
4. **Track performance metrics** (response times, throughput)
5. **Log all important events** for debugging

### Alerting Strategy

1. **Critical alerts** for system down
2. **Warning alerts** for high resource usage
3. **Info alerts** for important events
4. **Escalation policies** for unhandled alerts

### Dashboard Design

1. **Overview panel** with key metrics
2. **Bot status panel** with connection details
3. **Performance panel** with response times
4. **Error panel** with error rates and logs
5. **Resource panel** with CPU/memory usage
