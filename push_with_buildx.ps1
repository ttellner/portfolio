# Alternative push method using Docker Buildx (often more reliable for large images)

$AWS_ACCOUNT_ID = "083738448444"
$AWS_REGION = "us-east-1"
$ECR_REPOSITORY_NAME = "portfolio-streamlit"
$ECR_REPOSITORY_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

Write-Host "=== Pushing with Docker Buildx ===" -ForegroundColor Cyan
Write-Host ""

# Authenticate
Write-Host "Authenticating with ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
if ($LASTEXITCODE -ne 0) {
    Write-Host "Authentication failed!" -ForegroundColor Red
    exit 1
}

# Create buildx builder if it doesn't exist
Write-Host "Setting up buildx..." -ForegroundColor Yellow
docker buildx create --name mybuilder --use 2>&1 | Out-Null
docker buildx inspect --bootstrap | Out-Null

# Build and push in one step (more reliable)
Write-Host "Building and pushing image (this may take a while)..." -ForegroundColor Yellow
Write-Host ""

docker buildx build `
    --platform linux/amd64 `
    --tag "${ECR_REPOSITORY_URI}:latest" `
    --push `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Successfully pushed image!" -ForegroundColor Green
    Write-Host "Image URI: ${ECR_REPOSITORY_URI}:latest" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "✗ Push failed" -ForegroundColor Red
    Write-Host "Try running: .\diagnose_push_issue.ps1" -ForegroundColor Yellow
    exit 1
}

