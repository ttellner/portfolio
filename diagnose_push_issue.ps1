# Diagnostic script for ECR push issues

Write-Host "=== ECR Push Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "   ✓ Docker is installed" -ForegroundColor Green
    docker --version
} else {
    Write-Host "   ✗ Docker not found in PATH" -ForegroundColor Red
    exit 1
}

# Check Docker is running
Write-Host ""
Write-Host "2. Checking Docker daemon..." -ForegroundColor Yellow
try {
    docker info | Select-String "Server Version" | Out-Null
    Write-Host "   ✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Docker daemon is not running" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Check image exists
Write-Host ""
Write-Host "3. Checking if image exists..." -ForegroundColor Yellow
$imageInfo = docker images portfolio-streamlit:latest --format "{{.Repository}}:{{.Tag}} - Size: {{.Size}}" 2>&1
if ($LASTEXITCODE -eq 0 -and $imageInfo) {
    Write-Host "   ✓ Image found:" -ForegroundColor Green
    Write-Host "   $imageInfo" -ForegroundColor White
    
    # Get detailed size info
    $sizeBytes = docker images portfolio-streamlit:latest --format "{{.Size}}" | ForEach-Object {
        if ($_ -match '(\d+(?:\.\d+)?)(\w*)') {
            $value = [double]$matches[1]
            $unit = $matches[2]
            switch ($unit) {
                'GB' { $value * 1GB }
                'MB' { $value * 1MB }
                'KB' { $value * 1KB }
                default { $value }
            }
        }
    }
    
    if ($sizeBytes -gt 5GB) {
        Write-Host "   ⚠ WARNING: Image is very large (>5GB). This may cause push failures." -ForegroundColor Yellow
        Write-Host "   Consider optimizing the image or removing Seurat from Dockerfile." -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ Image not found. Build it first with: docker build -t portfolio-streamlit ." -ForegroundColor Red
    exit 1
}

# Check AWS CLI
Write-Host ""
Write-Host "4. Checking AWS CLI..." -ForegroundColor Yellow
$aws = Get-Command aws -ErrorAction SilentlyContinue
if ($aws) {
    Write-Host "   ✓ AWS CLI is installed" -ForegroundColor Green
    aws --version
} else {
    Write-Host "   ✗ AWS CLI not found" -ForegroundColor Red
    exit 1
}

# Check AWS credentials
Write-Host ""
Write-Host "5. Checking AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ AWS credentials are valid" -ForegroundColor Green
        $identity | ConvertFrom-Json | Format-List
    } else {
        Write-Host "   ✗ AWS credentials invalid or not configured" -ForegroundColor Red
        Write-Host "   Run: aws configure" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ✗ Error checking AWS credentials" -ForegroundColor Red
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
        Write-Host "   ✓ ECR repository exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ ECR repository not found" -ForegroundColor Red
        Write-Host "   Creating repository..." -ForegroundColor Yellow
        aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
    }
} catch {
    Write-Host "   ✗ Error checking ECR repository" -ForegroundColor Red
}

# Check ECR authentication
Write-Host ""
Write-Host "7. Testing ECR authentication..." -ForegroundColor Yellow
$ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
try {
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ ECR authentication successful" -ForegroundColor Green
    } else {
        Write-Host "   ✗ ECR authentication failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Error authenticating with ECR" -ForegroundColor Red
}

# Network connectivity test
Write-Host ""
Write-Host "8. Testing network connectivity..." -ForegroundColor Yellow
try {
    $testResult = Test-NetConnection -ComputerName "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com" -Port 443 -InformationLevel Quiet
    if ($testResult) {
        Write-Host "   ✓ Can reach ECR endpoint" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Cannot reach ECR endpoint" -ForegroundColor Red
        Write-Host "   Check your firewall/proxy settings" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠ Could not test network connectivity" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Diagnostic Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all checks passed, try these solutions:" -ForegroundColor Yellow
Write-Host "1. Use Docker Buildx: docker buildx build --platform linux/amd64 --push -t ..." -ForegroundColor White
Write-Host "2. Try pushing during off-peak hours" -ForegroundColor White
Write-Host "3. Check Docker Desktop network settings" -ForegroundColor White
Write-Host "4. Temporarily disable VPN/proxy" -ForegroundColor White
Write-Host "5. Use a lighter Dockerfile (without Seurat) to test" -ForegroundColor White

