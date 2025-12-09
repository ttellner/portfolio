# AWS No-Code / Low-Code Deployment Options

Since you want to deploy to AWS specifically, here are the easiest options that require minimal manual work.

## 🎯 Option 1: GitHub Actions → ECR → App Runner (Recommended - Low-Code)

**This is the best solution** - it solves your network issues by building in GitHub's infrastructure, then automatically pushes to ECR. App Runner can auto-deploy from ECR.

### Setup Steps:

#### 1. Add GitHub Secrets

1. Go to your GitHub repo: `https://github.com/ttellner/portfolio`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add these two secrets:
   - **Name**: `AWS_ACCESS_KEY_ID`
     - **Value**: Your AWS Access Key ID
   - **Name**: `AWS_SECRET_ACCESS_KEY`
     - **Value**: Your AWS Secret Access Key

#### 2. The Workflow is Already Created!

I've already created `.github/workflows/deploy.yml` in your repo. Just commit and push it:

```powershell
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions workflow for AWS deployment"
git push origin main
```

#### 3. Configure App Runner for Auto-Deploy

1. Go to AWS App Runner Console
2. Create/Edit your service
3. **Source**: Container registry → Amazon ECR
4. **Repository**: `portfolio-streamlit`
5. **Image tag**: `latest`
6. **Deployment trigger**: Select **"Automatic"** (deploys when new image is pushed)

#### 4. That's It!

Now every time you push to `main`:
- ✅ GitHub Actions builds your Docker image (in GitHub's network - no local issues!)
- ✅ Pushes to ECR automatically
- ✅ App Runner detects new image and deploys automatically

**No more manual Docker builds or network issues!**

---

## 🏗️ Option 2: AWS CodeBuild (No-Code Setup)

AWS CodeBuild can automatically build and push to ECR when you push to GitHub.

### Setup Steps:

#### 1. Create CodeBuild Project

1. Go to AWS Console → **CodeBuild**
2. Click **"Create build project"**

#### 2. Configure Project

**Project configuration:**
- **Project name**: `portfolio-streamlit-build`

**Source:**
- **Source provider**: GitHub
- **Repository**: Connect your GitHub account
- **Repository**: `ttellner/portfolio`
- **Branch**: `main`
- **Source version**: `main`

**Environment:**
- **Operating system**: Ubuntu
- **Runtime**: Standard
- **Image**: `aws/codebuild/standard:7.0` (or latest)
- **Image version**: Always use the latest
- **Privileged**: ✅ **Enable this** (required for Docker builds)
- **Service role**: Create new service role (or use existing)

**Buildspec:**
- Select **"Use a buildspec file"**
- **Buildspec name**: `buildspec.yml` (we'll create this)

#### 3. Create buildspec.yml

Create this file in your repo root:

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
```

#### 4. Set Environment Variables

In CodeBuild project settings, add:
- **Name**: `AWS_ACCOUNT_ID`
  - **Value**: `083738448444`
- **Name**: `AWS_DEFAULT_REGION`
  - **Value**: `us-east-1`

#### 5. Configure IAM Permissions

1. Go to **IAM** → **Roles**
2. Find your CodeBuild service role (e.g., `codebuild-portfolio-streamlit-build-service-role`)
3. Attach policy: `AmazonEC2ContainerRegistryFullAccess`

#### 6. Create ECR Repository (if needed)

```bash
aws ecr create-repository --repository-name portfolio-streamlit --region us-east-1
```

#### 7. Connect to App Runner

1. Go to **App Runner** → Create/Edit service
2. **Source**: Container registry → Amazon ECR
3. **Repository**: `portfolio-streamlit`
4. **Deployment trigger**: Automatic

#### 8. Trigger Build

- **Manual**: Click "Start build" in CodeBuild
- **Automatic**: Every push to `main` will trigger a build (if webhook is set up)

---

## 🔄 Option 3: AWS CodePipeline (Full CI/CD - No-Code)

This creates a complete pipeline: GitHub → CodeBuild → ECR → App Runner.

### Setup:

1. Go to **AWS CodePipeline**
2. Click **"Create pipeline"**
3. **Pipeline name**: `portfolio-deployment`
4. **Source**: GitHub (Version 2)
   - Connect GitHub
   - Repository: `ttellner/portfolio`
   - Branch: `main`
5. **Build**: AWS CodeBuild
   - Create new project (use settings from Option 2)
6. **Deploy**: AWS App Runner
   - Create new App Runner service
   - Connect to ECR repository

This creates a complete automated pipeline with a visual interface!

---

## 📊 Comparison

| Option | Setup Time | Automation | Best For |
|--------|-----------|------------|----------|
| **GitHub Actions** | 5 minutes | ✅ Full auto | Easiest, most reliable |
| **CodeBuild** | 15 minutes | ⚠️ Manual/Webhook | AWS-native solution |
| **CodePipeline** | 20 minutes | ✅ Full auto | Visual pipeline management |

---

## 🎯 My Recommendation

**Use Option 1 (GitHub Actions)** because:
- ✅ Fastest to set up (5 minutes)
- ✅ Solves your network issues (builds in GitHub's infrastructure)
- ✅ Free for public repos
- ✅ Already created the workflow file for you
- ✅ Most reliable

**Steps:**
1. Add the two GitHub secrets (AWS credentials)
2. Commit and push the workflow file
3. Configure App Runner for auto-deploy
4. Done! Every push = automatic deployment

---

## 🚀 Quick Start: GitHub Actions

1. **Add secrets** (2 minutes):
   - GitHub repo → Settings → Secrets → Actions
   - Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

2. **Push workflow** (1 minute):
   ```powershell
   git add .github/workflows/deploy.yml
   git commit -m "Add auto-deploy workflow"
   git push origin main
   ```

3. **Configure App Runner** (2 minutes):
   - App Runner → Create/Edit service
   - Source: ECR → `portfolio-streamlit`
   - Deployment: Automatic

**Total time: ~5 minutes, then fully automated!**

