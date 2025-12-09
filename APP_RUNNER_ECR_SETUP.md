# Updated App Runner + ECR Setup Instructions

## Current Issue

App Runner requires an image tag to be selected, but if no images have been pushed to ECR yet, there won't be any tags available.

## Solution: Push an Image First

You need to push at least one image to ECR before configuring App Runner. Here are your options:

### Option 1: Use GitHub Actions (Recommended - Easiest)

This is the **best solution** - it builds and pushes automatically:

1. **Add GitHub Secrets** (if not done already):
   - Go to: `https://github.com/ttellner/portfolio/settings/secrets/actions`
   - Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

2. **Push the workflow file**:
   ```powershell
   git add .github/workflows/deploy.yml
   git commit -m "Add auto-deploy workflow"
   git push origin main
   ```

3. **Wait for workflow to complete**:
   - Go to: `https://github.com/ttellner/portfolio/actions`
   - Wait for the workflow to finish (takes ~15-20 minutes for first build)

4. **Then configure App Runner** (see steps below)

### Option 2: Push Manually (Quick Test)

If you want to test immediately:

1. **Check what's in ECR**:
   ```powershell
   .\check_ecr_images.ps1
   ```

2. **If no images, push one**:
   ```powershell
   .\build_then_push.ps1
   ```
   (This may still have network issues, but worth trying)

3. **Then configure App Runner**

---

## Updated App Runner Configuration Steps

### Step 1: Verify Image Exists in ECR

First, make sure you have an image pushed:

```powershell
.\check_ecr_images.ps1
```

You should see at least one image with a tag (usually `latest`).

### Step 2: Configure App Runner

1. **Go to AWS App Runner Console**
   - Navigate to: https://console.aws.amazon.com/apprunner/

2. **Create Service** (or Edit existing)

3. **Configure Source**:
   - **Source type**: Select **"Container registry"**
   - **Provider**: Select **"Amazon ECR"** (NOT ECR Public)
   - **Container image URI**: You have two options:
     
     **Option A - Browse and Select:**
     - Click the **browse/search icon** next to the field
     - Select your repository: `portfolio-streamlit`
     - **Important**: After selecting the repository, you should see tags appear
     - Select tag: `latest` (or whatever tag exists)
     
     **Option B - Type Full URI:**
     - Type the full URI with tag: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
     - This includes the tag at the end (`:latest`)

4. **Deployment settings**:
   - **Deployment trigger**: 
     - **Automatic** = Deploys when new image is pushed (recommended)
     - **Manual** = You manually trigger deployments
   - **Tag**: Leave as `latest` (or select the tag you want)

5. **Configure Service**:
   - **Service name**: `portfolio-streamlit`
   - **Virtual CPU**: 1 vCPU (minimum)
   - **Memory**: 2 GB (minimum)
   - **Port**: `8501`

6. **Create & Deploy**

---

## About ECR Public

**No, you cannot use Amazon ECR Public** for this because:
- ECR Public is for public images (like Docker Hub)
- Your repository is private
- App Runner needs access to your private ECR repository

You must use **Amazon ECR** (private), not ECR Public.

---

## Troubleshooting: "No tags available"

If you see "No tags available" in App Runner:

### Check 1: Verify image exists
```powershell
.\check_ecr_images.ps1
```

### Check 2: Verify you're in the right region
- Make sure your ECR repository is in `us-east-1`
- Make sure App Runner is looking in the same region

### Check 3: Verify permissions
- Your AWS user needs `ecr:DescribeImages` permission
- Check IAM permissions for your user

### Check 4: Try typing the full URI
Instead of browsing, type:
```
083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

---

## Recommended Workflow

1. **Set up GitHub Actions** (one-time, 5 minutes)
   - Add secrets
   - Push workflow file
   
2. **Wait for first build** (~20 minutes)
   - Check: https://github.com/ttellner/portfolio/actions
   
3. **Verify image in ECR** (1 minute)
   ```powershell
   .\check_ecr_images.ps1
   ```
   Should show `latest` tag

4. **Configure App Runner** (5 minutes)
   - Use full URI: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
   - Or browse and select `latest` tag
   
5. **Done!** Every future push auto-deploys

---

## Quick Fix: Push Image Now

If you want to push an image right now to test App Runner:

```powershell
# Option 1: Try the build script (may have network issues)
.\build_then_push.ps1

# Option 2: Use GitHub Actions (more reliable)
# Just push the workflow file and wait
```

The GitHub Actions approach is more reliable because it builds in GitHub's infrastructure, avoiding your local network issues.

