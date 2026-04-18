"""
MCP Routes for AxonHIS

Provides API endpoints for MCP tool integration.
"""
import logging
from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.mcp.server import MCPServer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP Integration"])


@router.get("/tools")
async def list_mcp_tools(db: AsyncSession = Depends(get_db)):
    """List available MCP tools"""
    try:
        server = MCPServer(db)
        tools = server.list_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error listing MCP tools: {str(e)}")
        raise HTTPException(500, f"Failed to list tools: {str(e)}")


@router.post("/tools/chain")
async def execute_tool_chain(
    tool_calls: list,
    db: AsyncSession = Depends(get_db)
):
    """Execute a chain of MCP tools"""
    try:
        from app.core.mcp.client import MCPClient
        
        client = MCPClient(db)
        results = await client.execute_tool_chain(tool_calls)
        
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        import traceback
        err = traceback.format_exc()
        logger.error(f"Error executing tool chain: {err}")
        raise HTTPException(500, f"Tool chain execution failed: {err}")


@router.post("/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Call a specific MCP tool"""
    try:
        server = MCPServer(db)
        result = await server.call_tool(tool_name, arguments)
        
        if not result.get("success"):
            raise HTTPException(500, result.get("error", "Tool execution failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
        raise HTTPException(500, f"Tool execution failed: {str(e)}")
