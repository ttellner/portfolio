# Debug: WebSocket Still Failing After New Service

## Current Situation

✅ New service created with:
- Port: 8080
- Health check: HTTP, path `/_stcore/health`
- Access role: Correct

❌ Still getting:
- Blank page with "glowing boxes"
- WebSocket connection error

## Possible Causes

### 1. Old Image Still Deployed (Most Likely)

The new service might be using an **old image** (without nginx).

**Check:**
1. **App Runner → New Service → Configuration → Source**
2. **Image URI:** Check the timestamp
3. **Activity tab:** Check which image was deployed

**If old image:**
- Wait for GitHub Actions to finish building new image
- Or manually trigger deployment of latest image

### 2. nginx Not Starting

nginx might not be starting properly in the container.

**Check App Runner logs:**
1. **App Runner → New Service → Logs tab**
2. Look for:
   - `nginx` startup messages
   - `streamlit` startup messages
   - Any errors

**What to look for:**
- ✅ `nginx: [notice] ... ready to handle connections`
- ✅ `You can now view your Streamlit app`
- ❌ `nginx: [emerg] ...` (errors)
- ❌ `streamlit: command not found`

### 3. Both Services Not Running

The `start.sh` script might not be starting both services correctly.

**Check logs for:**
- Streamlit starting on port 8501
- nginx starting on port 8080
- Both processes running

### 4. Health Check Passing But App Not Working

Health check might pass (nginx responds), but Streamlit isn't accessible.

## Debugging Steps

### Step 1: Check Which Image is Deployed

1. **App Runner → New Service → Configuration → Source**
2. **Image URI:** Note the full URI
3. **ECR → portfolio-streamlit → Images**
4. **Compare timestamps:**
   - Image in ECR should be recent (after you pushed Dockerfile)
   - Image in App Runner should match

**If mismatch:**
- App Runner is using old image
- Wait for new deployment or manually trigger

### Step 2: Check App Runner Logs

1. **App Runner → New Service → Logs tab**
2. **Look for startup messages:**

**Good signs:**
```
nginx: [notice] ... ready to handle connections
You can now view your Streamlit app in your browser.
```

**Bad signs:**
```
nginx: [emerg] bind() to 0.0.0.0:8080 failed
streamlit: command not found
```

### Step 3: Test Health Endpoint

1. **Get service URL:** App Runner → New Service → Default domain
2. **Test:** `https://your-service-url/_stcore/health`
3. **Should return:** `{"status": "healthy"}`

**If health check works but app doesn't:**
- nginx is running ✅
- But Streamlit might not be running ❌

### Step 4: Check Container Processes

If you can access logs, verify both processes are running:

**Expected processes:**
- `nginx` (master process)
- `streamlit` (Python process)
- `nginx` (worker processes)

## Potential Fixes

### Fix 1: Ensure New Image is Deployed

1. **Check ECR:** Verify new image exists with nginx
2. **App Runner → New Service → Deploy**
3. **Select:** "Deploy latest revision" or specific image tag
4. **Wait for deployment**

### Fix 2: Check start.sh Script

The script should:
1. Start Streamlit in background (`&`)
2. Wait 3 seconds (`sleep 3`)
3. Start nginx in foreground (`exec nginx`)

**Verify the script is correct:**
- Streamlit on `127.0.0.1:8501`
- nginx listening on `8080`
- nginx proxying to `127.0.0.1:8501`

### Fix 3: Increase Startup Time

If Streamlit takes longer to start:

**Edit `start.sh`:**
```bash
# Change sleep 3 to sleep 5 or 10
sleep 10  # Give Streamlit more time to start
```

### Fix 4: Check nginx Configuration

Verify `nginx.conf`:
- Listens on port 8080 ✅
- Proxies to `127.0.0.1:8501` ✅
- Has WebSocket headers ✅
- Health check endpoint configured ✅

## Quick Diagnostic Commands

**Check if new image exists:**
```powershell
aws ecr describe-images --repository-name portfolio-streamlit --region us-east-1 --query 'sort_by(imageDetails,&imagePushedAt)[-1]'
```

**Check App Runner service status:**
```powershell
aws apprunner describe-service --service-arn <your-service-arn> --region us-east-1
```

## Most Likely Issue

**The new service is probably using an old image** (without nginx).

**Solution:**
1. **Check ECR** - does new image with nginx exist?
2. **Check App Runner** - which image is it using?
3. **If old image:** Wait for GitHub Actions or manually deploy latest image
4. **If new image:** Check logs to see why nginx/Streamlit aren't starting

## Next Steps

1. **Check App Runner logs** - what do they show?
2. **Check which image is deployed** - is it the new one with nginx?
3. **Test health endpoint** - does `/_stcore/health` work?
4. **Share log output** - I can help diagnose specific errors

The logs will tell us exactly what's wrong!

