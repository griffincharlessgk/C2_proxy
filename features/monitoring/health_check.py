"""
Health check functionality.
"""

import time
from typing import Dict, Any

class HealthChecker:
    """Health check manager."""
    
    def __init__(self, server_instance):
        self.server = server_instance
        self._start_time = time.time()
        self._last_health_check = time.time()
        self._health_status = "healthy"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        current_time = time.time()
        uptime = current_time - self._start_time
        
        # Check if we have any bots
        has_bots = len(self.server.bots) > 0
        
        # Check if any bots are overloaded
        overloaded_bots = 0
        for bot_id, count in self.server._connection_counts.items():
            if count >= self.server.max_connections_per_bot:
                overloaded_bots += 1
        
        # Determine overall health status
        if not has_bots:
            health_status = "degraded"
            health_message = "No bots connected"
        elif overloaded_bots > 0:
            health_status = "warning"
            health_message = f"{overloaded_bots} bots overloaded"
        elif len(self.server.bots) >= self.server.max_bots * 0.9:  # 90% of max bots
            health_status = "warning"
            health_message = "Approaching bot limit"
        else:
            health_status = "healthy"
            health_message = "All systems operational"
        
        # Update internal health status
        self._health_status = health_status
        self._last_health_check = current_time
        
        return {
            "status": health_status,
            "message": health_message,
            "timestamp": current_time,
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "bots": {
                "total": len(self.server.bots),
                "max": self.server.max_bots,
                "overloaded": overloaded_bots,
                "list": list(self.server.bots.keys())
            },
            "connections": {
                "total": self.server._total_connections,
                "max_per_bot": self.server.max_connections_per_bot,
                "per_bot": dict(self.server._connection_counts)
            },
            "servers": {
                "bot_port": self.server.bot_port,
                "http_port": self.server.http_port,
                "socks_port": self.server.socks_port,
                "api_port": self.server.api_port
            }
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
