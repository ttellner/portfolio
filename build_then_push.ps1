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

# Step 4: Push with retry logic
Write-Host "Step 4: Pushing image to ECR..." -ForegroundColor Yellow
Write-Host "This may take 10-30 minutes depending on image size and network..." -ForegroundColor Yellow
Write-Host ""

$maxRetries = 5
$retryCount = 0
$pushSuccess = $false

while ($retryCount -lt $maxRetries -and -not $pushSuccess) {
    if ($retryCount -gt 0) {
        $waitTime = [math]::Min($retryCount * 10, 60)
        Write-Host "Retry attempt $retryCount of $maxRetries (waiting $waitTime seconds)..." -ForegroundColor Yellow
        Start-Sleep -Seconds $waitTime
    }
    
    Write-Host "Attempting push..." -ForegroundColor Cyan
    docker push "${ECR_REPOSITORY_URI}:latest" 2>&1 | Tee-Object -Variable pushOutput
    
    if ($LASTEXITCODE -eq 0) {
        $pushSuccess = $true
        Write-Host ""
        Write-Host "OK - Image pushed successfully!" -ForegroundColor Green
    } else {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host ""
            Write-Host "Push failed, will retry..." -ForegroundColor Yellow
            # Check if it's a network error
            if ($pushOutput -match "broken pipe|closed network connection|timeout") {
                Write-Host "Network error detected. This is common with large images." -ForegroundColor Yellow
            }
        } else {
            Write-Host ""
            Write-Host "ERROR - Failed to push after $maxRetries attempts" -ForegroundColor Red
            Write-Host ""
            Write-Host "Recommendations:" -ForegroundColor Yellow
            Write-Host "1. Check your internet connection stability" -ForegroundColor White
            Write-Host "2. Try during off-peak hours" -ForegroundColor White
            Write-Host "3. Use AWS CodeBuild to build and push automatically" -ForegroundColor White
            Write-Host "4. Consider using a smaller image (Dockerfile.simple)" -ForegroundColor White
            Write-Host "5. Check Docker Desktop network settings" -ForegroundColor White
            exit 1
        }
    }
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Image URI: ${ECR_REPOSITORY_URI}:latest" -ForegroundColor Cyan

