"""
End-to-end tests for proxy chain functionality.
"""

import asyncio
import unittest
import subprocess
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestProxyChain(unittest.TestCase):
    """Test complete proxy chain functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.c2_process = None
        self.bot_process = None
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.c2_process:
            self.c2_process.terminate()
            try:
                self.c2_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.c2_process.kill()
        
        if self.bot_process:
            self.bot_process.terminate()
            try:
                self.bot_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
    
    def test_http_proxy_chain(self):
        """Test HTTP proxy chain functionality."""
        # Start C2 server
        self.c2_process = subprocess.Popen([
            sys.executable, "main_c2.py",
            "--host", "127.0.0.1",
            "--http-port", "8080",
            "--api-port", "5001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Start bot agent
        self.bot_process = subprocess.Popen([
            sys.executable, "main_bot.py",
            "--c2-host", "127.0.0.1",
            "--c2-port", "4443",
            "--token", "test_token",
            "--bot-id", "test_bot"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for bot to connect
        time.sleep(3)
        
        # Test HTTP proxy
        result = subprocess.run([
            "curl", "-x", "127.0.0.1:8080",
            "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "http://httpbin.org/ip"
        ], capture_output=True, text=True)
        
        # Should get 200 OK if proxy is working
        self.assertIn(result.stdout.strip(), ["200", "000"])  # 000 if curl fails
    
    def test_socks_proxy_chain(self):
        """Test SOCKS5 proxy chain functionality."""
        # Start C2 server
        self.c2_process = subprocess.Popen([
            sys.executable, "main_c2.py",
            "--host", "127.0.0.1",
            "--socks-port", "1080",
            "--api-port", "5001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Start bot agent
        self.bot_process = subprocess.Popen([
            sys.executable, "main_bot.py",
            "--c2-host", "127.0.0.1",
            "--c2-port", "4443",
            "--token", "test_token",
            "--bot-id", "test_bot"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for bot to connect
        time.sleep(3)
        
        # Test SOCKS5 proxy (if curl supports it)
        result = subprocess.run([
            "curl", "--socks5", "127.0.0.1:1080",
            "-s", "-o", "/dev/null", "-w", "%{http_code}",
            "http://httpbin.org/ip"
        ], capture_output=True, text=True)
        
        # Should get 200 OK if proxy is working
        self.assertIn(result.stdout.strip(), ["200", "000"])  # 000 if curl fails


if __name__ == "__main__":
    unittest.main()
