# Fix IAM Role Manually (If App Runner Won't Create It)

## Problem

App Runner says "Create new service role" but:
- Role doesn't appear in IAM
- "Invalid Access Role" error persists
- Can't pull image from ECR

## Solution: Create Role Manually in IAM

### Step 1: Create the IAM Role

1. Go to **IAM → Roles → Create role**
2. **Trusted entity type:** Select **AWS service**
3. **Use case:** Search for and select **"App Runner"**
4. Click **Next**

### Step 2: Add Permissions

1. In the search box, type: `ECR`
2. Check the box for: **AmazonEC2ContainerRegistryReadOnly**
3. Click **Next**

### Step 3: Name the Role

1. **Role name:** `AppRunner-ECR-AccessRole` (or any name you prefer)
2. **Description:** `Allows App Runner to pull images from ECR`
3. Click **Create role**

### Step 4: Verify the Role

1. Go to **IAM → Roles**
2. Find your role: `AppRunner-ECR-AccessRole`
3. Click on it
4. **Permissions** tab should show: `AmazonEC2ContainerRegistryReadOnly`
5. **Trust relationships** tab should show:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Service": "build.apprunner.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```

### Step 5: Use the Role in App Runner

1. Go to **App Runner → Your Service → Edit**
2. **Deployment Settings → Access role**
3. **Select:** "Use existing service role"
4. **Choose the role:** `AppRunner-ECR-AccessRole` (the one you just created)
5. **Save**

## Alternative: Use ARN Directly

If you can't find the role in the dropdown:

1. Note the role ARN (from IAM → Roles → Your role)
2. In App Runner, paste the ARN directly
3. Format: `arn:aws:iam::083738448444:role/AppRunner-ECR-AccessRole`

## Why This Works

- **Manual creation** ensures the role exists
- **Correct trust policy** allows App Runner to assume the role
- **ECR permissions** allow pulling images
- **Explicit selection** in App Runner uses the correct role

## After Fixing Role

1. **Push Dockerfile** (if not already done)
2. **Wait for image** to build in ECR
3. **Deploy** in App Runner
4. Health check should pass (once new image with nginx is deployed)

