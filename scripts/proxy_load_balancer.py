#!/usr/bin/env python3
"""
PROXY LOAD BALANCER
Cân bằng tải giữa các bot exit nodes với nhiều thuật toán khác nhau
"""

import random
import time
import threading
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime
import statistics

class ProxyLoadBalancer:
    def __init__(self):
        self.bot_exit_nodes = {}
        self.load_balancing_strategies = {
            'round_robin': self.round_robin_selection,
            'least_connections': self.least_connections_selection,
            'health_based': self.health_based_selection,
            'response_time': self.response_time_selection,
            'weighted_round_robin': self.weighted_round_robin_selection,
            'random': self.random_selection,
            'region_aware': self.region_aware_selection,
            'circuit_breaker': self.circuit_breaker_selection
        }
        
        # Round robin state
        self.current_bot_index = 0
        self.round_robin_lock = threading.Lock()
        
        # Statistics
        self.selection_stats = {
            'total_selections': 0,
            'successful_selections': 0,
            'failed_selections': 0,
            'strategy_usage': {strategy: 0 for strategy in self.load_balancing_strategies.keys()}
        }
        
    def register_bot(self, bot_id: str, bot_info: Dict):
        """Đăng ký bot exit node"""
        self.bot_exit_nodes[bot_id] = {
            'bot_id': bot_id,
            'status': 'active',
            'connections': 0,
            'max_connections': bot_info.get('max_connections', 50),
            'health_score': 100.0,
            'response_time': deque(maxlen=100),
            'last_health_check': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'bytes_transferred': 0,
            'weight': bot_info.get('weight', 1),
            'region': bot_info.get('region', 'default'),
            'circuit_breaker_state': 'closed',  # closed, open, half_open
            'circuit_breaker_failures': 0,
            'circuit_breaker_last_failure': None,
            'created_at': datetime.now()
        }
        
        print(f"✅ Bot {bot_id} registered as exit node")
        
    def unregister_bot(self, bot_id: str):
        """Hủy đăng ký bot exit node"""
        if bot_id in self.bot_exit_nodes:
            del self.bot_exit_nodes[bot_id]
            print(f"❌ Bot {bot_id} unregistered from exit nodes")
            
    def select_bot(self, strategy: str = "round_robin", client_region: str = None) -> Optional[str]:
        """Chọn bot exit node theo strategy"""
        self.selection_stats['total_selections'] += 1
        self.selection_stats['strategy_usage'][strategy] += 1
        
        try:
            if strategy in self.load_balancing_strategies:
                selected_bot = self.load_balancing_strategies[strategy](client_region)
                if selected_bot:
                    self.selection_stats['successful_selections'] += 1
                    return selected_bot
                else:
                    self.selection_stats['failed_selections'] += 1
                    return None
            else:
                print(f"❌ Unknown load balancing strategy: {strategy}")
                return None
                
        except Exception as e:
            print(f"❌ Error in load balancing: {e}")
            self.selection_stats['failed_selections'] += 1
            return None
            
    def round_robin_selection(self, client_region: str = None) -> Optional[str]:
        """Round Robin selection"""
        with self.round_robin_lock:
            active_bots = self.get_active_bots()
            if not active_bots:
                return None
                
            bot_ids = list(active_bots.keys())
            selected_bot = bot_ids[self.current_bot_index % len(bot_ids)]
            self.current_bot_index += 1
            return selected_bot
            
    def least_connections_selection(self, client_region: str = None) -> Optional[str]:
        """Least Connections selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        return min(active_bots.keys(), 
                  key=lambda x: active_bots[x]['connections'])
                  
    def health_based_selection(self, client_region: str = None) -> Optional[str]:
        """Health-based selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        # Filter bots with health score > 70
        healthy_bots = {bot_id: info for bot_id, info in active_bots.items() 
                       if info['health_score'] > 70}
        
        if not healthy_bots:
            return None
            
        return max(healthy_bots.keys(), 
                  key=lambda x: healthy_bots[x]['health_score'])
                  
    def response_time_selection(self, client_region: str = None) -> Optional[str]:
        """Response time based selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        # Calculate average response time for each bot
        bot_response_times = {}
        for bot_id, info in active_bots.items():
            if info['response_time']:
                avg_response_time = statistics.mean(info['response_time'])
                bot_response_times[bot_id] = avg_response_time
            else:
                bot_response_times[bot_id] = 1.0  # Default response time
                
        # Select bot with lowest response time
        return min(bot_response_times.keys(), 
                  key=lambda x: bot_response_times[x])
                  
    def weighted_round_robin_selection(self, client_region: str = None) -> Optional[str]:
        """Weighted Round Robin selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        # Create weighted list
        weighted_bots = []
        for bot_id, info in active_bots.items():
            weight = info.get('weight', 1)
            for _ in range(weight):
                weighted_bots.append(bot_id)
                
        if not weighted_bots:
            return None
            
        # Select from weighted list
        return random.choice(weighted_bots)
        
    def random_selection(self, client_region: str = None) -> Optional[str]:
        """Random selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        return random.choice(list(active_bots.keys()))
        
    def region_aware_selection(self, client_region: str = None) -> Optional[str]:
        """Region-aware selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        # If client region is specified, prefer bots in same region
        if client_region:
            same_region_bots = {bot_id: info for bot_id, info in active_bots.items() 
                              if info.get('region') == client_region}
            if same_region_bots:
                return random.choice(list(same_region_bots.keys()))
                
        # Fallback to random selection
        return random.choice(list(active_bots.keys()))
        
    def circuit_breaker_selection(self, client_region: str = None) -> Optional[str]:
        """Circuit breaker pattern selection"""
        active_bots = self.get_active_bots()
        if not active_bots:
            return None
            
        # Filter bots with closed circuit breaker
        available_bots = {bot_id: info for bot_id, info in active_bots.items() 
                         if info['circuit_breaker_state'] == 'closed'}
        
        if not available_bots:
            # Try half-open circuit breakers
            half_open_bots = {bot_id: info for bot_id, info in active_bots.items() 
                             if info['circuit_breaker_state'] == 'half_open'}
            if half_open_bots:
                return random.choice(list(half_open_bots.keys()))
            return None
            
        return random.choice(list(available_bots.keys()))
        
    def get_active_bots(self) -> Dict:
        """Lấy danh sách bot đang hoạt động"""
        return {bot_id: info for bot_id, info in self.bot_exit_nodes.items() 
                if info['status'] == 'active' and 
                info['connections'] < info['max_connections']}
                
    def update_bot_stats(self, bot_id: str, stats: Dict):
        """Cập nhật thống kê bot"""
        if bot_id in self.bot_exit_nodes:
            bot_info = self.bot_exit_nodes[bot_id]
            
            # Update basic stats
            if 'connections' in stats:
                bot_info['connections'] = stats['connections']
            if 'health_score' in stats:
                bot_info['health_score'] = stats['health_score']
            if 'response_time' in stats:
                bot_info['response_time'].append(stats['response_time'])
            if 'total_requests' in stats:
                bot_info['total_requests'] = stats['total_requests']
            if 'successful_requests' in stats:
                bot_info['successful_requests'] = stats['successful_requests']
            if 'failed_requests' in stats:
                bot_info['failed_requests'] = stats['failed_requests']
            if 'bytes_transferred' in stats:
                bot_info['bytes_transferred'] = stats['bytes_transferred']
                
            # Update circuit breaker state
            self.update_circuit_breaker(bot_id, stats)
            
    def update_circuit_breaker(self, bot_id: str, stats: Dict):
        """Cập nhật circuit breaker state"""
        if bot_id not in self.bot_exit_nodes:
            return
            
        bot_info = self.bot_exit_nodes[bot_id]
        current_time = datetime.now()
        
        # Check for failures
        if 'failed_requests' in stats and stats['failed_requests'] > 0:
            bot_info['circuit_breaker_failures'] += 1
            bot_info['circuit_breaker_last_failure'] = current_time
            
            # Open circuit breaker if too many failures
            if bot_info['circuit_breaker_failures'] >= 5:
                bot_info['circuit_breaker_state'] = 'open'
                print(f"🔴 Circuit breaker opened for bot {bot_id}")
                
        # Check for recovery
        if bot_info['circuit_breaker_state'] == 'open':
            # Wait 60 seconds before trying half-open
            if bot_info['circuit_breaker_last_failure']:
                time_since_failure = (current_time - bot_info['circuit_breaker_last_failure']).total_seconds()
                if time_since_failure > 60:
                    bot_info['circuit_breaker_state'] = 'half_open'
                    print(f"🟡 Circuit breaker half-open for bot {bot_id}")
                    
        # Close circuit breaker if successful
        if bot_info['circuit_breaker_state'] == 'half_open':
            if 'successful_requests' in stats and stats['successful_requests'] > 0:
                bot_info['circuit_breaker_state'] = 'closed'
                bot_info['circuit_breaker_failures'] = 0
                print(f"🟢 Circuit breaker closed for bot {bot_id}")
                
    def get_load_balancing_stats(self) -> Dict:
        """Lấy thống kê load balancing"""
        active_bots = self.get_active_bots()
        
        return {
            'total_bots': len(self.bot_exit_nodes),
            'active_bots': len(active_bots),
            'total_connections': sum(info['connections'] for info in self.bot_exit_nodes.values()),
            'total_requests': sum(info['total_requests'] for info in self.bot_exit_nodes.values()),
            'total_bytes': sum(info['bytes_transferred'] for info in self.bot_exit_nodes.values()),
            'selection_stats': self.selection_stats,
            'bot_stats': {
                bot_id: {
                    'status': info['status'],
                    'connections': info['connections'],
                    'health_score': info['health_score'],
                    'total_requests': info['total_requests'],
                    'successful_requests': info['successful_requests'],
                    'failed_requests': info['failed_requests'],
                    'circuit_breaker_state': info['circuit_breaker_state']
                }
                for bot_id, info in self.bot_exit_nodes.items()
            }
        }
        
    def get_bot_recommendations(self) -> Dict:
        """Lấy khuyến nghị cho bot"""
        recommendations = {}
        
        for bot_id, info in self.bot_exit_nodes.items():
            bot_recommendations = []
            
            # Health recommendations
            if info['health_score'] < 50:
                bot_recommendations.append("Health score is low, consider maintenance")
                
            # Connection recommendations
            if info['connections'] > info['max_connections'] * 0.8:
                bot_recommendations.append("High connection usage, consider scaling")
                
            # Circuit breaker recommendations
            if info['circuit_breaker_state'] == 'open':
                bot_recommendations.append("Circuit breaker is open, check bot health")
                
            # Response time recommendations
            if info['response_time']:
                avg_response_time = statistics.mean(info['response_time'])
                if avg_response_time > 5.0:
                    bot_recommendations.append("High response time, check network")
                    
            # Failure rate recommendations
            if info['total_requests'] > 0:
                failure_rate = (info['failed_requests'] / info['total_requests']) * 100
                if failure_rate > 20:
                    bot_recommendations.append("High failure rate, investigate issues")
                    
            recommendations[bot_id] = bot_recommendations
            
        return recommendations

