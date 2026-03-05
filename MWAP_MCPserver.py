#!/usr/bin/env python3
"""
MWID Dashboard MCP Server

This MCP server provides AI models with access to the MetaWealth Asset Launch Dashboard API.
It enables natural language interaction with asset management, task tracking, user management,
and other dashboard features.

Author: MetaWealth Team
License: MIT
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

import httpx
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    api_url: str = Field(default="http://localhost:8080/api/v1", alias="MWID_API_URL")
    auth_method: str = Field(default="jwt", alias="MWID_AUTH_METHOD")  # jwt, supabase, or google
    jwt_token: str = Field(default="", alias="MWID_JWT_TOKEN")
    supabase_url: str = Field(default="", alias="MWID_SUPABASE_URL")
    supabase_key: str = Field(default="", alias="MWID_SUPABASE_KEY")
    supabase_email: str = Field(default="", alias="MWID_SUPABASE_EMAIL")
    supabase_password: str = Field(default="", alias="MWID_SUPABASE_PASSWORD")
    google_access_token: str = Field(default="", alias="MWID_GOOGLE_ACCESS_TOKEN")
    external_api_url: str = Field(default="https://mwid.up.railway.app/api/v1/external", alias="MWID_EXTERNAL_API_URL")
    external_api_key: str = Field(default="", alias="MWID_EXTERNAL_API_KEY")
    request_timeout: int = Field(default=30, alias="MWID_REQUEST_TIMEOUT")
    debug: bool = Field(default=False, alias="MWID_DEBUG")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class MWIDMCPServer:
    """MCP Server for MWID Dashboard API"""
    
    def __init__(self):
        self.settings = Settings()
        self.server = Server("mwid-dashboard")
        self.client: Optional[httpx.AsyncClient] = None
        self.authenticated = False
        
        # Configure logging
        log_level = logging.DEBUG if self.settings.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("mwid-mcp-server")
        
        # Register handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools"""
            return self._get_all_tools()
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Handle tool calls"""
            self.logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            try:
                # Initialize client if not already done
                if self.client is None:
                    await self._initialize_client()
                
                # Route to appropriate handler
                result = await self._handle_tool_call(name, arguments)
                
                # Format response
                if isinstance(result, dict) or isinstance(result, list):
                    response_text = json.dumps(result, indent=2, default=str)
                else:
                    response_text = str(result)
                
                return [TextContent(type="text", text=response_text)]
                
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
                self.logger.error(error_msg)
                return [TextContent(type="text", text=f"Error: {error_msg}")]
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=f"Error: {error_msg}")]
    
        self.authenticated = True
        self.logger.info("Successfully authenticated with Supabase")
    
    async def _initialize_client(self):
        """Initialize HTTP client and authenticate if needed"""
        self.client = httpx.AsyncClient(timeout=self.settings.request_timeout)
        
        # Authenticate based on method
        if self.settings.auth_method == "jwt" and self.settings.jwt_token:
            self.authenticated = True
            self.logger.info("Using JWT token authentication")
        elif self.settings.auth_method == "supabase":
            await self._authenticate_supabase()
        elif self.settings.auth_method == "google":
            await self._authenticate_google()
        else:
            self.logger.warning(f"No authentication configured or missing credentials for method: {self.settings.auth_method}. Internal API requests may fail with 401/403.")
    
    async def _authenticate_supabase(self):
        """Authenticate with Supabase and get JWT token"""
        if not all([self.settings.supabase_url, self.settings.supabase_key, 
                   self.settings.supabase_email, self.settings.supabase_password]):
            raise ValueError("Supabase credentials not fully configured")
        
        # Authenticate with Supabase
        auth_url = f"{self.settings.supabase_url}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": self.settings.supabase_key,
            "Content-Type": "application/json"
        }
        data = {
            "email": self.settings.supabase_email,
            "password": self.settings.supabase_password
        }
        
        response = await self.client.post(auth_url, headers=headers, json=data)
        response.raise_for_status()
        
        auth_data = response.json()
        self.settings.jwt_token = auth_data.get("access_token", "")
        self.authenticated = True
        self.logger.info("Successfully authenticated with Supabase")
    
    async def _authenticate_google(self):
        """Authenticate using Google OAuth token through Supabase"""
        if not all([self.settings.supabase_url, self.settings.supabase_key, 
                   self.settings.google_access_token]):
            raise ValueError("Google OAuth credentials not fully configured. Need SUPABASE_URL, SUPABASE_KEY, and GOOGLE_ACCESS_TOKEN")
        
        # Exchange Google access token for Supabase JWT
        auth_url = f"{self.settings.supabase_url}/auth/v1/token?grant_type=id_token"
        headers = {
            "apikey": self.settings.supabase_key,
            "Content-Type": "application/json"
        }
        data = {
            "provider": "google",
            "id_token": self.settings.google_access_token
        }
        
        try:
            response = await self.client.post(auth_url, headers=headers, json=data)
            response.raise_for_status()
            
            auth_data = response.json()
            self.settings.jwt_token = auth_data.get("access_token", "")
            self.authenticated = True
            self.logger.info("Successfully authenticated with Google OAuth via Supabase")
        except httpx.HTTPStatusError as e:
            self.logger.error(f"Google OAuth authentication failed: {e.response.text}")
            raise ValueError(f"Failed to authenticate with Google: {e.response.text}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.settings.jwt_token:
            headers["Authorization"] = f"Bearer {self.settings.jwt_token}"
        
        return headers
    
    async def _api_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Any:
        """Make authenticated API request"""
        if self.client is None:
            await self._initialize_client()
        
        url = f"{self.settings.api_url}{endpoint}"
        headers = self._get_headers()
        
        self.logger.debug(f"{method} {url}")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            
            response.raise_for_status()
            
            try:
                return response.json()
            except:
                return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code in [401, 403]:
                error_detail = (
                    f"Authentication failed (HTTP {e.response.status_code}) for internal API request. "
                    "Please verify MWID_JWT_TOKEN or Supabase/Google credentials in your environment."
                )
                self.logger.error(f"{error_detail} Response: {e.response.text}")
                raise ValueError(error_detail)
            raise
        except Exception as e:
            self.logger.error(f"Internal API error: {str(e)}")
            raise
    
    async def _external_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Any:
        """Make API request to external endpoints using X-API-Key auth"""
        if self.client is None:
            await self._initialize_client()
        
        if not self.settings.external_api_key:
            raise ValueError("External API key not configured. Set MWID_EXTERNAL_API_KEY in .env")
        
        url = f"{self.settings.external_api_url}{endpoint}"
        headers = {
            "X-API-Key": self.settings.external_api_key,
            "Content-Type": "application/json"
        }
        
        self.logger.debug(f"EXTERNAL {method} {url}")
        
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
                error_detail = f"Authentication failed (HTTP {e.response.status_code}). Please verify MWID_EXTERNAL_API_KEY in your environment variables."
                self.logger.error(f"{error_detail} Response: {e.response.text}")
                raise ValueError(error_detail)
            raise
        except Exception as e:
            self.logger.error(f"External API error: {str(e)}")
            raise
    
    def _get_all_tools(self) -> List[Tool]:
        """Get all available tools"""
        return [
            # Authentication Tools
            Tool(
                name="get_current_user",
                description="Get information about the currently authenticated user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Asset Management Tools
            Tool(
                name="list_assets",
                description="List all assets in the dashboard with optional filtering",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["Pre-Launch", "VIP Pre-Sale", "Live", "Closed"],
                            "description": "Filter assets by status"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_asset",
                description="Get detailed information about a specific asset by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            Tool(
                name="create_asset",
                description="Create a new asset with workflow template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the asset"
                        },
                        "target_amount": {
                            "type": "number",
                            "description": "Target amount for the asset"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["Pre-Launch", "VIP Pre-Sale", "Live", "Closed"],
                            "description": "Initial status of the asset",
                            "default": "Pre-Launch"
                        },
                        "launch_date": {
                            "type": "string",
                            "description": "Launch date in ISO format (YYYY-MM-DD)",
                            "format": "date"
                        }
                    },
                    "required": ["name", "target_amount"]
                }
            ),
            Tool(
                name="update_asset",
                description="Update an existing asset's details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the asset"
                        },
                        "target_amount": {
                            "type": "number",
                            "description": "New target amount"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["Pre-Launch", "VIP Pre-Sale", "Live", "Closed"],
                            "description": "New status"
                        },
                        "launch_date": {
                            "type": "string",
                            "description": "New launch date in ISO format"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            Tool(
                name="delete_asset",
                description="Delete an asset (admin only, cascades to phases and tasks)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset to delete"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            Tool(
                name="get_asset_phases",
                description="Get all phases for a specific asset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            Tool(
                name="get_asset_tasks",
                description="Get all tasks for a specific asset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            Tool(
                name="calculate_minimum_time",
                description="Calculate the minimum predicted time to complete all tasks for an asset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset"
                        }
                    },
                    "required": ["asset_id"]
                }
            ),
            
            # Task Management Tools
            Tool(
                name="get_task",
                description="Get detailed information about a specific task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="update_task",
                description="Update a task's details (title, status, description, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task to update"
                        },
                        "title": {
                            "type": "string",
                            "description": "New title for the task"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["To Do", "In Progress", "Blocked", "Done"],
                            "description": "New status for the task"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description"
                        },
                        "detailed_description": {
                            "type": "string",
                            "description": "New detailed description"
                        },
                        "due_date": {
                            "type": "string",
                            "description": "New due date in ISO format"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "New start date in ISO format"
                        },
                        "estimated_duration_days": {
                            "type": "integer",
                            "description": "Estimated duration in days"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="assign_task",
                description="Assign a task to one or more users",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "UUID of the user to assign (for single assignment)"
                        },
                        "user_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of user UUIDs (for multiple assignments)"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="unassign_task",
                description="Remove task assignment from a user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="get_task_comments",
                description="Get all comments for a specific task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="create_task_comment",
                description="Add a comment to a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        },
                        "content": {
                            "type": "string",
                            "description": "Comment content"
                        }
                    },
                    "required": ["task_id", "content"]
                }
            ),
            Tool(
                name="get_task_progress",
                description="Get instruction progress for a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        }
                    },
                    "required": ["task_id"]
                }
            ),
            Tool(
                name="update_task_progress",
                description="Update instruction completion status for a task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "UUID of the task"
                        },
                        "progress": {
                            "type": "object",
                            "description": "Progress data with instruction indices and completion status"
                        }
                    },
                    "required": ["task_id", "progress"]
                }
            ),
            Tool(
                name="get_my_department_tasks",
                description="Get all tasks for the current user's department",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_assigned_tasks",
                description="Get tasks assigned to a specific user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "UUID of the user"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="get_unassigned_tasks",
                description="Get unassigned tasks for a specific department",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department_id": {
                            "type": "string",
                            "description": "UUID of the department"
                        }
                    },
                    "required": ["department_id"]
                }
            ),
            
            # Phase Management Tools
            Tool(
                name="update_phase",
                description="Update a phase's details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "string",
                            "description": "UUID of the phase to update"
                        },
                        "name": {
                            "type": "string",
                            "description": "New name for the phase"
                        },
                        "status": {
                            "type": "string",
                            "description": "New status for the phase"
                        }
                    },
                    "required": ["phase_id"]
                }
            ),
            Tool(
                name="get_phase_tasks",
                description="Get all tasks for a specific phase",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_id": {
                            "type": "string",
                            "description": "UUID of the phase"
                        }
                    },
                    "required": ["phase_id"]
                }
            ),
            
            # User Management Tools
            Tool(
                name="list_users",
                description="List all users (admin only)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_user",
                description="Get detailed information about a specific user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "UUID of the user"
                        }
                    },
                    "required": ["user_id"]
                }
            ),
            Tool(
                name="get_users_for_assignment",
                description="Get list of users available for task assignment",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_my_team",
                description="Get the current user's team members",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_department_members",
                description="Get all members of a specific department",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department_id": {
                            "type": "string",
                            "description": "UUID of the department"
                        }
                    },
                    "required": ["department_id"]
                }
            ),
            
            # Department Management Tools
            Tool(
                name="list_departments",
                description="List all departments in the organization",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_department",
                description="Get detailed information about a specific department",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department_id": {
                            "type": "string",
                            "description": "UUID of the department"
                        }
                    },
                    "required": ["department_id"]
                }
            ),
            Tool(
                name="get_department_stats",
                description="Get statistics for a specific department",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "department_id": {
                            "type": "string",
                            "description": "UUID of the department"
                        }
                    },
                    "required": ["department_id"]
                }
            ),
            
            # Notification Tools
            Tool(
                name="get_notifications",
                description="Get notifications for the current user",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of notifications to return",
                            "default": 50
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="get_unread_notification_count",
                description="Get the count of unread notifications",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="mark_notification_read",
                description="Mark a specific notification as read",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "notification_id": {
                            "type": "string",
                            "description": "UUID of the notification"
                        }
                    },
                    "required": ["notification_id"]
                }
            ),
            Tool(
                name="mark_all_notifications_read",
                description="Mark all notifications as read for the current user",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            
            # Workflow Template Tools
            Tool(
                name="list_workflow_templates",
                description="List all available workflow templates",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_workflow_template",
                description="Get detailed information about a specific workflow template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "UUID of the workflow template"
                        }
                    },
                    "required": ["template_id"]
                }
            ),
            Tool(
                name="apply_workflow_template",
                description="Apply a workflow template to an asset",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "UUID of the workflow template"
                        },
                        "asset_id": {
                            "type": "string",
                            "description": "UUID of the asset"
                        }
                    },
                    "required": ["template_id", "asset_id"]
                }
            ),
            
            # Manual Sales Tools (External API)
            Tool(
                name="list_manual_sales",
                description="List manual sales records with optional filtering and pagination. Returns sales data including amount, currency, asset info, approval status, and investor details.",
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
                    "required": []
                }
            ),
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
                    "required": ["sale_id"]
                }
            ),
            
            # Manual Investors Tools (External API)
            Tool(
                name="list_manual_investors",
                description="List manual investor records with optional filtering and pagination. Returns investor profiles including name, email, country, and account type.",
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
            
            # Internal Investor Records Tools (Legacy Support)
            Tool(
                name="list_investor_records",
                description="List internal investor records (Legacy tool using internal API)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_investor_record",
                description="Get detailed internal information about a specific investor record (Legacy tool using internal API)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "record_id": {
                            "type": "string",
                            "description": "UUID of the investor record"
                        }
                    },
                    "required": ["record_id"]
                }
            ),
        ]
    
    async def _handle_tool_call(self, name: str, arguments: dict) -> Any:
        """Route tool calls to appropriate handlers"""
        
        # Authentication Tools
        if name == "get_current_user":
            return await self._api_request("GET", "/users/current")
        
        # Asset Management Tools
        elif name == "list_assets":
            params = {}
            if "status" in arguments:
                params["status"] = arguments["status"]
            return await self._api_request("GET", "/assets", params=params)
        
        elif name == "get_asset":
            asset_id = arguments["asset_id"]
            return await self._api_request("GET", f"/assets/{asset_id}")
        
        elif name == "create_asset":
            payload = {
                "name": arguments["name"],
                "target_amount": arguments["target_amount"],
                "status": arguments.get("status", "Pre-Launch")
            }
            if "launch_date" in arguments:
                payload["launch_date"] = arguments["launch_date"]
            return await self._api_request("POST", "/assets", json_data=payload)
        
        elif name == "update_asset":
            asset_id = arguments.pop("asset_id")
            return await self._api_request("PUT", f"/assets/{asset_id}", json_data=arguments)
        
        elif name == "delete_asset":
            asset_id = arguments["asset_id"]
            return await self._api_request("DELETE", f"/admin/assets/{asset_id}")
        
        elif name == "get_asset_phases":
            asset_id = arguments["asset_id"]
            return await self._api_request("GET", f"/assets/{asset_id}/phases")
        
        elif name == "get_asset_tasks":
            asset_id = arguments["asset_id"]
            return await self._api_request("GET", f"/assets/{asset_id}/tasks")
        
        elif name == "calculate_minimum_time":
            asset_id = arguments["asset_id"]
            return await self._api_request("GET", f"/assets/{asset_id}/minimum-time")
        
        # Task Management Tools
        elif name == "get_task":
            task_id = arguments["task_id"]
            return await self._api_request("GET", f"/tasks/{task_id}/data")
        
        elif name == "update_task":
            task_id = arguments.pop("task_id")
            return await self._api_request("PUT", f"/tasks/{task_id}", json_data=arguments)
        
        elif name == "assign_task":
            task_id = arguments["task_id"]
            if "user_ids" in arguments:
                payload = {"user_ids": arguments["user_ids"]}
                return await self._api_request("POST", f"/tasks/{task_id}/assign-multiple", json_data=payload)
            elif "user_id" in arguments:
                payload = {"user_id": arguments["user_id"]}
                return await self._api_request("POST", f"/tasks/{task_id}/assign", json_data=payload)
            else:
                raise ValueError("Either user_id or user_ids must be provided")
        
        elif name == "unassign_task":
            task_id = arguments["task_id"]
            return await self._api_request("DELETE", f"/tasks/{task_id}/assign")
        
        elif name == "get_task_comments":
            task_id = arguments["task_id"]
            return await self._api_request("GET", f"/tasks/{task_id}/comments")
        
        elif name == "create_task_comment":
            task_id = arguments["task_id"]
            payload = {"content": arguments["content"]}
            return await self._api_request("POST", f"/tasks/{task_id}/comments", json_data=payload)
        
        elif name == "get_task_progress":
            task_id = arguments["task_id"]
            return await self._api_request("GET", f"/tasks/{task_id}/progress")
        
        elif name == "update_task_progress":
            task_id = arguments["task_id"]
            payload = arguments["progress"]
            return await self._api_request("PUT", f"/tasks/{task_id}/progress", json_data=payload)
        
        elif name == "get_my_department_tasks":
            return await self._api_request("GET", "/tasks/my-department")
        
        elif name == "get_assigned_tasks":
            user_id = arguments["user_id"]
            return await self._api_request("GET", f"/tasks/assigned/{user_id}")
        
        elif name == "get_unassigned_tasks":
            dept_id = arguments["department_id"]
            return await self._api_request("GET", f"/tasks/unassigned/{dept_id}")
        
        # Phase Management Tools
        elif name == "update_phase":
            phase_id = arguments.pop("phase_id")
            return await self._api_request("PUT", f"/phases/{phase_id}", json_data=arguments)
        
        elif name == "get_phase_tasks":
            phase_id = arguments["phase_id"]
            return await self._api_request("GET", f"/phases/{phase_id}/tasks")
        
        # User Management Tools
        elif name == "list_users":
            return await self._api_request("GET", "/admin/users")
        
        elif name == "get_user":
            user_id = arguments["user_id"]
            return await self._api_request("GET", f"/admin/users/{user_id}")
        
        elif name == "get_users_for_assignment":
            return await self._api_request("GET", "/users/for-assignment")
        
        elif name == "get_my_team":
            return await self._api_request("GET", "/teams/my-team")
        
        elif name == "get_department_members":
            dept_id = arguments["department_id"]
            return await self._api_request("GET", f"/teams/{dept_id}/members")
        
        # Department Management Tools
        elif name == "list_departments":
            return await self._api_request("GET", "/departments")
        
        elif name == "get_department":
            dept_id = arguments["department_id"]
            return await self._api_request("GET", f"/departments/{dept_id}")
        
        elif name == "get_department_stats":
            dept_id = arguments["department_id"]
            return await self._api_request("GET", f"/departments/{dept_id}/stats")
        
        # Notification Tools
        elif name == "get_notifications":
            params = {}
            if "limit" in arguments:
                params["limit"] = arguments["limit"]
            return await self._api_request("GET", "/notifications", params=params)
        
        elif name == "get_unread_notification_count":
            return await self._api_request("GET", "/notifications/unread-count")
        
        elif name == "mark_notification_read":
            notif_id = arguments["notification_id"]
            return await self._api_request("PUT", f"/notifications/{notif_id}/read")
        
        elif name == "mark_all_notifications_read":
            return await self._api_request("PUT", "/notifications/mark-all-read")
        
        # Workflow Template Tools
        elif name == "list_workflow_templates":
            return await self._api_request("GET", "/workflow-templates")
        
        elif name == "get_workflow_template":
            template_id = arguments["template_id"]
            return await self._api_request("GET", f"/workflow-templates/{template_id}")
        
        elif name == "apply_workflow_template":
            template_id = arguments["template_id"]
            asset_id = arguments["asset_id"]
            return await self._api_request("POST", f"/workflow-templates/{template_id}/apply", 
                                          json_data={"asset_id": asset_id})
        
        # Manual Sales Tools (External API)
        elif name == "list_manual_sales":
            params = {}
            for key in ["page", "pageSize", "userId", "assetId", "adjustmentType"]:
                if key in arguments:
                    params[key] = arguments[key]
            return await self._external_api_request("GET", "/manual-sales", params=params)
        
        elif name == "get_manual_sale":
            sale_id = arguments["sale_id"]
            return await self._external_api_request("GET", f"/manual-sales/{sale_id}")
        
        # Manual Investors Tools (External API)
        elif name == "list_manual_investors":
            params = {}
            for key in ["page", "pageSize", "email", "userId", "country"]:
                if key in arguments:
                    params[key] = arguments[key]
            return await self._external_api_request("GET", "/manual-investors", params=params)
        
        elif name == "get_manual_investor":
            investor_id = arguments["investor_id"]
            return await self._external_api_request("GET", f"/manual-investors/{investor_id}")
        
        # Internal Investor Records Tools (Legacy Support)
        elif name == "list_investor_records":
            return await self._api_request("GET", "/investor-records")
        
        elif name == "get_investor_record":
            record_id = arguments["record_id"]
            return await self._api_request("GET", f"/investor-records/{record_id}")
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            self.logger.info("MWID MCP Server starting...")
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()


async def main():
    """Main entry point"""
    server = MWIDMCPServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
