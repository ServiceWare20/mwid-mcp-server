# MWID MCP Server

Model Context Protocol (MCP) server for the MetaWealth Asset Launch Dashboard. This server enables AI assistants like ChatGPT and Claude to interact with the MWID Dashboard API for asset management, task tracking, and team collaboration.

## Features

- 🔧 **Comprehensive Tool Suite**: 40+ tools for assets, tasks, users, departments, and teams
- 🔐 **Multiple Auth Methods**: JWT, Supabase, and Google OAuth support
- 📊 **Real-time Data**: Access to live dashboard data via REST API
- 🌐 **SSE Transport**: Server-Sent Events for reliable AI assistant connections
- 🚀 **Production Ready**: Dockerized and optimized for cloud deployment

## Deploy to Railway

### Step-by-Step Deployment

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Railway configuration"
   git push origin main
   ```

2. **Create New Project on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository: `mwid-mcp-server`

3. **Configure Environment Variables:**
   
   In Railway Dashboard → Variables, add these required variables:
   ```
   MWID_API_URL=https://your-backend-api.com/api/v1
   MWID_AUTH_METHOD=jwt
   MWID_JWT_TOKEN=your-jwt-token-here
   ```
   
   Optional variables:
   ```
   MWID_REQUEST_TIMEOUT=30
   MWID_DEBUG=false
   ```

4. **Railway Auto-Detection:**
   
   Railway will automatically detect:
   - ✅ `Dockerfile` for containerized deployment
   - ✅ `railway.json` for build/deploy configuration
   - ✅ `Procfile` for process management
   - ✅ Port configuration (Railway sets `PORT` automatically)

5. **Deploy:**
   
   Railway will automatically build and deploy. Monitor the deployment in the Railway dashboard logs.

6. **Get Your MCP Server URL:**
   
   Railway provides a public URL like: `https://mwid-mcp-server-production-xxxx.up.railway.app`
   
   You can also set a custom domain in Railway settings.

7. **Configure Your AI Assistant:**
   
   - **ChatGPT**: Add MCP server at `https://your-railway-url.railway.app/sse`
   - **Claude Desktop**: Add to `claude_desktop_config.json` (see configuration below)

## Manual Deployment

### Prerequisites

- Python 3.13+
- pip
- Docker (optional)

### Local Development

```bash
# Clone the repository
git clone https://github.com/MetaWealth/mwid-mcp-server.git
cd mwid-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
MWID_API_URL=http://localhost:8080/api/v1
MWID_AUTH_METHOD=jwt
MWID_JWT_TOKEN=your-token-here
EOF

# Run the server
python serve.py
```

Server will start on `http://localhost:8000`

### Docker Deployment

```bash
# Build image
docker build -t mwid-mcp-server .

# Run container
docker run -p 8000:8000 \
  -e MWID_API_URL=https://your-api.com/api/v1 \
  -e MWID_AUTH_METHOD=jwt \
  -e MWID_JWT_TOKEN=your-token \
  mwid-mcp-server
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MWID_API_URL` | Yes | `http://localhost:8080/api/v1` | Backend API endpoint |
| `MWID_AUTH_METHOD` | Yes | `jwt` | Authentication method: `jwt`, `supabase`, or `google` |
| `MWID_JWT_TOKEN` | For JWT | - | JWT authentication token |
| `MWID_SUPABASE_URL` | For Supabase | - | Supabase project URL |
| `MWID_SUPABASE_KEY` | For Supabase | - | Supabase anon key |
| `MWID_GOOGLE_ACCESS_TOKEN` | For Google | - | Google OAuth access token |
| `PORT` | No | `8000` | Server port (Railway sets automatically) |

### ChatGPT Configuration

Add the MCP server in ChatGPT settings:

```
Server URL: https://your-app.railway.app/sse
```

### Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mwid-dashboard": {
      "url": "https://your-app.railway.app/sse"
    }
  }
}
```

## Available Tools

The server provides 40+ tools organized into these categories:

### ✅ Working Features (External API - No JWT Required)

These tools work immediately with just the `MWID_EXTERNAL_API_KEY`:

#### Sales & Investor Data
- `list_manual_sales` - List sales records with filtering/pagination (3,692+ records)
  - Filters: `userId`, `assetId`, `adjustmentType`
  - Pagination: `page`, `pageSize` (max 500)
- `get_manual_sale` - Get specific sale details by ID
- `list_manual_investors` - List investor records with filtering/pagination (1,064+ records)
  - Filters: `email`, `userId`, `country`
  - Pagination: `page`, `pageSize` (max 500)
- `get_manual_investor` - Get specific investor details by ID

### ⚠️ Future Features (Internal API - Requires JWT Token)

These tools require `MWID_JWT_TOKEN` to be configured. They will return 403 errors until JWT authentication is set up.

#### Asset Management
- `get_current_user` - Get authenticated user info
- `list_assets` - List all assets
- `get_asset` - Get asset details
- `create_asset` - Create new asset
- `update_asset` - Update asset
- `delete_asset` - Delete asset (admin only)
- `get_asset_phases` - Get asset phases
- `get_asset_tasks` - Get tasks for asset
- `calculate_minimum_time` - Calculate task completion time

#### Task Management
- `get_task` - Get task details
- `update_task` - Update task
- `assign_task` - Assign task to user
- `unassign_task` - Remove task assignment
- `get_assigned_tasks` - Get user's assigned tasks
- `get_unassigned_tasks` - Get unassigned tasks
- `get_my_department_tasks` - Get department tasks
- `get_task_comments` - Get task comments
- `create_task_comment` - Add comment to task
- `get_task_progress` - Get task progress
- `update_task_progress` - Update task progress

#### Phase Management
- `update_phase` - Update phase details
- `get_phase_tasks` - Get tasks for a phase

#### User & Department Management
- `list_users` - List all users (admin only)
- `get_user` - Get user details
- `get_users_for_assignment` - Get assignable users
- `get_my_team` - Get team members
- `get_department_members` - Get department members
- `list_departments` - List departments
- `get_department` - Get department details
- `get_department_stats` - Get department statistics

#### Notifications
- `get_notifications` - Get user notifications
- `get_unread_notification_count` - Get unread count
- `mark_notification_read` - Mark notification as read
- `mark_all_notifications_read` - Mark all as read

#### Workflow Templates
- `list_workflow_templates` - List available templates
- `get_workflow_template` - Get template details
- `apply_workflow_template` - Apply template to asset

#### Legacy Internal API
- `list_investor_records` - List internal investor records
- `get_investor_record` - Get internal investor record details

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  ChatGPT/   │  SSE    │  MCP Server  │  HTTP   │   MWID      │
│   Claude    │◄────────┤  (Railway)   │────────►│  Backend    │
└─────────────┘         └──────────────┘         └─────────────┘
                         /sse endpoint             REST API
                         /messages endpoint        (8080)
```

## Troubleshooting

### Connection Timeout

**Issue**: ChatGPT times out connecting to the server

**Solution**:
- Ensure Railway deployment is running (check Railway dashboard)
- Verify environment variables are set correctly
- Check Railway logs for errors: `railway logs`

### 403 Forbidden

**Issue**: Getting 403 errors

**Solution**:
- Check `MWID_JWT_TOKEN` is valid and not expired
- Verify backend API is accessible from Railway
- Ensure backend CORS settings allow Railway domain

### Empty Responses

**Issue**: Tools return empty data

**Solution**:
- Verify `MWID_API_URL` points to correct backend
- Check JWT token has necessary permissions
- Test backend API directly with curl/Postman

## Development

### Running Tests

```bash
python test_server.py
```

### Debug Logging

Enable debug logging:

```bash
export MWID_DEBUG=true
python serve.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/MetaWealth/mwid-mcp-server/issues
- Documentation: https://your-docs-site.com
- Email: support@metawealth.co
