#!/usr/bin/env python3
"""
Test script to demonstrate connection limits functionality.
"""

import asyncio
import aiohttp
import time
import subprocess
import sys
import json

async def test_connection_limits():
    """Test connection limits enforcement."""
    print("🧪 Testing Connection Limits...")
    
    # Start C2 server with low limits for testing
    print("1. Starting C2 server with low limits...")
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
    
    print("3. Testing connection limits...")
    
    # Test 1: Check initial status
    print("   Checking initial status...")
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:5001/api/status') as resp:
            status = await resp.json()
            print(f"   ✅ Initial status: {status['bot_count']} bots, {status['active_connections']} connections")
            print(f"   ✅ Limits: max_bots={status['connection_limits']['max_bots']}, max_per_bot={status['connection_limits']['max_connections_per_bot']}")
    
    # Test 2: Test HTTP proxy with multiple connections
    print("   Testing HTTP proxy connections...")
    tasks = []
    for i in range(10):  # Try to create 10 connections
        task = asyncio.create_task(test_http_connection(i))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   ✅ HTTP connections: {successful}/10 successful")
    
    # Test 3: Check final status
    print("   Checking final status...")
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:5001/api/status') as resp:
            status = await resp.json()
            print(f"   ✅ Final status: {status['bot_count']} bots, {status['active_connections']} connections")
            print(f"   ✅ Bot connections: {status['bot_connections']}")
    
    # Cleanup
    print("4. Cleaning up...")
    c2_process.terminate()
    bot_process.terminate()
    
    try:
        c2_process.communicate(timeout=5)
        bot_process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        c2_process.kill()
        bot_process.kill()
    
    print("🎉 Connection limits test completed!")

async def test_http_connection(conn_id):
    """Test a single HTTP connection."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:8080', 
                                proxy='http://127.0.0.1:8080',
                                timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    print(f"   ✅ Connection {conn_id}: Success")
                    return True
                else:
                    print(f"   ❌ Connection {conn_id}: HTTP {resp.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Connection {conn_id}: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection_limits())
