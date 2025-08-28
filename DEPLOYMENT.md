# Deployment Guide - C2 Hybrid Botnet Management System

> ⚠️ **For Educational/Research Purposes Only**  
> Only deploy in controlled environments with explicit permission.

## 🎯 Deployment Overview

This guide covers deploying the C2 Hybrid Botnet Management System for:
- Educational environments
- Authorized penetration testing
- Security research labs
- Academic studies

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 10GB free space
- **Network**: Static IP preferred

### Recommended for Production Testing
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **Network**: Dedicated server/VPS

## 📦 Installation Steps

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git

# Install system dependencies for Bane
sudo apt install -y sshpass tor

# Create dedicated user (recommended)
sudo useradd -m -s /bin/bash c2user
sudo usermod -aG sudo c2user
```

### 2. Download and Setup

```bash
# Switch to c2user (if created)
sudo su - c2user

# Clone repository
git clone <repository-url> C2
cd C2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Bane library
cd bane
pip install -e .
cd ..
```

### 3. Configuration

```bash
# Copy configuration template
cd bane
cp config_template.json botnet_config.json

# Edit configuration
nano botnet_config.json
```

**Key Configuration Settings:**

```json
{
  "c2_host": "YOUR_SERVER_IP",
  "c2_users_port": 22222,
  "c2_bots_port": 7777,
  "web_port": 5000,
  "encryption_key": "STRONG_ENCRYPTION_KEY_HERE",
  "max_users": 10,
  "max_bots": 1000,
  "security": {
    "enable_encryption": true,
    "max_login_attempts": 3,
    "session_timeout": 3600
  }
}
```

### 4. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow C2 ports (adjust as needed)
sudo ufw allow 5000/tcp    # Web interface
sudo ufw allow 22222/tcp   # C2 users port
sudo ufw allow 7777/tcp    # C2 bots port
sudo ufw allow 6666/tcp    # Malware server port

# Check status
sudo ufw status
```

### 5. Testing Installation

```bash
# Run test suite
cd tests
python3 run_all_tests.py

# Test basic functionality
cd ../bane
python3 -c "from hybrid_botnet_manager import HybridBotnetManager; print('✅ Import successful')"
```

## 🚀 Running the System

### 1. CLI Mode (Recommended for testing)

```bash
cd bane
python3 hybrid_botnet_manager.py --cli
```

### 2. Web Interface Mode

```bash
cd bane
python3 hybrid_botnet_manager.py --web
```

### 3. Hybrid Mode (Both CLI and Web)

```bash
cd bane
python3 hybrid_botnet_manager.py
```

### 4. Background Service

Create systemd service for production:

```bash
# Create service file
sudo nano /etc/systemd/system/c2-manager.service
```

```ini
[Unit]
Description=C2 Hybrid Botnet Manager
After=network.target

[Service]
Type=simple
User=c2user
WorkingDirectory=/home/c2user/C2/bane
Environment=PATH=/home/c2user/C2/venv/bin
ExecStart=/home/c2user/C2/venv/bin/python hybrid_botnet_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable c2-manager
sudo systemctl start c2-manager

# Check status
sudo systemctl status c2-manager
```

## 🔧 Advanced Configuration

### TOR Integration

```bash
# Configure TOR
sudo nano /etc/tor/torrc

# Add these lines:
SocksPort 9050
ControlPort 9051
CookieAuthentication 1

# Restart TOR
sudo systemctl restart tor
```

### Proxy Configuration

```bash
# For proxy support, configure in botnet_config.json:
{
  "proxy": {
    "enabled": true,
    "type": "socks5",
    "host": "127.0.0.1",
    "port": 9050
  }
}
```

### SSL/TLS Setup

```bash
# Generate SSL certificates for web interface
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update config to use SSL
{
  "web_ssl": {
    "enabled": true,
    "cert_file": "cert.pem",
    "key_file": "key.pem"
  }
}
```

## 📊 Monitoring and Logging

### Log Configuration

```bash
# Create log directory
mkdir -p /home/c2user/C2/logs

# Configure log rotation
sudo nano /etc/logrotate.d/c2-manager
```

```
/home/c2user/C2/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### System Monitoring

```bash
# Monitor system resources
htop

# Monitor network connections
netstat -tlnp | grep python

# Monitor logs
tail -f logs/c2_manager.log
```

## 🛡️ Security Hardening

### 1. System Security

```bash
# Disable root SSH
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 2. Application Security

```bash
# Set proper file permissions
chmod 600 botnet_config.json
chmod -R 750 /home/c2user/C2
```

### 3. Network Security

```bash
# Use VPN for additional security
# Configure iptables for advanced filtering
# Monitor network traffic with tcpdump/wireshark
```

## 🔄 Backup and Recovery

### Backup Script

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/c2-$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup configuration
cp /home/c2user/C2/bane/botnet_config.json $BACKUP_DIR/

# Backup logs
cp -r /home/c2user/C2/logs $BACKUP_DIR/

# Create archive
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR
```

### Recovery Process

```bash
# Stop service
sudo systemctl stop c2-manager

# Restore from backup
tar -xzf backup-file.tar.gz
cp backup/botnet_config.json /home/c2user/C2/bane/

# Restart service
sudo systemctl start c2-manager
```

## ⚠️ Troubleshooting

### Common Issues

1. **Port binding errors**
   ```bash
   # Check what's using the port
   sudo netstat -tlnp | grep :5000
   # Kill the process or change port
   ```

2. **Permission errors**
   ```bash
   # Fix ownership
   sudo chown -R c2user:c2user /home/c2user/C2
   ```

3. **Module import errors**
   ```bash
   # Reinstall Bane library
   cd bane
   pip install -e . --force-reinstall
   ```

4. **TOR connection issues**
   ```bash
   # Restart TOR service
   sudo systemctl restart tor
   # Check TOR status
   sudo systemctl status tor
   ```

### Performance Optimization

```bash
# Increase file descriptor limits
echo "c2user soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "c2user hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 65536" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 📋 Checklist

Before going live, ensure:

- [ ] All tests pass (`python3 run_all_tests.py`)
- [ ] Firewall properly configured
- [ ] SSL certificates installed (if using HTTPS)
- [ ] Logs directory writable
- [ ] Configuration file secured (600 permissions)
- [ ] Backup procedures in place
- [ ] Monitoring tools configured
- [ ] Legal authorization obtained
- [ ] Incident response plan ready

## 🚨 Emergency Procedures

### Immediate Shutdown

```bash
# Emergency stop
sudo systemctl stop c2-manager
sudo pkill -f hybrid_botnet_manager

# Block all traffic
sudo ufw reset
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default deny outgoing
```

### Forensic Mode

```bash
# Preserve logs
cp -r logs logs-forensic-$(date +%Y%m%d-%H%M%S)

# Create memory dump (if needed)
sudo dd if=/dev/mem of=memory-dump-$(date +%Y%m%d-%H%M%S).img

# Document incident
echo "Incident at $(date): [description]" >> incident.log
```

## 📞 Support

For deployment issues:
1. Check logs first: `tail -f logs/c2_manager.log`
2. Run diagnostics: `python3 run_all_tests.py`
3. Review system resources: `htop` and `df -h`
4. Check network connectivity: `netstat -tlnp`

Remember: This system is for authorized educational/research use only! 🛡️