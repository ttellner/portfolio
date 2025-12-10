# Correct Order to Fix Everything

## Current Situation

- ❌ Health check failing (HTTP protocol is correct, but old image doesn't have nginx)
- ❌ IAM role not being created by App Runner
- ❌ Can't pull image from ECR

## The Problem

You're trying to fix App Runner config **before** the new Docker image exists. The old image doesn't have nginx, so health checks fail even with correct HTTP protocol.

## Correct Fix Order

### Step 1: Create IAM Role Manually (Do This First!)

**App Runner's "Create new service role" isn't working, so create it manually:**

1. **IAM → Roles → Create role**
2. **Trusted entity:** AWS service → **App Runner**
3. **Permissions:** Attach `AmazonEC2ContainerRegistryReadOnly`
4. **Name:** `AppRunner-ECR-AccessRole`
5. **Create role**

### Step 2: Use the Role in App Runner

1. **App Runner → Your Service → Edit**
2. **Deployment Settings → Access role**
3. **Select:** "Use existing service role"
4. **Choose:** `AppRunner-ECR-AccessRole`
5. **Save** (don't deploy yet)

### Step 3: Push Dockerfile (Build New Image)

```powershell
git add Dockerfile nginx.conf start.sh
git commit -m "Add nginx for WebSocket support"
git push origin main
```

**Wait for:**
- GitHub Actions to build (~20 minutes)
- Image to appear in ECR with `latest` tag

### Step 4: Configure App Runner (After Image Exists)

1. **App Runner → Your Service → Edit**
2. **Service Settings:**
   - **Port:** `8080`
   - **Health check protocol:** `HTTP`
   - **Health check path:** `/_stcore/health`
3. **Save and Deploy**

### Step 5: Wait for Deployment

- App Runner pulls new image (with nginx)
- Health checks pass (nginx is running)
- Service becomes "Running"

## Why This Order?

1. **IAM role first:** Without it, App Runner can't pull ANY images
2. **Build image second:** Need the new image with nginx
3. **Configure App Runner third:** Once image exists, configure to use it
4. **Deploy last:** Everything is ready

## Current Error Explanation

**"Health check failed on HTTP"** means:
- ✅ Protocol is correct (HTTP)
- ❌ But old image doesn't have nginx on port 8080
- ❌ So health check fails

**"Invalid Access Role"** means:
- ❌ App Runner can't use the role to authenticate to ECR
- ❌ Need to create role manually

## Quick Checklist

- [ ] **Create IAM role manually** (IAM → Roles → Create role)
- [ ] **Attach ECR permissions** (`AmazonEC2ContainerRegistryReadOnly`)
- [ ] **Use role in App Runner** (Deployment Settings → Access role)
- [ ] **Push Dockerfile** (git push)
- [ ] **Wait for image in ECR** (check ECR console)
- [ ] **Configure App Runner** (port 8080, HTTP health check)
- [ ] **Deploy**

## Most Important

**Create the IAM role manually first!** App Runner's auto-create isn't working for you.

See `FIX_IAM_ROLE_MANUALLY.md` for detailed steps.

