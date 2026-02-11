# MWID MCP Server

Model Context Protocol (MCP) server for the MetaWealth Asset Launch Dashboard. This server enables AI assistants like ChatGPT and Claude to interact with the MWID Dashboard API for asset management, task tracking, and team collaboration.

## Features

- 🔧 **Comprehensive Tool Suite**: 40+ tools for assets, tasks, users, departments, and teams
- 🔐 **Multiple Auth Methods**: JWT, Supabase, and Google OAuth support
- 📊 **Real-time Data**: Access to live dashboard data via REST API
- 🌐 **SSE Transport**: Server-Sent Events for reliable AI assistant connections
- 🚀 **Production Ready**: Dockerized and optimized for cloud deployment

## Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

### Step-by-Step Deployment

1. **Click "Deploy on Railway"** button above (or follow manual steps below)

2. **Set Environment Variables:**
   ```
   MWID_API_URL=https://your-backend-api.com/api/v1
   MWID_AUTH_METHOD=jwt
   MWID_JWT_TOKEN=your-jwt-token-here
   ```

3. **Get Your MCP Server URL:**
   Railway will provide a URL like: `https://mwid-mcp-server-production.railway.app`

4. **Configure Your AI Assistant:**
   - **ChatGPT**: Add MCP server at `https://your-app.railway.app/sse`
   - **Claude Desktop**: Add to `claude_desktop_config.json`

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

### Asset Management
- `list_assets` - List all assets
- `get_asset` - Get asset details
- `create_asset` - Create new asset
- `update_asset` - Update asset
- `get_asset_phases` - Get asset phases
- `get_asset_tasks` - Get tasks for asset

### Task Management
- `list_tasks` - List tasks
- `get_task` - Get task details
- `update_task` - Update task
- `assign_task` - Assign task to user
- `get_assigned_tasks` - Get user's assigned tasks
- `get_unassigned_tasks` - Get unassigned tasks
- `get_task_comments` - Get task comments
- `create_task_comment` - Add comment to task

### User & Department Management
- `list_users` - List all users
- `get_current_user` - Get authenticated user info
- `list_departments` - List departments
- `get_department_members` - Get department members
- `get_my_team` - Get user's team

### And many more...

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
