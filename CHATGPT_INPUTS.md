# ChatGPT MCP Server Configuration - Quick Reference

## 📋 Exact Inputs for ChatGPT Form

Copy and paste these values into the ChatGPT "New App" form:

---

### Name
```
MWAD Dashboard
```

### Icon (optional)
```
Skip for now
```

### Description (optional)
```
Access MetaWealth sales and investor data
```

### MCP Server URL
```
https://YOUR-RAILWAY-URL.up.railway.app/sse
```

⚠️ **IMPORTANT**: Replace `YOUR-RAILWAY-URL` with your actual Railway deployment URL.

To get your Railway URL:
1. Go to https://railway.app/dashboard
2. Open your `mwid-mcp-server` project
3. Click on the service
4. Go to Settings → Generate Domain (if not already done)
5. Copy the domain (e.g., `mwid-mcp-server-production-abc123.up.railway.app`)
6. Use: `https://mwid-mcp-server-production-abc123.up.railway.app/sse`

### Authentication
```
None
```
**Action**: Change dropdown from "OAuth" to "None"

### Callback URL
```
(Leave as auto-filled by ChatGPT)
```

### OAuth Client ID (Optional)
```
(Leave empty)
```

### OAuth Client Secret (Optional)
```
(Leave empty)
```

---

## ✅ Then Click

1. Check the box: ☑️ "I understand and want to continue"
2. Click the **"Create"** button

---

## 🚀 Quick Deploy to Railway

If you haven't deployed yet:

1. **Go to**: https://railway.app/new
2. **Click**: "Deploy from GitHub repo"
3. **Select**: `ServiceWare20/mwid-mcp-server`
4. **Add Environment Variables**:
   ```
   MWID_API_URL=https://mwid.up.railway.app/api/v1
   MWID_AUTH_METHOD=jwt
   MWID_JWT_TOKEN=
   MWID_EXTERNAL_API_URL=https://mwid.up.railway.app/api/v1/external
   MWID_EXTERNAL_API_KEY=mw_c113e903c344b676abcfae6a1443d9b2c91a37db1514c7848c0e8f480ab2022c
   MWID_REQUEST_TIMEOUT=30
   MWID_DEBUG=false
   ```
5. **Generate Domain** in Settings
6. **Copy URL** and use it in ChatGPT configuration

---

## 💬 What You Can Ask ChatGPT

Once configured, try these queries:

### Sales Queries (✅ Working)
```
"List all manual sales records"
"Show me the top 10 largest sales"
"How many total sales do we have?"
"Get details for sale ID: b546f408-fcb9-4c96-82a8-66a43d647c9d"
"What's the total investment amount across all sales?"
"Find all sales for BESS 1 asset"
"Show me sales from February 2026"
```

### Investor Queries (✅ Working)
```
"List all investors"
"Show me investors from Romania"
"How many investors do we have?"
"Find investor by email: catalinruja@yahoo.com"
"List all business account investors"
"Show me investors created by hubspot-sync"
```

### Asset Queries (❌ Not Working - Requires JWT)
```
"List all assets" → Will return 403 error
"Get BESS 1 asset details" → Will return 403 error
"Show me asset phases" → Will return 403 error
```

---

## 🔧 Troubleshooting

### "Connection Failed"
- ✅ Check Railway deployment is running
- ✅ Verify URL ends with `/sse`
- ✅ Check Railway logs for errors

### "Authentication Failed" (403)
- ✅ For **Sales/Investors**: Verify `MWID_EXTERNAL_API_KEY` in Railway
- ❌ For **Assets/Tasks**: Need to add `MWID_JWT_TOKEN` (future feature)

### "No Response"
- ✅ Wait 30 seconds after deployment
- ✅ Check Railway logs: Look for "Uvicorn running" message
- ✅ Test the endpoint: `curl https://your-url.up.railway.app/`

---

## 📊 Current Limitations

**✅ What Works** (No JWT needed):
- Sales data: 3,692+ records
- Investor data: 1,064+ records
- Filtering and pagination
- Read-only access

**❌ What Doesn't Work** (Needs JWT token):
- Asset management (list_assets, get_asset, etc.)
- Task management
- User & department data
- Notifications
- Workflow templates

To enable these features, you need to add a valid JWT token to Railway environment variables.

---

## 📚 More Documentation

- `README.md` - Full server documentation
- `CHATGPT_SETUP.md` - Detailed ChatGPT setup guide
- `CURSOR_SETUP.md` - Cursor IDE configuration
- `QUICKSTART.md` - Quick deployment guide
