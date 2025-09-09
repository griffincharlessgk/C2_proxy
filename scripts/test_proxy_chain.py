#!/usr/bin/env python3
"""
TEST PROXY CHAIN SYSTEM
Test script để kiểm tra toàn bộ hệ thống C2 Proxy Chain
"""

import time
import threading
import subprocess
import requests
import socket
import sys
import os
from datetime import datetime

class ProxyChainTester:
    def __init__(self, c2_host="localhost", c2_port=3333, proxy_port=8080, socks_port=1080):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.proxy_port = proxy_port
        self.socks_port = socks_port
        
        self.c2_process = None
        self.bot_processes = []
        self.test_results = {}
        
    def start_c2_server(self):
        """Khởi động C2 server"""
        print("🚀 Starting C2 Proxy Server...")
        try:
            cmd = [
                sys.executable, 
                "c2_proxy_server.py",
                "--c2-host", self.c2_host,
                "--c2-port", str(self.c2_port),
                "--proxy-port", str(self.proxy_port),
                "--socks-port", str(self.socks_port)
            ]
            
            self.c2_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Wait for server to start
            time.sleep(3)
            
            if self.c2_process.poll() is None:
                print("✅ C2 Proxy Server started")
                return True
            else:
                print("❌ C2 Proxy Server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting C2 server: {e}")
            return False
            
    def start_bot_servers(self, num_bots=3):
        """Khởi động bot servers"""
        print(f"🤖 Starting {num_bots} bot servers...")
        
        for i in range(num_bots):
            try:
                cmd = [
                    sys.executable,
                    "child_bot_server.py",
                    "--c2-host", self.c2_host,
                    "--c2-port", str(self.c2_port),
                    "--bot-id", f"test_bot_{i+1}"
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                self.bot_processes.append(process)
                print(f"✅ Bot {i+1} started")
                
                # Wait between bot starts
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error starting bot {i+1}: {e}")
                
        # Wait for bots to connect
        time.sleep(5)
        print(f"✅ {len(self.bot_processes)} bot servers started")
        
    def test_http_proxy(self):
        """Test HTTP proxy functionality"""
        print("\n🌐 Testing HTTP Proxy...")
        
        try:
            proxies = {
                'http': f'http://{self.c2_host}:{self.proxy_port}',
                'https': f'http://{self.c2_host}:{self.proxy_port}'
            }
            
            # Test basic HTTP request
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ HTTP Proxy test passed - IP: {data.get('origin', 'Unknown')}")
                self.test_results['http_proxy'] = True
                return True
            else:
                print(f"❌ HTTP Proxy test failed - Status: {response.status_code}")
                self.test_results['http_proxy'] = False
                return False
                
        except Exception as e:
            print(f"❌ HTTP Proxy test error: {e}")
            self.test_results['http_proxy'] = False
            return False
            
    def test_https_proxy(self):
        """Test HTTPS proxy functionality"""
        print("\n🔒 Testing HTTPS Proxy...")
        
        try:
            proxies = {
                'http': f'http://{self.c2_host}:{self.proxy_port}',
                'https': f'http://{self.c2_host}:{self.proxy_port}'
            }
            
            # Test HTTPS request
            response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ HTTPS Proxy test passed - IP: {data.get('origin', 'Unknown')}")
                self.test_results['https_proxy'] = True
                return True
            else:
                print(f"❌ HTTPS Proxy test failed - Status: {response.status_code}")
                self.test_results['https_proxy'] = False
                return False
                
        except Exception as e:
            print(f"❌ HTTPS Proxy test error: {e}")
            self.test_results['https_proxy'] = False
            return False
            
    def test_socks5_proxy(self):
        """Test SOCKS5 proxy functionality"""
        print("\n🧦 Testing SOCKS5 Proxy...")
        
        try:
            import socks
            
            # Create SOCKS5 socket
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, self.c2_host, self.socks_port)
            sock.settimeout(10)
            
            # Test connection
            sock.connect(('httpbin.org', 80))
            
            # Send HTTP request
            request = b'GET /ip HTTP/1.1\r\nHost: httpbin.org\r\n\r\n'
            sock.send(request)
            
            # Receive response
            response = sock.recv(4096)
            sock.close()
            
            if b'200 OK' in response:
                print("✅ SOCKS5 Proxy test passed")
                self.test_results['socks5_proxy'] = True
                return True
            else:
                print("❌ SOCKS5 Proxy test failed")
                self.test_results['socks5_proxy'] = False
                return False
                
        except ImportError:
            print("⚠️  PySocks not installed, skipping SOCKS5 test")
            self.test_results['socks5_proxy'] = None
            return None
        except Exception as e:
            print(f"❌ SOCKS5 Proxy test error: {e}")
            self.test_results['socks5_proxy'] = False
            return False
            
    def test_load_balancing(self):
        """Test load balancing functionality"""
        print("\n⚖️  Testing Load Balancing...")
        
        try:
            proxies = {
                'http': f'http://{self.c2_host}:{self.proxy_port}',
                'https': f'http://{self.c2_host}:{self.proxy_port}'
            }
            
            # Make multiple requests to test load balancing
            ips = []
            for i in range(10):
                try:
                    response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        ips.append(data.get('origin', 'Unknown'))
                    time.sleep(0.5)
                except:
                    pass
                    
            if ips:
                unique_ips = set(ips)
                print(f"✅ Load balancing test - {len(unique_ips)} unique IPs from {len(ips)} requests")
                print(f"   IPs: {', '.join(unique_ips)}")
                self.test_results['load_balancing'] = len(unique_ips) > 1
                return len(unique_ips) > 1
            else:
                print("❌ Load balancing test failed - No successful requests")
                self.test_results['load_balancing'] = False
                return False
                
        except Exception as e:
            print(f"❌ Load balancing test error: {e}")
            self.test_results['load_balancing'] = False
            return False
            
    def test_health_monitoring(self):
        """Test health monitoring"""
        print("\n🏥 Testing Health Monitoring...")
        
        try:
            # Check C2 server status
            response = requests.get(f'http://{self.c2_host}:3334/api/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                bot_count = data.get('connected_bots', 0)
                print(f"✅ Health monitoring test - {bot_count} bots connected")
                self.test_results['health_monitoring'] = bot_count > 0
                return bot_count > 0
            else:
                print("❌ Health monitoring test failed")
                self.test_results['health_monitoring'] = False
                return False
                
        except Exception as e:
            print(f"❌ Health monitoring test error: {e}")
            self.test_results['health_monitoring'] = False
            return False
            
    def test_stress(self):
        """Test stress với nhiều requests"""
        print("\n💪 Testing Stress...")
        
        def make_request():
            try:
                proxies = {
                    'http': f'http://{self.c2_host}:{self.proxy_port}',
                    'https': f'http://{self.c2_host}:{self.proxy_port}'
                }
                response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=5)
                return response.status_code == 200
            except:
                return False
                
        # Start multiple threads
        threads = []
        results = []
        
        for i in range(20):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        success_count = sum(results)
        print(f"✅ Stress test - {success_count}/{len(results)} requests successful")
        self.test_results['stress'] = success_count >= len(results) * 0.8
        return success_count >= len(results) * 0.8
        
    def run_all_tests(self):
        """Chạy tất cả tests"""
        print("🧪 Starting Proxy Chain Tests...")
        print("=" * 50)
        
        # Start services
        if not self.start_c2_server():
            print("❌ Cannot start C2 server, aborting tests")
            return False
            
        self.start_bot_servers(3)
        
        # Run tests
        tests = [
            ("HTTP Proxy", self.test_http_proxy),
            ("HTTPS Proxy", self.test_https_proxy),
            ("SOCKS5 Proxy", self.test_socks5_proxy),
            ("Load Balancing", self.test_load_balancing),
            ("Health Monitoring", self.test_health_monitoring),
            ("Stress Test", self.test_stress)
        ]
        
        passed = 0
        total = 0
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                if result is not None:
                    total += 1
                    if result:
                        passed += 1
            except Exception as e:
                print(f"❌ Test error: {e}")
                total += 1
                
        # Print results
        print("\n" + "="*50)
        print("📊 TEST RESULTS")
        print("="*50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL" if result is not None else "⚠️  SKIP"
            print(f"{test_name:20} {status}")
            
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed")
            
        return passed == total
        
    def cleanup(self):
        """Cleanup tất cả processes"""
        print("\n🧹 Cleaning up...")
        
        # Stop bot processes
        for process in self.bot_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
                    
        # Stop C2 process
        if self.c2_process:
            try:
                self.c2_process.terminate()
                self.c2_process.wait(timeout=5)
            except:
                try:
                    self.c2_process.kill()
                except:
                    pass
                    
        print("✅ Cleanup completed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test C2 Proxy Chain System")
    parser.add_argument("--c2-host", default="localhost", help="C2 server host")
    parser.add_argument("--c2-port", type=int, default=3333, help="C2 server port")
    parser.add_argument("--proxy-port", type=int, default=8080, help="HTTP proxy port")
    parser.add_argument("--socks-port", type=int, default=1080, help="SOCKS5 proxy port")
    parser.add_argument("--num-bots", type=int, default=3, help="Number of bot servers")
    
    args = parser.parse_args()
    
    tester = ProxyChainTester(args.c2_host, args.c2_port, args.proxy_port, args.socks_port)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        tester.cleanup()
        sys.exit(1)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
