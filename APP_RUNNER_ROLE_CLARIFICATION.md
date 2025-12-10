# App Runner Role Clarification

## Two Different Roles in App Runner

### 1. Access Role (For ECR - What You Need to Fix)

**Location:** Deployment Settings → Access role

**Purpose:** Allows App Runner to pull Docker images from ECR

**What to do:**
- Select **"Create new service role"**
- **Name it:** `AppRunner-ECR-AccessRole` or `portfolio-streamlit-ecr-role`
- App Runner will automatically:
  - Create the IAM role
  - Attach `AmazonEC2ContainerRegistryReadOnly` policy
  - Set correct trust policy for `build.apprunner.amazonaws.com`

**This fixes:** "Invalid Access Role" and "Failed to copy image from ECR"

### 2. Instance Role (For AWS Services - Optional)

**Location:** Security → Instance role

**Purpose:** Allows your application to access other AWS services (S3, DynamoDB, etc.)

**What to do:**
- Leave as default (no instance role) unless you need AWS service access
- This is NOT needed for basic deployment
- This is NOT what fixes the ECR error

## About the Custom Policy (`apprunner-ecr-policy.json`)

**Don't use it!** 

The `apprunner-ecr-policy.json` file I created earlier was for **manual setup** if you wanted to create the role yourself. But App Runner's "Create new service role" option is easier and more reliable.

**Just let App Runner create the role automatically.**

## Step-by-Step: Creating the Access Role

1. **App Runner → Your Service → Edit**
2. **Deployment Settings** section
3. **Access role** field
4. Click **"Create new service role"** (or similar button)
5. **Enter role name:** `AppRunner-ECR-AccessRole` (or any name you prefer)
6. App Runner creates it automatically
7. **Save**

## Verify It Worked

After creating the role:

1. Go to **IAM → Roles**
2. Search for the role name you entered
3. Click on it
4. **Permissions** tab should show: `AmazonEC2ContainerRegistryReadOnly`
5. **Trust relationships** should show: `build.apprunner.amazonaws.com`

## Summary

| Role Type | Location | Purpose | Required? |
|-----------|----------|---------|-----------|
| **Access Role** | Deployment Settings | ECR access | ✅ YES (fixes ECR error) |
| **Instance Role** | Security | AWS service access | ❌ NO (optional) |

**For your current errors, you only need to fix the Access Role!**

