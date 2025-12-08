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

### 2. Deploy to AWS App Runner

1. **Navigate to AWS App Runner Console**
   - Go to AWS Console → App Runner
   - Click "Create service"

2. **Configure Source**
   - Select "Source: GitHub"
   - Connect your GitHub account (if not already connected)
   - Select your repository: `portfolio`
   - Select branch: `main` (or your default branch)
   - Deployment trigger: "Automatic" (deploys on every push)

3. **Configure Build**
   - Build type: "Docker"
   - Dockerfile path: `Dockerfile` (default)
   - Docker build context: `.` (root directory)

4. **Configure Service**
   - Service name: `portfolio-streamlit` (or your preferred name)
   - Virtual CPU: 1 vCPU (minimum, increase if needed)
   - Memory: 2 GB (minimum, increase if needed)
   - Port: `8501`
   - Environment variables (optional):
     - `STREAMLIT_SERVER_PORT=8501`
     - `STREAMLIT_SERVER_ADDRESS=0.0.0.0`

5. **Review and Create**
   - Review all settings
   - Click "Create & deploy"

### 3. Build Time

**Important**: The first build will take 15-20 minutes because:
- Installing R and R packages
- Installing Seurat (large package, ~10-15 minutes)
- Installing Python packages including TensorFlow

Subsequent builds will be faster due to Docker layer caching.

### 4. Access Your Application

Once deployment completes:
- App Runner will provide a service URL (e.g., `https://xxxxx.us-east-1.awsapprunner.com`)
- Your Streamlit app will be accessible at this URL

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

