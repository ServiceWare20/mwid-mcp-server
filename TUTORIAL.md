# Building an MCP Server from Scratch - Complete Tutorial

## 📚 Table of Contents

1. [Introduction - What is MCP?](#introduction)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Step 1: Environment Setup](#step-1-environment-setup)
5. [Step 2: Configuration & Settings](#step-2-configuration--settings)
6. [Step 3: Creating the MCP Server Class](#step-3-creating-the-mcp-server-class)
7. [Step 4: HTTP Client & Authentication](#step-4-http-client--authentication)
8. [Step 5: Defining Tools](#step-5-defining-tools)
9. [Step 6: Implementing Tool Handlers](#step-6-implementing-tool-handlers)
10. [Step 7: Running the Server (stdio mode)](#step-7-running-the-server-stdio-mode)
11. [Step 8: Running the Server (SSE mode for web)](#step-8-running-the-server-sse-mode-for-web)
12. [Step 9: Deployment](#step-9-deployment)
13. [Testing Your Server](#testing-your-server)
14. [Common Patterns & Best Practices](#common-patterns--best-practices)

---

## Introduction

### What is MCP?

**MCP (Model Context Protocol)** is a standard protocol that allows AI assistants (like ChatGPT, Claude, or Cursor) to interact with external tools and data sources.

Think of it like this:
- **Without MCP**: AI can only answer based on its training data
- **With MCP**: AI can call real APIs, access databases, and perform actions

### What We're Building

We're building an MCP server that connects AI assistants to the MetaWealth Dashboard API. This allows AI to:
- Query sales records
- Access investor data
- (Future) Manage assets, tasks, and users

### Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  ChatGPT/   │  MCP    │  MCP Server  │  HTTP   │   MWID      │
│   Claude    │◄────────┤  (Python)    │────────►│  Backend    │
│   Cursor    │         │              │         │   API       │
└─────────────┘         └──────────────┘         └─────────────┘
     AI Model           Your Server Code         Your Data
```

---

## Prerequisites

### What You Need to Know
- Basic Python (functions, classes, async/await)
- Basic HTTP/REST APIs (GET, POST requests)
- Basic command line usage

### What You'll Learn
- How MCP protocol works
- How to create MCP tools
- How to handle authentication
- How to deploy to production

### Software Requirements
```bash
# Python 3.13+ (check version)
python3 --version

# pip (Python package manager)
pip --version

# Git (for version control)
git --version
```

---

## Project Structure

Here's what our final project looks like:

```
mwid-mcp-server/
├── MWAP_MCPserver.py      # Main MCP server (stdio mode)
├── serve.py                # Web server wrapper (SSE mode)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (secrets)
├── Dockerfile              # Container configuration
├── railway.json            # Railway deployment config
├── Procfile                # Process definition
├── test_api.py             # API testing script
└── README.md               # Documentation
```

**Two modes of operation**:
1. **stdio mode** (`MWAP_MCPserver.py`) - For desktop apps (Claude, Cursor)
2. **SSE mode** (`serve.py`) - For web apps (ChatGPT)

---

## Step 1: Environment Setup

### Create Project Directory

```bash
mkdir mwid-mcp-server
cd mwid-mcp-server
```

### Create Virtual Environment (Optional but Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows
```

### Create requirements.txt

Create a file called `requirements.txt`:

```txt
mcp>=1.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
starlette>=0.27.0
uvicorn>=0.22.0
```

**What each package does**:
- `mcp` - The MCP protocol library (core)
- `httpx` - Modern HTTP client for making API requests
- `python-dotenv` - Load environment variables from .env file
- `pydantic` - Data validation and settings management
- `pydantic-settings` - Settings from environment variables
- `starlette` - Web framework for SSE mode
- `uvicorn` - ASGI server for running web server

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 2: Configuration & Settings

### Create .env File

Create a file called `.env` to store your secrets:

```bash
# Backend API Configuration
MWID_API_URL=https://mwid.up.railway.app/api/v1

# Authentication Method
MWID_AUTH_METHOD=jwt

# JWT Token (leave empty if not available)
MWID_JWT_TOKEN=

# External API (for sales & investors)
MWID_EXTERNAL_API_URL=https://mwid.up.railway.app/api/v1/external
MWID_EXTERNAL_API_KEY=your-api-key-here

# Request timeout in seconds
MWID_REQUEST_TIMEOUT=30

# Debug mode
MWID_DEBUG=false
```

**Why use .env?**
- Keeps secrets out of code
- Easy to change without editing code
- Different values for dev/production

### Create Settings Class

Now let's create the beginning of `MWAP_MCPserver.py`:

```python
#!/usr/bin/env python3
"""
MWID Dashboard MCP Server
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    api_url: str = Field(
        default="http://localhost:8080/api/v1",
        alias="MWID_API_URL"
    )
    
    # Authentication
    auth_method: str = Field(default="jwt", alias="MWID_AUTH_METHOD")
    jwt_token: str = Field(default="", alias="MWID_JWT_TOKEN")
    
    # External API (for sales & investors)
    external_api_url: str = Field(
        default="https://mwid.up.railway.app/api/v1/external",
        alias="MWID_EXTERNAL_API_URL"
    )
    external_api_key: str = Field(default="", alias="MWID_EXTERNAL_API_KEY")
    
    # Other settings
    request_timeout: int = Field(default=30, alias="MWID_REQUEST_TIMEOUT")
    debug: bool = Field(default=False, alias="MWID_DEBUG")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars like PORT
```

**What's happening here?**

1. **`load_dotenv()`** - Reads `.env` file and loads variables
2. **`Settings` class** - Uses Pydantic to validate and type-check settings
3. **`Field(alias=...)`** - Maps environment variable names to Python attributes
4. **`Config.extra = "ignore"`** - Allows extra env vars without errors

**Example**: When you set `MWID_API_URL=https://api.example.com` in `.env`, it becomes `settings.api_url` in Python.

---

## Step 3: Creating the MCP Server Class

### Basic Server Structure

```python
class MWIDMCPServer:
    """MCP Server for MWID Dashboard API"""
    
    def __init__(self):
        # Load settings
        self.settings = Settings()
        
        # Create MCP server instance with a name
        self.server = Server("mwid-dashboard")
        
        # HTTP client (will be initialized later)
        self.client: Optional[httpx.AsyncClient] = None
        
        # Authentication status
        self.authenticated = False
        
        # Set up logging
        log_level = logging.DEBUG if self.settings.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("mwid-mcp-server")
        
        # Register handlers (we'll create this next)
        self._register_handlers()
```

**What's happening?**

1. **`Server("mwid-dashboard")`** - Creates an MCP server with a name
2. **`self.client`** - HTTP client for making API requests (lazy initialization)
3. **`self.authenticated`** - Tracks if we're logged in
4. **`self.logger`** - For debugging and monitoring
5. **`_register_handlers()`** - Sets up the MCP protocol handlers

### Understanding MCP Handlers

MCP servers respond to two main types of requests:

1. **`list_tools`** - "What can you do?" (returns list of available tools)
2. **`call_tool`** - "Do this specific thing" (executes a tool)

```python
def _register_handlers(self):
    """Register MCP server handlers"""
    
    # Handler 1: List available tools
    @self.server.list_tools()
    async def list_tools() -> List[Tool]:
        """Called when AI asks: 'What tools do you have?'"""
        return self._get_all_tools()
    
    # Handler 2: Execute a tool
    @self.server.call_tool()
    async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
        """Called when AI says: 'Use tool X with arguments Y'"""
        self.logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        try:
            # Initialize HTTP client if needed
            if self.client is None:
                await self._initialize_client()
            
            # Execute the tool
            result = await self._handle_tool_call(name, arguments)
            
            # Format response as JSON
            if isinstance(result, dict) or isinstance(result, list):
                response_text = json.dumps(result, indent=2, default=str)
            else:
                response_text = str(result)
            
            # Return as TextContent (MCP format)
            return [TextContent(type="text", text=response_text)]
            
        except httpx.HTTPStatusError as e:
            # Handle HTTP errors (404, 403, etc.)
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
            self.logger.error(error_msg)
            return [TextContent(type="text", text=f"Error: {error_msg}")]
            
        except Exception as e:
            # Handle other errors
            error_msg = f"Error executing tool '{name}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return [TextContent(type="text", text=f"Error: {error_msg}")]
```

**Key Concepts**:

- **`@self.server.list_tools()`** - Decorator that registers the function as a handler
- **`async def`** - Asynchronous function (can wait for I/O without blocking)
- **`TextContent`** - MCP's way of returning text responses
- **Error handling** - Always catch errors and return helpful messages

---

## Step 4: HTTP Client & Authentication

### Initialize HTTP Client

```python
async def _initialize_client(self):
    """Initialize HTTP client and authenticate if needed"""
    # Create async HTTP client with timeout
    self.client = httpx.AsyncClient(timeout=self.settings.request_timeout)
    
    # Authenticate based on configured method
    if self.settings.auth_method == "jwt" and self.settings.jwt_token:
        self.authenticated = True
        self.logger.info("Using JWT token authentication")
    else:
        self.logger.warning(
            f"No authentication configured for method: {self.settings.auth_method}. "
            "Internal API requests may fail with 401/403."
        )
```

**What's happening?**

1. **`httpx.AsyncClient`** - Creates a reusable HTTP client
2. **`timeout`** - Prevents requests from hanging forever
3. **Authentication check** - Validates JWT token if provided
4. **Warning** - Alerts if authentication is missing

### Making API Requests

Here's how to make authenticated requests:

```python
def _get_headers(self) -> Dict[str, str]:
    """Get HTTP headers for API requests"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add JWT token if available
    if self.settings.jwt_token:
        headers["Authorization"] = f"Bearer {self.settings.jwt_token}"
    
    return headers


async def _api_request(
    self, 
    method: str,      # "GET", "POST", etc.
    endpoint: str,    # "/assets", "/tasks", etc.
    params: Optional[Dict] = None,      # Query parameters (?page=1)
    json_data: Optional[Dict] = None    # Request body
) -> Any:
    """Make authenticated API request to internal API"""
    
    # Ensure client is initialized
    if self.client is None:
        await self._initialize_client()
    
    # Build full URL
    url = f"{self.settings.api_url}{endpoint}"
    
    # Get headers with authentication
    headers = self._get_headers()
    
    self.logger.debug(f"{method} {url}")
    
    try:
        # Make the HTTP request
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data
        )
        
        # Raise error if status code is 4xx or 5xx
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
        
    except httpx.HTTPStatusError as e:
        # Handle authentication errors specially
        if e.response.status_code in [401, 403]:
            error_detail = (
                f"Authentication failed (HTTP {e.response.status_code}). "
                "Please verify MWID_JWT_TOKEN or Supabase/Google credentials."
            )
            self.logger.error(f"{error_detail} Response: {e.response.text}")
            raise ValueError(error_detail)
        raise
        
    except Exception as e:
        self.logger.error(f"API error: {str(e)}")
        raise
```

**Key Concepts**:

- **`async/await`** - Allows multiple requests to run concurrently
- **`response.raise_for_status()`** - Automatically raises error for bad status codes
- **Error handling** - Provides helpful messages for authentication failures
- **Logging** - Helps debug issues in production

### External API Requests (No JWT Needed)

For the external API (sales & investors), we use a different authentication method:

```python
async def _external_api_request(
    self,
    method: str,
    endpoint: str,
    params: Optional[Dict] = None
) -> Any:
    """Make API request to external endpoints using X-API-Key auth"""
    
    if self.client is None:
        await self._initialize_client()
    
    # Check API key is configured
    if not self.settings.external_api_key:
        raise ValueError(
            "External API key not configured. "
            "Set MWID_EXTERNAL_API_KEY in .env"
        )
    
    # Build URL
    url = f"{self.settings.external_api_url}{endpoint}"
    
    # Headers with API key (different from JWT!)
    headers = {
        "X-API-Key": self.settings.external_api_key,
        "Content-Type": "application/json"
    }
    
    self.logger.debug(f"{method} {url}")
    
    try:
        response = await self.client.request(
            method=method,
            url=url,
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code in [401, 403]:
            error_detail = (
                f"Authentication failed (HTTP {e.response.status_code}). "
                "Please verify MWID_EXTERNAL_API_KEY."
            )
            self.logger.error(f"{error_detail} Response: {e.response.text}")
            raise ValueError(error_detail)
        raise
        
    except Exception as e:
        self.logger.error(f"External API error: {str(e)}")
        raise
```

**Difference from Internal API**:
- Uses `X-API-Key` header instead of `Bearer` token
- Simpler authentication (just an API key)
- Different base URL

---

## Step 5: Defining Tools

### What is a Tool?

A **tool** is a function that AI can call. Each tool has:
1. **Name** - Unique identifier (e.g., `list_manual_sales`)
2. **Description** - What it does (shown to AI)
3. **Input Schema** - What parameters it accepts
4. **Handler** - The code that executes it

### Tool Definition Example

```python
def _get_all_tools(self) -> List[Tool]:
    """Return list of all available tools"""
    return [
        # Tool 1: List Manual Sales
        Tool(
            name="list_manual_sales",
            description=(
                "List manual sales records with optional filtering and pagination. "
                "Returns sales data including amount, currency, asset info, "
                "approval status, and investor details."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of items per page (default: 100, max: 500)",
                        "default": 100
                    },
                    "userId": {
                        "type": "string",
                        "description": "Filter by user/investor ID"
                    },
                    "assetId": {
                        "type": "string",
                        "description": "Filter by asset ID"
                    },
                    "adjustmentType": {
                        "type": "string",
                        "description": "Filter by adjustment type (e.g. ADD)"
                    }
                },
                "required": []  # No required parameters
            }
        ),
        
        # Tool 2: Get Specific Sale
        Tool(
            name="get_manual_sale",
            description="Get detailed information about a specific manual sale by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "sale_id": {
                        "type": "string",
                        "description": "UUID of the manual sale record"
                    }
                },
                "required": ["sale_id"]  # sale_id is required
            }
        ),
        
        # Tool 3: List Manual Investors
        Tool(
            name="list_manual_investors",
            description=(
                "List manual investor records with optional filtering and pagination. "
                "Returns investor profiles including name, email, country, and account type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default: 1)",
                        "default": 1
                    },
                    "pageSize": {
                        "type": "integer",
                        "description": "Number of items per page (default: 100, max: 500)",
                        "default": 100
                    },
                    "email": {
                        "type": "string",
                        "description": "Filter by investor email"
                    },
                    "userId": {
                        "type": "string",
                        "description": "Filter by user/investor ID"
                    },
                    "country": {
                        "type": "string",
                        "description": "Filter by country"
                    }
                },
                "required": []
            }
        ),
        
        # Tool 4: Get Specific Investor
        Tool(
            name="get_manual_investor",
            description="Get detailed information about a specific manual investor by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "investor_id": {
                        "type": "string",
                        "description": "UUID of the manual investor record"
                    }
                },
                "required": ["investor_id"]
            }
        ),
        
        # Add more tools here...
    ]
```

**Understanding the Schema**:

- **`type: "object"`** - Tool accepts an object (dictionary) of parameters
- **`properties`** - Defines each parameter (name, type, description)
- **`required`** - List of parameters that must be provided
- **`default`** - Default value if parameter is not provided

**How AI Uses This**:

When you ask ChatGPT: *"Show me sales from Romania"*

1. AI reads tool descriptions
2. AI picks `list_manual_sales` tool
3. AI generates arguments: `{"country": "Romania"}`
4. AI calls the tool with those arguments

---

## Step 6: Implementing Tool Handlers

### The Tool Router

```python
async def _handle_tool_call(self, name: str, arguments: dict) -> Any:
    """Route tool calls to appropriate handler"""
    
    # ============================================================
    # WORKING FEATURES - External API (No JWT Required)
    # ============================================================
    
    if name == "list_manual_sales":
        # Extract parameters from arguments
        params = {}
        for key in ["page", "pageSize", "userId", "assetId", "adjustmentType"]:
            if key in arguments:
                params[key] = arguments[key]
        
        # Make API request
        return await self._external_api_request("GET", "/manual-sales", params=params)
    
    elif name == "get_manual_sale":
        sale_id = arguments["sale_id"]
        return await self._external_api_request("GET", f"/manual-sales/{sale_id}")
    
    elif name == "list_manual_investors":
        params = {}
        for key in ["page", "pageSize", "email", "userId", "country"]:
            if key in arguments:
                params[key] = arguments[key]
        return await self._external_api_request("GET", "/manual-investors", params=params)
    
    elif name == "get_manual_investor":
        investor_id = arguments["investor_id"]
        return await self._external_api_request("GET", f"/manual-investors/{investor_id}")
    
    # ============================================================
    # FUTURE FEATURES - Internal API (Requires JWT Token)
    # ============================================================
    
    elif name == "list_assets":
        # This will return 403 if JWT token is not configured
        return await self._api_request("GET", "/assets")
    
    elif name == "get_asset":
        asset_id = arguments["asset_id"]
        return await self._api_request("GET", f"/assets/{asset_id}")
    
    elif name == "create_asset":
        # POST request with JSON body
        return await self._api_request(
            "POST", 
            "/assets",
            json_data={
                "name": arguments["name"],
                "target_amount": arguments["target_amount"],
                "status": arguments.get("status", "Pre-Launch"),
                "launch_date": arguments.get("launch_date")
            }
        )
    
    # ... more handlers ...
    
    else:
        raise ValueError(f"Unknown tool: {name}")
```

**Pattern Explanation**:

1. **Check tool name** with `if/elif` chain
2. **Extract arguments** from the `arguments` dict
3. **Call appropriate API** using `_api_request` or `_external_api_request`
4. **Return result** (will be formatted by the handler)

**Why separate functions?**

- `_external_api_request` - Uses X-API-Key (works now)
- `_api_request` - Uses JWT Bearer token (needs JWT)

---

## Step 7: Running the Server (stdio mode)

### What is stdio Mode?

**stdio** = Standard Input/Output

- Desktop AI apps (Claude, Cursor) run your server as a subprocess
- They communicate via stdin/stdout (like command line pipes)
- No network ports needed

### Implementation

```python
async def run(self):
    """Run the MCP server in stdio mode"""
    from mcp.server.stdio import stdio_server
    
    # stdio_server() provides read/write streams
    async with stdio_server() as (read_stream, write_stream):
        self.logger.info("MWID MCP Server starting...")
        
        # Run the MCP server with the streams
        await self.server.run(
            read_stream,
            write_stream,
            self.server.create_initialization_options()
        )


async def cleanup(self):
    """Cleanup resources when shutting down"""
    if self.client:
        await self.client.aclose()


# Entry point for stdio mode
async def main():
    """Main entry point for stdio mode"""
    server = MWIDMCPServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
```

**How it works**:

1. **`stdio_server()`** - Sets up stdin/stdout communication
2. **`server.run()`** - Starts the MCP protocol loop
3. **`cleanup()`** - Closes HTTP client when done
4. **`asyncio.run()`** - Runs the async main function

**Testing stdio mode**:

```bash
# Run the server
python3 MWAP_MCPserver.py

# It will wait for JSON-RPC messages on stdin
# Press Ctrl+C to stop
```

---

## Step 8: Running the Server (SSE mode for web)

### What is SSE Mode?

**SSE** = Server-Sent Events

- Web-based AI apps (ChatGPT) need HTTP endpoints
- SSE allows real-time bidirectional communication over HTTP
- Requires a web server (we use Starlette + Uvicorn)

### Create serve.py

```python
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route

from mcp.server.sse import SseServerTransport
from MWAP_MCPserver import MWIDMCPServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mwid-sse-server")

# Global server instance
mcp_server = None
sse_transport = None


@asynccontextmanager
async def lifespan(app):
    """Startup and shutdown logic"""
    global mcp_server, sse_transport
    
    logger.info("Initializing MWID MCP Server...")
    
    # Create MCP server instance
    mwid_server = MWIDMCPServer()
    
    # Get the actual MCP Server instance
    mcp_server = mwid_server.server
    
    # Create SSE transport (handles /messages endpoint)
    sse_transport = SseServerTransport("/messages")
    
    yield  # Server runs here
    
    logger.info("Shutting down MWID MCP Server...")
    if hasattr(mwid_server, 'cleanup'):
        await mwid_server.cleanup()


async def handle_sse(request):
    """Handle SSE connection from AI client"""
    logger.info("SSE connection request received")
    
    try:
        # Establish SSE connection
        async with sse_transport.connect_sse(
            request.scope, 
            request.receive, 
            request._send
        ) as (read_stream, write_stream):
            logger.info("SSE transport connected")
            
            # Run MCP server with SSE streams
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
            
    except Exception as e:
        logger.error(f"Error in handle_sse: {e}", exc_info=True)
        raise
    
    return Response()


async def handle_root(request):
    """Handle root request (health check)"""
    return Response(
        "MWID MCP Server Running. Connect via /sse endpoint.",
        media_type="text/plain"
    )


async def handle_messages(request):
    """Handle client messages (POST /messages)"""
    await sse_transport.handle_post_message(
        request.scope,
        request.receive,
        request._send
    )


# Create Starlette app
app = Starlette(
    debug=True,
    routes=[
        Route("/", endpoint=handle_root),                    # Health check
        Route("/sse", endpoint=handle_sse),                  # SSE connection
        Route("/messages", endpoint=handle_messages, methods=["POST"])  # Client messages
    ],
    lifespan=lifespan  # Startup/shutdown logic
)


def main():
    """Run the server with Uvicorn"""
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting SSE MCP Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
```

**What's happening?**

1. **`lifespan`** - Runs code on startup/shutdown
2. **`handle_sse`** - Main SSE endpoint for AI connections
3. **`handle_messages`** - Receives messages from AI
4. **`Starlette`** - Web framework that routes requests
5. **`uvicorn.run`** - Starts the web server

**Three endpoints**:
- `/` - Health check (returns "Server Running")
- `/sse` - SSE connection (AI connects here)
- `/messages` - POST endpoint (AI sends messages here)

**Testing SSE mode**:

```bash
# Run the server
python3 serve.py

# Server starts on http://0.0.0.0:8000
# Open http://localhost:8000 in browser to see health check
```

---

## Step 9: Deployment

### Create Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Run the SSE server
CMD ["python", "serve.py"]
```

**What's happening?**

1. **`FROM python:3.13-slim`** - Base image with Python
2. **`COPY requirements.txt`** - Copy dependencies first
3. **`RUN pip install`** - Install dependencies
4. **`COPY . .`** - Copy all code
5. **`CMD`** - Command to run when container starts

### Create railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python serve.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**What this does**:
- Tells Railway to use Docker
- Sets restart policy (auto-restart on failure)
- Defines start command

### Create .dockerignore

```
.env
.git
.gitignore
__pycache__
*.pyc
venv/
.venv/
*.md
test_*.py
```

**Why?**
- Keeps secrets out of Docker image
- Reduces image size
- Faster builds

### Deploy to Railway

```bash
# 1. Push to GitHub
git add .
git commit -m "Initial MCP server"
git push origin main

# 2. Go to Railway
# Visit: https://railway.app/new

# 3. Deploy from GitHub
# Select your repository

# 4. Set environment variables in Railway dashboard
MWID_API_URL=https://mwid.up.railway.app/api/v1
MWID_AUTH_METHOD=jwt
MWID_JWT_TOKEN=
MWID_EXTERNAL_API_URL=https://mwid.up.railway.app/api/v1/external
MWID_EXTERNAL_API_KEY=your-api-key-here
MWID_REQUEST_TIMEOUT=30
MWID_DEBUG=false

# 5. Generate domain
# Go to Settings → Generate Domain

# 6. Get your URL
# Example: https://mwid-mcp-server-production.up.railway.app
```

---

## Testing Your Server

### Test 1: Direct API Test

Create `test_api.py`:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://mwid.up.railway.app/api/v1/external"
API_KEY = os.environ.get("MWID_EXTERNAL_API_KEY")

headers = {"X-API-Key": API_KEY}

# Test sales endpoint
response = requests.get(f"{BASE_URL}/manual-sales?pageSize=2", headers=headers)
print(f"Status: {response.status_code}")
print(f"Data: {response.json()}")
```

Run it:
```bash
python3 test_api.py
```

### Test 2: MCP Server Test

Create `test_mcp.py`:

```python
import asyncio
import json
from MWAP_MCPserver import MWIDMCPServer

async def test():
    server = MWIDMCPServer()
    
    # Initialize
    if server.client is None:
        await server._initialize_client()
    
    # Test tool call
    result = await server._handle_tool_call("list_manual_sales", {
        "page": 1,
        "pageSize": 2
    })
    
    print(json.dumps(result, indent=2, default=str))
    
    await server.cleanup()

asyncio.run(test())
```

Run it:
```bash
python3 test_mcp.py
```

### Test 3: SSE Server Test

```bash
# Start server
python3 serve.py

# In another terminal, test health check
curl http://localhost:8000/

# Should return: "MWID MCP Server Running..."
```

---

## Common Patterns & Best Practices

### Pattern 1: Pagination

```python
# Always provide pagination for list endpoints
params = {
    "page": arguments.get("page", 1),
    "pageSize": arguments.get("pageSize", 100)
}
```

**Why?** Prevents loading too much data at once.

### Pattern 2: Optional Filters

```python
# Only add filters if they're provided
params = {}
for key in ["userId", "assetId", "country"]:
    if key in arguments:
        params[key] = arguments[key]
```

**Why?** Makes filters optional, more flexible.

### Pattern 3: Error Messages

```python
try:
    result = await api_call()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 403:
        return "Authentication failed. Please check your API key."
    elif e.response.status_code == 404:
        return "Resource not found."
    else:
        return f"HTTP Error {e.response.status_code}"
```

**Why?** Helps AI (and users) understand what went wrong.

### Pattern 4: Logging

```python
# Log important events
self.logger.info(f"Tool called: {name}")
self.logger.debug(f"GET {url}")
self.logger.error(f"Error: {error}", exc_info=True)
```

**Why?** Essential for debugging production issues.

### Pattern 5: Async/Await

```python
# Good - runs concurrently
async def get_data():
    result1 = await api_call_1()  # Waits for response
    result2 = await api_call_2()  # Then waits for this
    return result1, result2

# Better - runs in parallel
async def get_data():
    task1 = asyncio.create_task(api_call_1())
    task2 = asyncio.create_task(api_call_2())
    result1 = await task1  # Both run at same time
    result2 = await task2
    return result1, result2
```

**Why?** Async makes your server faster and more efficient.

---

## Complete Minimal Example

Here's a minimal MCP server (50 lines):

```python
#!/usr/bin/env python3
import asyncio
import json
from typing import List, Sequence

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent


class MinimalMCPServer:
    def __init__(self):
        self.server = Server("minimal-server")
        self.client = httpx.AsyncClient()
        self._register_handlers()
    
    def _register_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_joke",
                    description="Get a random joke",
                    inputSchema={"type": "object", "properties": {}, "required": []}
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            if name == "get_joke":
                response = await self.client.get("https://official-joke-api.appspot.com/random_joke")
                joke = response.json()
                result = f"{joke['setup']} - {joke['punchline']}"
                return [TextContent(type="text", text=result)]
            raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())


async def main():
    server = MinimalMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
```

**This is a complete working MCP server!**

Run it:
```bash
python3 minimal_server.py
```

---

## Building Your Own MCP Server - Checklist

### Phase 1: Setup
- [ ] Create project directory
- [ ] Create `requirements.txt` with dependencies
- [ ] Install packages: `pip install -r requirements.txt`
- [ ] Create `.env` file for secrets

### Phase 2: Core Server
- [ ] Create Settings class with Pydantic
- [ ] Create MCP Server class
- [ ] Initialize Server instance
- [ ] Set up logging

### Phase 3: Handlers
- [ ] Register `list_tools` handler
- [ ] Register `call_tool` handler
- [ ] Create `_get_all_tools()` method
- [ ] Create `_handle_tool_call()` router

### Phase 4: Tools
- [ ] Define Tool objects with schemas
- [ ] Implement tool handlers
- [ ] Add error handling
- [ ] Test each tool individually

### Phase 5: HTTP Client
- [ ] Create `_initialize_client()` method
- [ ] Implement authentication logic
- [ ] Create `_api_request()` helper
- [ ] Add request/response logging

### Phase 6: Run Methods
- [ ] Implement `run()` for stdio mode
- [ ] (Optional) Create `serve.py` for SSE mode
- [ ] Add cleanup logic
- [ ] Create main entry point

### Phase 7: Deployment
- [ ] Create Dockerfile
- [ ] Create railway.json
- [ ] Push to GitHub
- [ ] Deploy to Railway
- [ ] Set environment variables
- [ ] Generate domain

### Phase 8: Testing
- [ ] Test API directly
- [ ] Test MCP server locally
- [ ] Test with AI assistant
- [ ] Verify error handling

---

## Key Concepts Explained

### 1. Async/Await

```python
# Synchronous (blocking)
def get_data():
    response = requests.get(url)  # Waits here, blocks everything
    return response.json()

# Asynchronous (non-blocking)
async def get_data():
    response = await client.get(url)  # Waits here, but other tasks can run
    return response.json()
```

**Why async?** Your server can handle multiple AI requests at the same time.

### 2. Type Hints

```python
# Without type hints
def add(a, b):
    return a + b

# With type hints
def add(a: int, b: int) -> int:
    return a + b
```

**Benefits**: 
- Catches bugs early
- Better IDE autocomplete
- Self-documenting code

### 3. Pydantic Settings

```python
# Without Pydantic
api_url = os.environ.get("API_URL", "http://localhost")
timeout = int(os.environ.get("TIMEOUT", "30"))

# With Pydantic
class Settings(BaseSettings):
    api_url: str = Field(default="http://localhost")
    timeout: int = Field(default=30)

settings = Settings()  # Automatically loads from env vars
```

**Benefits**:
- Type validation
- Default values
- Error messages if required vars missing

### 4. JSON-RPC Protocol

MCP uses JSON-RPC for communication:

```json
// Request (AI → Server)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_manual_sales",
    "arguments": {"page": 1}
  }
}

// Response (Server → AI)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"data\": [...], \"total\": 3692}"
      }
    ]
  }
}
```

**You don't need to handle this manually** - the MCP library does it for you!

### 5. Tool Schema (JSON Schema)

```python
inputSchema = {
    "type": "object",           # Tool accepts an object
    "properties": {             # Define each parameter
        "page": {
            "type": "integer",  # Must be a number
            "description": "Page number",
            "default": 1        # Optional: default value
        },
        "email": {
            "type": "string",   # Must be text
            "description": "Filter by email"
        }
    },
    "required": ["email"]       # email is required, page is optional
}
```

**JSON Schema Types**:
- `string` - Text
- `integer` - Whole number
- `number` - Decimal number
- `boolean` - true/false
- `array` - List
- `object` - Dictionary

---

## Debugging Tips

### Enable Debug Logging

```bash
# In .env
MWID_DEBUG=true

# Or in environment
export MWID_DEBUG=true
python3 MWAP_MCPserver.py
```

### Check HTTP Requests

```python
# Add this to see all HTTP requests
logging.getLogger("httpx").setLevel(logging.DEBUG)
```

### Test Individual Functions

```python
# Test authentication
async def test_auth():
    server = MWIDMCPServer()
    await server._initialize_client()
    print(f"Authenticated: {server.authenticated}")

asyncio.run(test_auth())
```

### Common Errors

**Error**: `ValidationError: Extra inputs are not permitted`
**Fix**: Add `extra = "ignore"` to Settings Config

**Error**: `ClosedResourceError` in stdio mode
**Fix**: Normal when testing with echo/pipe - ignore it

**Error**: `403 Authentication failed`
**Fix**: Check API key or JWT token is correct

**Error**: `Module not found: mcp`
**Fix**: Run `pip install mcp`

---

## Next Steps

### Beginner Projects

1. **Weather MCP Server**
   - Tool: `get_weather(city: str)`
   - API: OpenWeatherMap
   - Learn: Basic tool creation

2. **News MCP Server**
   - Tool: `get_headlines(category: str)`
   - API: NewsAPI
   - Learn: Filtering and pagination

3. **Calculator MCP Server**
   - Tools: `add`, `subtract`, `multiply`, `divide`
   - No external API needed
   - Learn: Multiple tools, parameter validation

### Intermediate Projects

4. **Database MCP Server**
   - Tools: `query`, `insert`, `update`, `delete`
   - Database: PostgreSQL or SQLite
   - Learn: Database connections, SQL

5. **GitHub MCP Server**
   - Tools: `list_repos`, `create_issue`, `get_commits`
   - API: GitHub REST API
   - Learn: OAuth, complex APIs

### Advanced Topics

- **Streaming responses** - For long-running operations
- **Resource management** - Serve files, images, etc.
- **Prompts** - Pre-defined prompts for AI
- **Sampling** - Let server request AI completions
- **Error recovery** - Retry logic, circuit breakers

---

## Resources

### Official Documentation
- MCP Specification: https://spec.modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Pydantic Docs: https://docs.pydantic.dev/

### Example Servers
- SQLite MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite
- GitHub MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/github
- This Server: https://github.com/ServiceWare20/mwid-mcp-server

### Community
- MCP Discord: https://discord.gg/mcp
- GitHub Discussions: https://github.com/modelcontextprotocol/specification/discussions

---

## Glossary

**MCP** - Model Context Protocol. Standard for AI-to-tool communication.

**Tool** - A function that AI can call (like an API endpoint).

**stdio** - Standard Input/Output. Communication via stdin/stdout.

**SSE** - Server-Sent Events. HTTP-based real-time communication.

**JSON-RPC** - Remote Procedure Call protocol using JSON.

**Bearer Token** - Authentication token sent in `Authorization` header.

**API Key** - Authentication token sent in `X-API-Key` header.

**Schema** - Definition of data structure (what fields, types, etc.).

**Async/Await** - Non-blocking code that can handle multiple operations concurrently.

**ASGI** - Asynchronous Server Gateway Interface (like WSGI but async).

---

## FAQ

**Q: Do I need to know async/await?**
A: Basic understanding helps, but you can copy the patterns shown here.

**Q: Can I use a different language?**
A: Yes! MCP has SDKs for Python, TypeScript, and more.

**Q: How do I add a new tool?**
A: 1) Add Tool definition to `_get_all_tools()`, 2) Add handler to `_handle_tool_call()`

**Q: Why two modes (stdio and SSE)?**
A: Desktop apps use stdio, web apps use SSE. Different AI clients need different modes.

**Q: Can I use a database instead of an API?**
A: Yes! Replace `_api_request()` with database queries.

**Q: How do I handle authentication?**
A: Store tokens in Settings, add to request headers in `_get_headers()`.

**Q: What if my API is slow?**
A: Increase `request_timeout` in settings, use async for parallel requests.

**Q: Can I return images or files?**
A: Yes! Use `ImageContent` or `EmbeddedResource` instead of `TextContent`.

---

## Congratulations! 🎉

You now understand:
- ✅ What MCP is and why it's useful
- ✅ How to structure an MCP server
- ✅ How to define tools and handle calls
- ✅ How to authenticate with APIs
- ✅ How to deploy to production
- ✅ How to test and debug

**Your turn**: Try building your own MCP server!

Start small (weather API), then expand to more complex projects.

---

## Need Help?

- 📖 Read the code in `MWAP_MCPserver.py` - it's well-commented
- 🔍 Check `README.md` for feature documentation
- 🚀 See `CHATGPT_SETUP.md` for deployment guide
- 💬 Ask questions in MCP Discord community

Happy coding! 🚀
