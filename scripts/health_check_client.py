#!/usr/bin/env python3
"""
Health check client for C2 server monitoring.
Supports various monitoring systems and formats.
"""

import asyncio
import aiohttp
import json
import sys
import time
import argparse
from typing import Dict, Any

class HealthChecker:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_health(self, endpoint: str = "/health") -> Dict[str, Any]:
        """Check health status from specified endpoint."""
        try:
            async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                data = await resp.json()
                return {
                    "endpoint": endpoint,
                    "status_code": resp.status,
                    "response_time": resp.headers.get("X-Response-Time", "unknown"),
                    "data": data,
                    "success": resp.status < 400
                }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "error": str(e),
                "success": False
            }

    async def check_all_endpoints(self) -> Dict[str, Any]:
        """Check all health endpoints."""
        endpoints = [
            "/health",
            "/health/detailed", 
            "/health/ready",
            "/health/live"
        ]
        
        results = {}
        for endpoint in endpoints:
            results[endpoint] = await self.check_health(endpoint)
        
        return results

    def format_nagios(self, result: Dict[str, Any]) -> str:
        """Format result for Nagios monitoring."""
        if result["success"]:
            data = result["data"]
            status = data.get("status", "unknown")
            message = data.get("message", "No message")
            
            if status == "healthy":
                return f"OK - {message}"
            elif status == "warning":
                return f"WARNING - {message}"
            else:
                return f"CRITICAL - {message}"
        else:
            return f"CRITICAL - Health check failed: {result.get('error', 'Unknown error')}"

    def format_prometheus(self, result: Dict[str, Any]) -> str:
        """Format result for Prometheus monitoring."""
        if not result["success"]:
            return f"c2_health_check{{endpoint=\"{result['endpoint']}\"}} 0"
        
        data = result["data"]
        status_value = 1 if data.get("status") == "healthy" else 0
        
        return f"c2_health_check{{endpoint=\"{result['endpoint']}\",status=\"{data.get('status', 'unknown')}\"}} {status_value}"

    def format_json(self, result: Dict[str, Any]) -> str:
        """Format result as JSON."""
        return json.dumps(result, indent=2)

    def format_human(self, result: Dict[str, Any]) -> str:
        """Format result for human reading."""
        if not result["success"]:
            return f"❌ {result['endpoint']}: FAILED - {result.get('error', 'Unknown error')}"
        
        data = result["data"]
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️", 
            "degraded": "❌"
        }.get(data.get("status", "unknown"), "❓")
        
        return f"{status_emoji} {result['endpoint']}: {data.get('status', 'unknown').upper()} - {data.get('message', 'No message')}"

async def main():
    parser = argparse.ArgumentParser(description="C2 Server Health Checker")
    parser.add_argument("--url", default="http://localhost:5001", help="C2 server URL")
    parser.add_argument("--endpoint", default="/health", help="Health check endpoint")
    parser.add_argument("--format", choices=["nagios", "prometheus", "json", "human"], 
                       default="human", help="Output format")
    parser.add_argument("--all", action="store_true", help="Check all endpoints")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    async with HealthChecker(args.url) as checker:
        if args.all:
            results = await checker.check_all_endpoints()
            
            if args.format == "json":
                print(json.dumps(results, indent=2))
            else:
                for endpoint, result in results.items():
                    if args.format == "nagios":
                        print(checker.format_nagios(result))
                    elif args.format == "prometheus":
                        print(checker.format_prometheus(result))
                    else:  # human
                        print(checker.format_human(result))
        else:
            result = await checker.check_health(args.endpoint)
            
            if args.format == "nagios":
                print(checker.format_nagios(result))
            elif args.format == "prometheus":
                print(checker.format_prometheus(result))
            elif args.format == "json":
                print(checker.format_json(result))
            else:  # human
                print(checker.format_human(result))
            
            # Exit with appropriate code
            if not result["success"]:
                sys.exit(2)  # Critical
            elif result["data"].get("status") == "warning":
                sys.exit(1)  # Warning
            else:
                sys.exit(0)  # OK

if __name__ == "__main__":
    asyncio.run(main())
