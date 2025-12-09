# Using AWS CodeBuild Instead of Local Push

If you're experiencing persistent network issues pushing large Docker images from your local machine, **AWS CodeBuild** is a much more reliable solution. CodeBuild runs in AWS's network, so uploads are faster and more stable.

## Why CodeBuild?

- ✅ **Faster uploads** - Builds and pushes happen within AWS network
- ✅ **More reliable** - No local network issues
- ✅ **Automatic** - Triggers on every Git push
- ✅ **Free tier** - 100 build minutes/month free

## Setup Steps

### 1. Create CodeBuild Project

1. Go to AWS Console → CodeBuild
2. Click "Create build project"
3. Configure:
   - **Project name**: `portfolio-streamlit-build`
   - **Source**: GitHub (connect your repo)
   - **Repository**: `ttellner/portfolio`
   - **Branch**: `main`
   - **Environment**:
     - **Operating system**: Ubuntu
     - **Runtime**: Standard
     - **Image**: `aws/codebuild/standard:7.0` (or latest)
     - **Privileged**: ✅ **Enable** (required for Docker)
   - **Buildspec**: Use a buildspec file (see below)

### 2. Create buildspec.yml

Create this file in your repository root:

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/portfolio-streamlit
      - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
      - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $REPOSITORY_URI:latest .
      - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $REPOSITORY_URI:latest
      - docker push $REPOSITORY_URI:$IMAGE_TAG
      - echo Writing image definitions file...
      - printf '[{"name":"portfolio-streamlit","imageUri":"%s"}]' $REPOSITORY_URI:latest > imagedefinitions.json
artifacts:
  files:
    - imagedefinitions.json
```

### 3. Set Up IAM Permissions

CodeBuild needs permissions to push to ECR:

1. Go to IAM → Roles
2. Find your CodeBuild service role (e.g., `codebuild-portfolio-streamlit-build-service-role`)
3. Attach these policies:
   - `AmazonEC2ContainerRegistryFullAccess`
   - Or create a custom policy with:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "ecr:GetAuthorizationToken",
             "ecr:BatchCheckLayerAvailability",
             "ecr:GetDownloadUrlForLayer",
             "ecr:BatchGetImage",
             "ecr:PutImage",
             "ecr:InitiateLayerUpload",
             "ecr:UploadLayerPart",
             "ecr:CompleteLayerUpload"
           ],
           "Resource": "*"
         }
       ]
     }
     ```

### 4. Create ECR Repository (if not exists)

```bash
aws ecr create-repository --repository-name portfolio-streamlit --region us-east-1
```

### 5. Configure Environment Variables

In CodeBuild project settings, add:
- `AWS_ACCOUNT_ID`: `083738448444`
- `AWS_DEFAULT_REGION`: `us-east-1`

### 6. Trigger Build

- **Manual**: Click "Start build" in CodeBuild console
- **Automatic**: Every push to `main` branch will trigger a build

### 7. Connect to App Runner

Once CodeBuild successfully pushes the image:

1. Go to AWS App Runner Console
2. Create/Update service
3. Select "Container registry" → "Amazon ECR"
4. Select repository: `portfolio-streamlit`
5. Select image tag: `latest`
6. Deploy!

## Benefits

- **No more network timeouts** - Everything happens in AWS
- **Faster builds** - AWS has better bandwidth
- **Automatic deployments** - Push to GitHub → Build → Deploy
- **Cost effective** - Free tier covers most use cases

## Alternative: GitHub Actions

You can also use GitHub Actions with similar benefits:

```yaml
name: Build and Push to ECR

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: portfolio-streamlit
          IMAGE_TAG: latest
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

This is often easier to set up than CodeBuild!

