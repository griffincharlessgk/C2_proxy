#!/usr/bin/env python3
"""
Bot Monitor - Monitor và xử lý bot connections
"""

import os
import sys
import time
import json
import socket
import threading
from datetime import datetime
from typing import Dict, List, Set
import subprocess

class BotMonitor:
    def __init__(self, c2_port=7777):
        self.c2_port = c2_port
        self.connected_bots = {}
        self.trusted_ips = set()
        self.blocked_ips = set()
        self.suspicious_ips = set()
        self.monitoring = False
        self.log_file = "bot_monitor.log"
        
    def load_trusted_ips(self):
        """Load trusted IPs from file"""
        try:
            if os.path.exists("trusted_ips.txt"):
                with open("trusted_ips.txt", 'r') as f:
                    for line in f:
                        ip = line.strip()
                        if ip and not ip.startswith('#'):
                            self.trusted_ips.add(ip)
                print(f"✅ Loaded {len(self.trusted_ips)} trusted IPs")
        except Exception as e:
            print(f"❌ Error loading trusted IPs: {e}")
    
    def is_ip_trusted(self, ip: str) -> bool:
        """Check if IP is trusted"""
        return ip in self.trusted_ips
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips
    
    def block_ip_immediately(self, ip: str, reason: str = "Suspicious activity"):
        """Block IP immediately using iptables"""
        try:
            # Block using iptables
            result = subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.log_action(f"BLOCKED", ip, reason)
                print(f"🚫 Blocked IP {ip}: {reason}")
                return True
            else:
                print(f"❌ Failed to block IP {ip}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error blocking IP {ip}: {e}")
            return False
    
    def disconnect_bot(self, ip: str, port: int):
        """Disconnect bot by killing connection"""
        try:
            # Find and kill connection
            result = subprocess.run([
                'sudo', 'netstat', '-tulpn'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port}" in line and ip in line:
                        # Extract PID and kill connection
                        parts = line.split()
                        if len(parts) > 6:
                            pid_info = parts[6]
                            if '/' in pid_info:
                                pid = pid_info.split('/')[0]
                                subprocess.run(['sudo', 'kill', '-9', pid])
                                print(f"🔌 Disconnected bot {ip}:{port} (PID: {pid})")
                                return True
            
            print(f"⚠️  Could not find connection for {ip}:{port}")
            return False
            
        except Exception as e:
            print(f"❌ Error disconnecting bot {ip}:{port}: {e}")
            return False
    
    def analyze_connection(self, ip: str, port: int) -> Dict:
        """Analyze bot connection"""
        analysis = {
            'ip': ip,
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'is_trusted': self.is_ip_trusted(ip),
            'is_blocked': self.is_ip_blocked(ip),
            'risk_level': 'LOW',
            'action_taken': None,
            'recommendations': []
        }
        
        # Risk assessment
        if analysis['is_trusted']:
            analysis['risk_level'] = 'LOW'
        elif analysis['is_blocked']:
            analysis['risk_level'] = 'CRITICAL'
            analysis['action_taken'] = 'ALREADY_BLOCKED'
        else:
            # Check if it's a private IP
            try:
                import ipaddress
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    analysis['risk_level'] = 'MEDIUM'
                    analysis['recommendations'].append("Private IP - Monitor closely")
                else:
                    analysis['risk_level'] = 'HIGH'
                    analysis['recommendations'].append("Public IP - Consider blocking")
                    analysis['recommendations'].append("Immediate action recommended")
            except:
                analysis['risk_level'] = 'CRITICAL'
                analysis['recommendations'].append("Invalid IP format")
        
        return analysis
    
    def log_action(self, action: str, target: str, details: str):
        """Log security action"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'details': details
        }
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging action: {e}")
    
    def scan_connections(self) -> List[Dict]:
        """Scan for active connections"""
        connections = []
        
        try:
            # Use netstat to find connections
            result = subprocess.run([
                'netstat', '-tulpn'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{self.c2_port}" in line and "ESTABLISHED" in line:
                        # Parse connection info
                        parts = line.split()
                        if len(parts) >= 4:
                            local_addr = parts[3]
                            remote_addr = parts[4]
                            
                            if ':' in remote_addr:
                                ip, port = remote_addr.rsplit(':', 1)
                                try:
                                    port = int(port)
                                    analysis = self.analyze_connection(ip, port)
                                    connections.append(analysis)
                                except ValueError:
                                    continue
            
        except Exception as e:
            print(f"❌ Error scanning connections: {e}")
        
        return connections
    
    def auto_security_response(self, connections: List[Dict]):
        """Automatic security response"""
        for conn in connections:
            if conn['risk_level'] == 'CRITICAL' and not conn['is_blocked']:
                # Block immediately
                if self.block_ip_immediately(conn['ip'], "High risk connection"):
                    conn['action_taken'] = 'BLOCKED'
                    self.disconnect_bot(conn['ip'], conn['port'])
            
            elif conn['risk_level'] == 'HIGH' and not conn['is_trusted']:
                # Disconnect and flag for review
                if self.disconnect_bot(conn['ip'], conn['port']):
                    conn['action_taken'] = 'DISCONNECTED'
                    self.log_action("DISCONNECTED", f"{conn['ip']}:{conn['port']}", "High risk - disconnected")
    
    def generate_report(self, connections: List[Dict]) -> str:
        """Generate monitoring report"""
        report = []
        report.append("=" * 80)
        report.append("🤖 BOT CONNECTION MONITORING REPORT")
        report.append("=" * 80)
        report.append(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"🔍 Port: {self.c2_port}")
        report.append(f"🤖 Total connections: {len(connections)}")
        report.append("")
        
        # Categorize connections
        trusted = [c for c in connections if c['is_trusted']]
        suspicious = [c for c in connections if c['risk_level'] in ['HIGH', 'CRITICAL']]
        blocked = [c for c in connections if c['is_blocked']]
        
        report.append("📊 CONNECTION SUMMARY:")
        report.append(f"  ✅ Trusted: {len(trusted)}")
        report.append(f"  ⚠️  Suspicious: {len(suspicious)}")
        report.append(f"  🚫 Blocked: {len(blocked)}")
        report.append("")
        
        # Detailed connections
        if connections:
            report.append("🔍 CONNECTION DETAILS:")
            for conn in connections:
                status_icon = "✅" if conn['is_trusted'] else "⚠️" if conn['risk_level'] == 'HIGH' else "🚫" if conn['is_blocked'] else "🔸"
                report.append(f"  {status_icon} {conn['ip']}:{conn['port']} - {conn['risk_level']} risk")
                
                if conn['action_taken']:
                    report.append(f"     Action: {conn['action_taken']}")
                
                if conn['recommendations']:
                    for rec in conn['recommendations']:
                        report.append(f"     💡 {rec}")
            report.append("")
        
        # Security recommendations
        report.append("💡 SECURITY RECOMMENDATIONS:")
        if suspicious:
            report.append("  🚨 IMMEDIATE ACTIONS:")
            report.append("    1. Block all suspicious public IPs")
            report.append("    2. Review connection logs")
            report.append("    3. Implement IP whitelist")
            report.append("    4. Enable authentication")
        else:
            report.append("  ✅ No immediate threats detected")
        
        report.append("")
        report.append("=" * 80)
        
        return '\n'.join(report)
    
    def monitor_loop(self, interval=30):
        """Main monitoring loop"""
        print(f"🔍 Starting bot monitoring on port {self.c2_port}")
        print(f"⏱️  Scan interval: {interval} seconds")
        print("Press Ctrl+C to stop")
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                print(f"\n🔍 Scanning connections... ({datetime.now().strftime('%H:%M:%S')})")
                
                # Scan connections
                connections = self.scan_connections()
                
                if connections:
                    print(f"🤖 Found {len(connections)} active connections")
                    
                    # Auto security response
                    self.auto_security_response(connections)
                    
                    # Generate and display report
                    report = self.generate_report(connections)
                    print(report)
                    
                    # Save report
                    timestamp = int(time.time())
                    with open(f"bot_report_{timestamp}.txt", 'w') as f:
                        f.write(report)
                    
                else:
                    print("✅ No active connections found")
                
                # Wait for next scan
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
        finally:
            self.monitoring = False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot Connection Monitor")
    parser.add_argument('--port', type=int, default=7777, help='C2 port to monitor')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval in seconds')
    parser.add_argument('--scan', action='store_true', help='Single scan mode')
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring mode')
    
    args = parser.parse_args()
    
    monitor = BotMonitor(args.port)
    monitor.load_trusted_ips()
    
    if args.scan:
        # Single scan
        connections = monitor.scan_connections()
        report = monitor.generate_report(connections)
        print(report)
        
    elif args.monitor:
        # Continuous monitoring
        monitor.monitor_loop(args.interval)
        
    else:
        print("🤖 Bot Connection Monitor")
        print("Use --help for available options")
        print("\nQuick commands:")
        print("  python3 bot_monitor.py --scan      # Single scan")
        print("  python3 bot_monitor.py --monitor   # Continuous monitoring")

if __name__ == "__main__":
    main()

