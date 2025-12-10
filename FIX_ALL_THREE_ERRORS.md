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
2. Scroll to **Deployment Settings** section (NOT Security)
3. Under **Access role** (for ECR access), you'll see your current role
4. **Select: "Create new service role"**
5. **Name the role:** Use something like `AppRunner-ECR-AccessRole` or `portfolio-streamlit-ecr-role`
   - App Runner will create this role automatically
   - It will grant ECR read permissions
   - It will configure trust policy correctly
6. **Note:** The "Instance role" under Security is different - that's for AWS service access, not ECR
7. **Save** (don't deploy yet)

**Why this fixes errors #2 and #3:**
- Error #2: Invalid Access Role → New role has correct trust policy
- Error #3: Failed to copy image → New role has ECR permissions

**Important:** Do NOT use the custom policy role (`apprunner-ecr-policy.json`) - that was for manual setup. Let App Runner create the role automatically.

### ✅ Fix 2: Health Check Configuration (Fixes error #1)

1. Still in **App Runner → Your Service → Edit**
2. Go to **Service Settings** section
3. Find **Health check** configuration
4. **Protocol:** Change from `TCP` to **`HTTP`** ⚠️ CRITICAL!
5. **Path:** `/_stcore/health` (or just `/`)
6. **Port:** `8080`
7. **Save**

**If you don't see Health check settings:**
- Look in **Service Settings** section
- Find **Health check path** field
- Set to: `/_stcore/health`
- Ensure **Port** is `8080` in the same section

### ✅ Fix 3: Verify Port Configuration

1. In **App Runner → Your Service → Edit → Service Settings**
2. **Port:** Must be **`8080`** (not 8501)
3. This should be in the same section as Health check
4. **Save**

### ✅ Fix 4: Deploy

1. After saving all changes, click **Deploy** (or it may auto-deploy)
2. Wait 5-10 minutes
3. Check **Activity** tab for deployment status

## Complete Checklist

Before deploying, verify:

- [ ] **Access role (Deployment Settings):** "Create new service role" selected and named
- [ ] **Port (Service Settings):** `8080` (not 8501)
- [ ] **Health check protocol (Service Settings):** `HTTP` (NOT TCP)
- [ ] **Health check path (Service Settings):** `/_stcore/health` or `/`
- [ ] **Health check port (Service Settings):** `8080`
- [ ] **Image exists in ECR:** Check ECR → portfolio-streamlit → latest tag

**Note:** All Service Settings (port, health check) are in the same section.

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

