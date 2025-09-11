"""
Logging utilities.
"""

import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """Setup logging configuration."""
    if format_string is None:
        format_string = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        stream=sys.stdout
    )

def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
