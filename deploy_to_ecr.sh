#!/bin/bash
# Script to build and push Docker image to Amazon ECR for AWS App Runner deployment

# Configuration - UPDATE THESE VALUES
AWS_REGION="us-east-1"  # Change to your preferred region
AWS_ACCOUNT_ID=""  # Your AWS account ID (12 digits)
ECR_REPOSITORY_NAME="portfolio-streamlit"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS account ID is set
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: AWS_ACCOUNT_ID is not set. Please update the script with your AWS account ID.${NC}"
    echo "You can find your AWS account ID in the AWS Console (top right corner)."
    exit 1
fi

ECR_REPOSITORY_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"

echo -e "${GREEN}Building and deploying to AWS App Runner via ECR${NC}"
echo "=========================================="
echo "Region: ${AWS_REGION}"
echo "Repository: ${ECR_REPOSITORY_NAME}"
echo "URI: ${ECR_REPOSITORY_URI}"
echo ""

# Step 1: Authenticate Docker to ECR
echo -e "${YELLOW}Step 1: Authenticating Docker to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPOSITORY_URI}
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to authenticate with ECR. Check your AWS credentials.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Step 2: Create ECR repository if it doesn't exist
echo -e "${YELLOW}Step 2: Checking ECR repository...${NC}"
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY_NAME} --region ${AWS_REGION} > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Repository doesn't exist. Creating..."
    aws ecr create-repository --repository-name ${ECR_REPOSITORY_NAME} --region ${AWS_REGION}
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create ECR repository.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Repository created${NC}"
else
    echo -e "${GREEN}✓ Repository exists${NC}"
fi
echo ""

# Step 3: Build Docker image
echo -e "${YELLOW}Step 3: Building Docker image...${NC}"
docker build -t ${ECR_REPOSITORY_NAME}:latest .
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Image built successfully${NC}"
echo ""

# Step 4: Tag image for ECR
echo -e "${YELLOW}Step 4: Tagging image for ECR...${NC}"
docker tag ${ECR_REPOSITORY_NAME}:latest ${ECR_REPOSITORY_URI}:latest
echo -e "${GREEN}✓ Image tagged${NC}"
echo ""

# Step 5: Push to ECR
echo -e "${YELLOW}Step 5: Pushing image to ECR...${NC}"
docker push ${ECR_REPOSITORY_URI}:latest
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to push image to ECR.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Image pushed successfully${NC}"
echo ""

echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Go to AWS App Runner Console"
echo "2. Create a new service"
echo "3. Select 'Source: Container registry'"
echo "4. Choose 'Amazon ECR'"
echo "5. Select repository: ${ECR_REPOSITORY_NAME}"
echo "6. Select image tag: latest"
echo "7. Set port: 8501"
echo "8. Create and deploy"
echo ""
echo "ECR Repository URI: ${ECR_REPOSITORY_URI}:latest"

