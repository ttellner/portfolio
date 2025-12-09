# Testing ECR Authentication

## Quick Test Commands

### 1. Test AWS Credentials

```powershell
# Verify your AWS credentials work
aws sts get-caller-identity
```

Should return your AWS account ID and user ARN.

### 2. Test ECR Login Token

```powershell
# Get ECR login password (this is what GitHub Actions does)
aws ecr get-login-password --region us-east-1
```

Should return a long token string.

### 3. Test Docker Login to ECR

```powershell
# Login Docker to ECR (simulates GitHub Actions step)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com
```

Should show: `Login Succeeded`

### 4. Test ECR Repository Access

```powershell
# Check if you can access the repository
aws ecr describe-repositories --repository-names portfolio-streamlit --region us-east-1
```

Should return repository details (or error if it doesn't exist yet, which is OK).

---

## Automated Test Script

Run the complete test:

```powershell
.\test_ecr_auth.ps1
```

This script tests:
- ✅ AWS credentials
- ✅ ECR login token retrieval
- ✅ Docker login to ECR
- ✅ Repository access
- ✅ Push permissions

---

## Manual Step-by-Step Test

### Step 1: Verify AWS CLI is configured

```powershell
aws configure list
```

Should show your access key ID and region.

### Step 2: Get your AWS identity

```powershell
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDARG7ZTKI6LQKRPUSEL",
    "Account": "083738448444",
    "Arn": "arn:aws:iam::083738448444:user/apprunner-deploy"
}
```

### Step 3: Get ECR login token

```powershell
aws ecr get-login-password --region us-east-1
```

Should output a long base64-encoded token.

### Step 4: Login Docker to ECR

```powershell
$ECR_URI = "083738448444.dkr.ecr.us-east-1.amazonaws.com"
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
```

Expected output:
```
Login Succeeded
```

### Step 5: Verify repository (optional)

```powershell
aws ecr describe-repositories --repository-names portfolio-streamlit --region us-east-1
```

If repository doesn't exist, that's OK - it will be created on first push.

---

## What GitHub Actions Does

The GitHub Actions workflow does exactly these steps:

1. **Configure AWS credentials** (from GitHub secrets)
   ```yaml
   aws-actions/configure-aws-credentials@v2
   ```

2. **Login to ECR** (gets token and logs in Docker)
   ```yaml
   aws-actions/amazon-ecr-login@v1
   ```
   This internally runs:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <registry>
   ```

3. **Build and push** (uses the authenticated Docker session)

---

## Troubleshooting

### "Unable to locate credentials"
- Run `aws configure` to set up credentials
- Or set environment variables:
  ```powershell
  $env:AWS_ACCESS_KEY_ID = "your-key"
  $env:AWS_SECRET_ACCESS_KEY = "your-secret"
  ```

### "Access Denied" when getting login token
- Your IAM user needs `ecr:GetAuthorizationToken` permission
- This is included in `AmazonEC2ContainerRegistryFullAccess`

### "Login Succeeded" but can't push
- Check IAM permissions for `ecr:PutImage`, `ecr:InitiateLayerUpload`, etc.
- Ensure `AmazonEC2ContainerRegistryFullAccess` policy is attached

### Docker not found
- Make sure Docker Desktop is running
- Verify Docker is in PATH: `docker --version`

---

## Quick Verification

Run this one-liner to test everything:

```powershell
aws sts get-caller-identity && aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 083738448444.dkr.ecr.us-east-1.amazonaws.com
```

If both commands succeed, your authentication is working! ✅

