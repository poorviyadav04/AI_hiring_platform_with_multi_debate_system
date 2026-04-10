"""
MCP Server Base Classes and Registry
Implements Model Context Protocol for tool discovery and execution.

MCP enables:
- Tool discovery via server registry
- Formal tool boundaries
- Versioned capabilities
- Interoperability between agents and tools
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import inspect


class ToolParameterType(str, Enum):
    """Tool parameter types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    param_type: ToolParameterType
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass
class Tool:
    """Tool definition in MCP protocol."""
    name: str
    description: str
    parameters: List[ToolParameter]
    handler: Callable
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.param_type.value,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "metadata": self.metadata
        }
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        # Validate required parameters
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        # Execute handler
        return self.handler(**kwargs)


@dataclass
class ServerCapabilities:
    """MCP Server capabilities."""
    tools: bool = True
    schemas: bool = True
    prompts: bool = False
    resources: bool = False


class MCPServer:
    """
    Base class for MCP servers.
    
    Provides:
    - Tool registration
    - Capability advertisement
    - Tool discovery
    - Tool execution
    
    Example:
        class ScoringServer(MCPServer):
            def __init__(self):
                super().__init__("scoring", "Candidate scoring tools")
                self.register_tools()
            
            def register_tools(self):
                self.register_tool(...)
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize MCP server.
        
        Args:
            name: Server name
            description: Server description
        """
        self.name = name
        self.description = description
        self.tools: Dict[str, Tool] = {}
        self.capabilities = ServerCapabilities()
    
    def register_tool(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: List[ToolParameter],
        version: str = "1.0.0",
        metadata: Optional[Dict] = None
    ):
        """
        Register a tool with the server.
        
        Args:
            name: Tool name
            handler: Tool function
            description: Tool description
            parameters: Tool parameters
            version: Tool version
            metadata: Additional metadata
        """
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            version=version,
            metadata=metadata or {}
        )
        
        self.tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool if found, None otherwise
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """
        List all available tools.
        
        Returns:
            List of tool definitions
        """
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_capabilities(self) -> Dict:
        """
        Get server capabilities.
        
        Returns:
            Capabilities dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": {
                "tools": self.capabilities.tools,
                "schemas": self.capabilities.schemas,
                "prompts": self.capabilities.prompts,
                "resources": self.capabilities.resources
            },
            "tools_count": len(self.tools)
        }
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        return tool.execute(**kwargs)


class ServerRegistry:
    """
    Global registry for MCP servers.
    
    Enables tool discovery across servers.
    
    Example:
        registry = ServerRegistry()
        registry.register(ScoringServer())
        registry.register(MemoryServer())
        
        tools = registry.discover_tools()
        result = registry.execute("scoring", "calculate_score", ...)
    """
    
    def __init__(self):
        """Initialize server registry."""
        self.servers: Dict[str, MCPServer] = {}
    
    def register(self, server: MCPServer):
        """
        Register an MCP server.
        
        Args:
            server: MCP server instance
        """
        self.servers[server.name] = server
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """
        Get server by name.
        
        Args:
            name: Server name
            
        Returns:
            Server if found, None otherwise
        """
        return self.servers.get(name)
    
    def list_servers(self) -> List[Dict]:
        """
        List all registered servers.
        
        Returns:
            List of server capabilities
        """
        return [server.get_capabilities() for server in self.servers.values()]
    
    def discover_tools(self, server_name: Optional[str] = None) -> List[Dict]:
        """
        Discover all available tools.
        
        Args:
            server_name: Optional server name to filter by
            
        Returns:
            List of tool definitions with server info
        """
        tools = []
        
        servers_to_search = (
            [self.servers[server_name]] if server_name and server_name in self.servers
            else self.servers.values()
        )
        
        for server in servers_to_search:
            for tool in server.list_tools():
                tools.append({
                    "server": server.name,
                    "tool": tool
                })
        
        return tools
    
    def execute(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool from a specific server.
        
        Args:
            server_name: Server name
            tool_name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If server or tool not found
        """
        server = self.get_server(server_name)
        if not server:
            raise ValueError(f"Server not found: {server_name}")
        
        return server.execute_tool(tool_name, **kwargs)


# Global registry instance
_registry: Optional[ServerRegistry] = None


def get_registry() -> ServerRegistry:
    """Get or create global server registry."""
    global _registry
    if _registry is None:
        _registry = ServerRegistry()
    return _registry


__all__ = [
    "ToolParameter",
    "ToolParameterType",
    "Tool",
    "MCPServer",
    "ServerCapabilities",
    "ServerRegistry",
    "get_registry"
]
