# Fix: Network Connection Error When Pushing to ECR

## Error Message

```
failed to copy: failed to do request: Put "...": write tcp ...: use of closed network connection
```

This error occurs when the network connection drops during the long upload process (large Docker images).

## ✅ Best Solution: Use GitHub Actions

**This is the recommended fix** - it completely avoids local network issues:

### Steps:

1. **Ensure workflow file is in repo**:
   ```powershell
   git add .github/workflows/deploy.yml
   git commit -m "Add deployment workflow"
   git push origin main
   ```

2. **GitHub Actions will automatically**:
   - Build the image in GitHub's infrastructure
   - Push to ECR (no local network issues!)
   - Takes ~20 minutes for first build

3. **Check progress**:
   - Go to: `https://github.com/ttellner/portfolio/actions`

**Why this works**: GitHub Actions builds in the cloud, so uploads happen within AWS/GitHub's network, avoiding your local network issues.

---

## Alternative Solutions (If You Must Push Locally)

### Solution 1: Use Docker Buildx (More Reliable)

```powershell
# Enable buildx
docker buildx create --use

# Build and push in one step (more reliable)
docker buildx build --platform linux/amd64 --push -t 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest .
```

### Solution 2: Check Docker Desktop Settings

1. Open Docker Desktop
2. Go to Settings → Resources → Network
3. Try these settings:
   - Enable "Use kernel networking for UDP"
   - Or disable it if already enabled
4. Restart Docker Desktop
5. Try pushing again

### Solution 3: Disable VPN/Proxy

If you're using a VPN or proxy:
1. Temporarily disable it
2. Try pushing again
3. Re-enable after push completes

### Solution 4: Increase Docker Timeout

1. Docker Desktop → Settings → Docker Engine
2. Add to JSON:
```json
{
  "max-concurrent-uploads": 3,
  "max-concurrent-downloads": 3
}
```
3. Apply & Restart
4. Try pushing again

### Solution 5: Push During Off-Peak Hours

Network congestion can cause timeouts. Try pushing:
- Early morning or late evening
- When network usage is lower

### Solution 6: Use Smaller Image

If the image is very large (>5GB), consider:

1. **Use simplified Dockerfile** (without Seurat):
   ```powershell
   # Current Dockerfile is already simplified
   # Just rebuild and push
   docker build -t portfolio-streamlit .
   ```

2. **Or optimize the image**:
   - Remove unnecessary files
   - Use multi-stage builds
   - Clean up build artifacts

---

## Updated Script with Better Retry Logic

I've updated `build_then_push.ps1` with:
- Better retry logic
- Re-authentication on retry
- More informative error messages
- Recommendations for GitHub Actions

Try running it again:
```powershell
.\build_then_push.ps1
```

---

## Why This Happens

1. **Large image size**: Your Docker image is likely 2-5GB
2. **Long upload time**: Takes 10-30 minutes to push
3. **Network instability**: Connection drops during long upload
4. **Docker Desktop networking**: Can have issues with large transfers

---

## Recommended Workflow

**For now (quick fix)**:
1. Use GitHub Actions (push workflow file, let it build/push)

**For future**:
- All deployments via GitHub Actions
- Automatic on every push
- No local network issues
- More reliable

---

## Summary

- ❌ **Local push**: Prone to network errors with large images
- ✅ **GitHub Actions**: Builds in cloud, avoids network issues
- ✅ **Best practice**: Use GitHub Actions for all deployments

The workflow file is already created - just push it to GitHub and it will handle everything automatically!

