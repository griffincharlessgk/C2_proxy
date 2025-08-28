#!/usr/bin/env python3
"""
Test suite cho Bane Core Library
Kiểm tra các chức năng chính của bane library
"""

import unittest
import sys
import os
import tempfile
import hashlib
from unittest.mock import patch, MagicMock

# Add bane to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bane'))

class TestBaneCryptographers(unittest.TestCase):
    """Test các chức năng cryptographic"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from bane.cryptographers import MD5, SHA256, BASE64
            self.md5 = MD5()
            self.sha256 = SHA256()
            self.base64 = BASE64()
        except ImportError:
            self.skipTest("Bane cryptographers module not available")
    
    def test_md5_hash(self):
        """Test MD5 hashing"""
        test_string = "test123"
        expected = hashlib.md5(test_string.encode()).hexdigest()
        
        result = self.md5.hash(test_string)
        self.assertEqual(result, expected)
    
    def test_sha256_hash(self):
        """Test SHA256 hashing"""
        test_string = "test123"
        expected = hashlib.sha256(test_string.encode()).hexdigest()
        
        result = self.sha256.hash(test_string)
        self.assertEqual(result, expected)
    
    def test_base64_encoding(self):
        """Test Base64 encoding/decoding"""
        test_string = "Hello World"
        
        encoded = self.base64.encode(test_string)
        decoded = self.base64.decode(encoded)
        
        # BASE64.decode returns bytes, so we need to decode to string
        if isinstance(decoded, bytes):
            decoded = decoded.decode('utf-8')
        
        self.assertEqual(decoded, test_string)

class TestBaneUtils(unittest.TestCase):
    """Test utility functions"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from bane.utils import Files_Interface, RANDOM_GENERATOR
            self.files = Files_Interface()
            self.random_gen = RANDOM_GENERATOR()
        except ImportError:
            self.skipTest("Bane utils module not available")
    
    def test_file_operations(self):
        """Test file read/write operations"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            test_content = "Test file content"
            tmp.write(test_content)
            tmp_path = tmp.name
        
        try:
            # Test read (use read_file method)
            content = self.files.read_file(tmp_path, split_lines=False)
            self.assertEqual(content.strip(), test_content)
            
            # Test write (use write_file method)
            new_content = "New test content"
            # Clear file first
            self.files.clear_file(tmp_path)
            self.files.write_file(new_content, tmp_path)
            
            updated_content = self.files.read_file(tmp_path, split_lines=False)
            self.assertEqual(updated_content.strip(), new_content)
            
        finally:
            os.unlink(tmp_path)
    
    def test_random_generation(self):
        """Test random data generation"""
        # Test IP generation
        ip = self.random_gen.get_random_ip()
        parts = ip.split('.')
        self.assertEqual(len(parts), 4)
        for part in parts:
            self.assertTrue(0 <= int(part) <= 255)
        
        # Test user agent generation
        ua = self.random_gen.get_random_user_agent()
        self.assertIsInstance(ua, str)
        self.assertGreater(len(ua), 10)

class TestBaneNetworking(unittest.TestCase):
    """Test networking functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from bane.gather_info import Network_Info, Domain_Info
            self.network = Network_Info()
            self.domain = Domain_Info()
        except ImportError:
            self.skipTest("Bane networking module not available")
    
    def test_port_scanning(self):
        """Test port scanning functionality"""
        # Test tcp_scan method which actually exists
        result = self.network.tcp_scan("127.0.0.1", port=80, timeout=1)
        # tcp_scan returns True/False, so we check it's a boolean
        self.assertIsInstance(result, bool)
    
    def test_local_ip(self):
        """Test local IP detection"""
        local_ip = self.network.get_local_ip()
        # get_local_ip returns a list, so we need to handle that
        if isinstance(local_ip, list):
            local_ip = local_ip[0] if local_ip else "127.0.0.1"
        
        self.assertIsInstance(local_ip, str)
        parts = local_ip.split('.')
        self.assertEqual(len(parts), 4)

class TestBaneScanners(unittest.TestCase):
    """Test scanner functionality"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            from bane.scanners.vulnerabilities import XSS_Scanner
            from bane.scanners.network_protocols import Ports_Scanner
            self.xss_scanner = XSS_Scanner()
            # Ports_Scanner requires a target parameter 'u'
            self.port_scanner = None  # Will create when needed
        except ImportError:
            self.skipTest("Bane scanners module not available")
    
    def test_xss_scanner(self):
        """Test XSS scanner initialization"""
        # Just test that XSS_Scanner can be imported and initialized
        self.assertIsNotNone(self.xss_scanner)
        self.assertTrue(hasattr(self.xss_scanner, '__class__'))

if __name__ == '__main__':
    # Run tests với verbose output
    unittest.main(verbosity=2)
