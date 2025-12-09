# Build locally first, then push separately (more reliable for large images)

$AWS_ACCOUNT_ID = "083738448444"
$AWS_REGION = "us-east-1"
$ECR_REPOSITORY_NAME = "portfolio-streamlit"
$ECR_REPOSITORY_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

Write-Host "=== Build and Push (Separate Steps) ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build locally
Write-Host "Step 1: Building image locally..." -ForegroundColor Yellow
Write-Host "This may take 15-20 minutes..." -ForegroundColor Yellow
Write-Host ""

docker build -t portfolio-streamlit:latest .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "OK - Build completed successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Tag for ECR
Write-Host "Step 2: Tagging image for ECR..." -ForegroundColor Yellow
docker tag portfolio-streamlit:latest "${ECR_REPOSITORY_URI}:latest"
Write-Host "OK - Image tagged" -ForegroundColor Green
Write-Host ""

# Step 3: Authenticate
Write-Host "Step 3: Authenticating with ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR - Authentication failed!" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Authenticated" -ForegroundColor Green
Write-Host ""

# Step 4: Push with retry logic and connection handling
Write-Host "Step 4: Pushing image to ECR..." -ForegroundColor Yellow
Write-Host "This may take 10-30 minutes depending on image size and network..." -ForegroundColor Yellow
Write-Host "Note: If this fails due to network issues, use GitHub Actions instead (see PUSH_TO_ECR.md)" -ForegroundColor Yellow
Write-Host ""

# Check image size first
Write-Host "Checking image size..." -ForegroundColor Cyan
$imageSize = docker images portfolio-streamlit:latest --format "{{.Size}}"
Write-Host "Image size: $imageSize" -ForegroundColor White
if ($imageSize -match "GB") {
    Write-Host "WARNING: Large image detected. Push may take a long time and may timeout." -ForegroundColor Yellow
    Write-Host "Consider using GitHub Actions for more reliable uploads." -ForegroundColor Yellow
}
Write-Host ""

$maxRetries = 3
$retryCount = 0
$pushSuccess = $false

while ($retryCount -lt $maxRetries -and -not $pushSuccess) {
    if ($retryCount -gt 0) {
        $waitTime = [math]::Min($retryCount * 15, 60)
        Write-Host "Retry attempt $retryCount of $maxRetries (waiting $waitTime seconds)..." -ForegroundColor Yellow
        Write-Host "Re-authenticating with ECR..." -ForegroundColor Cyan
        # Re-authenticate before retry (tokens can expire)
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI 2>&1 | Out-Null
        Start-Sleep -Seconds $waitTime
    }
    
    Write-Host "Attempting push (this may take 10-20 minutes for large images)..." -ForegroundColor Cyan
    Write-Host "Please be patient and don't interrupt the process..." -ForegroundColor Yellow
    
    # Push with progress output
    $pushOutput = docker push "${ECR_REPOSITORY_URI}:latest" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $pushSuccess = $true
        Write-Host ""
        Write-Host "OK - Image pushed successfully!" -ForegroundColor Green
    } else {
        $retryCount++
        Write-Host ""
        Write-Host "Push failed (attempt $retryCount of $maxRetries)" -ForegroundColor Red
        
        # Check error type
        if ($pushOutput -match "broken pipe|closed network connection|timeout|connection reset") {
            Write-Host "Network connection error detected." -ForegroundColor Yellow
            Write-Host "This is common with large images and unstable networks." -ForegroundColor Yellow
        } elseif ($pushOutput -match "unauthorized|access denied") {
            Write-Host "Authentication error. Re-authenticating..." -ForegroundColor Yellow
            aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI 2>&1 | Out-Null
        }
        
        if ($retryCount -lt $maxRetries) {
            Write-Host "Will retry..." -ForegroundColor Yellow
        } else {
            Write-Host ""
            Write-Host "ERROR - Failed to push after $maxRetries attempts" -ForegroundColor Red
            Write-Host ""
            Write-Host "This is a network connectivity issue. Solutions:" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "RECOMMENDED: Use GitHub Actions (avoids local network issues):" -ForegroundColor Green
            Write-Host "  1. Push .github/workflows/deploy.yml to GitHub" -ForegroundColor White
            Write-Host "  2. GitHub Actions will build and push automatically" -ForegroundColor White
            Write-Host "  3. No local network issues!" -ForegroundColor White
            Write-Host ""
            Write-Host "Alternative solutions:" -ForegroundColor Yellow
            Write-Host "  1. Check Docker Desktop network settings" -ForegroundColor White
            Write-Host "  2. Disable VPN/proxy temporarily" -ForegroundColor White
            Write-Host "  3. Try during off-peak hours" -ForegroundColor White
            Write-Host "  4. Use a more stable internet connection" -ForegroundColor White
            Write-Host ""
            Write-Host "See PUSH_TO_ECR.md for GitHub Actions setup instructions." -ForegroundColor Cyan
            exit 1
        }
    }
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Image URI: ${ECR_REPOSITORY_URI}:latest" -ForegroundColor Cyan

