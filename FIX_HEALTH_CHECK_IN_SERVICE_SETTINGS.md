# Fix Health Check Protocol in Service Settings

## Problem

Health check settings are **only in Service Settings** (no separate Health Check section), but App Runner is still using **TCP** instead of **HTTP**.

## Solution: Look for Protocol Option in Service Settings

Since health check is in Service Settings, look for these fields:

### In Service Settings Section:

1. **Port:** `8080` ✅ (you already set this)

2. **Health check path:** `/_stcore/health` (or `/`)
   - This should be visible

3. **Health check protocol:** Look for a dropdown or field that says:
   - "Protocol" or "Health check protocol"
   - Options: `TCP` or `HTTP`
   - **Change to: `HTTP`** ⚠️ CRITICAL

4. **Health check port:** May be separate or may default to service port
   - Should be `8080` (same as service port)

## If You Don't See Protocol Option

Some App Runner configurations **don't show protocol** in the UI but use defaults. Try:

### Option 1: Check Advanced/Additional Settings

1. In **Service Settings**, look for:
   - "Advanced settings"
   - "Additional configuration"
   - "Show more options"
   - Expand/collapse arrows

2. Protocol might be hidden there

### Option 2: Use App Runner Configuration File

If the UI doesn't allow changing protocol, you might need to use `apprunner.yaml`:

1. Create `apprunner.yaml` in your repo root:

```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "No build needed, using pre-built image"
run:
  runtime-version: latest
  command: /app/start.sh
  network:
    port: 8080
  healthcheck:
    path: /_stcore/health
    interval: 30
    timeout: 10
    healthy-threshold: 1
    unhealthy-threshold: 5
```

**Note:** This might not work if you're using Container Registry (ECR) source. App Runner might ignore this for ECR deployments.

### Option 3: Delete and Recreate Service

If protocol can't be changed in existing service:

1. **Note your current settings:**
   - Image URI
   - Port: 8080
   - Access role name

2. **Delete the App Runner service**

3. **Create new service:**
   - Source: ECR → `portfolio-streamlit:latest`
   - During creation, you might see protocol options
   - Port: `8080`
   - Health check path: `/_stcore/health`
   - Access role: `AppRunner-ECR-AccessRole`

4. **Deploy**

## What to Look For in Service Settings

Scroll through **Service Settings** and look for:

- [ ] **Port:** `8080` ✅
- [ ] **Health check path:** `/_stcore/health` ✅
- [ ] **Health check protocol:** `HTTP` (or dropdown to change) ⚠️
- [ ] **Health check port:** `8080` (or uses service port)

## Alternative: Check if New Image is Deployed

The error might also be because:
- **Old image** (without nginx) is still deployed
- Health check fails because nginx isn't running on port 8080

**Check:**
1. **App Runner → Your Service → Configuration → Source**
2. **Image URI:** Should show recent timestamp
3. **Activity tab:** Check if latest deployment used the new image

## Quick Test

Can you see a field in Service Settings that says:
- "Protocol"
- "Health check protocol" 
- "Health check type"
- Or any dropdown/option related to TCP/HTTP?

If not, the protocol might be hardcoded or need to be set during service creation.

## Most Likely Solution

Since you can't find protocol in Service Settings, **the service might need to be recreated** with HTTP protocol set during initial creation, OR App Runner might automatically use HTTP when it detects the health check path.

**Try this:**
1. Set health check path to `/_stcore/health` in Service Settings
2. Save and deploy
3. App Runner might auto-detect HTTP based on the path

If that doesn't work, recreating the service is the most reliable solution.

