#!/usr/bin/env python3
"""
Simple health check client for C2 server monitoring.
Uses only standard library modules.
"""

import urllib.request
import urllib.error
import json
import sys
import time
import argparse
from typing import Dict, Any

class SimpleHealthChecker:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url

    def check_health(self, endpoint: str = "/health") -> Dict[str, Any]:
        """Check health status from specified endpoint."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                response_time = time.time() - start_time
                
                return {
                    "endpoint": endpoint,
                    "status_code": response.status,
                    "response_time": f"{response_time:.3f}s",
                    "data": data,
                    "success": response.status < 400
                }
        except urllib.error.HTTPError as e:
            return {
                "endpoint": endpoint,
                "status_code": e.code,
                "error": f"HTTP {e.code}: {e.reason}",
                "success": False
            }
        except urllib.error.URLError as e:
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "error": f"URL Error: {e.reason}",
                "success": False
            }
        except Exception as e:
            return {
                "endpoint": endpoint,
                "status_code": 0,
                "error": str(e),
                "success": False
            }

    def check_all_endpoints(self) -> Dict[str, Any]:
        """Check all health endpoints."""
        endpoints = [
            "/health",
            "/health/detailed", 
            "/health/ready",
            "/health/live"
        ]
        
        results = {}
        for endpoint in endpoints:
            results[endpoint] = self.check_health(endpoint)
        
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

def main():
    parser = argparse.ArgumentParser(description="C2 Server Health Checker (Simple)")
    parser.add_argument("--url", default="http://localhost:5001", help="C2 server URL")
    parser.add_argument("--endpoint", default="/health", help="Health check endpoint")
    parser.add_argument("--format", choices=["nagios", "prometheus", "json", "human"], 
                       default="human", help="Output format")
    parser.add_argument("--all", action="store_true", help="Check all endpoints")
    
    args = parser.parse_args()
    
    checker = SimpleHealthChecker(args.url)
    
    if args.all:
        results = checker.check_all_endpoints()
        
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
        result = checker.check_health(args.endpoint)
        
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
    main()
