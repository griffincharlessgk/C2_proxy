#!/usr/bin/env python3
"""
Emergency Bot Cleanup - Xử lý khẩn cấp các bot không mong muốn
"""

import os
import sys
import time
import json
import socket
import subprocess
from datetime import datetime
from typing import Dict, List, Set

class EmergencyBotCleanup:
    def __init__(self, c2_port=7777):
        self.c2_port = c2_port
        self.trusted_ips = set()
        self.blocked_ips = set()
        self.emergency_log = "emergency_cleanup.log"
        
    def load_trusted_ips(self):
        """Load trusted IPs"""
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
    
    def get_active_connections(self) -> List[Dict]:
        """Get active connections to C2 port"""
        connections = []
        
        try:
            result = subprocess.run([
                'netstat', '-tulpn'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{self.c2_port}" in line and "ESTABLISHED" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            remote_addr = parts[4]
                            if ':' in remote_addr:
                                ip, port = remote_addr.rsplit(':', 1)
                                try:
                                    port = int(port)
                                    connections.append({
                                        'ip': ip,
                                        'port': port,
                                        'is_trusted': ip in self.trusted_ips,
                                        'timestamp': datetime.now().isoformat()
                                    })
                                except ValueError:
                                    continue
            
        except Exception as e:
            print(f"❌ Error getting connections: {e}")
        
        return connections
    
    def block_ip_emergency(self, ip: str, reason: str = "Emergency block"):
        """Emergency block IP"""
        try:
            # Block using iptables
            result = subprocess.run([
                'sudo', 'iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.blocked_ips.add(ip)
                self.log_emergency_action("BLOCKED", ip, reason)
                print(f"🚫 Emergency blocked IP: {ip}")
                return True
            else:
                print(f"❌ Failed to block IP {ip}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error blocking IP {ip}: {e}")
            return False
    
    def kill_connection(self, ip: str, port: int):
        """Kill specific connection"""
        try:
            # Find connection PID
            result = subprocess.run([
                'sudo', 'netstat', '-tulpn'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{self.c2_port}" in line and ip in line and "ESTABLISHED" in line:
                        parts = line.split()
                        if len(parts) > 6:
                            pid_info = parts[6]
                            if '/' in pid_info:
                                pid = pid_info.split('/')[0]
                                # Kill the connection
                                subprocess.run(['sudo', 'kill', '-9', pid])
                                print(f"🔌 Killed connection {ip}:{port} (PID: {pid})")
                                return True
            
            print(f"⚠️  Could not find connection for {ip}:{port}")
            return False
            
        except Exception as e:
            print(f"❌ Error killing connection {ip}:{port}: {e}")
            return False
    
    def log_emergency_action(self, action: str, target: str, reason: str):
        """Log emergency action"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'reason': reason
        }
        
        try:
            with open(self.emergency_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging action: {e}")
    
    def emergency_cleanup(self):
        """Emergency cleanup of suspicious connections"""
        print("🚨 EMERGENCY BOT CLEANUP")
        print("=" * 50)
        
        # Get active connections
        connections = self.get_active_connections()
        
        if not connections:
            print("✅ No active connections found")
            return
        
        print(f"🔍 Found {len(connections)} active connections")
        
        # Categorize connections
        trusted_connections = [c for c in connections if c['is_trusted']]
        suspicious_connections = [c for c in connections if not c['is_trusted']]
        
        print(f"✅ Trusted connections: {len(trusted_connections)}")
        print(f"⚠️  Suspicious connections: {len(suspicious_connections)}")
        
        if suspicious_connections:
            print("\n🚨 SUSPICIOUS CONNECTIONS:")
            for conn in suspicious_connections:
                print(f"  🔸 {conn['ip']}:{conn['port']}")
            
            # Ask for action
            print("\n🤔 What would you like to do?")
            print("  1. Block all suspicious IPs")
            print("  2. Kill all suspicious connections")
            print("  3. Block and kill all suspicious")
            print("  4. Manual selection")
            print("  5. Cancel")
            
            try:
                choice = input("\nEnter choice (1-5): ").strip()
                
                if choice == "1":
                    self.block_all_suspicious(suspicious_connections)
                elif choice == "2":
                    self.kill_all_suspicious(suspicious_connections)
                elif choice == "3":
                    self.block_and_kill_all(suspicious_connections)
                elif choice == "4":
                    self.manual_selection(suspicious_connections)
                elif choice == "5":
                    print("❌ Cancelled")
                else:
                    print("❌ Invalid choice")
                    
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
        else:
            print("✅ No suspicious connections found")
    
    def block_all_suspicious(self, connections: List[Dict]):
        """Block all suspicious IPs"""
        print("🚫 Blocking all suspicious IPs...")
        
        for conn in connections:
            if self.block_ip_emergency(conn['ip'], "Emergency cleanup"):
                self.log_emergency_action("BLOCKED", conn['ip'], "Emergency cleanup")
        
        print("✅ All suspicious IPs blocked")
    
    def kill_all_suspicious(self, connections: List[Dict]):
        """Kill all suspicious connections"""
        print("🔌 Killing all suspicious connections...")
        
        for conn in connections:
            if self.kill_connection(conn['ip'], conn['port']):
                self.log_emergency_action("KILLED", f"{conn['ip']}:{conn['port']}", "Emergency cleanup")
        
        print("✅ All suspicious connections killed")
    
    def block_and_kill_all(self, connections: List[Dict]):
        """Block and kill all suspicious connections"""
        print("🚫🔌 Blocking and killing all suspicious connections...")
        
        for conn in connections:
            # Kill connection first
            self.kill_connection(conn['ip'], conn['port'])
            # Then block IP
            self.block_ip_emergency(conn['ip'], "Emergency cleanup")
            self.log_emergency_action("BLOCKED_AND_KILLED", conn['ip'], "Emergency cleanup")
        
        print("✅ All suspicious connections blocked and killed")
    
    def manual_selection(self, connections: List[Dict]):
        """Manual selection of connections to handle"""
        print("\n🔍 Manual selection mode:")
        
        for i, conn in enumerate(connections):
            print(f"\n[{i+1}] {conn['ip']}:{conn['port']}")
            print("   Actions: [b]lock, [k]ill, [s]kip")
            
            try:
                action = input("   Action: ").strip().lower()
                
                if action == 'b':
                    self.block_ip_emergency(conn['ip'], "Manual selection")
                elif action == 'k':
                    self.kill_connection(conn['ip'], conn['port'])
                elif action == 's':
                    print("   ⏭️  Skipped")
                else:
                    print("   ❌ Invalid action")
                    
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                break
    
    def show_trusted_ips(self):
        """Show trusted IPs"""
        print("📋 Trusted IPs:")
        if self.trusted_ips:
            for ip in sorted(self.trusted_ips):
                print(f"  ✅ {ip}")
        else:
            print("  ❌ No trusted IPs configured")
    
    def add_trusted_ip(self, ip: str):
        """Add trusted IP"""
        try:
            # Validate IP
            socket.inet_aton(ip)
            
            self.trusted_ips.add(ip)
            
            # Save to file
            with open("trusted_ips.txt", 'a') as f:
                f.write(f"{ip}\n")
            
            print(f"✅ Added trusted IP: {ip}")
            
        except socket.error:
            print(f"❌ Invalid IP address: {ip}")
        except Exception as e:
            print(f"❌ Error adding trusted IP: {e}")
    
    def show_emergency_log(self):
        """Show emergency log"""
        print("📋 Emergency Log:")
        print("=" * 50)
        
        try:
            if os.path.exists(self.emergency_log):
                with open(self.emergency_log, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                log_entry = json.loads(line.strip())
                                print(f"  {log_entry['timestamp']} - {log_entry['action']} - {log_entry['target']} - {log_entry['reason']}")
                            except:
                                print(f"  {line.strip()}")
            else:
                print("  ❌ No emergency log found")
        except Exception as e:
            print(f"❌ Error reading emergency log: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Emergency Bot Cleanup")
    parser.add_argument('--port', type=int, default=7777, help='C2 port to monitor')
    parser.add_argument('--cleanup', action='store_true', help='Run emergency cleanup')
    parser.add_argument('--trusted', action='store_true', help='Show trusted IPs')
    parser.add_argument('--add-trusted', type=str, help='Add trusted IP')
    parser.add_argument('--log', action='store_true', help='Show emergency log')
    
    args = parser.parse_args()
    
    cleanup = EmergencyBotCleanup(args.port)
    cleanup.load_trusted_ips()
    
    if args.cleanup:
        cleanup.emergency_cleanup()
    elif args.trusted:
        cleanup.show_trusted_ips()
    elif args.add_trusted:
        cleanup.add_trusted_ip(args.add_trusted)
    elif args.log:
        cleanup.show_emergency_log()
    else:
        print("🚨 Emergency Bot Cleanup Tool")
        print("=" * 40)
        print("⚠️  For emergency situations only!")
        print("")
        print("Available commands:")
        print("  --cleanup        Run emergency cleanup")
        print("  --trusted        Show trusted IPs")
        print("  --add-trusted    Add trusted IP")
        print("  --log            Show emergency log")
        print("")
        print("Example:")
        print("  python3 emergency_bot_cleanup.py --cleanup")

if __name__ == "__main__":
    main()

