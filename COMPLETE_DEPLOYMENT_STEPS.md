# Complete Deployment Steps - Final Order

## ✅ Step 1-4: Create IAM Role (Already Done)

- [x] Created IAM role with custom trust policy
- [x] Attached `AmazonEC2ContainerRegistryReadOnly` permissions
- [x] Named it `AppRunner-ECR-AccessRole`

## ✅ Step 5: Use Role in App Runner (Just Completed)

- [x] App Runner → Your Service → Edit
- [x] Deployment Settings → Access role
- [x] Selected "Use existing service role"
- [x] Chose `AppRunner-ECR-AccessRole`
- [x] **Saved** ✅

## ✅ Step 6: Push Dockerfile and Related Files (Do This Now!)

```powershell
git add Dockerfile nginx.conf start.sh
git commit -m "Add nginx reverse proxy for WebSocket support"
git push origin main
```

**Files to push:**
- ✅ `Dockerfile` (with nginx setup)
- ✅ `nginx.conf` (WebSocket proxy config)
- ✅ `start.sh` (starts Streamlit + nginx)

## ⏳ Step 7: Wait for Build (20-30 minutes)

**What happens:**
1. GitHub Actions triggers automatically
2. Builds Docker image with nginx
3. Pushes to ECR with tag `latest`
4. App Runner detects new image (if auto-deploy enabled)

**How to monitor:**
- **GitHub:** Go to Actions tab → Latest workflow run
- **ECR:** Check `portfolio-streamlit` repository → Should see new image with timestamp

## ✅ Step 8: Configure App Runner (After Image Exists)

**Once you see the new image in ECR:**

1. **App Runner → Your Service → Edit**
2. **Service Settings:**
   - **Port:** `8080` (not 8501)
   - **Health check protocol:** `HTTP` (not TCP)
   - **Health check path:** `/_stcore/health` (or `/`)
3. **Save and Deploy**

## ⏳ Step 9: Wait for Deployment (5-10 minutes)

**What happens:**
1. App Runner pulls new image from ECR
2. Starts container with nginx + Streamlit
3. Health checks pass (HTTP on port 8080)
4. Service status becomes "Running"

**Monitor:**
- **App Runner → Activity tab:** Watch deployment progress
- **Logs tab:** Check for startup messages

## ✅ Step 10: Test

1. **Service URL:** Should load your Streamlit app
2. **WebSocket:** Should connect (no more errors!)
3. **All features:** Test Python projects, R projects, etc.

## Summary Checklist

- [x] IAM role created and used in App Runner
- [ ] **Push Dockerfile, nginx.conf, start.sh** ← You are here
- [ ] Wait for image in ECR
- [ ] Configure App Runner (port 8080, HTTP health check)
- [ ] Deploy and test

## Important Notes

**After pushing files:**
- Don't configure App Runner port/health check yet
- Wait for the new image to appear in ECR first
- Then configure App Runner to use the new image

**Why this order:**
1. IAM role first → App Runner can pull images
2. Push Dockerfile → Builds new image with nginx
3. Wait for image → Ensures it exists before configuring
4. Configure App Runner → Points to new image on port 8080
5. Deploy → Everything works!

## Quick Command Reference

```powershell
# Push files
git add Dockerfile nginx.conf start.sh
git commit -m "Add nginx reverse proxy for WebSocket support"
git push origin main

# Check GitHub Actions (after push)
# Go to: https://github.com/ttellner/portfolio/actions

# Check ECR (after ~20 minutes)
# Go to: AWS Console → ECR → portfolio-streamlit → Images
```

You're ready to push! 🚀

