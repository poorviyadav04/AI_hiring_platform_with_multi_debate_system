"""
Initialize MCP servers and registry.
Auto-registers all servers for tool discovery.
"""

from mcp_servers.mcp_base import get_registry
from mcp_servers.scoring_server import ScoringServer
from mcp_servers.memory_server import MemoryServer


def initialize_mcp_servers():
    """
    Initialize and register all MCP servers.
    
    Returns:
        ServerRegistry instance
    """
    registry = get_registry()
    
    # Register servers
    registry.register(ScoringServer())
    registry.register(MemoryServer())
    
    return registry


# Auto-initialize on import
_registry = initialize_mcp_servers()


__all__ = ["initialize_mcp_servers", "get_registry"]
