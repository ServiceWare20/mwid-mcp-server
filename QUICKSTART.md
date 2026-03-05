# Quick Start: Push to GitHub and Deploy to Railway

## Step 1: Push to GitHub

```bash
cd ~/Work/GitHub_Repo/MWAD/mwid-mcp-server

# Create GitHub repo (you'll need to be logged into GitHub CLI)
gh repo create MetaWealth/mwid-mcp-server --public --description "MCP server for MWID Dashboard" --source . --remote origin

# Push code
git push -u origin main
```

**OR** create manually on GitHub.com:
1. Go to https://github.com/new
2. Repository name: `mwid-mcp-server`
3. Description: "Model Context Protocol server for MWID Dashboard"
4. Choose Public
5. Click "Create repository"
6. Then run:
   ```bash
   git remote add origin https://github.com/MetaWealth/mwid-mcp-server.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy to Railway

### Via GitHub (Recommended)

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select `MetaWealth/mwid-mcp-server`
4. Railway will auto-detect the Dockerfile and deploy

### Set Environment Variables in Railway

After deployment, click on your service → Variables tab → Add these:

```
MWID_API_URL=https://your-backend-api-url.com/api/v1
MWID_AUTH_METHOD=jwt
MWID_JWT_TOKEN=your-actual-jwt-token-here

# Required for Sales & Investors tools
MWID_EXTERNAL_API_URL=https://mwid.up.railway.app/api/v1/external
MWID_EXTERNAL_API_KEY=your-external-api-key-here
```

## Step 3: Get Your Railway URL

1. Go to Settings tab
2. Click "Generate Domain"
3. Your URL will be: `https://mwid-mcp-server-production.railway.app`

## Step 4: Configure ChatGPT

In ChatGPT settings, add MCP server:
```
https://mwid-mcp-server-production.railway.app/sse
```

## Done! 🎉

Your MCP server is now deployed and accessible company-wide!

## Updating the Server

When you make changes:

```bash
cd ~/Work/GitHub_Repo/MWAD/mwid-mcp-server
git add .
git commit -m "Update: description of changes"
git push

# Railway will auto-deploy the changes
```

## Monitoring

View logs in Railway dashboard or via CLI:
```bash
railway logs
```
