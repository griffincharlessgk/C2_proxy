"""
Unit tests for protocol module.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.protocol import Frame, FramedStream, Heartbeat


class TestFrame(unittest.TestCase):
    """Test Frame class."""
    
    def test_frame_creation(self):
        """Test frame creation."""
        frame = Frame(type="DATA", request_id="123", payload=b"test")
        self.assertEqual(frame.type, "DATA")
        self.assertEqual(frame.request_id, "123")
        self.assertEqual(frame.payload, b"test")
        self.assertEqual(frame.meta, {})
    
    def test_frame_with_meta(self):
        """Test frame with metadata."""
        meta = {"host": "example.com", "port": 80}
        frame = Frame(type="PROXY_REQUEST", request_id="456", meta=meta)
        self.assertEqual(frame.type, "PROXY_REQUEST")
        self.assertEqual(frame.request_id, "456")
        self.assertEqual(frame.meta, meta)
        self.assertIsNone(frame.payload)


class TestFramedStream(unittest.TestCase):
    """Test FramedStream class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = Mock()
        self.writer = Mock()
        self.stream = FramedStream(self.reader, self.writer)
    
    def test_send_frame(self):
        """Test sending a frame."""
        frame = Frame(type="DATA", request_id="123", payload=b"test")
        
        # Mock writer methods
        self.writer.write = Mock()
        self.writer.drain = AsyncMock()
        
        # Test sending
        asyncio.run(self.stream.send(frame))
        
        # Verify writer was called
        self.writer.write.assert_called_once()
        self.writer.drain.assert_called_once()
    
    def test_recv_frame(self):
        """Test receiving a frame."""
        # Mock reader with proper async methods
        # First call returns length (4 bytes), second call returns JSON body
        self.reader.readexactly = AsyncMock(side_effect=[
            b'\x00\x00\x00\x1a',  # Length: 26 bytes
            b'{"type":"DATA","request_id":"123","payload":"dGVzdA=="}'  # JSON body
        ])
        
        # Test receiving
        frame = asyncio.run(self.stream.recv())
        
        # Verify frame was parsed correctly
        self.assertEqual(frame.type, "DATA")
        self.assertEqual(frame.request_id, "123")
        self.assertEqual(frame.payload, b"test")


class TestHeartbeat(unittest.TestCase):
    """Test Heartbeat class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.stream = Mock()
        self.stream.send = AsyncMock()
        self.heartbeat = Heartbeat(self.stream, interval=1, timeout=5)
    
    def test_heartbeat_creation(self):
        """Test heartbeat creation."""
        self.assertEqual(self.heartbeat.interval, 1)
        self.assertEqual(self.heartbeat.timeout, 5)
        self.assertFalse(self.heartbeat._running)
    
    def test_handle_rx_ping(self):
        """Test handling PING frame."""
        frame = Frame(type="PING", request_id="heartbeat")
        result = asyncio.run(self.heartbeat.handle_rx(frame))
        self.assertTrue(result)
        self.stream.send.assert_called_once()
    
    def test_handle_rx_pong(self):
        """Test handling PONG frame."""
        frame = Frame(type="PONG", request_id="heartbeat")
        result = asyncio.run(self.heartbeat.handle_rx(frame))
        self.assertTrue(result)
        self.stream.send.assert_not_called()
    
    def test_handle_rx_other(self):
        """Test handling non-heartbeat frame."""
        frame = Frame(type="DATA", request_id="123", payload=b"test")
        result = asyncio.run(self.heartbeat.handle_rx(frame))
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
