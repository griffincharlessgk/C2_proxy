# C2 Server Monitoring Examples

This document provides examples of how to monitor the C2 server using various monitoring systems.

## Health Check Endpoints

### 1. Basic Health Check
```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "timestamp": 1640995200.0,
  "uptime_seconds": 3600.0,
  "uptime_human": "1h 0m 0s",
  "bots": {
    "total": 3,
    "max": 100,
    "overloaded": 0,
    "list": ["bot_1", "bot_2", "bot_3"]
  },
  "connections": {
    "total": 15,
    "max_per_bot": 50,
    "per_bot": {
      "bot_1": 5,
      "bot_2": 7,
      "bot_3": 3
    }
  },
  "servers": {
    "bot_port": 4443,
    "http_port": 8080,
    "socks_port": 1080,
    "api_port": 5001
  }
}
```

### 2. Detailed Health Check
```bash
curl http://localhost:5001/health/detailed
```

### 3. Kubernetes Readiness Probe
```bash
curl http://localhost:5001/health/ready
```

### 4. Kubernetes Liveness Probe
```bash
curl http://localhost:5001/health/live
```

## Monitoring System Integration

### 1. Nagios/Icinga

**Command Definition:**
```bash
# /etc/nagios/commands.cfg
define command {
    command_name    check_c2_health
    command_line    /usr/local/bin/health_check_client.py --url http://$HOSTADDRESS$:5001 --format nagios
}
```

**Service Definition:**
```bash
# /etc/nagios/services.cfg
define service {
    use                 generic-service
    host_name           c2-server
    service_description C2 Server Health
    check_command       check_c2_health
    check_interval      5
    retry_interval      1
    max_check_attempts  3
}
```

### 2. Prometheus

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'c2-server'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/health'
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Custom Metrics Collection:**
```bash
# Collect metrics every 30 seconds
*/30 * * * * /usr/local/bin/health_check_client.py --url http://localhost:5001 --format prometheus >> /var/log/c2-metrics.log
```

### 3. Zabbix

**User Parameter:**
```bash
# /etc/zabbix/zabbix_agentd.d/c2.conf
UserParameter=c2.health,/usr/local/bin/health_check_client.py --url http://localhost:5001 --format json
```

**Zabbix Template:**
```json
{
  "name": "C2 Server Health",
  "items": [
    {
      "name": "C2 Health Status",
      "key": "c2.health",
      "type": "Zabbix agent",
      "value_type": "Text"
    }
  ],
  "triggers": [
    {
      "name": "C2 Server Down",
      "expression": "find(/C2 Server Health/c2.health,,\"like\",\"healthy\")=0",
      "priority": "High"
    }
  ]
}
```

### 4. Custom Monitoring Script

**Bash Script:**
```bash
#!/bin/bash
# monitor_c2.sh

C2_URL="http://localhost:5001"
LOG_FILE="/var/log/c2-monitor.log"

check_health() {
    local response=$(curl -s -w "%{http_code}" "$C2_URL/health")
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        local status=$(echo "$body" | jq -r '.status')
        local message=$(echo "$body" | jq -r '.message')
        echo "$(date): OK - $status: $message" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): CRITICAL - HTTP $http_code" >> "$LOG_FILE"
        return 2
    fi
}

check_health
```

**Python Script:**
```python
#!/usr/bin/env python3
import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_c2():
    try:
        response = requests.get("http://localhost:5001/health", timeout=10)
        data = response.json()
        
        if data["status"] == "healthy":
            logger.info(f"✅ C2 Server healthy: {data['message']}")
            return 0
        elif data["status"] == "warning":
            logger.warning(f"⚠️ C2 Server warning: {data['message']}")
            return 1
        else:
            logger.error(f"❌ C2 Server degraded: {data['message']}")
            return 2
    except Exception as e:
        logger.error(f"❌ C2 Server check failed: {e}")
        return 2

if __name__ == "__main__":
    exit(monitor_c2())
```

### 5. Docker Health Check

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 health_check_client.py --url http://localhost:5001 --format nagios || exit 1

# Start C2 server
CMD ["python3", "c2_server.py"]
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  c2-server:
    build: .
    ports:
      - "5001:5001"
      - "8080:8080"
      - "1080:1080"
      - "4443:4443"
    healthcheck:
      test: ["CMD", "python3", "health_check_client.py", "--url", "http://localhost:5001"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    environment:
      - BOT_TOKEN=your_bot_token_here
```

### 6. Kubernetes

**Deployment with Health Checks:**
```yaml
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
        - containerPort: 8080
        - containerPort: 1080
        - containerPort: 4443
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Health Check Client Usage

### Basic Usage
```bash
# Human readable format
python3 health_check_client.py

# JSON format
python3 health_check_client.py --format json

# Check specific endpoint
python3 health_check_client.py --endpoint /health/ready

# Check all endpoints
python3 health_check_client.py --all
```

### Advanced Usage
```bash
# Nagios format
python3 health_check_client.py --format nagios

# Prometheus format
python3 health_check_client.py --format prometheus

# Custom URL
python3 health_check_client.py --url http://c2.example.com:5001

# With timeout
python3 health_check_client.py --timeout 30
```

## Alerting Rules

### Prometheus Alerting Rules
```yaml
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

  - alert: C2ServerDegraded
    expr: c2_health_check{status="degraded"} == 1
    for: 30s
    labels:
      severity: warning
    annotations:
      summary: "C2 Server is degraded"
      description: "C2 Server is in degraded state: {{ $value }}"

  - alert: C2ServerNoBots
    expr: c2_bots_total == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "C2 Server has no bots"
      description: "C2 Server has no connected bots for more than 2 minutes"
```

## Troubleshooting

### Common Issues

1. **Health check returns 503**
   - Check if bots are connected
   - Verify connection limits
   - Check server logs

2. **Health check timeout**
   - Increase timeout value
   - Check network connectivity
   - Verify server is running

3. **Inconsistent health status**
   - Check for race conditions
   - Verify bot connection stability
   - Monitor resource usage

### Debug Commands
```bash
# Check server status
curl -v http://localhost:5001/health

# Check detailed status
curl http://localhost:5001/health/detailed | jq

# Check readiness
curl http://localhost:5001/health/ready

# Check liveness
curl http://localhost:5001/health/live

# Test with health check client
python3 health_check_client.py --all --format json
```
