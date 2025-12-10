# Create AWS App Runner Service - Step by Step

## Prerequisites

✅ Docker image pushed to ECR with tag `latest`  
✅ Image URI: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`

## Step-by-Step Instructions

### Step 1: Navigate to App Runner

1. Go to AWS Console: https://console.aws.amazon.com/
2. Search for "App Runner" in the search bar
3. Click on **"App Runner"** service

### Step 2: Create Service

1. Click the **"Create service"** button (orange button, top right)

### Step 3: Configure Source

1. **Source type**: Select **"Container registry"** (NOT "Source code repository")
2. **Provider**: Select **"Amazon ECR"** (NOT "ECR Public")
3. **Container image URI**: You have two options:

   **Option A - Browse (Recommended)**:
   - Click the **browse/search icon** next to the field
   - Select repository: `portfolio-streamlit`
   - Select image tag: `latest`
   - The URI will auto-populate

   **Option B - Type manually**:
   - Type the full URI: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
   - Make sure to include `:latest` at the end

4. **Deployment trigger**: 
   - Select **"Automatic"** (deploys when new image is pushed)
   - Or "Manual" if you want to control deployments

5. Click **"Next"**

### Step 4: Configure Build Settings

**For Container Registry, you can skip this or configure:**

- **Build command**: Leave empty (Dockerfile handles it)
- **Start command**: Leave empty (uses Dockerfile CMD)
- **Port**: `8080` (nginx proxy port)

Click **"Next"**

### Step 5: Configure Service

1. **Service name**: `portfolio-streamlit` (or your preferred name)

2. **Virtual CPU**: 
   - Select **1 vCPU** (minimum, sufficient for most apps)
   - Increase if you expect high traffic

3. **Memory**: 
   - Select **2 GB** (minimum, sufficient for most apps)
   - Increase if you have large models/data

4. **Port**: `8080` (must match your Dockerfile EXPOSE - nginx runs on 8080)

5. **Environment variables** (optional):
   - Click "Add environment variable"
   - Add if needed:
     - `STREAMLIT_SERVER_PORT` = `8501`
     - `STREAMLIT_SERVER_ADDRESS` = `0.0.0.0`

6. Click **"Next"**

### Step 6: Configure Security

1. **VPC**: Leave as default (no VPC) unless you need VPC access

2. **IAM role**: 
   - App Runner will create a service role automatically
   - Or select existing role if you have one

3. **Encryption**: 
   - Leave default settings (AWS managed encryption)

4. Click **"Next"**

### Step 7: Review and Create

1. **Review all settings**:
   - Source: ECR → `portfolio-streamlit:latest`
   - Service name: `portfolio-streamlit`
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Port: 8501
   - Deployment: Automatic

2. **Cost estimate**: Review the estimated monthly cost

3. Click **"Create & deploy"**

### Step 8: Wait for Deployment

1. You'll see the service being created
2. **First deployment takes 5-10 minutes**:
   - Pulling image from ECR
   - Starting containers
   - Health checks

3. **Status will show**:
   - "Creating" → "Running" (when ready)

### Step 9: Access Your Application

Once status is **"Running"**:

1. Click on your service name
2. Find the **"Default domain"** (e.g., `xxxxx.us-east-1.awsapprunner.com`)
3. Click the URL or copy it
4. Your Streamlit app should be accessible!

## Important Settings Summary

| Setting | Value |
|---------|-------|
| **Source** | Container registry → Amazon ECR |
| **Image URI** | `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest` |
| **Deployment** | Automatic (recommended) |
| **Service name** | `portfolio-streamlit` |
| **CPU** | 1 vCPU (minimum) |
| **Memory** | 2 GB (minimum) |
| **Port** | `8080` |

## Troubleshooting

### "No tags available" Error

If you see this when browsing:
- Make sure the image was pushed with tag `latest`
- Verify in ECR: https://console.aws.amazon.com/ecr/repositories
- Check: `aws ecr describe-images --repository-name portfolio-streamlit --region us-east-1`

### Service Won't Start

1. **Check service logs**:
   - App Runner → Your service → Logs tab
   - Look for error messages

2. **Common issues**:
   - Port mismatch (should be 8501)
   - Health check failing
   - Application error

3. **Verify Dockerfile**:
   - `EXPOSE 8501` is set
   - `CMD` runs Streamlit on port 8501

### Health Check Failing

**IMPORTANT:** App Runner needs **HTTP health checks**, not TCP!

1. Go to **App Runner → Your Service → Configuration → Health check**
2. **Protocol:** Must be **HTTP** (not TCP)
3. **Path:** `/_stcore/health` or `/`
4. **Port:** `8080`

Your Dockerfile has:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8080/_stcore/health || exit 1
```

If health checks fail:
- Verify protocol is **HTTP** (not TCP) in App Runner config
- Check service logs
- Verify nginx and Streamlit are running
- Increase `start-period` if app takes longer to start

## After Deployment

### Automatic Deployments

With "Automatic" deployment trigger:
- Every time you push a new image to ECR with tag `latest`
- App Runner will automatically detect and deploy
- Takes 5-10 minutes per deployment

### Manual Deployments

If you selected "Manual":
- Go to App Runner → Your service
- Click "Deploy" → "Deploy latest revision"
- Or deploy a specific image tag

### Monitor Your Service

1. **Metrics**: App Runner → Your service → Metrics tab
2. **Logs**: App Runner → Your service → Logs tab
3. **Activity**: App Runner → Your service → Activity tab

## Cost Optimization

- **Auto-scaling**: App Runner automatically scales based on traffic
- **Idle time**: Service runs 24/7 (no auto-pause)
- **Estimated cost**: ~$7-15/month for 1 vCPU, 2GB (varies by region and usage)

## Next Steps

1. ✅ Service created and running
2. ✅ Access your app via the default domain
3. ✅ Test all features (Python projects, R projects with fallback)
4. ✅ Set up custom domain (optional)
5. ✅ Monitor usage and costs

## Quick Reference

- **App Runner Console**: https://console.aws.amazon.com/apprunner/
- **ECR Console**: https://console.aws.amazon.com/ecr/
- **Service URL**: Found in App Runner service details

Your app should now be live! 🚀

