"""
Integration tests for C2 server and bot agent.
"""

import asyncio
import unittest
import subprocess
import time
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestC2BotIntegration(unittest.TestCase):
    """Test C2 server and bot agent integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.c2_process = None
        self.bot_process = None
        self.base_url = "http://localhost:5001"
    
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
    
    def test_c2_server_startup(self):
        """Test C2 server starts successfully."""
        # Start C2 server
        self.c2_process = subprocess.Popen([
            sys.executable, "main_c2.py",
            "--host", "127.0.0.1",
            "--bot-port", "4443",
            "--http-port", "8080",
            "--socks-port", "1080",
            "--api-port", "5001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server is running
        self.assertIsNotNone(self.c2_process.poll())
        self.assertEqual(self.c2_process.returncode, None)  # Still running
    
    def test_health_check_endpoints(self):
        """Test health check endpoints."""
        # Start C2 server
        self.c2_process = subprocess.Popen([
            sys.executable, "main_c2.py",
            "--host", "127.0.0.1",
            "--api-port", "5001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test health check
        result = subprocess.run([
            sys.executable, "scripts/simple_health_check.py",
            "--url", self.base_url,
            "--format", "json"
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("data", data)
        self.assertIn("status", data["data"])
    
    def test_bot_connection(self):
        """Test bot connection to C2 server."""
        # Start C2 server
        self.c2_process = subprocess.Popen([
            sys.executable, "main_c2.py",
            "--host", "127.0.0.1",
            "--bot-port", "4443",
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
        
        # Check bot status via API
        result = subprocess.run([
            sys.executable, "scripts/simple_health_check.py",
            "--url", self.base_url,
            "--endpoint", "/api/status",
            "--format", "json"
        ], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("data", data)
        self.assertIn("bots", data["data"])
        self.assertGreater(len(data["data"]["bots"]), 0)


if __name__ == "__main__":
    unittest.main()
