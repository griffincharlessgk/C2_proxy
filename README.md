# 🤖 C2 Hybrid Botnet Manager

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Purpose-Research%20Only-red.svg)](#disclaimer)

**Advanced Command & Control (C2) system combining CLI and Web Interface for cybersecurity research and educational purposes.**

## ⚠️ **DISCLAIMER - EDUCATIONAL USE ONLY**

This project is developed **strictly for educational and research purposes**. It is designed to help security professionals, researchers, and students understand:

- How botnet infrastructure works
- Command & Control communication protocols  
- Distributed attack coordination
- Security vulnerability assessment
- Defensive countermeasure development

**🚫 NOT FOR MALICIOUS USE - Use only in authorized, controlled environments**

---

## 🎯 **Features**

### 🌐 **Hybrid Interface**
- **Web Dashboard**: Modern Flask-based interface
- **CLI Management**: Command-line control and monitoring
- **Real-time Communication**: WebSocket-based updates
- **Multi-user Support**: Concurrent operator access

### ⚔️ **Security Testing Capabilities**
- **DDoS Testing**: HTTP/TCP/UDP flood testing
- **Network Scanning**: Port scanning and service detection
- **Vulnerability Assessment**: Security weakness identification
- **System Intelligence**: Target reconnaissance and mapping

### 🤖 **Botnet Simulation**
- **Agent Management**: Simulated bot coordination
- **Command Distribution**: Broadcast commands to multiple agents
- **Result Aggregation**: Collect and analyze test results
- **Performance Monitoring**: Real-time botnet statistics

### 🔧 **Research Tools**
- **Bane Security Framework**: Comprehensive security testing toolkit
- **Malware Distribution**: Sample malware for analysis
- **Attack Coordination**: Distributed testing scenarios
- **Data Collection**: Security assessment reporting

---

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Clone repository
git clone https://github.com/yourusername/C2-Hybrid-Botnet-Manager.git
cd C2-Hybrid-Botnet-Manager

# Install dependencies
sudo apt update
sudo apt install python3-flask python3-socketio python3-bs4 \
                 python3-pymysql python3-future python3-cryptography \
                 python3-psutil python3-requests

# Verify installation
python3 scripts/test_dependencies.py
```

### **2. Quick Start**

```bash
# Navigate to project directory
cd bane/

# Start the hybrid manager
python3 hybrid_botnet_manager.py

# Access web interface
# Open browser: http://localhost:5000
```

### **3. Basic Usage**

```bash
# CLI Commands
help                           # Show available commands
status                        # Display system status  
scan <target> --type <type>   # Security scan
attack <target> --method <m>  # Security testing
web                           # Launch web interface
```

---

## 📁 **Project Structure**

```
C2-Hybrid-Botnet-Manager/
├── bane/                     # Core Bane security framework
│   ├── bane/                 # Security modules
│   │   ├── bruteforce/      # Authentication testing
│   │   ├── cryptographers/  # Encryption utilities  
│   │   ├── ddos/           # Load testing tools
│   │   ├── gather_info/    # Information gathering
│   │   ├── scanners/       # Security scanners
│   │   └── utils/          # Common utilities
│   ├── malware/            # Sample malware for analysis
│   ├── templates/          # Web interface templates
│   └── hybrid_botnet_manager.py  # Main application
├── tests/                  # Test suites
├── scripts/               # Utility scripts
├── requirements.txt       # Dependencies
└── README.md             # This file
```

---

## 🔧 **Configuration**

### **Network Settings**
```json
{
  "c2_host": "0.0.0.0",
  "c2_users_port": 22222,
  "c2_bots_port": 7777,
  "malware_port": 6666,
  "web_port": 5000
}
```

### **Security Options**
- **Encryption**: Optional XOR encryption for communications
- **Authentication**: User authentication for web interface
- **Access Control**: IP-based access restrictions
- **Logging**: Comprehensive activity logging

---

## 🧪 **Testing & Development**

### **Run Tests**
```bash
# Full test suite
python3 tests/run_all_tests.py

# Dependency verification
python3 scripts/test_dependencies.py

# Component testing
python3 scripts/test_malware_server.py
```

### **Development Setup**
```bash
# Create virtual environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install development dependencies (uncomment in requirements.txt)
pip install pytest coverage flake8 black

# Run code quality checks
flake8 bane/
black bane/
```

---

## 📊 **System Requirements**

### **Minimum Requirements**
- **OS**: Linux (Ubuntu 20.04+), Windows 10+, macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 512MB available
- **Storage**: 100MB free space
- **Network**: Internet connection for updates

### **Recommended**
- **RAM**: 2GB+ for optimal performance
- **CPU**: Multi-core for concurrent operations
- **Storage**: 1GB+ for logs and data
- **Network**: High-speed connection for testing

---

## 🛡️ **Security Considerations**

### **Firewall Configuration**
```bash
# Allow necessary ports (configure as needed)
sudo ufw allow 5000/tcp      # Web interface
sudo ufw allow 6666/tcp      # Malware server
sudo ufw allow 22222/tcp     # C2 users
sudo ufw allow 7777/tcp      # C2 bots
```

### **Access Control**
- Use only in isolated, controlled networks
- Implement proper authentication
- Monitor all activities
- Regular security updates

---

## 📚 **Documentation**

### **Technical Documentation**
- [🚀 Deployment Guide](DEPLOYMENT.md)
- [📊 System Status](SYSTEM_STATUS_REPORT.md)  
- [🤖 Malware Analysis](MALWARE_OPERATION_ANALYSIS.md)

### **Research Resources**
- Botnet communication protocols
- Attack vector analysis
- Defense mechanism development
- Security assessment methodologies

---

## 🤝 **Contributing**

### **Development Guidelines**
1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### **Code Standards**
- Follow PEP 8 Python style guide
- Include comprehensive documentation
- Add tests for new features
- Maintain security best practices

---

## 📜 **License**

This project is licensed under the **Educational Use License** - see [LICENSE](LICENSE) file for details.

### **Usage Restrictions**
- ✅ Educational research and learning
- ✅ Security testing in controlled environments  
- ✅ Academic research and analysis
- ❌ Malicious activities or unauthorized access
- ❌ Commercial exploitation
- ❌ Illegal or unethical purposes

---

## 🎓 **Educational Context**

### **Learning Objectives**
- Understand botnet architecture and operation
- Analyze command & control protocols
- Study distributed attack methodologies  
- Develop security countermeasures
- Practice ethical hacking techniques

### **Research Applications**
- Cybersecurity curriculum development
- Security awareness training
- Penetration testing methodologies
- Incident response preparation
- Threat intelligence analysis

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**Dependencies Missing:**
```bash
python3 scripts/test_dependencies.py
sudo apt install python3-flask python3-socketio
```

**Port Conflicts:**
```bash
netstat -tlnp | grep :5000
# Kill conflicting processes or change ports
```

**Permission Errors:**
```bash
chmod +x scripts/*.py
sudo chown -R $USER:$USER /home/ubuntu/C2
```

---

## 📧 **Contact & Support**

### **Research Inquiries**
For academic research collaboration or security research questions, please open an issue in this repository.

### **Security Reports**
If you discover security vulnerabilities in this educational tool, please report them responsibly through GitHub issues.

---

## 🔄 **Version History**

- **v2.0.0** - Complete system optimization and GitHub integration
- **v1.5.0** - Added hybrid web/CLI interface
- **v1.0.0** - Initial Bane framework integration

---

## ⭐ **Acknowledgments**

- **Bane Security Framework** - Core security testing capabilities
- **Flask Community** - Web interface framework
- **Cybersecurity Research Community** - Educational insights and feedback

---

**🎯 Remember: Use responsibly, learn ethically, secure the digital world! 🛡️**