#!/usr/bin/env python3
"""
Bot Security Manager - Quản lý bảo mật cho C2 server
Giúp phân tích, phân loại và xử lý các bot connections
"""

import os
import sys
import time
import json
import socket
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
import ipaddress

class BotSecurityManager:
    def __init__(self, c2_host="localhost", c2_port=7777):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.trusted_ips = set()
        self.blocked_ips = set()
        self.suspicious_ips = set()
        self.bot_analysis = {}
        
    def load_trusted_ips(self, file_path="trusted_ips.txt"):
        """Load danh sách IP đáng tin cậy"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith('#'):
                            self.trusted_ips.add(ip)
                print(f"✅ Loaded {len(self.trusted_ips)} trusted IPs")
            else:
                print("⚠️  No trusted IPs file found")
        except Exception as e:
            print(f"❌ Error loading trusted IPs: {e}")
    
    def save_trusted_ips(self, file_path="trusted_ips.txt"):
        """Save danh sách IP đáng tin cậy"""
        try:
            with open(file_path, 'w') as f:
                f.write("# Trusted IP addresses\n")
                f.write("# Add your trusted IPs here\n")
                for ip in sorted(self.trusted_ips):
                    f.write(f"{ip}\n")
            print(f"✅ Saved {len(self.trusted_ips)} trusted IPs to {file_path}")
        except Exception as e:
            print(f"❌ Error saving trusted IPs: {e}")
    
    def analyze_bot_connection(self, ip: str, port: int) -> Dict:
        """Phân tích kết nối bot"""
        analysis = {
            'ip': ip,
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'is_trusted': ip in self.trusted_ips,
            'is_blocked': ip in self.blocked_ips,
            'is_suspicious': False,
            'risk_level': 'LOW',
            'recommendations': []
        }
        
        # Kiểm tra IP range
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                analysis['ip_type'] = 'Private'
                analysis['risk_level'] = 'MEDIUM'
            elif ip_obj.is_loopback:
                analysis['ip_type'] = 'Loopback'
                analysis['risk_level'] = 'LOW'
            else:
                analysis['ip_type'] = 'Public'
                analysis['risk_level'] = 'HIGH'
                analysis['is_suspicious'] = True
                analysis['recommendations'].append("Public IP - Consider blocking")
        except:
            analysis['ip_type'] = 'Invalid'
            analysis['risk_level'] = 'CRITICAL'
            analysis['is_suspicious'] = True
        
        # Kiểm tra port
        if port not in [7777, 22222]:  # Default C2 ports
            analysis['is_suspicious'] = True
            analysis['recommendations'].append(f"Non-standard port: {port}")
        
        # Kiểm tra geolocation (simplified)
        if analysis['ip_type'] == 'Public':
            analysis['recommendations'].append("Check geolocation")
        
        return analysis
    
    def get_connected_bots(self) -> List[Dict]:
        """Lấy danh sách bots đang kết nối"""
        bots = []
        try:
            # Kết nối đến C2 server để lấy thông tin bots
            # Đây là implementation giả lập - cần modify theo C2 server thực tế
            print("🔍 Scanning for connected bots...")
            
            # Giả lập danh sách bots (thay thế bằng code thực tế)
            sample_bots = [
                {'ip': '192.168.1.100', 'port': 7777, 'status': 'active'},
                {'ip': '10.0.0.50', 'port': 7777, 'status': 'active'},
                {'ip': '203.0.113.1', 'port': 7777, 'status': 'active'},  # Public IP
            ]
            
            for bot in sample_bots:
                analysis = self.analyze_bot_connection(bot['ip'], bot['port'])
                analysis['status'] = bot['status']
                bots.append(analysis)
                
        except Exception as e:
            print(f"❌ Error getting connected bots: {e}")
        
        return bots
    
    def block_ip(self, ip: str, reason: str = "Suspicious activity"):
        """Block IP address"""
        try:
            # Block using iptables
            subprocess.run(['sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], 
                         check=True, capture_output=True)
            self.blocked_ips.add(ip)
            print(f"🚫 Blocked IP {ip}: {reason}")
            
            # Log the action
            self.log_security_action('BLOCK', ip, reason)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to block IP {ip}: {e}")
        except Exception as e:
            print(f"❌ Error blocking IP {ip}: {e}")
    
    def unblock_ip(self, ip: str):
        """Unblock IP address"""
        try:
            # Remove from iptables
            subprocess.run(['sudo', 'iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], 
                         check=True, capture_output=True)
            self.blocked_ips.discard(ip)
            print(f"✅ Unblocked IP {ip}")
            
            # Log the action
            self.log_security_action('UNBLOCK', ip, "Manual unblock")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to unblock IP {ip}: {e}")
        except Exception as e:
            print(f"❌ Error unblocking IP {ip}: {e}")
    
    def disconnect_bot(self, ip: str, port: int):
        """Disconnect specific bot"""
        try:
            # Gửi disconnect command đến bot
            # Implementation depends on C2 server protocol
            print(f"🔌 Disconnecting bot {ip}:{port}")
            
            # Log the action
            self.log_security_action('DISCONNECT', f"{ip}:{port}", "Manual disconnect")
            
        except Exception as e:
            print(f"❌ Error disconnecting bot {ip}:{port}: {e}")
    
    def log_security_action(self, action: str, target: str, reason: str):
        """Log security actions"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'reason': reason
        }
        
        try:
            with open('security_log.json', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging security action: {e}")
    
    def generate_security_report(self, bots: List[Dict]) -> str:
        """Generate security report"""
        report = []
        report.append("=" * 80)
        report.append("🔒 BOT SECURITY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🤖 Total bots: {len(bots)}")
        report.append("")
        
        # Phân loại bots
        trusted_bots = [b for b in bots if b['is_trusted']]
        suspicious_bots = [b for b in bots if b['is_suspicious']]
        blocked_bots = [b for b in bots if b['is_blocked']]
        
        report.append("📊 BOT CLASSIFICATION:")
        report.append(f"  ✅ Trusted: {len(trusted_bots)}")
        report.append(f"  ⚠️  Suspicious: {len(suspicious_bots)}")
        report.append(f"  🚫 Blocked: {len(blocked_bots)}")
        report.append("")
        
        # Chi tiết suspicious bots
        if suspicious_bots:
            report.append("⚠️  SUSPICIOUS BOTS:")
            for bot in suspicious_bots:
                report.append(f"  🔸 {bot['ip']}:{bot['port']} - Risk: {bot['risk_level']}")
                for rec in bot['recommendations']:
                    report.append(f"     💡 {rec}")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        if suspicious_bots:
            report.append("  1. Block suspicious public IPs immediately")
            report.append("  2. Review connection logs")
            report.append("  3. Implement IP whitelist")
            report.append("  4. Enable authentication for bot connections")
        else:
            report.append("  ✅ No suspicious activity detected")
        
        report.append("")
        report.append("=" * 80)
        
        return '\n'.join(report)
    
    def interactive_mode(self):
        """Interactive security management mode"""
        print("🔒 Bot Security Manager - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\n📋 Available commands:")
            print("  1. scan     - Scan connected bots")
            print("  2. block    - Block IP address")
            print("  3. unblock  - Unblock IP address")
            print("  4. report   - Generate security report")
            print("  5. trusted  - Manage trusted IPs")
            print("  6. quit     - Exit")
            
            try:
                command = input("\n🔒 security@c2:~$ ").strip().lower()
                
                if command == "scan":
                    bots = self.get_connected_bots()
                    print(f"\n🤖 Found {len(bots)} connected bots:")
                    for bot in bots:
                        status_icon = "✅" if bot['is_trusted'] else "⚠️" if bot['is_suspicious'] else "🔸"
                        print(f"  {status_icon} {bot['ip']}:{bot['port']} - {bot['risk_level']} risk")
                
                elif command == "block":
                    ip = input("Enter IP to block: ").strip()
                    reason = input("Reason (optional): ").strip() or "Suspicious activity"
                    self.block_ip(ip, reason)
                
                elif command == "unblock":
                    ip = input("Enter IP to unblock: ").strip()
                    self.unblock_ip(ip)
                
                elif command == "report":
                    bots = self.get_connected_bots()
                    report = self.generate_security_report(bots)
                    print(report)
                    
                    # Save report
                    with open(f"security_report_{int(time.time())}.txt", 'w') as f:
                        f.write(report)
                    print("📄 Report saved to file")
                
                elif command == "trusted":
                    print(f"\n📝 Current trusted IPs: {len(self.trusted_ips)}")
                    for ip in sorted(self.trusted_ips):
                        print(f"  ✅ {ip}")
                    
                    action = input("\nAdd (a) or Remove (r) IP? ").strip().lower()
                    if action == 'a':
                        ip = input("Enter IP to add: ").strip()
                        self.trusted_ips.add(ip)
                        self.save_trusted_ips()
                    elif action == 'r':
                        ip = input("Enter IP to remove: ").strip()
                        self.trusted_ips.discard(ip)
                        self.save_trusted_ips()
                
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
    """Main function"""
    print("🚀 Bot Security Manager")
    print("⚠️  For educational/research purposes only!")
    print("")
    
    # Load trusted IPs
    manager = BotSecurityManager()
    manager.load_trusted_ips()
    
    # Start interactive mode
    manager.interactive_mode()

if __name__ == "__main__":
    main()
