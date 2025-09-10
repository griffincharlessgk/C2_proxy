#!/usr/bin/env python3
import requests
import time

def test_proxy_debug():
    """Test proxy với debug logging"""
    proxy_url = "http://45.38.42.232:8080"
    
    print("🧪 Testing proxy with debug logging...")
    print("=" * 50)
    
    try:
        print("📡 Making request to httpbin.org/ip...")
        response = requests.get(
            "http://httpbin.org/ip",
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=15
        )
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("=" * 50)
    print("🔍 Check C2 server logs for debug info")
    print("🔍 Check bot logs for PROXY_REQUEST messages")

if __name__ == "__main__":
    test_proxy_debug()
