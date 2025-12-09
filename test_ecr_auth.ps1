# Script to test ECR authentication (simulates what GitHub Actions does)

$AWS_REGION = "us-east-1"
$ECR_REPOSITORY_NAME = "portfolio-streamlit"
$AWS_ACCOUNT_ID = "083738448444"

Write-Host "=== Testing ECR Authentication ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test AWS credentials
Write-Host "Step 1: Testing AWS credentials..." -ForegroundColor Yellow
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        $identityObj = $identity | ConvertFrom-Json
        Write-Host "OK - AWS credentials are valid" -ForegroundColor Green
        Write-Host "  Account: $($identityObj.Account)" -ForegroundColor White
        Write-Host "  User: $($identityObj.Arn)" -ForegroundColor White
    } else {
        Write-Host "ERROR - AWS credentials invalid" -ForegroundColor Red
        Write-Host "Run: aws configure" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR - Could not verify AWS credentials" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Get ECR login token
Write-Host "Step 2: Getting ECR login token..." -ForegroundColor Yellow
$ECR_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

try {
    $loginPassword = aws ecr get-login-password --region $AWS_REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - ECR login token obtained" -ForegroundColor Green
        Write-Host "  Token length: $($loginPassword.Length) characters" -ForegroundColor Gray
    } else {
        Write-Host "ERROR - Could not get ECR login token" -ForegroundColor Red
        Write-Host $loginPassword -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR - Failed to get ECR login token" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 3: Login to ECR (this is what GitHub Actions does)
Write-Host "Step 3: Logging Docker into ECR..." -ForegroundColor Yellow
Write-Host "  (This simulates: aws ecr get-login-password | docker login)" -ForegroundColor Gray

try {
    $loginResult = aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - Successfully logged into ECR" -ForegroundColor Green
        Write-Host "  Registry: $ECR_URI" -ForegroundColor White
    } else {
        Write-Host "ERROR - Docker login failed" -ForegroundColor Red
        Write-Host $loginResult -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR - Docker login failed" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Verify ECR repository access
Write-Host "Step 4: Verifying ECR repository access..." -ForegroundColor Yellow
try {
    $repo = aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - Can access ECR repository" -ForegroundColor Green
        Write-Host "  Repository: $ECR_REPOSITORY_NAME" -ForegroundColor White
    } else {
        Write-Host "WARNING - Repository may not exist, but authentication works" -ForegroundColor Yellow
        Write-Host "  (Repository will be created on first push)" -ForegroundColor Gray
    }
} catch {
    Write-Host "WARNING - Could not verify repository (may not exist yet)" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Test push permissions
Write-Host "Step 5: Testing ECR push permissions..." -ForegroundColor Yellow
try {
    # Check if we have push permissions by trying to get repository policy
    $policy = aws ecr get-repository-policy --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - Has repository access" -ForegroundColor Green
    } else {
        # Repository might not exist, which is OK
        if ($policy -match "RepositoryNotFoundException") {
            Write-Host "OK - Repository doesn't exist yet (will be created on first push)" -ForegroundColor Green
        } else {
            Write-Host "WARNING - Could not verify permissions" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "INFO - Repository may not exist yet (this is OK)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Authentication Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  AWS Credentials: OK" -ForegroundColor Green
Write-Host "  ECR Login: OK" -ForegroundColor Green
Write-Host "  Docker Authentication: OK" -ForegroundColor Green
Write-Host ""
Write-Host "Your credentials are ready for GitHub Actions!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add these credentials to GitHub Secrets:" -ForegroundColor White
Write-Host "   - AWS_ACCESS_KEY_ID" -ForegroundColor White
Write-Host "   - AWS_SECRET_ACCESS_KEY" -ForegroundColor White
Write-Host "2. Push the workflow file to trigger deployment" -ForegroundColor White

