"""
Configuration utilities.
"""

import json
import os
from typing import Dict, Any

def load_config(config_file: str = "config/config.json") -> Dict[str, Any]:
    """Load configuration from JSON file with fallback to defaults."""
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "bot_port": 4443,
            "http_port": 8080,
            "socks_port": 1080,
            "api_port": 5001
        },
        "security": {
            "bot_token": "r9K7aLDcCtDZTB7S_wXkKWLuc8qrlrTYM00SmUTLRxg0P6d9kAiJajcU7qehaHsk",
            "tls_enabled": False,
            "certfile": "certs/server.crt",
            "keyfile": "certs/server.key"
        },
        "logging": {
            "level": "INFO",
            "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        },
        "limits": {
            "max_bots": 100,
            "max_connections_per_bot": 50,
            "connection_timeout": 300
        },
        "heartbeat": {
            "interval": 30,
            "timeout": 10
        },
        "network": {
            "buffer_size": 4096,
            "read_timeout": 30,
            "write_timeout": 30,
            "connect_timeout": 10
        }
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            return _merge_config(default_config, config)
        except Exception as e:
            print(f"Error loading config {config_file}: {e}, using defaults")
            return default_config
    else:
        print(f"Config file {config_file} not found, using defaults")
        return default_config

def _merge_config(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user config with defaults."""
    result = default.copy()
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration."""
    required_keys = ["server", "security", "limits", "network"]
    for key in required_keys:
        if key not in config:
            print(f"Missing required config section: {key}")
            return False
    
    # Validate server config
    server = config["server"]
    required_ports = ["bot_port", "http_port", "socks_port", "api_port"]
    for port in required_ports:
        if port not in server or not isinstance(server[port], int):
            print(f"Invalid or missing port: {port}")
            return False
    
    # Validate limits
    limits = config["limits"]
    if limits.get("max_bots", 0) <= 0:
        print("max_bots must be positive")
        return False
    
    if limits.get("max_connections_per_bot", 0) <= 0:
        print("max_connections_per_bot must be positive")
        return False
    
    return True
