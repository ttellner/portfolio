# Container Registry Deployment Guide

## Dockerfile Status

✅ **Yes, your Dockerfile is valid for container registry deployment!**

The current `Dockerfile` includes:
- ✅ Python 3.11
- ✅ R and R packages (basic set, without Seurat)
- ✅ All Python dependencies
- ✅ Streamlit configuration
- ✅ Health checks for App Runner
- ✅ Proper port configuration

## Two Dockerfile Versions

You have two versions:

### 1. `Dockerfile` (Current - Simplified)
- **Includes**: Basic R packages
- **Excludes**: Seurat (large package)
- **Build time**: ~10-15 minutes
- **Size**: Smaller image
- **Use for**: Faster builds, testing, or if Seurat isn't needed

### 2. `Dockerfile.full` (Full Version)
- **Includes**: Seurat + all R packages
- **Build time**: ~20-25 minutes
- **Size**: Larger image (~2-3GB more)
- **Use for**: Full bioinformatics support

## Using Container Registry Deployment

### Option 1: Use Current Dockerfile (Simplified)

**If you want to use the current simplified version:**

1. **Build and push using GitHub Actions** (recommended):
   - The workflow (`.github/workflows/deploy.yml`) is already set up
   - Just add GitHub secrets and push
   - It will build and push automatically

2. **Or push manually**:
   ```powershell
   .\build_then_push.ps1
   ```

3. **Configure App Runner**:
   - Source: Container registry → Amazon ECR
   - Image URI: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
   - Port: `8501`

### Option 2: Use Full Dockerfile (With Seurat)

**If you need Seurat for bioinformatics projects:**

1. **Switch to full version**:
   ```powershell
   # Backup current
   Copy-Item Dockerfile Dockerfile.simple.backup
   
   # Use full version
   Copy-Item Dockerfile.full Dockerfile
   ```

2. **Build and push** (same as above)

3. **Configure App Runner** (same as above)

## Verification Checklist

Before deploying, verify your Dockerfile has:

- [x] `FROM` statement (base image)
- [x] Python installation
- [x] R installation (if needed)
- [x] `COPY requirements.txt` and `pip install -r requirements.txt`
- [x] `COPY . .` (copies app code)
- [x] `EXPOSE 8501` (Streamlit port)
- [x] `CMD` with Streamlit run command
- [x] Health check (optional but recommended)

**Your Dockerfile has all of these! ✅**

## Quick Start: Container Deployment

### Using GitHub Actions (Recommended)

1. **Add GitHub Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

2. **Push workflow**:
   ```powershell
   git add .github/workflows/deploy.yml
   git commit -m "Add container deployment"
   git push origin main
   ```

3. **Wait for build** (~15-20 minutes):
   - Check: https://github.com/ttellner/portfolio/actions

4. **Configure App Runner**:
   - Container registry → ECR
   - Image: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`

### Using Manual Push

1. **Build locally**:
   ```powershell
   docker build -t portfolio-streamlit .
   ```

2. **Push to ECR**:
   ```powershell
   .\build_then_push.ps1
   ```

3. **Configure App Runner** (same as above)

## Summary

- ✅ **Dockerfile is valid** for container registry deployment
- ✅ **Current version** works (simplified, no Seurat)
- ✅ **Full version** available if you need Seurat
- ✅ **GitHub Actions** is the easiest way to build/push
- ✅ **App Runner** will deploy from ECR automatically

Your Dockerfile is ready to use! 🚀

