#!/usr/bin/env python3
"""
Bot Agent Main Entry Point
"""

import sys
import os
import asyncio

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.client.bot_agent import main

if __name__ == "__main__":
    asyncio.run(main())
