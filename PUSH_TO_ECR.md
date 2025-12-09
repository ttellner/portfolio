# Push Docker Image to ECR - Commands

## Quick Commands

### Step 1: Authenticate with ECR

```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Build the Docker Image

```powershell
docker build -t portfolio-streamlit .
```

### Step 3: Tag the Image for ECR

```powershell
docker tag portfolio-streamlit:latest 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

### Step 4: Push to ECR

```powershell
docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

---

## One-Liner (All Steps Combined)

```powershell
# Authenticate, build, tag, and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com && docker build -t portfolio-streamlit . && docker tag portfolio-streamlit:latest 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest && docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

---

## Using the Script (Easier)

Instead of manual commands, use the script we created:

```powershell
.\build_then_push.ps1
```

This script:
- ✅ Checks if Docker is running
- ✅ Authenticates with ECR
- ✅ Creates repository if needed
- ✅ Builds the image
- ✅ Tags it correctly
- ✅ Pushes with retry logic

---

## Step-by-Step with Explanations

### 1. Ensure ECR Repository Exists

```powershell
aws ecr create-repository --repository-name portfolio-streamlit --region us-east-1
```

(Only needed once - will error if it already exists, which is OK)

### 2. Authenticate Docker to ECR

```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com
```

**Expected output**: `Login Succeeded`

### 3. Build Docker Image

```powershell
docker build -t portfolio-streamlit .
```

**Time**: ~10-20 minutes (depending on your Dockerfile version)

### 4. Tag Image for ECR

```powershell
docker tag portfolio-streamlit:latest 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

This creates a tag pointing to your ECR repository.

### 5. Push Image to ECR

```powershell
docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

**Time**: ~5-15 minutes (depending on image size and network)

**Expected output**: Shows progress of layers being pushed.

---

## Verify Image Was Pushed

After pushing, verify it's in ECR:

```powershell
aws ecr describe-images --repository-name portfolio-streamlit --region us-east-1
```

Or use the check script:

```powershell
.\check_ecr_images.ps1
```

---

## Troubleshooting

### "RepositoryNotFoundException"
- Create the repository first:
  ```powershell
  aws ecr create-repository --repository-name portfolio-streamlit --region us-east-1
  ```

### "Login Succeeded" but push fails
- Re-authenticate (tokens expire after 12 hours)
- Check your IAM permissions

### Network errors during push
- Use the `build_then_push.ps1` script (has retry logic)
- Or use GitHub Actions (builds in cloud, avoids local network issues)

### "Access Denied"
- Check IAM permissions for your user
- Ensure `AmazonEC2ContainerRegistryFullAccess` policy is attached

---

## Alternative: Use GitHub Actions (Recommended)

Instead of pushing manually, use GitHub Actions:

1. **Push the workflow file** (already created):
   ```powershell
   git add .github/workflows/deploy.yml
   git commit -m "Add deployment workflow"
   git push origin main
   ```

2. **Workflow automatically**:
   - Builds the image
   - Tags it for ECR
   - Pushes to ECR
   - No local network issues!

3. **Check progress**:
   - Go to: `https://github.com/ttellner/portfolio/actions`

This is more reliable because it builds in GitHub's infrastructure.

---

## Summary

**Manual push** (if you want to do it now):
```powershell
.\build_then_push.ps1
```

**Automatic push** (recommended for future):
- Use GitHub Actions workflow
- Push to GitHub, it handles everything

