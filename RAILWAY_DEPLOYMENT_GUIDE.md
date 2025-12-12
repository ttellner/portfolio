# Railway Deployment Guide - Complete Setup

## How Railway Works

Railway is **much simpler** than AWS:
- ✅ **Connects directly to GitHub** - Auto-deploys on push
- ✅ **Uses your Dockerfile automatically** - No configuration needed
- ✅ **Custom domains** - Easy setup, free SSL
- ✅ **WebSocket support** - Works out of the box
- ✅ **No ECR needed** - Railway builds from GitHub

## Work Estimate

**Time:** 15-30 minutes (much faster than ECS Fargate!)  
**Complexity:** Easy (simpler than App Runner!)

## Step-by-Step Setup

### Step 1: Sign Up for Railway (2 minutes)

1. Go to https://railway.app
2. **Sign up** with GitHub (recommended - easier integration)
3. **Authorize** Railway to access your GitHub account

### Step 2: Create New Project (3 minutes)

1. **Railway Dashboard → New Project**
2. **Deploy from GitHub repo**
3. **Select your repository:** `ttellner/portfolio`
4. **Select branch:** `main`
5. **Railway automatically detects Dockerfile** ✅

### Step 3: Configure Service (5 minutes)

Railway will:
- ✅ **Detect your Dockerfile** automatically
- ✅ **Build the Docker image** (uses your Dockerfile)
- ✅ **Start the container** (runs your CMD)

**You may need to set:**
1. **Port:** Railway auto-detects `EXPOSE 8080`, but verify:
   - **Settings → Networking → Port:** `8080`
2. **Health check:** (optional)
   - **Settings → Healthcheck → Path:** `/_stcore/health`

### Step 4: Deploy (Automatic - 10-15 minutes)

Railway will:
1. **Clone your repo**
2. **Build Docker image** using your Dockerfile
3. **Push to Railway's registry** (no ECR needed!)
4. **Deploy container**
5. **Assign URL:** `your-app-name.up.railway.app`

**First deployment takes 10-15 minutes** (builds image)

### Step 5: Add Custom Domain (5 minutes)

1. **Railway → Your Project → Settings → Domains**
2. **Add custom domain**
3. **Enter domain:** `app.ttellnerai.com` (or `ttellnerai.com`)
4. **Railway provides DNS instructions:**
   - **Type:** CNAME
   - **Name:** `app` (or `@` for root)
   - **Value:** `your-app-name.up.railway.app`
5. **Add DNS record** in your domain provider (Route 53, etc.)
6. **Wait for verification** (5-30 minutes)
7. **SSL certificate** - Railway provides automatically! ✅

## How It Works with Your Setup

### Your Dockerfile

Railway uses your existing Dockerfile **exactly as-is**:
- ✅ Builds from `FROM ubuntu:22.04`
- ✅ Installs Python, R, nginx
- ✅ Copies your code
- ✅ Runs `CMD ["/app/start.sh"]`
- ✅ Exposes port 8080

**No changes needed!**

### Your GitHub Repo

Railway:
- ✅ **Watches your GitHub repo** for pushes
- ✅ **Auto-deploys** when you push to `main`
- ✅ **Builds from your Dockerfile**
- ✅ **No manual deployment needed**

### Your nginx Setup

Your nginx configuration works perfectly:
- ✅ nginx listens on port 8080
- ✅ Railway routes traffic to port 8080
- ✅ WebSocket connections work (Railway supports them!)
- ✅ Health checks work

## Comparison: Railway vs AWS

| Feature | Railway | AWS (ECS Fargate) |
|---------|---------|-------------------|
| **Setup time** | 15-30 min | 1-2 hours |
| **Complexity** | Easy | Medium |
| **GitHub integration** | Native | Manual (via ECR) |
| **Dockerfile** | Auto-detected | Manual task definition |
| **Custom domain** | 5 min setup | 15 min (Route 53 + ACM) |
| **SSL certificate** | Automatic | Manual (ACM) |
| **WebSocket support** | ✅ Yes | ✅ Yes (ALB) |
| **Cost** | ~$5-20/month | ~$46-50/month |
| **ECR needed?** | ❌ No | ✅ Yes |

