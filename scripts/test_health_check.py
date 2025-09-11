#!/usr/bin/env python3
"""
Test script to demonstrate health check functionality.
"""

import subprocess
import sys
import time
import json

def test_health_check():
    """Test health check endpoints."""
    print("🧪 Testing Health Check Endpoints...")
    
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
    time.sleep(3)
    
    print("2. Testing health check endpoints...")
    
    # Test basic health check
    print("   Testing /health...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--endpoint", "/health",
        "--format", "human"
    ], capture_output=True, text=True)
    print(f"   Result: {result.stdout.strip()}")
    print(f"   Exit code: {result.returncode}")
    
    # Test detailed health check
    print("   Testing /health/detailed...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--endpoint", "/health/detailed",
        "--format", "json"
    ], capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"   Status: {data['data']['status']}")
        print(f"   Message: {data['data']['message']}")
        print(f"   Uptime: {data['data']['uptime_human']}")
        print(f"   Bots: {data['data']['bots']['total']}")
    
    # Test readiness probe
    print("   Testing /health/ready...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--endpoint", "/health/ready",
        "--format", "human"
    ], capture_output=True, text=True)
    print(f"   Result: {result.stdout.strip()}")
    
    # Test liveness probe
    print("   Testing /health/live...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--endpoint", "/health/live",
        "--format", "human"
    ], capture_output=True, text=True)
    print(f"   Result: {result.stdout.strip()}")
    
    # Test all endpoints
    print("   Testing all endpoints...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--all",
        "--format", "human"
    ], capture_output=True, text=True)
    print("   Results:")
    for line in result.stdout.strip().split('\n'):
        print(f"     {line}")
    
    # Test Nagios format
    print("   Testing Nagios format...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--format", "nagios"
    ], capture_output=True, text=True)
    print(f"   Result: {result.stdout.strip()}")
    
    # Test Prometheus format
    print("   Testing Prometheus format...")
    result = subprocess.run([
        sys.executable, "simple_health_check.py",
        "--url", "http://127.0.0.1:5001",
        "--format", "prometheus"
    ], capture_output=True, text=True)
    print(f"   Result: {result.stdout.strip()}")
    
    # Cleanup
    print("3. Cleaning up...")
    c2_process.terminate()
    
    try:
        c2_process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        c2_process.kill()
        c2_process.communicate()
    
    print("🎉 Health check test completed!")

if __name__ == "__main__":
    test_health_check()