class BotHealthMonitor:
    def __init__(self):
        self.health_check_interval = 30
        self.health_thresholds = {
            'critical': 30,
            'warning': 60,
            'good': 80
        }
        
    def check_bot_health(self, connected_bots: Dict, bot_exit_nodes: Dict):
        """Kiểm tra sức khỏe bot"""
        current_time = datetime.now()
        
        for bot_id, bot_info in connected_bots.items():
            try:
                # Check if bot is responsive
                last_seen = bot_info.get('last_seen', current_time)
                time_diff = (current_time - last_seen).total_seconds()
                
                # Update health score based on last seen
                if time_diff > 120:  # No response for 2 minutes
                    bot_info['status'] = 'offline'
                    if bot_id in bot_exit_nodes:
                        bot_exit_nodes[bot_id]['status'] = 'offline'
                        bot_exit_nodes[bot_id]['health_score'] = 0
                elif time_diff > 60:  # No response for 1 minute
                    if bot_id in bot_exit_nodes:
                        bot_exit_nodes[bot_id]['health_score'] = max(0, 
                            bot_exit_nodes[bot_id]['health_score'] - 20)
                else:
                    # Bot is responsive, increase health score
                    if bot_id in bot_exit_nodes:
                        bot_exit_nodes[bot_id]['health_score'] = min(100, 
                            bot_exit_nodes[bot_id]['health_score'] + 5)
                            
                # Send ping to bot
                bot_socket = bot_info['socket']
                bot_socket.send("PING".encode())
                
            except Exception as e:
                print(f"❌ Health check failed for bot {bot_id}: {e}")
                bot_info['status'] = 'offline'
                if bot_id in bot_exit_nodes:
                    bot_exit_nodes[bot_id]['status'] = 'offline'
                    bot_exit_nodes[bot_id]['health_score'] = 0
                    
    def get_health_status(self, bot_exit_nodes: Dict) -> Dict:
        """Lấy trạng thái sức khỏe tổng thể"""
        total_bots = len(bot_exit_nodes)
        if total_bots == 0:
            return {'status': 'no_bots', 'message': 'No bots available'}
            
        health_scores = [info['health_score'] for info in bot_exit_nodes.values()]
        avg_health = statistics.mean(health_scores)
        
        # Categorize health status
        if avg_health >= self.health_thresholds['good']:
            status = 'excellent'
        elif avg_health >= self.health_thresholds['warning']:
            status = 'good'
        elif avg_health >= self.health_thresholds['critical']:
            status = 'warning'
        else:
            status = 'critical'
            
        return {
            'status': status,
            'average_health': avg_health,
            'total_bots': total_bots,
            'healthy_bots': len([s for s in health_scores if s >= self.health_thresholds['good']]),
            'warning_bots': len([s for s in health_scores if self.health_thresholds['warning'] <= s < self.health_thresholds['good']]),
            'critical_bots': len([s for s in health_scores if s < self.health_thresholds['critical']])
        }

def main():
    """Test load balancer"""
    lb = ProxyLoadBalancer()
    
    # Register some test bots
    lb.register_bot("bot1", {'max_connections': 50, 'weight': 2, 'region': 'us-east'})
    lb.register_bot("bot2", {'max_connections': 30, 'weight': 1, 'region': 'us-west'})
    lb.register_bot("bot3", {'max_connections': 40, 'weight': 3, 'region': 'eu-west'})
    
    # Test different strategies
    strategies = ['round_robin', 'least_connections', 'health_based', 'random', 'weighted_round_robin']
    
    for strategy in strategies:
        print(f"\n🧪 Testing {strategy}:")
        for i in range(5):
            selected = lb.select_bot(strategy)
            print(f"  Selection {i+1}: {selected}")
            
    # Show stats
    print(f"\n📊 Load Balancer Stats:")
    stats = lb.get_load_balancing_stats()
    print(f"  Total selections: {stats['selection_stats']['total_selections']}")
    print(f"  Successful selections: {stats['selection_stats']['successful_selections']}")
    print(f"  Strategy usage: {stats['selection_stats']['strategy_usage']}")

if __name__ == "__main__":
    main()
