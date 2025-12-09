# Diagnostic script for ECR push issues

Write-Host "=== ECR Push Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "   OK - Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "   ERROR - Docker not found in PATH" -ForegroundColor Red
    exit 1
}

# Check Docker is running
Write-Host ""
Write-Host "2. Checking Docker daemon..." -ForegroundColor Yellow
try {
    $null = docker info 2>&1 | Select-String "Server Version"
    Write-Host "   OK - Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "   ERROR - Docker daemon is not running" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Check image exists
Write-Host ""
Write-Host "3. Checking if image exists..." -ForegroundColor Yellow
$imageInfo = docker images portfolio-streamlit:latest --format "{{.Repository}}:{{.Tag}} - Size: {{.Size}}" 2>&1
if ($LASTEXITCODE -eq 0 -and $imageInfo -and $imageInfo -notmatch "Error") {
    Write-Host "   OK - Image found:" -ForegroundColor Green
    Write-Host "   $imageInfo" -ForegroundColor White
    
    # Check if size indicates it's large
    if ($imageInfo -match "GB") {
        Write-Host "   WARNING - Image is large (GB). This may cause push failures." -ForegroundColor Yellow
        Write-Host "   Consider optimizing the image or removing Seurat from Dockerfile." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ERROR - Image not found. Build it first with: docker build -t portfolio-streamlit ." -ForegroundColor Red
    exit 1
}

# Check AWS CLI
Write-Host ""
Write-Host "4. Checking AWS CLI..." -ForegroundColor Yellow
$aws = Get-Command aws -ErrorAction SilentlyContinue
if ($aws) {
    Write-Host "   OK - AWS CLI is installed" -ForegroundColor Green
    aws --version
} else {
    Write-Host "   ERROR - AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host ""
Write-Host "5. Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK - AWS credentials are valid" -ForegroundColor Green
        $identityObj = $identity | ConvertFrom-Json
        Write-Host "   Account: $($identityObj.Account)" -ForegroundColor White
        Write-Host "   User: $($identityObj.Arn)" -ForegroundColor White
    } else {
        Write-Host "   ERROR - AWS credentials invalid or not configured" -ForegroundColor Red
        Write-Host "   Run: aws configure" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ERROR - Error checking AWS credentials" -ForegroundColor Red
    exit 1
}

# Check ECR repository
Write-Host ""
Write-Host "6. Checking ECR repository..." -ForegroundColor Yellow
$AWS_ACCOUNT_ID = "083738448444"
$AWS_REGION = "us-east-1"
$ECR_REPOSITORY_NAME = "portfolio-streamlit"

try {
    $repo = aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK - ECR repository exists" -ForegroundColor Green
    } else {
        Write-Host "   WARNING - ECR repository not found" -ForegroundColor Yellow
        Write-Host "   Creating repository..." -ForegroundColor Yellow
        aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   OK - Repository created" -ForegroundColor Green
        } else {
            Write-Host "   ERROR - Failed to create repository" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "   ERROR - Error checking ECR repository" -ForegroundColor Red
}

# Check ECR authentication
Write-Host ""
Write-Host "7. Testing ECR authentication..." -ForegroundColor Yellow
$ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
try {
    $loginResult = aws ecr get-login-password --region $AWS_REGION 2>&1 | docker login --username AWS --password-stdin $ECR_URI 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK - ECR authentication successful" -ForegroundColor Green
    } else {
        Write-Host "   ERROR - ECR authentication failed" -ForegroundColor Red
        Write-Host "   $loginResult" -ForegroundColor Red
    }
} catch {
    Write-Host "   ERROR - Error authenticating with ECR" -ForegroundColor Red
}

# Network connectivity test
Write-Host ""
Write-Host "8. Testing network connectivity..." -ForegroundColor Yellow
try {
    $testResult = Test-NetConnection -ComputerName "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($testResult) {
        Write-Host "   OK - Can reach ECR endpoint" -ForegroundColor Green
    } else {
        Write-Host "   WARNING - Cannot reach ECR endpoint" -ForegroundColor Yellow
        Write-Host "   Check your firewall/proxy settings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   WARNING - Could not test network connectivity" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Diagnostic Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all checks passed, try these solutions:" -ForegroundColor Yellow
Write-Host "1. Use Docker Buildx: .\push_with_buildx.ps1" -ForegroundColor White
Write-Host "2. Try pushing during off-peak hours" -ForegroundColor White
Write-Host "3. Check Docker Desktop network settings" -ForegroundColor White
Write-Host "4. Temporarily disable VPN/proxy" -ForegroundColor White
Write-Host "5. Use a lighter Dockerfile (without Seurat) to test" -ForegroundColor White