## Railway Advantages

✅ **Much simpler** - No ECR, no task definitions, no load balancers  
✅ **Faster setup** - 15-30 minutes vs 1-2 hours  
✅ **Auto-deploy** - Push to GitHub, Railway deploys automatically  
✅ **Free SSL** - Automatic certificates  
✅ **WebSocket support** - Works out of the box  
✅ **Custom domain** - Easy setup  
✅ **Lower cost** - More affordable than AWS  

## Cost Estimate

**Railway pricing:**
- **Hobby plan:** $5/month (500 hours free, then $0.000463/hour)
- **Pro plan:** $20/month (unlimited hours)
- **Your app:** ~$5-10/month (depending on usage)

**Much cheaper than AWS!**

## What Happens on Each Push

1. **You push to GitHub:**
   ```powershell
   git push origin main
   ```

2. **Railway detects push** (via webhook)

3. **Railway builds new image:**
   - Uses your Dockerfile
   - Builds in Railway's environment
   - No ECR needed!

4. **Railway deploys:**
   - Stops old container
   - Starts new container
   - Zero-downtime deployment

5. **Done!** (~5-10 minutes after push)

## Environment Variables (If Needed)

If you need environment variables:

1. **Railway → Your Project → Variables**
2. **Add variable:**
   - **Key:** `STREAMLIT_SERVER_PORT`
   - **Value:** `8501`
3. **Railway injects** into container automatically

## Monitoring & Logs

**Railway provides:**
- ✅ **Real-time logs** - See container output
- ✅ **Metrics** - CPU, memory usage
- ✅ **Deployment history** - See all deployments
- ✅ **Error tracking** - See what went wrong

## Custom Domain Setup Details

### For Subdomain (Recommended)

**DNS Record:**
```
Type: CNAME
Name: app
Value: your-app-name.up.railway.app
TTL: 3600
```

**Result:** `https://app.ttellnerai.com`

### For Root Domain

**DNS Record:**
```
Type: CNAME (or ALIAS if supported)
Name: @
Value: your-app-name.up.railway.app
TTL: 3600
```

**Result:** `https://ttellnerai.com`

**Note:** Some DNS providers don't allow CNAME on root. Railway provides ALIAS instructions if needed.

## SSL Certificate

- ✅ **Automatic** - Railway provides free SSL
- ✅ **Auto-renewal** - No manual work
- ✅ **HTTPS only** - Forces HTTPS
- ✅ **Works immediately** - After DNS verification

## Troubleshooting

### Build Fails

**Check:**
- Railway → Deployments → Click failed deployment → Logs
- Look for Docker build errors
- Verify Dockerfile syntax

### App Doesn't Start

**Check:**
- Railway → Your Project → Logs
- Look for nginx/Streamlit startup errors
- Verify port is 8080

### Custom Domain Not Working

**Check:**
- DNS records are correct
- DNS propagation (can take up to 48 hours)
- Railway → Settings → Domains → Verify status

## Migration from App Runner

**What you can keep:**
- ✅ Your Dockerfile (works as-is)
- ✅ Your nginx.conf (works as-is)
- ✅ Your start.sh (works as-is)
- ✅ Your GitHub repo (just connect it)

**What you don't need:**
- ❌ ECR (Railway builds from GitHub)
- ❌ Task definitions
- ❌ Load balancers
- ❌ Target groups

**Much simpler!**

## Summary

**Railway is the easiest option:**
- ✅ **15-30 minutes** to set up
- ✅ **Uses your Dockerfile** automatically
- ✅ **Connects to GitHub** - auto-deploys
- ✅ **Custom domain** - 5 minute setup
- ✅ **WebSocket support** - works out of the box
- ✅ **Free SSL** - automatic
- ✅ **Lower cost** - $5-10/month vs $46-50/month

**Perfect for your use case!**

## Quick Start

1. **Sign up:** https://railway.app (with GitHub)
2. **New Project → Deploy from GitHub**
3. **Select your repo**
4. **Wait for deployment** (~10-15 minutes)
5. **Add custom domain** (5 minutes)
6. **Done!** ✅

Your app will work with WebSockets and custom domain!

