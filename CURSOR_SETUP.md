# MWID MCP Server - Cursor Setup Guide

## ✅ Setup Complete

The MWID MCP server has been successfully configured in Cursor and is ready to use!

## Configuration Summary

### MCP Server Location
- **Config File**: `~/.cursor/mcp.json`
- **Server Name**: `MWID-Dashboard`
- **Script Path**: `/Users/paiusanionut/Work/GitHub_Repo/MWAD/mwid-mcp-server/MWAP_MCPserver.py`

### Authentication Status

#### ✅ Working: External API (Sales & Investors)
- **Method**: X-API-Key authentication
- **API Key**: Configured and working
- **Endpoints**: 
  - `list_manual_sales` - List sales records (3,692 total records available)
  - `get_manual_sale` - Get specific sale by ID
  - `list_manual_investors` - List investor records (1,064 total records available)
  - `get_manual_investor` - Get specific investor by ID

#### ⚠️ Not Configured: Internal API (Assets, Tasks, Users)
- **Method**: JWT Bearer token required
- **Status**: `MWID_JWT_TOKEN` is empty
- **Impact**: Internal API tools will return 401/403 errors
- **Tools Affected**: 
  - Asset management (list_assets, get_asset, create_asset, etc.)
  - Task management (list_tasks, get_task, update_task, etc.)
  - User management (list_users, get_user, etc.)
  - Department management
  - Notifications
  - Workflow templates

## Available Tools (40+)

### ✅ External API Tools (Working)
1. `list_manual_sales` - List sales with filtering and pagination
2. `get_manual_sale` - Get specific sale details
3. `list_manual_investors` - List investors with filtering and pagination
4. `get_manual_investor` - Get specific investor details

### ⚠️ Internal API Tools (Need JWT Token)
5. `get_current_user` - Get authenticated user info
6. `list_assets` - List all assets
7. `get_asset` - Get asset details
8. `create_asset` - Create new asset
9. `update_asset` - Update asset
10. `delete_asset` - Delete asset
11. `get_asset_phases` - Get asset phases
12. `get_asset_tasks` - Get tasks for asset
13. `calculate_minimum_time` - Calculate completion time
14. `get_task` - Get task details
15. `update_task` - Update task
16. `assign_task` - Assign task to user
17. `unassign_task` - Remove task assignment
18. `get_task_comments` - Get task comments
19. `create_task_comment` - Add comment to task
20. `get_task_progress` - Get task progress
21. `update_task_progress` - Update task progress
22. `get_my_department_tasks` - Get department tasks
23. `get_assigned_tasks` - Get user's assigned tasks
24. `get_unassigned_tasks` - Get unassigned tasks
25. `update_phase` - Update phase details
26. `get_phase_tasks` - Get phase tasks
27. `list_users` - List all users
28. `get_user` - Get user details
29. `get_users_for_assignment` - Get assignable users
30. `get_my_team` - Get team members
31. `get_department_members` - Get department members
32. `list_departments` - List departments
33. `get_department` - Get department details
34. `get_department_stats` - Get department statistics
35. `get_notifications` - Get user notifications
36. `get_unread_notification_count` - Get unread count
37. `mark_notification_read` - Mark notification as read
38. `mark_all_notifications_read` - Mark all as read
39. `list_workflow_templates` - List workflow templates
40. `get_workflow_template` - Get template details
41. `apply_workflow_template` - Apply template to asset

## Testing Results

### ✅ External API Test (Successful)
```bash
$ python3 test_api.py
✅ All tests completed.
- Sales: 3,692 records available
- Investors: 1,064 records available
```

### ✅ MCP Server Test (Successful)
```bash
$ python3 MWAP_MCPserver.py
✅ Server initialized successfully
✅ Tools list retrieved (40+ tools)
✅ External API calls working (200 OK)
```

## How to Use in Cursor

### For Sales & Investor Data (Working Now)
You can now use these tools in Cursor:

```
"List all manual sales records from the last month"
"Show me investors from Romania"
"Get details for sale ID: b546f408-fcb9-4c96-82a8-66a43d647c9d"
```

### For Internal API (Requires JWT Token)
To enable internal API tools, you need to:

1. **Option A: Get JWT Token Manually**
   - Log into the MWID Dashboard
   - Extract JWT token from browser (localStorage or cookies)
   - Add to `~/.cursor/mcp.json` under `MWID_JWT_TOKEN`

2. **Option B: Use Supabase Authentication**
   Update `~/.cursor/mcp.json`:
   ```json
   "MWID_AUTH_METHOD": "supabase",
   "MWID_SUPABASE_URL": "your-supabase-url",
   "MWID_SUPABASE_KEY": "your-supabase-key",
   "MWID_SUPABASE_EMAIL": "your-email",
   "MWID_SUPABASE_PASSWORD": "your-password"
   ```

3. **Option C: Use Google OAuth**
   Update `~/.cursor/mcp.json`:
   ```json
   "MWID_AUTH_METHOD": "google",
   "MWID_GOOGLE_ACCESS_TOKEN": "your-google-token",
   "MWID_SUPABASE_URL": "your-supabase-url",
   "MWID_SUPABASE_KEY": "your-supabase-key"
   ```

## Restart Cursor

After making configuration changes, restart Cursor to reload the MCP server:
1. Cmd+Shift+P (or Ctrl+Shift+P)
2. Type "Reload Window"
3. Press Enter

## Troubleshooting

### 403 Authentication Error
- **For External API**: Check that `MWID_EXTERNAL_API_KEY` is correct
- **For Internal API**: Add valid `MWID_JWT_TOKEN` or configure Supabase/Google auth

### Server Not Starting
- Ensure Python 3.13+ is installed: `python3 --version`
- Verify dependencies: `pip list | grep mcp`
- Check logs in Cursor's Output panel

### Tools Not Appearing
- Restart Cursor after configuration changes
- Check MCP server status in Cursor settings
- Look for errors in Cursor's Output panel

## Changes Made

1. ✅ Added MWID-Dashboard to `~/.cursor/mcp.json`
2. ✅ Installed required Python packages (`mcp`, `uvicorn`, etc.)
3. ✅ Fixed Settings validation error (added `extra = "ignore"`)
4. ✅ Fixed authentication logging bug
5. ✅ Tested external API tools successfully

## Next Steps

1. **Restart Cursor** to load the MCP server
2. **Test external API tools** - they should work immediately
3. **Add JWT token** if you need internal API access (assets, tasks, users)
4. **Optional**: Deploy to Railway for company-wide access (see README.md)
