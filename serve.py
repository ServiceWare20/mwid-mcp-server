
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from mcp.server.sse import SseServerTransport
from MWAP_MCPserver import MWIDMCPServer

# Configure logging - enable DEBUG for MCP SDK
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mwid-sse-server")

# Also enable debug logging for MCP SDK modules
logging.getLogger("mcp").setLevel(logging.DEBUG)
logging.getLogger("mcp.server.sse").setLevel(logging.DEBUG)

# Global server instance
mcp_server = None
sse_transport = None

@asynccontextmanager
async def lifespan(app):
    global mcp_server, sse_transport
    
    logger.info("Initializing MWID MCP Server...")
    # Initialize the specific MCP server implementation
    mwid_server = MWIDMCPServer()
    # verify initialization
    if hasattr(mwid_server, 'initialize'):
         await mwid_server.initialize() # if it has an async init
    
    # The actual MCP Server instance from the wrapper
    mcp_server = mwid_server.server
    sse_transport = SseServerTransport("/messages")
    
    yield
    
    logger.info("Shutting down MWID MCP Server...")
    if hasattr(mwid_server, 'cleanup'):
        await mwid_server.cleanup()

async def handle_sse(request):
    """Handle SSE connection"""
    logger.info("🔵 SSE connection request received")
    logger.info(f"🔍 Request headers: {dict(request.headers)}")
    
    try:
        logger.info("🔵 Establishing SSE transport connection...")
        async with sse_transport.connect_sse(
            request.scope, 
            request.receive, 
            request._send
        ) as (read_stream, write_stream):
            logger.info("✅ SSE transport connected successfully")
            logger.info("🔵 Starting MCP server.run()...")
            
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
            
            logger.info("✅ MCP server.run() completed")
    except Exception as e:
        logger.error(f"❌ Error in handle_sse: {e}", exc_info=True)
        raise
    finally:
        logger.info("🔵 SSE connection closing")
    
    return Response()


async def handle_root(request):
    """Handle root request"""
    return Response("MWID MCP Server Running. Connect via /sse and /messages endpoints.", media_type="text/plain")

async def handle_messages(request):
    """Handle client messages"""
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)

# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/", endpoint=handle_root),
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"])
    ],
    lifespan=lifespan
)

def main():
    """Run the server with Uvicorn"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting SSE MCP Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
