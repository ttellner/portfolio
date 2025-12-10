# Fix All Three App Runner Errors - Step by Step

## Current Errors

1. ❌ **Health check failed on protocol `TCP` [Port: '8080']**
2. ❌ **Invalid Access Role in AuthenticationConfiguration**
3. ❌ **Failed to copy the image from ECR**

## Root Cause

- **Error #1:** App Runner is using TCP health checks instead of HTTP
- **Error #2 & #3:** IAM role doesn't have ECR permissions or wrong trust policy

## Fix Order (Do These In Sequence)

### ✅ Fix 1: IAM Role (MUST DO FIRST - Fixes errors #2 and #3)

**This is the most critical fix!**

1. Go to **App Runner → Your Service → Edit**
2. Scroll to **Security** section
3. Under **Access role**, you'll see your current role
4. **Select: "Create new service role"** (or choose this option)
5. App Runner will automatically:
   - Create a new role
   - Grant it ECR read permissions
   - Configure trust policy correctly
6. **Save** (don't deploy yet)

**Why this fixes errors #2 and #3:**
- Error #2: Invalid Access Role → New role has correct trust policy
- Error #3: Failed to copy image → New role has ECR permissions

### ✅ Fix 2: Health Check Configuration (Fixes error #1)

1. Still in **App Runner → Your Service → Edit**
2. Go to **Health check** section (or **Service** section)
3. **Protocol:** Change from `TCP` to **`HTTP`** ⚠️ CRITICAL!
4. **Path:** `/_stcore/health` (or just `/`)
5. **Port:** `8080`
6. **Save**

**If you don't see Health check settings:**
- Go to **Configuration → Service**
- Look for **Health check path** field
- Set to: `/_stcore/health`
- Ensure **Port** is `8080`

### ✅ Fix 3: Verify Port Configuration

1. In **App Runner → Your Service → Configuration → Service**
2. **Port:** Must be **`8080`** (not 8501)
3. **Save**

### ✅ Fix 4: Deploy

1. After saving all changes, click **Deploy** (or it may auto-deploy)
2. Wait 5-10 minutes
3. Check **Activity** tab for deployment status

## Complete Checklist

Before deploying, verify:

- [ ] **Access role:** "Create new service role" selected (or new role created)
- [ ] **Port:** `8080` (in Service configuration)
- [ ] **Health check protocol:** `HTTP` (NOT TCP)
- [ ] **Health check path:** `/_stcore/health` or `/`
- [ ] **Health check port:** `8080`
- [ ] **Image exists in ECR:** Check ECR → portfolio-streamlit → latest tag

## Why Each Fix Works

### Fix 1: IAM Role
- **Problem:** Old role lacks ECR permissions or has wrong trust policy
- **Solution:** New role automatically has `AmazonEC2ContainerRegistryReadOnly` policy
- **Result:** App Runner can authenticate and pull from ECR

### Fix 2: Health Check Protocol
- **Problem:** App Runner defaulted to TCP, but nginx needs HTTP
- **Solution:** Change to HTTP protocol
- **Result:** Health checks pass through nginx on port 8080

### Fix 3: Port Configuration
- **Problem:** App Runner might be configured for port 8501 (Streamlit) instead of 8080 (nginx)
- **Solution:** Ensure port is 8080 everywhere
- **Result:** App Runner connects to nginx, which proxies to Streamlit

## Architecture Reminder

```
App Runner → Port 8080 (nginx) → Port 8501 (Streamlit, localhost only)
```

- **App Runner** connects to **nginx** on port **8080**
- **nginx** proxies to **Streamlit** on port **8501** (internal)
- **Health checks** go through **nginx** (HTTP on port 8080)

## After Fixing

Once all three are fixed:
1. ✅ Health check passes (HTTP on 8080)
2. ✅ App Runner can pull image from ECR
3. ✅ Deployment succeeds
4. ✅ Service status becomes "Running"

## Still Failing?

If errors persist after all fixes:

1. **Delete the App Runner service**
2. **Create a new one** from scratch:
   - Source: ECR → `portfolio-streamlit:latest`
   - Port: `8080`
   - Health check: HTTP, path `/_stcore/health`
   - Access role: **"Create new service role"**
3. **Deploy**

This ensures a clean configuration.

## Quick Reference

| Setting | Value |
|---------|-------|
| **Port** | `8080` |
| **Health Protocol** | `HTTP` |
| **Health Path** | `/_stcore/health` |
| **Access Role** | Create new service role |
| **Image URI** | `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest` |

