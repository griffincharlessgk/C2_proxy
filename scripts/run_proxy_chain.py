#!/usr/bin/env python3
"""
RUN PROXY CHAIN SYSTEM
Script để chạy toàn bộ hệ thống C2 Proxy Chain
"""

import os
import sys
import time
import subprocess
import threading
import signal
from datetime import datetime

class ProxyChainManager:
    def __init__(self, c2_host="0.0.0.0", c2_port=3333, proxy_port=8080, socks_port=1080, num_bots=3):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.proxy_port = proxy_port
        self.socks_port = socks_port
        self.num_bots = num_bots
        
        self.processes = {}
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)
        
    def start_c2_server(self):
        """Khởi động C2 Proxy Server"""
        print("🚀 Starting C2 Proxy Server...")
        
        try:
            cmd = [
                sys.executable,
                "c2_proxy_server.py",
                "--c2-host", self.c2_host,
                "--c2-port", str(self.c2_port),
                "--proxy-port", str(self.proxy_port),
                "--socks-port", str(self.socks_port)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.processes['c2_server'] = process
            
            # Wait for server to start
            time.sleep(3)
            
            if process.poll() is None:
                print("✅ C2 Proxy Server started")
                return True
            else:
                print("❌ C2 Proxy Server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting C2 server: {e}")
            return False
            
    def start_bot_servers(self):
        """Khởi động Bot Servers"""
        print(f"🤖 Starting {self.num_bots} Bot Servers...")
        
        for i in range(self.num_bots):
            try:
                cmd = [
                    sys.executable,
                    "child_bot_server.py",
                    "--c2-host", "localhost",  # Connect to local C2
                    "--c2-port", str(self.c2_port),
                    "--bot-id", f"bot_{i+1}_{int(time.time())}"
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                self.processes[f'bot_{i+1}'] = process
                print(f"✅ Bot {i+1} started")
                
                # Wait between bot starts
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error starting bot {i+1}: {e}")
                
        print(f"✅ {self.num_bots} Bot Servers started")
        
    def start_web_dashboard(self):
        """Khởi động Web Dashboard"""
        print("🌐 Starting Web Dashboard...")
        
        try:
            cmd = [
                sys.executable,
                "proxy_web_dashboard.py",
                "--host", "0.0.0.0",
                "--port", "5001"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.processes['web_dashboard'] = process
            
            # Wait for dashboard to start
            time.sleep(2)
            
            if process.poll() is None:
                print("✅ Web Dashboard started")
                return True
            else:
                print("❌ Web Dashboard failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting web dashboard: {e}")
            return False
            
    def monitor_processes(self):
        """Monitor tất cả processes"""
        while self.running:
            try:
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        print(f"❌ Process {name} has stopped")
                        del self.processes[name]
                        
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error monitoring processes: {e}")
                break
                
    def print_status(self):
        """In trạng thái hệ thống"""
        print("\n" + "="*60)
        print("📊 C2 PROXY CHAIN SYSTEM STATUS")
        print("="*60)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🖥️  C2 Server: {self.c2_host}:{self.c2_port}")
        print(f"🌐 HTTP Proxy: {self.c2_host}:{self.proxy_port}")
        print(f"🧦 SOCKS5 Proxy: {self.c2_host}:{self.socks_port}")
        print(f"🌐 Web Dashboard: http://{self.c2_host}:5001")
        print(f"🤖 Active Bots: {len([p for p in self.processes.keys() if p.startswith('bot_')])}")
        print(f"🔄 Active Processes: {len(self.processes)}")
        
        print("\n📋 Process Status:")
        for name, process in self.processes.items():
            status = "🟢 Running" if process.poll() is None else "🔴 Stopped"
            print(f"   {name:15} {status}")
            
        print("="*60)
        
    def start_all(self):
        """Khởi động toàn bộ hệ thống"""
        print("🚀 Starting C2 Proxy Chain System...")
        print("="*60)
        
        # Start C2 server
        if not self.start_c2_server():
            print("❌ Failed to start C2 server, aborting")
            return False
            
        # Start bot servers
        self.start_bot_servers()
        
        # Start web dashboard
        self.start_web_dashboard()
        
        # Set running flag
        self.running = True
        
        # Print status
        self.print_status()
        
        print("\n✅ System started successfully!")
        print("📝 Usage:")
        print(f"   HTTP Proxy:  http://{self.c2_host}:{self.proxy_port}")
        print(f"   SOCKS5 Proxy: {self.c2_host}:{self.socks_port}")
        print(f"   Web Dashboard: http://{self.c2_host}:5001")
        print("\n🛑 Press Ctrl+C to stop")
        
        return True
        
    def stop_all(self):
        """Dừng toàn bộ hệ thống"""
        print("\n🛑 Stopping C2 Proxy Chain System...")
        
        self.running = False
        
        # Stop all processes
        for name, process in self.processes.items():
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
                
        print("✅ All processes stopped")
        
    def run(self):
        """Chạy hệ thống"""
        try:
            if self.start_all():
                # Start monitoring thread
                monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
                monitor_thread.start()
                
                # Keep running
                while self.running:
                    time.sleep(10)
                    self.print_status()
                    
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        except Exception as e:
            print(f"❌ Error running system: {e}")
        finally:
            self.stop_all()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run C2 Proxy Chain System")
    parser.add_argument("--c2-host", default="0.0.0.0", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=3333, help="C2 server port")
    parser.add_argument("--proxy-port", type=int, default=8080, help="HTTP proxy port")
    parser.add_argument("--socks-port", type=int, default=1080, help="SOCKS5 proxy port")
    parser.add_argument("--num-bots", type=int, default=3, help="Number of bot servers")
    parser.add_argument("--dashboard-port", type=int, default=5001, help="Web dashboard port")
    
    args = parser.parse_args()
    
    # Create and run manager
    manager = ProxyChainManager(
        args.c2_host,
        args.c2_port,
        args.proxy_port,
        args.socks_port,
        args.num_bots
    )
    
    manager.run()

if __name__ == "__main__":
    main()
