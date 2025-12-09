# Troubleshooting ECR Push Issues

## Common Error: "broken pipe" or "write: broken pipe"

This error typically occurs when:
1. **Network connectivity issues** - Unstable internet connection
2. **Large image size** - Images >2GB can timeout during push
3. **Docker Desktop proxy settings** - Misconfigured proxy
4. **AWS region latency** - Slow connection to ECR

## Solutions

### 1. Check Image Size

```powershell
docker images portfolio-streamlit:latest
```

If the image is very large (>5GB), consider optimizing:
- Remove unnecessary files from the image
- Use multi-stage builds
- Remove build dependencies after installation

### 2. Check Network Connection

```powershell
# Test AWS connectivity
aws ecr describe-repositories --region us-east-1

# Test Docker connectivity
docker info
```

### 3. Retry the Push

The deployment script now includes automatic retry logic (3 attempts). If it still fails:

```powershell
# Try pushing manually with verbose output
docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest
```

### 4. Check Docker Desktop Settings

1. Open Docker Desktop
2. Go to Settings → Resources → Network
3. Ensure "Use kernel networking for UDP" is enabled
4. Try disabling VPN/proxy if enabled

### 5. Increase Docker Timeout

If you're on a slow connection, you may need to increase Docker's timeout:

1. Docker Desktop → Settings → Docker Engine
2. Add or modify:
```json
{
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5
}
```

### 6. Use Docker Buildx (Alternative)

Docker Buildx can be more reliable for large images:

```powershell
# Enable buildx
docker buildx create --use

# Build and push in one step
docker buildx build --platform linux/amd64 -t 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest --push .
```

### 7. Check AWS Credentials and Permissions

```powershell
# Verify you're authenticated
aws sts get-caller-identity

# Check ECR permissions
aws ecr describe-repositories --repository-names portfolio-streamlit --region us-east-1
```

### 8. Optimize Dockerfile (Reduce Image Size)

If the image is too large, consider:

1. **Remove Seurat** (if not needed):
   - Comment out Seurat installation in Dockerfile
   - This can save 1-2GB

2. **Use .dockerignore**:
   - Ensure large files aren't copied
   - Check that `.dockerignore` is working

3. **Clean up after installations**:
   ```dockerfile
   RUN apt-get update && apt-get install -y ... && \
       apt-get clean && \
       rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
   ```

### 9. Push in Smaller Chunks (Advanced)

If the image is extremely large, you might need to:
1. Split the Dockerfile into multiple images
2. Use Docker layer caching more effectively
3. Push base layers separately

### 10. Check ECR Repository Limits

ECR has some limits:
- Maximum image size: 10GB per layer
- Maximum layers: 127 layers per image

Check your image:
```powershell
docker history portfolio-streamlit:latest
```

## Still Having Issues?

1. **Check AWS Service Health**: https://status.aws.amazon.com/
2. **Try a different AWS region** (if latency is the issue)
3. **Contact AWS Support** if it's a persistent ECR issue
4. **Consider using AWS CodeBuild** to build and push the image automatically

## Quick Test

To verify everything is working:

```powershell
# 1. Build a small test image
docker build -t test-image - <<EOF
FROM alpine:latest
RUN echo "test"
EOF

# 2. Tag it for ECR
docker tag test-image 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:test

# 3. Try pushing the small image
docker push 083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:test
```

If the small image pushes successfully, the issue is likely the large size of your main image.

