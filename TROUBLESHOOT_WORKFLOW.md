# Troubleshooting: Workflow Not Showing in GitHub Actions

## Why Workflows Don't Appear

GitHub Actions workflows only appear if:
1. ✅ File is in `.github/workflows/` directory
2. ✅ File has `.yml` or `.yaml` extension
3. ✅ File has valid YAML syntax
4. ✅ File is on the `main` branch (or default branch)
5. ✅ File has been pushed to GitHub

## Quick Fix: Upload via GitHub Web Interface

Since Git push is having issues, upload directly:

### Step 1: Go to GitHub

1. Navigate to: https://github.com/ttellner/portfolio
2. Make sure you're on the `main` branch (check branch dropdown)

### Step 2: Create the Workflow File

1. Click **"Add file"** → **"Create new file"**
2. In the filename box, type: `.github/workflows/deploy.yml`
   - GitHub will automatically create the `.github` and `workflows` folders
3. Copy and paste this content:

```yaml
name: Deploy to AWS App Runner via ECR

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: portfolio-streamlit
  AWS_ACCOUNT_ID: 083738448444

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
      
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: latest
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "Image pushed: $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
    
    - name: Success message
      run: |
        echo "✅ Image successfully pushed to ECR!"
        echo "App Runner will automatically deploy the new image (if auto-deploy is enabled)"
```

4. Scroll down and click **"Commit new file"**
5. Add commit message: "Add deployment workflow"
6. Click **"Commit new file"**

### Step 3: Verify It Appears

1. Go to: https://github.com/ttellner/portfolio/actions
2. You should now see **"Deploy to AWS App Runner via ECR"** in the workflows list
3. If it doesn't appear immediately, wait 1-2 minutes and refresh

## Alternative: Check if File Exists on GitHub

1. Go to: https://github.com/ttellner/portfolio/tree/main/.github/workflows
2. Check if `deploy.yml` exists
3. If it exists but workflow doesn't show:
   - Check for YAML syntax errors
   - Make sure it's on the `main` branch
   - Try making a small edit and committing

## Verify YAML Syntax

The workflow file should be valid YAML. Common issues:
- ❌ Tabs instead of spaces (must use spaces)
- ❌ Missing colons after keys
- ❌ Incorrect indentation
- ❌ Special characters in wrong places

## Force Refresh GitHub Actions

Sometimes GitHub needs a moment to detect new workflows:

1. Make a small change to the workflow file (add a comment)
2. Commit the change
3. Wait 1-2 minutes
4. Refresh the Actions page

## Check Branch

Make sure the workflow file is on your default branch:

1. Go to: https://github.com/ttellner/portfolio/branches
2. Check which branch is the default (usually `main`)
3. Make sure the workflow file is on that branch

## Still Not Showing?

If the workflow still doesn't appear after uploading:

1. **Check file path**: Must be exactly `.github/workflows/deploy.yml`
2. **Check file extension**: Must be `.yml` or `.yaml`
3. **Check YAML syntax**: Use a YAML validator
4. **Check branch**: Must be on default branch
5. **Wait a few minutes**: GitHub sometimes takes time to index

## Quick Test

Create a simple test workflow to verify Actions is working:

1. Create: `.github/workflows/test.yml`
2. Content:
```yaml
name: Test Workflow
on:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Hello World"
```

3. If this appears, Actions is working - the issue is with the deploy.yml file
4. If this doesn't appear, there's a broader issue with GitHub Actions

