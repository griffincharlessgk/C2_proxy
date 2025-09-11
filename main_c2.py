#!/usr/bin/env python3
"""
C2 Server Main Entry Point
"""

import sys
import os
import asyncio

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.server.c2_server_new import main

if __name__ == "__main__":
    asyncio.run(main())
