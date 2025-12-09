# PowerShell script to build and push Docker image to Amazon ECR for AWS App Runner deployment

# Configuration - UPDATE THESE VALUES
$AWS_REGION = "us-east-1"  # Change to your preferred region
$AWS_ACCOUNT_ID = "083738448444"  # Your AWS account ID (12 digits, no dashes)
$ECR_REPOSITORY_NAME = "portfolio-streamlit"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Check if AWS CLI is installed
$awsCli = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsCli) {
    Write-ColorOutput Red "Error: AWS CLI is not installed or not in PATH."
    Write-Output ""
    Write-Output "Please install AWS CLI:"
    Write-Output "1. Download from: https://aws.amazon.com/cli/"
    Write-Output "2. Or install via: winget install Amazon.AWSCLI"
    Write-Output "3. After installation, restart PowerShell and try again"
    exit 1
}

# Check if Docker is installed
$dockerCli = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCli) {
    Write-ColorOutput Red "Error: Docker is not installed or not in PATH."
    Write-Output ""
    Write-Output "Please install Docker Desktop:"
    Write-Output "1. Download from: https://www.docker.com/products/docker-desktop"
    Write-Output "2. After installation, restart PowerShell and try again"
    exit 1
}

# Check if AWS account ID is set
if ([string]::IsNullOrEmpty($AWS_ACCOUNT_ID)) {
    Write-ColorOutput Red "Error: AWS_ACCOUNT_ID is not set. Please update the script with your AWS account ID."
    Write-Output "You can find your AWS account ID in the AWS Console (top right corner)."
    Write-Output "Note: AWS account ID should be 12 digits without dashes (e.g., 083738448444)"
    exit 1
}

# Validate AWS account ID format (should be 12 digits)
if ($AWS_ACCOUNT_ID -notmatch '^\d{12}$') {
    Write-ColorOutput Red "Error: AWS_ACCOUNT_ID must be exactly 12 digits without dashes or spaces."
    Write-Output "Current value: $AWS_ACCOUNT_ID"
    Write-Output "Expected format: 083738448444 (12 digits)"
    exit 1
}

$ECR_REPOSITORY_URI = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

Write-ColorOutput Green "Building and deploying to AWS App Runner via ECR"
Write-Output "=========================================="
Write-Output "Region: $AWS_REGION"
Write-Output "Repository: $ECR_REPOSITORY_NAME"
Write-Output "URI: $ECR_REPOSITORY_URI"
Write-Output ""

# Step 1: Authenticate Docker to ECR
Write-ColorOutput Yellow "Step 1: Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to authenticate with ECR. Check your AWS credentials."
    exit 1
}
Write-ColorOutput Green "OK - Authenticated"
Write-Output ""

# Step 2: Create ECR repository if it doesn't exist
Write-ColorOutput Yellow "Step 2: Checking ECR repository..."
$repoExists = aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Output "Repository doesn't exist. Creating..."
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "Error: Failed to create ECR repository."
        exit 1
    }
    Write-ColorOutput Green "OK - Repository created"
} else {
    Write-ColorOutput Green "OK - Repository exists"
}
Write-Output ""

# Step 3: Build Docker image
Write-ColorOutput Yellow "Step 3: Building Docker image..."
docker build -t "${ECR_REPOSITORY_NAME}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Docker build failed."
    exit 1
}
Write-ColorOutput Green "OK - Image built successfully"
Write-Output ""

# Step 4: Tag image for ECR
Write-ColorOutput Yellow "Step 4: Tagging image for ECR..."
docker tag "${ECR_REPOSITORY_NAME}:latest" "${ECR_REPOSITORY_URI}:latest"
Write-ColorOutput Green "OK - Image tagged"
Write-Output ""

# Step 5: Push to ECR
Write-ColorOutput Yellow "Step 5: Pushing image to ECR..."
docker push "${ECR_REPOSITORY_URI}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to push image to ECR."
    exit 1
}
Write-ColorOutput Green "OK - Image pushed successfully"
Write-Output ""

Write-ColorOutput Green "=========================================="
Write-ColorOutput Green "Deployment complete!"
Write-Output ""
Write-Output "Next steps:"
Write-Output "1. Go to AWS App Runner Console"
Write-Output "2. Create a new service"
Write-Output "3. Select Source: Container registry"
Write-Output "4. Choose Amazon ECR"
Write-Output "5. Select repository: $ECR_REPOSITORY_NAME"
Write-Output "6. Select image tag: latest"
Write-Output "7. Set port: 8501"
Write-Output "8. Create and deploy"
Write-Output ""
Write-Output "ECR Repository URI: ${ECR_REPOSITORY_URI}:latest"
