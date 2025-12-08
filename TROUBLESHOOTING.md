# AWS App Runner Build Troubleshooting Guide

## Common Build Failure Causes

### 1. **R Package Installation Failures**

**Symptoms:**
- Build fails during R package installation
- Error messages about missing R packages
- Timeout errors

**Solutions:**

#### Option A: Use Simplified Dockerfile (Recommended for Testing)
1. Temporarily rename files:
   ```bash
   mv Dockerfile Dockerfile.full
   mv Dockerfile.simple Dockerfile
   ```
2. Commit and push to GitHub
3. Try building again
4. If successful, gradually add R packages back

#### Option B: Remove Seurat (Faster Builds)
Edit `Dockerfile` and remove `'Seurat'` from the R packages list:
```dockerfile
# Change this line:
install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'readxl', 'jsonlite', 'patchwork', 'Seurat'), \

# To this (remove Seurat):
install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'readxl', 'jsonlite', 'patchwork'), \
```

### 2. **Build Timeout**

**Symptoms:**
- Build fails after running for a long time
- No specific error, just timeout

**Solutions:**
- Increase App Runner build timeout (if available in settings)
- Remove heavy packages (Seurat, TensorFlow) temporarily
- Split R package installation into multiple RUN commands

### 3. **Memory Issues**

**Symptoms:**
- Build fails during package compilation
- "Killed" messages in logs
- Out of memory errors

**Solutions:**
- Increase App Runner instance size (more memory)
- Remove unnecessary packages
- Use pre-compiled binaries when possible

### 4. **Python Package Conflicts**

**Symptoms:**
- pip install failures
- Version conflicts
- Import errors

**Solutions:**
- Check `requirements.txt` for conflicting versions
- Pin specific versions
- Test locally first: `pip install -r requirements.txt`

## How to Check Build Logs

1. **In AWS App Runner Console:**
   - Go to your service
   - Click on "Deployments" tab
   - Click on the failed deployment
   - View "Build logs" and "Deploy logs"

2. **Look for:**
   - Error messages (usually near the end)
   - Which step failed (R packages, Python packages, etc.)
   - Timeout messages
   - Memory errors

## Step-by-Step Debugging

### Step 1: Test with Minimal Setup

1. Use `Dockerfile.simple` (without Seurat)
2. Build and deploy
3. If successful, you know the issue is with Seurat or other R packages

### Step 2: Test Python Only

Create a minimal test:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 3: Add R Gradually

1. Add R base installation
2. Test build
3. Add basic R packages
4. Test build
5. Add Seurat last

## Quick Fixes

### Fix 1: Make R Installation Non-Blocking

The current Dockerfile already has `|| echo` to continue on R failures. If you're still having issues, make it more explicit:

```dockerfile
RUN Rscript -e "install.packages('Seurat')" || true
```

### Fix 2: Increase Build Resources

In App Runner service settings:
- Increase CPU: 2 vCPU
- Increase Memory: 4 GB
- This helps with R package compilation

### Fix 3: Use Pre-built R Images

Consider using `rocker/r-ver:4.3` as base and adding Python:

```dockerfile
FROM rocker/r-ver:4.3
# Then install Python 3.11
```

## Testing Locally

Before deploying to App Runner, test locally:

```bash
# Build the image
docker build -t portfolio-test .

# If build succeeds, run it
docker run -p 8501:8501 portfolio-test

# Check if it works
curl http://localhost:8501/_stcore/health
```

## Common Error Messages and Fixes

### "package 'Seurat' is not available"
- **Fix:** Seurat might need Bioconductor dependencies first
- **Fix:** Try installing dependencies manually

### "Rscript: command not found"
- **Fix:** R installation failed - check apt-get install step

### "Build timeout"
- **Fix:** Remove Seurat, use Dockerfile.simple
- **Fix:** Increase App Runner instance size

### "No space left on device"
- **Fix:** Clean up Docker layers
- **Fix:** Remove unnecessary packages

## Recommended Approach

1. **Start with Dockerfile.simple** (no Seurat)
2. **Verify basic functionality works**
3. **Add Seurat later** if needed for bioinfoprojects
4. **Monitor build logs** for specific errors

## Getting Help

If builds continue to fail:
1. Copy the exact error message from build logs
2. Check which step failed (line number in Dockerfile)
3. Try the simplified Dockerfile first
4. Consider removing Seurat if bioinfoprojects R Markdown isn't critical

