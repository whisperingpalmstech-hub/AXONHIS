"""
MCP Client for AxonHIS

Provides client interface for calling MCP tools from AI services.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP Client for AI services to call clinical tools"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._server = None
    
    async def get_server(self):
        """Lazy load MCP server"""
        if self._server is None:
            from app.core.mcp.server import MCPServer
            self._server = MCPServer(self.db)
        return self._server
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool with error handling"""
        try:
            server = await self.get_server()
            result = await server.call_tool(tool_name, arguments)
            
            if not result.get("success"):
                logger.error(f"MCP tool {tool_name} failed: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        try:
            server = await self.get_server()
            return server.list_tools()
        except Exception as e:
            logger.error(f"Error listing MCP tools: {str(e)}")
            return []
    
    async def execute_tool_chain(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a chain of MCP tools in sequence"""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})
            result = await self.call_tool(tool_name, arguments)
            results.append({
                "tool_name": tool_name,
                "result": result
            })
            
            # Stop chain if a tool fails
            if not result.get("success"):
                logger.warning(f"Tool chain stopped at {tool_name} due to failure")
                break
        
        return results
