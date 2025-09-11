#!/usr/bin/env python3
"""
Test script to demonstrate graceful shutdown functionality.
"""

import asyncio
import signal
import sys
import time
import subprocess
import os

async def test_graceful_shutdown():
    """Test graceful shutdown of C2 server and bot."""
    print("🧪 Testing Graceful Shutdown...")
    
    # Start C2 server
    print("1. Starting C2 server...")
    c2_process = subprocess.Popen([
        sys.executable, "c2_server.py", 
        "--host", "127.0.0.1",
        "--bot-port", "4443",
        "--http-port", "8080",
        "--api-port", "5001"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    await asyncio.sleep(2)
    
    # Start bot
    print("2. Starting bot agent...")
    bot_process = subprocess.Popen([
        sys.executable, "bot_agent.py",
        "--c2-host", "127.0.0.1",
        "--c2-port", "4443",
        "--token", "test_token",
        "--bot-id", "test_bot"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for bot to connect
    await asyncio.sleep(2)
    
    print("3. Testing graceful shutdown...")
    print("   Sending SIGTERM to C2 server...")
    
    # Send SIGTERM to C2 server
    c2_process.terminate()
    
    # Wait for graceful shutdown
    try:
        stdout, stderr = c2_process.communicate(timeout=10)
        print("✅ C2 server shutdown gracefully")
        print(f"   Output: {stdout.decode()}")
        if stderr:
            print(f"   Errors: {stderr.decode()}")
    except subprocess.TimeoutExpired:
        print("❌ C2 server did not shutdown gracefully, killing...")
        c2_process.kill()
        c2_process.communicate()
    
    # Send SIGTERM to bot
    print("   Sending SIGTERM to bot agent...")
    bot_process.terminate()
    
    try:
        stdout, stderr = bot_process.communicate(timeout=5)
        print("✅ Bot agent shutdown gracefully")
        print(f"   Output: {stdout.decode()}")
        if stderr:
            print(f"   Errors: {stderr.decode()}")
    except subprocess.TimeoutExpired:
        print("❌ Bot agent did not shutdown gracefully, killing...")
        bot_process.kill()
        bot_process.communicate()
    
    print("🎉 Graceful shutdown test completed!")

if __name__ == "__main__":
    asyncio.run(test_graceful_shutdown())
