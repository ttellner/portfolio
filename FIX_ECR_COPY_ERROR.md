# Fix "Failed to copy the image from ECR" Error

## Error Message
```
[AppRunner] Deployment failed. Failure reason: Failed to copy the image from ECR.
```

## Possible Causes

1. **Image doesn't exist in ECR** (most common)
2. **App Runner service role lacks ECR permissions**
3. **Incorrect ECR repository URL in App Runner**
4. **Image tag mismatch** (App Runner looking for wrong tag)

## Step-by-Step Fix

### Step 1: Verify Image Exists in ECR

1. Go to **AWS Console → ECR → Repositories**
2. Find repository: `portfolio-streamlit`
3. Check if there's an image with tag `latest`
4. **If no image exists**, the GitHub Actions build might have failed

**Check GitHub Actions:**
1. Go to **GitHub → Your repo → Actions tab**
2. Find the latest workflow run
3. Check if it completed successfully
4. Look for "Image pushed" message

**If GitHub Actions failed:**
- Check the error logs
- Verify AWS secrets are set correctly
- Re-run the workflow manually

### Step 2: Verify ECR Repository URL in App Runner

1. Go to **App Runner → Your Service → Configuration → Source**
2. Check the **Image identifier** field
3. Should be: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
4. **If different, update it**

**To update:**
1. Click **Edit** on the service
2. Go to **Source and deployment**
3. Update **Image identifier** to: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
4. Click **Save** and **Deploy**

### Step 3: Check App Runner Service Role Permissions

1. Go to **App Runner → Your Service → Configuration → Security**
2. Note the **Access role** name (e.g., `AppRunner-ECR-AccessRole-xxxxx`)
3. Go to **IAM → Roles**
4. Find the role
5. Check if it has these permissions:
   - `ecr:GetAuthorizationToken`
   - `ecr:BatchGetImage`
   - `ecr:GetDownloadUrlForLayer`
   - `ecr:BatchCheckLayerAvailability`

**If missing permissions:**
1. Click on the role
2. Click **Add permissions → Attach policies**
3. Attach: `AmazonEC2ContainerRegistryReadOnly`
4. Save

### Step 4: Manually Push Image to ECR (If Needed)

If the image doesn't exist, push it manually:

```powershell
# Authenticate
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t portfolio-streamlit:latest .

# Tag
docker tag portfolio-streamlit:latest 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest

# Push
docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

### Step 5: Verify Image Tag

1. Go to **ECR → portfolio-streamlit → Images**
2. Note the exact tag (should be `latest`)
3. In **App Runner**, ensure the **Image tag** matches exactly

**If using a different tag:**
- Update App Runner configuration to match
- Or re-tag the image in ECR

## Quick Checklist

- [ ] Image exists in ECR with tag `latest`
- [ ] GitHub Actions workflow completed successfully
- [ ] App Runner Image identifier is correct: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
- [ ] App Runner service role has ECR read permissions
- [ ] Image tag in App Runner matches ECR tag (`latest`)

## Most Common Fix

**90% of the time, the issue is:**
1. Image doesn't exist in ECR (GitHub Actions failed or didn't run)
2. **Solution:** Check GitHub Actions, fix any errors, re-run workflow

## After Fixing

1. **Wait for GitHub Actions** to complete (~20 minutes)
2. **Verify image in ECR** (should see new image with timestamp)
3. **Trigger App Runner deployment** (should auto-deploy if enabled, or manually trigger)
4. **Check App Runner Activity tab** for deployment status

## Still Not Working?

If still failing after all steps:

1. **Delete and recreate the App Runner service** (last resort)
2. **Use "Create new service role"** when recreating
3. **Double-check ECR repository name** matches exactly

