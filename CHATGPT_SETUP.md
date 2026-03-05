# ChatGPT MCP Server Setup Guide

## Current Status

Your MWID MCP server is:
- ✅ Code pushed to GitHub: `ServiceWare20/mwid-mcp-server`
- ✅ Railway project exists: https://railway.com/project/b1649c81-4a9c-48ae-a55d-9073395c7130
- ⚠️ Needs deployment/redeploy with latest code

## Step-by-Step Setup for ChatGPT

### Step 1: Deploy to Railway

1. **Open Railway Dashboard**:
   - Go to: https://railway.app/dashboard
   - Log in if needed

2. **Find Your Project**:
   - Navigate to: https://railway.com/project/b1649c81-4a9c-48ae-a55d-9073395c7130
   - Or create new project from GitHub repo: `ServiceWare20/mwid-mcp-server`

3. **Configure Environment Variables**:
   
   Click on your service → Variables tab → Add these:
   
   ```
   MWID_API_URL=https://mwid.up.railway.app/api/v1
   MWID_AUTH_METHOD=jwt
   MWID_JWT_TOKEN=
   MWID_EXTERNAL_API_URL=https://mwid.up.railway.app/api/v1/external
   MWID_EXTERNAL_API_KEY=mw_c113e903c344b676abcfae6a1443d9b2c91a37db1514c7848c0e8f480ab2022c
   MWID_REQUEST_TIMEOUT=30
   MWID_DEBUG=false
   ```
   
   **Note**: Leave `MWID_JWT_TOKEN` empty for now. The external API tools (sales & investors) will work with just the API key.

4. **Generate Domain** (if not already done):
   - Go to Settings tab
   - Click "Generate Domain"
   - Copy the URL (e.g., `https://mwid-mcp-server-production-xxxx.up.railway.app`)

5. **Deploy**:
   - Railway should auto-deploy from your GitHub repo
   - Check deployment logs for any errors

### Step 2: Configure ChatGPT

Once your Railway deployment is live, add the MCP server in ChatGPT:

#### Input Fields:

**Name**:
```
MWAD Dashboard
```

**Description** (optional):
```
Access MetaWealth Asset Launch Dashboard - query sales records and investor data
```

**MCP Server URL**:
```
https://your-railway-url.up.railway.app/sse
```
*Replace `your-railway-url` with your actual Railway domain*

**Authentication**:
```
None
```
*(Select "None" from dropdown - authentication is handled server-side via the API key)*

**Callback URL**: *(Leave as provided by ChatGPT)*

**OAuth Client ID**: *(Leave empty)*

**OAuth Client Secret**: *(Leave empty)*

### Step 3: Test in ChatGPT

Once configured, try these queries:

```
"List the latest manual sales records"
"Show me all investors from Romania"
"How many total sales records are in the system?"
"Get details for sale ID: b546f408-fcb9-4c96-82a8-66a43d647c9d"
```

## What Works vs What Doesn't

### ✅ WORKING NOW (External API - No JWT needed)

These features work immediately with just the API key:

**Sales Data** (3,692+ records available):
- `list_manual_sales` - List all sales with filters (userId, assetId, adjustmentType)
- `get_manual_sale` - Get specific sale by ID

**Investor Data** (1,064+ records available):
- `list_manual_investors` - List all investors with filters (email, userId, country)
- `get_manual_investor` - Get specific investor by ID

**Example Queries**:
```
"List all sales records"
"Show me investors from Romania"
"How many total sales do we have?"
"Get sale details for ID: b546f408-fcb9-4c96-82a8-66a43d647c9d"
"What's the total investment amount across all sales?"
"Find all sales for asset BESS 1"
```

### ⚠️ FUTURE FEATURES (Internal API - Requires JWT Token)

These features will return **403 Authentication Error** until JWT token is configured:

**Asset Management**:
- ❌ `list_assets` - List all assets (e.g., BESS 1, BESS 2)
- ❌ `get_asset` - Get asset details
- ❌ `create_asset` - Create new asset
- ❌ `update_asset` - Update asset
- ❌ `delete_asset` - Delete asset
- ❌ `get_asset_phases` - Get asset phases
- ❌ `get_asset_tasks` - Get asset tasks
- ❌ `calculate_minimum_time` - Calculate completion time

**Task Management**:
- ❌ `get_task`, `update_task`, `assign_task`, `unassign_task`
- ❌ `get_assigned_tasks`, `get_unassigned_tasks`
- ❌ `get_task_comments`, `create_task_comment`
- ❌ `get_task_progress`, `update_task_progress`

**User & Department Management**:
- ❌ `get_current_user`, `list_users`, `get_user`
- ❌ `list_departments`, `get_department`, `get_department_members`
- ❌ `get_my_team`, `get_users_for_assignment`

**Notifications & Workflows**:
- ❌ `get_notifications`, `mark_notification_read`
- ❌ `list_workflow_templates`, `apply_workflow_template`

**To Enable These Features**:
Add a valid JWT token to Railway environment variables:
```
MWID_JWT_TOKEN=your-jwt-token-here
```

You can obtain a JWT token by:
1. Logging into the MWID Dashboard
2. Opening browser DevTools → Application → Local Storage
3. Finding the JWT token
4. Adding it to Railway environment variables

## Troubleshooting

### "Connection Failed" in ChatGPT
- Verify Railway deployment is running (check Railway dashboard)
- Ensure the URL ends with `/sse`
- Check Railway logs for errors

### "Authentication Failed" (403)
- **For External API**: Verify `MWID_EXTERNAL_API_KEY` is set correctly in Railway
- **For Internal API**: Add valid `MWID_JWT_TOKEN` to Railway environment variables

### "No Tools Available"
- Wait 30 seconds after deployment for Railway to fully start
- Check Railway logs: `railway logs` (if CLI is linked)
- Verify the server is listening on the PORT provided by Railway

## Quick Deploy Commands (Optional)

If Railway CLI is linked to the project:

```bash
cd ~/Work/GitHub_Repo/MWAD/mwid-mcp-server

# Link to Railway project (interactive)
railway link

# Set environment variables
railway variables set MWID_EXTERNAL_API_KEY="mw_c113e903c344b676abcfae6a1443d9b2c91a37db1514c7848c0e8f480ab2022c"

# Deploy
railway up

# Get deployment URL
railway domain
```

## Example ChatGPT Queries

Once connected, you can ask ChatGPT:

- "How many sales records do we have in total?"
- "Show me the top 5 largest sales transactions"
- "List all investors from Romania"
- "What's the total investment amount across all sales?"
- "Find sales for asset ID: 536ce13d-2b4a-42fb-939e-efd86a9fdd70"
- "Show me recent sales from the last week"

## Support

- **Local Testing**: Run `python3 test_api.py` to verify API access
- **Server Logs**: Check Railway dashboard for deployment logs
- **Documentation**: See `README.md` and `CURSOR_SETUP.md`
