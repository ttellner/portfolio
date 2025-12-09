# App Runner Source Code Deployment (No Dockerfile)

## Overview

Yes, you're correct! For **App Runner source code deployment** with managed runtime, you only need `apprunner.yaml` - **NO Dockerfile needed**.

However, there's an important limitation for your use case.

---

## ⚠️ Important Limitation: No R Support

**App Runner's managed Python runtime does NOT include R.**

This means:
- ✅ Your Streamlit app will work
- ✅ Python projects will work
- ✅ Banking projects (Python) will work
- ❌ **Bioinformatics projects requiring R will NOT work**
- ❌ R Markdown files won't render
- ❌ R subprocess calls will fail

---

## Setup Steps (Source Code Deployment)

### 1. Create apprunner.yaml

I've created `apprunner.yaml` for you. It's already in your repo.

### 2. Deploy to App Runner

1. **Go to AWS App Runner Console**
   - https://console.aws.amazon.com/apprunner/

2. **Create Service**
   - Click "Create service"

3. **Configure Source**
   - **Source**: Select **"Source code repository"** (NOT Container registry)
   - **Provider**: GitHub
   - **Repository**: `ttellner/portfolio`
   - **Branch**: `main`
   - **Source directory**: `/` (root)
   - **Deployment trigger**: Automatic

4. **Configure Build**
   - **Build type**: Select **"Use a configuration file"**
   - App Runner will automatically read `apprunner.yaml` from your repo

5. **Configure Service**
   - **Service name**: `portfolio-streamlit`
   - **Virtual CPU**: 1 vCPU
   - **Memory**: 2 GB
   - **Port**: `8501`

6. **Create & Deploy**

---

## What apprunner.yaml Does

The `apprunner.yaml` file I created:
- Uses Python 3 managed runtime
- Installs dependencies from `requirements.txt`
- Installs additional packages (nbconvert, etc.)
- Runs Streamlit on port 8501

**No Dockerfile needed!**

---

## Comparison: Source Code vs Container Registry

| Feature | Source Code (apprunner.yaml) | Container Registry (Dockerfile) |
|---------|------------------------------|----------------------------------|
| **Dockerfile needed?** | ❌ No | ✅ Yes |
| **apprunner.yaml needed?** | ✅ Yes | ⚠️ Optional |
| **R support?** | ❌ No | ✅ Yes (if installed in Dockerfile) |
| **Setup complexity** | ⭐ Easy | ⭐⭐ Medium |
| **Build time** | ~5 minutes | ~20 minutes |
| **Best for** | Python-only apps | Apps needing R, custom dependencies |

---

## Your Options

### Option 1: Use Source Code Deployment (apprunner.yaml)

**Pros:**
- ✅ Simple setup
- ✅ No Dockerfile needed
- ✅ Faster builds
- ✅ Works for Python projects

**Cons:**
- ❌ No R support
- ❌ Bioinformatics R projects won't work

**Use this if:** You're okay with R projects not working, or you want to test the Python parts first.

### Option 2: Use Container Registry (Dockerfile)

**Pros:**
- ✅ Full R support
- ✅ All projects work
- ✅ Complete control

**Cons:**
- ⚠️ Need to build/push Docker image first
- ⚠️ Longer setup

**Use this if:** You need R support (which you do for bioinformatics projects).

---

## Recommendation

Since you have **bioinformatics projects that require R**, I recommend:

1. **For now**: Use the source code approach (`apprunner.yaml`) to get the app running quickly
   - Python projects will work
   - Banking projects will work
   - R projects will show the fallback HTML (which you already implemented)

2. **Later**: Set up GitHub Actions to build Docker image and push to ECR
   - This gives you full R support
   - Automatic deployments
   - Solves your network issues

---

## Quick Start: Source Code Deployment

1. **Ensure apprunner.yaml is in your repo** (it is!)

2. **Push to GitHub**:
   ```powershell
   git add apprunner.yaml
   git commit -m "Add apprunner.yaml for source code deployment"
   git push origin main
   ```

3. **Create App Runner service**:
   - Source: GitHub → `ttellner/portfolio`
   - Build: Use configuration file
   - Deploy!

**That's it!** No Dockerfile, no ECR, no manual builds.

---

## If You Need R Support Later

When you're ready for full R support:
1. Use the GitHub Actions workflow (`.github/workflows/deploy.yml`)
2. It builds your Dockerfile and pushes to ECR
3. App Runner deploys from ECR
4. Everything works, including R!

---

## Summary

- ✅ **Yes, you're correct** - Source code deployment only needs `apprunner.yaml`
- ✅ **No Dockerfile needed** for source code deployment
- ⚠️ **But** - You won't have R support with managed runtime
- 💡 **Solution** - Use source code for now, switch to Docker/ECR when you need R

The `apprunner.yaml` file is ready to use!

