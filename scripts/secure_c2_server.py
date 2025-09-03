#!/usr/bin/env python3
"""
Secure C2 Server - Cải thiện bảo mật cho C2 server
"""

import os
import sys
import json
import socket
import threading
import time
import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Set, Optional

class SecureC2Server:
    def __init__(self, config_file="secure_c2_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.authenticated_bots = set()
        self.trusted_ips = set(self.config.get('security', {}).get('allowed_ips', []))
        self.blocked_ips = set(self.config.get('security', {}).get('blocked_ips', []))
        self.connection_attempts = {}
        self.max_attempts = 3
        self.connection_timeout = 30
        
    def load_config(self) -> Dict:
        """Load configuration"""
        default_config = {
            'c2_host': '127.0.0.1',
            'c2_port': 7777,
            'encryption_key': secrets.token_hex(32),
            'security': {
                'require_authentication': True,
                'allowed_ips': [],
                'blocked_ips': [],
                'max_connections_per_ip': 3,
                'connection_timeout': 30,
                'enable_encryption': True,
                'enable_logging': True,
                'log_file': 'secure_c2.log'
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"❌ Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Config saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if ip in self.blocked_ips:
            return False
        
        if self.trusted_ips:
            return ip in self.trusted_ips
        
        return True  # Allow if no whitelist configured
    
    def is_ip_rate_limited(self, ip: str) -> bool:
        """Check if IP is rate limited"""
        now = time.time()
        if ip not in self.connection_attempts:
            self.connection_attempts[ip] = []
        
        # Remove old attempts
        self.connection_attempts[ip] = [
            attempt for attempt in self.connection_attempts[ip]
            if now - attempt < 60  # 1 minute window
        ]
        
        # Check if too many attempts
        if len(self.connection_attempts[ip]) >= self.max_attempts:
            return True
        
        # Add current attempt
        self.connection_attempts[ip].append(now)
        return False
    
    def authenticate_bot(self, client_socket: socket.socket, client_address: tuple) -> bool:
        """Authenticate bot connection"""
        try:
            # Send authentication challenge
            challenge = secrets.token_hex(16)
            client_socket.send(f"AUTH_CHALLENGE:{challenge}\n".encode())
            
            # Receive response
            response = client_socket.recv(1024).decode().strip()
            
            # Verify response
            expected_response = hashlib.sha256(
                (challenge + self.config['encryption_key']).encode()
            ).hexdigest()
            
            if response == expected_response:
                self.authenticated_bots.add(client_address[0])
                self.log_security_event("AUTH_SUCCESS", client_address[0], "Bot authenticated")
                return True
            else:
                self.log_security_event("AUTH_FAILED", client_address[0], "Invalid authentication")
                return False
                
        except Exception as e:
            self.log_security_event("AUTH_ERROR", client_address[0], f"Authentication error: {e}")
            return False
    
    def log_security_event(self, event_type: str, ip: str, details: str):
        """Log security event"""
        if not self.config.get('security', {}).get('enable_logging', True):
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'ip': ip,
            'details': details
        }
        
        try:
            log_file = self.config.get('security', {}).get('log_file', 'secure_c2.log')
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"❌ Error logging security event: {e}")
    
    def handle_bot_connection(self, client_socket: socket.socket, client_address: tuple):
        """Handle bot connection"""
        ip, port = client_address
        
        try:
            # Check if IP is allowed
            if not self.is_ip_allowed(ip):
                self.log_security_event("BLOCKED_IP", ip, "IP in blocked list")
                client_socket.close()
                return
            
            # Check rate limiting
            if self.is_ip_rate_limited(ip):
                self.log_security_event("RATE_LIMITED", ip, "Too many connection attempts")
                client_socket.close()
                return
            
            # Authenticate if required
            if self.config.get('security', {}).get('require_authentication', True):
                if not self.authenticate_bot(client_socket, client_address):
                    client_socket.close()
                    return
            
            # Set timeout
            client_socket.settimeout(self.connection_timeout)
            
            # Bot is authenticated, handle commands
            self.log_security_event("BOT_CONNECTED", ip, f"Bot connected from {ip}:{port}")
            
            # Send welcome message
            client_socket.send("AUTHENTICATED:Welcome to secure C2 server\n".encode())
            
            # Handle bot commands
            while True:
                try:
                    command = client_socket.recv(1024).decode().strip()
                    if not command:
                        break
                    
                    # Process command
                    response = self.process_command(command, ip)
                    client_socket.send(f"RESPONSE:{response}\n".encode())
                    
                except socket.timeout:
                    break
                except Exception as e:
                    self.log_security_event("COMMAND_ERROR", ip, f"Command error: {e}")
                    break
            
        except Exception as e:
            self.log_security_event("CONNECTION_ERROR", ip, f"Connection error: {e}")
        finally:
            client_socket.close()
            if ip in self.authenticated_bots:
                self.authenticated_bots.remove(ip)
            self.log_security_event("BOT_DISCONNECTED", ip, "Bot disconnected")
    
    def process_command(self, command: str, ip: str) -> str:
        """Process bot command"""
        try:
            # Log command
            self.log_security_event("COMMAND_RECEIVED", ip, f"Command: {command}")
            
            # Simple command processing
            if command == "PING":
                return "PONG"
            elif command == "STATUS":
                return "ONLINE"
            elif command.startswith("INFO:"):
                return f"INFO_RECEIVED:{command[5:]}"
            else:
                return "UNKNOWN_COMMAND"
                
        except Exception as e:
            return f"ERROR:{str(e)}"
    
    def start_server(self):
        """Start secure C2 server"""
        print("🔒 Starting Secure C2 Server")
        print("=" * 40)
        
        # Create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Bind to address
            server_socket.bind((self.config['c2_host'], self.config['c2_port']))
            server_socket.listen(5)
            
            print(f"✅ Server listening on {self.config['c2_host']}:{self.config['c2_port']}")
            print(f"🔐 Authentication: {'Enabled' if self.config.get('security', {}).get('require_authentication', True) else 'Disabled'}")
            print(f"📝 Logging: {'Enabled' if self.config.get('security', {}).get('enable_logging', True) else 'Disabled'}")
            print(f"✅ Trusted IPs: {len(self.trusted_ips)}")
            print(f"🚫 Blocked IPs: {len(self.blocked_ips)}")
            print("")
            print("Press Ctrl+C to stop server")
            
            while True:
                try:
                    # Accept connection
                    client_socket, client_address = server_socket.accept()
                    
                    # Handle connection in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_bot_connection,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    print("\n🛑 Server stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Server error: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
        finally:
            server_socket.close()
    
    def add_trusted_ip(self, ip: str):
        """Add trusted IP"""
        try:
            # Validate IP
            socket.inet_aton(ip)
            
            self.trusted_ips.add(ip)
            self.config['security']['allowed_ips'] = list(self.trusted_ips)
            self.save_config()
            
            print(f"✅ Added trusted IP: {ip}")
            
        except socket.error:
            print(f"❌ Invalid IP address: {ip}")
        except Exception as e:
            print(f"❌ Error adding trusted IP: {e}")
    
    def block_ip(self, ip: str):
        """Block IP"""
        try:
            # Validate IP
            socket.inet_aton(ip)
            
            self.blocked_ips.add(ip)
            self.config['security']['blocked_ips'] = list(self.blocked_ips)
            self.save_config()
            
            print(f"🚫 Blocked IP: {ip}")
            
        except socket.error:
            print(f"❌ Invalid IP address: {ip}")
        except Exception as e:
            print(f"❌ Error blocking IP: {e}")
    
    def show_status(self):
        """Show server status"""
        print("🔒 Secure C2 Server Status")
        print("=" * 40)
        print(f"📁 Config file: {self.config_file}")
        print(f"🌐 Host: {self.config['c2_host']}")
        print(f"🔌 Port: {self.config['c2_port']}")
        print(f"🔐 Authentication: {'✅ Enabled' if self.config.get('security', {}).get('require_authentication', True) else '❌ Disabled'}")
        print(f"📝 Logging: {'✅ Enabled' if self.config.get('security', {}).get('enable_logging', True) else '❌ Disabled'}")
        print(f"🤖 Authenticated bots: {len(self.authenticated_bots)}")
        print(f"✅ Trusted IPs: {len(self.trusted_ips)}")
        print(f"🚫 Blocked IPs: {len(self.blocked_ips)}")
        
        if self.trusted_ips:
            print("\n📋 Trusted IPs:")
            for ip in sorted(self.trusted_ips):
                print(f"  ✅ {ip}")
        
        if self.blocked_ips:
            print("\n🚫 Blocked IPs:")
            for ip in sorted(self.blocked_ips):
                print(f"  🚫 {ip}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure C2 Server")
    parser.add_argument('--start', action='store_true', help='Start secure C2 server')
    parser.add_argument('--status', action='store_true', help='Show server status')
    parser.add_argument('--add-trusted', type=str, help='Add trusted IP')
    parser.add_argument('--block', type=str, help='Block IP')
    parser.add_argument('--config', type=str, default='secure_c2_config.json', help='Config file')
    
    args = parser.parse_args()
    
    server = SecureC2Server(args.config)
    
    if args.start:
        server.start_server()
    elif args.status:
        server.show_status()
    elif args.add_trusted:
        server.add_trusted_ip(args.add_trusted)
    elif args.block:
        server.block_ip(args.block)
    else:
        print("🔒 Secure C2 Server")
        print("Use --help for available options")

if __name__ == "__main__":
    main()

