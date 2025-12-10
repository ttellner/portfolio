# Fix App Runner Health Check and IAM Role Issues

## Current Errors

1. ❌ **Health check failed on protocol `TCP` [Port: '8080']**
2. ❌ **Invalid Access Role in AuthenticationConfiguration**
3. ❌ **Failed to copy the image from ECR**

## Fix 1: App Runner Port Configuration

App Runner needs to be configured for **HTTP health checks on port 8080**:

1. Go to **App Runner → Your Service → Configuration → Health check**
2. **Protocol:** Should be **HTTP** (not TCP)
3. **Path:** Should be `/_stcore/health` (or just `/`)
4. **Port:** Should be **8080**
5. **Save** and **Deploy**

**OR** if you don't see Health check settings:

1. Go to **App Runner → Your Service → Configuration → Service**
2. **Port:** Should be **8080**
3. **Health check path:** `/_stcore/health` (or `/`)
4. **Save** and **Deploy**

## Fix 2: IAM Role (CRITICAL - This is causing the ECR error)

The "Invalid Access Role" error means App Runner can't authenticate to ECR.

### Option A: Create New Service Role (RECOMMENDED - Easiest)

1. Go to **App Runner → Your Service → Edit**
2. Go to **Security** section
3. Under **Access role**, select **"Create new service role"**
4. App Runner will automatically create a role with correct permissions
5. **Save** and **Deploy**

### Option B: Fix Existing Role

If you want to keep your existing role:

1. Go to **IAM → Roles**
2. Find your App Runner role (the one currently selected in App Runner)
3. Click on it
4. Go to **Trust relationships** tab
5. Click **Edit trust policy**
6. Ensure it has this (or similar):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

7. **Save**
8. Go to **Permissions** tab
9. Click **Add permissions → Attach policies**
10. Search for: `ECR` or use ARN: `arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly`
11. If still can't find it, create custom policy using `apprunner-ecr-policy.json`
12. **Save**

## Fix 3: Verify ECR Image Exists

Before deploying, verify the image exists:

1. Go to **ECR → Repositories → portfolio-streamlit**
2. Check if image with tag `latest` exists
3. If not, check **GitHub Actions** to see if build completed
4. If GitHub Actions failed, fix errors and re-run

## Complete Fix Steps (In Order)

### Step 1: Fix IAM Role (Do This First!)

**Easiest:** Use "Create new service role" in App Runner
- App Runner → Your Service → Edit → Security
- Select "Create new service role"
- Save

### Step 2: Verify Port Configuration

1. App Runner → Your Service → Configuration → Service
2. **Port:** `8080`
3. **Health check path:** `/_stcore/health` or `/`
4. **Protocol:** HTTP (not TCP)

### Step 3: Verify Image in ECR

1. ECR → portfolio-streamlit
2. Confirm `latest` tag exists
3. If missing, check GitHub Actions

### Step 4: Deploy

1. App Runner → Your Service → Deploy
2. Wait for deployment (~5-10 minutes)
3. Check **Activity** tab for status

## Why These Errors Happened

1. **Health check TCP error:** App Runner defaulted to TCP instead of HTTP
2. **Invalid Access Role:** The role either doesn't exist, has wrong trust policy, or lacks ECR permissions
3. **Failed to copy image:** Caused by #2 - App Runner can't authenticate to ECR

## After Fixing

Once all three are fixed:
- ✅ Health check should pass (HTTP on port 8080)
- ✅ App Runner can pull image from ECR
- ✅ Deployment should succeed

## Still Having Issues?

If "Create new service role" doesn't work:
1. **Delete the App Runner service**
2. **Create a new one** from ECR
3. **Use "Create new service role"** during creation
4. **Set port to 8080** during creation

