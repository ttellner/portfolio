# PowerShell script to build and push Docker image to Amazon ECR for AWS App Runner deployment

# Configuration - UPDATE THESE VALUES
$AWS_REGION = "us-east-1"  # Change to your preferred region
$AWS_ACCOUNT_ID = ""  # Your AWS account ID (12 digits)
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

# Check if AWS account ID is set
if ([string]::IsNullOrEmpty($AWS_ACCOUNT_ID)) {
    Write-ColorOutput Red "Error: AWS_ACCOUNT_ID is not set. Please update the script with your AWS account ID."
    Write-Output "You can find your AWS account ID in the AWS Console (top right corner)."
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
$loginCommand = aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to authenticate with ECR. Check your AWS credentials."
    exit 1
}
Write-ColorOutput Green "✓ Authenticated"
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
    Write-ColorOutput Green "✓ Repository created"
} else {
    Write-ColorOutput Green "✓ Repository exists"
}
Write-Output ""

# Step 3: Build Docker image
Write-ColorOutput Yellow "Step 3: Building Docker image..."
docker build -t "${ECR_REPOSITORY_NAME}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Docker build failed."
    exit 1
}
Write-ColorOutput Green "✓ Image built successfully"
Write-Output ""

# Step 4: Tag image for ECR
Write-ColorOutput Yellow "Step 4: Tagging image for ECR..."
docker tag "${ECR_REPOSITORY_NAME}:latest" "${ECR_REPOSITORY_URI}:latest"
Write-ColorOutput Green "✓ Image tagged"
Write-Output ""

# Step 5: Push to ECR
Write-ColorOutput Yellow "Step 5: Pushing image to ECR..."
docker push "${ECR_REPOSITORY_URI}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput Red "Error: Failed to push image to ECR."
    exit 1
}
Write-ColorOutput Green "✓ Image pushed successfully"
Write-Output ""

Write-ColorOutput Green "=========================================="
Write-ColorOutput Green "Deployment complete!"
Write-Output ""
Write-Output "Next steps:"
Write-Output "1. Go to AWS App Runner Console"
Write-Output "2. Create a new service"
Write-Output "3. Select 'Source: Container registry'"
Write-Output "4. Choose 'Amazon ECR'"
Write-Output "5. Select repository: $ECR_REPOSITORY_NAME"
Write-Output "6. Select image tag: latest"
Write-Output "7. Set port: 8501"
Write-Output "8. Create and deploy"
Write-Output ""
Write-Output "ECR Repository URI: ${ECR_REPOSITORY_URI}:latest"

