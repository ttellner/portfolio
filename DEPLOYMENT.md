# AWS App Runner Deployment Guide

This guide explains how to deploy the Streamlit portfolio application to AWS App Runner using Docker.

## Prerequisites

- GitHub repository with this code
- AWS account with App Runner access
- Docker (for local testing, optional)

## Dockerfile Overview

The Dockerfile:
- Uses Ubuntu 22.04 as base image
- Installs Python 3.11
- Installs R and R packages (including Seurat for bioinformatics projects)
- Installs all Python dependencies from `requirements.txt`
- Sets up Streamlit to run on port 8501
- Includes health checks for AWS App Runner

## Deployment Steps

### 1. Push to GitHub

Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Add Dockerfile for AWS App Runner deployment"
git push origin main
```

### 2. Build and Push Docker Image to ECR

**Option A: Using the automated script (Recommended)**

1. **For Linux/Mac:**
   ```bash
   # Edit deploy_to_ecr.sh and set your AWS_ACCOUNT_ID
   chmod +x deploy_to_ecr.sh
   ./deploy_to_ecr.sh
   ```

2. **For Windows (PowerShell):**
   ```powershell
   # Edit deploy_to_ecr.ps1 and set your $AWS_ACCOUNT_ID
   .\deploy_to_ecr.ps1
   ```

**Option B: Manual commands**

```bash
# 1. Authenticate Docker to ECR (replace with your AWS account ID and region)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com

# 2. Create ECR repository (one-time, if it doesn't exist)
aws ecr create-repository --repository-name portfolio-streamlit --region us-east-1

# 3. Build Docker image
docker build -t portfolio-streamlit .

# 4. Tag image for ECR
docker tag portfolio-streamlit:latest <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest

# 5. Push to ECR
docker push <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

### 3. Deploy to AWS App Runner

**Important**: You MUST complete Step 2 (build and push to ECR) BEFORE creating the App Runner service. The ECR repository and image must exist first.

1. **Navigate to AWS App Runner Console**
   - Go to AWS Console → App Runner
   - Click "Create service"

2. **Configure Source**
   - Select **"Source: Container registry"** (NOT GitHub)
   - Choose **"Amazon ECR"**
   - **Container image URI**: You have two options:
     - **Option A (Browse)**: Click "Browse" and select `portfolio-streamlit` from the list (only appears after Step 2 is complete)
     - **Option B (Type)**: Enter the full URI: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
       - Replace `083738448444` with your AWS account ID if different
       - Replace `us-east-1` with your region if different
   - **Image tag**: `latest` (or leave blank if included in URI)
   - **Deployment trigger**: "Automatic" (deploys when you push new images)

3. **Configure Service**
   - Service name: `portfolio-streamlit` (or your preferred name)
   - Virtual CPU: 1 vCPU (minimum, increase if needed)
   - Memory: 2 GB (minimum, increase if needed)
   - Port: `8501`
   - Environment variables (optional):
     - `STREAMLIT_SERVER_PORT=8501`
     - `STREAMLIT_SERVER_ADDRESS=0.0.0.0`

4. **Review and Create**
   - Review all settings
   - Click "Create & deploy"

### 4. Build Time

**Important**: The first build will take 15-20 minutes because:
- Installing R and R packages
- Installing Seurat (large package, ~10-15 minutes)
- Installing Python packages including TensorFlow

Subsequent builds will be faster due to Docker layer caching.

### 5. Access Your Application

Once deployment completes:
- App Runner will provide a service URL (e.g., `https://xxxxx.us-east-1.awsapprunner.com`)
- Your Streamlit app will be accessible at this URL

## Updating Your Deployment

When you make changes to your code:

1. **Build and push new image to ECR:**
   ```bash
   # Use the deployment script or manual commands from Step 2
   ./deploy_to_ecr.sh  # or deploy_to_ecr.ps1 on Windows
   ```

2. **App Runner will automatically detect the new image** (if automatic deployment is enabled) and redeploy your service.

## Local Testing

To test the Docker image locally:

```bash
# Build the image
docker build -t portfolio-streamlit .

# Run the container
docker run -p 8501:8501 portfolio-streamlit

# Access at http://localhost:8501
```

## Customization

### Skip Seurat Installation (Faster Builds)

If you don't need Seurat for bioinformatics projects, comment out the Seurat installation in the Dockerfile:

```dockerfile
# Comment out or remove this section:
# RUN Rscript -e "if (requireNamespace('BiocManager', quietly = TRUE)) { \
#     BiocManager::install('Seurat', ask=FALSE, update=FALSE, quiet=TRUE) \
#     }" || echo "Seurat installation failed..."
```

This will reduce build time from ~20 minutes to ~5 minutes.

### Add More R Packages

To add additional R packages, edit the Dockerfile:

```dockerfile
# Add to the CRAN packages list:
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'YOUR_PACKAGE_HERE'), \
    dependencies=TRUE, quiet=TRUE)"
```

### Environment Variables

You can add environment variables in AWS App Runner service configuration:
- `STREAMLIT_SERVER_PORT`: Port for Streamlit (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)

## Troubleshooting

### Build Fails

1. **Check build logs** in AWS App Runner console
2. **Common issues**:
   - **"apprunner.yaml not found"**: This is OK! Docker builds don't need apprunner.yaml. Ensure Source directory is set to `/` (root).
   - **"Runtime version not supported"**: This happens if apprunner.yaml exists with invalid config. Delete apprunner.yaml - it's not needed for Docker.
   - R package installation failures (non-critical, app may still work)
   - Python package conflicts (check `requirements.txt`)
   - Memory issues during build (increase App Runner instance size)

### R Not Found

- R is installed at `/usr/bin/Rscript`
- The notebook runner should automatically detect it
- If issues persist, check R installation in build logs

### Application Won't Start

1. **Check service logs** in AWS App Runner
2. **Verify port**: Ensure port 8501 is correctly configured
3. **Check health endpoint**: `https://your-url/_stcore/health`

## Cost Optimization

- **Use smaller instances** for development/testing
- **Enable auto-scaling** to handle traffic spikes
- **Monitor usage** in AWS CloudWatch
- **Consider** removing Seurat if not needed (saves build time and resources)

## Security Notes

- The Dockerfile runs as root (default for App Runner)
- For production, consider creating a non-root user
- Review environment variables for sensitive data
- Use AWS Secrets Manager for API keys if needed

