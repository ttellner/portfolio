# Create IAM Role with Custom Trust Policy (When App Runner Not Listed)

## Problem

"App Runner" doesn't appear in the IAM role creation wizard's use case list.

## Solution: Create Role with Custom Trust Policy

### Step 1: Start Role Creation

1. Go to **IAM → Roles → Create role**
2. **Trusted entity type:** Select **"Custom trust policy"**
3. Click **Next**

### Step 2: Enter Trust Policy

In the **JSON** editor, paste this exact policy:

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

**Important:** This allows App Runner's build service to assume this role.

Click **Next**

### Step 3: Add Permissions

1. In the search box, type: `ECR`
2. Check the box for: **AmazonEC2ContainerRegistryReadOnly**
3. Click **Next**

### Step 4: Name the Role

1. **Role name:** `AppRunner-ECR-AccessRole` (or any name you prefer)
2. **Description:** `Allows App Runner to pull images from ECR`
3. Click **Create role**

### Step 5: Verify

1. Go to **IAM → Roles**
2. Find your role: `AppRunner-ECR-AccessRole`
3. Click on it
4. **Permissions** tab should show: `AmazonEC2ContainerRegistryReadOnly` ✅
5. **Trust relationships** tab should show the custom policy with `build.apprunner.amazonaws.com` ✅

### Step 6: Use in App Runner

1. **App Runner → Your Service → Edit**
2. **Deployment Settings → Access role**
3. **Select:** "Use existing service role"
4. **Choose:** `AppRunner-ECR-AccessRole`
5. **Save**

## Alternative: Use "EC2" as Use Case

If "Custom trust policy" doesn't work either:

1. **Trusted entity type:** Select **"AWS service"**
2. **Use case:** Select **"EC2"** (closest match)
3. Click **Next**
4. **Add permissions:** `AmazonEC2ContainerRegistryReadOnly`
5. Click **Next**
6. **Name:** `AppRunner-ECR-AccessRole`
7. **Create role**
8. **After creation:** Go to **Trust relationships** tab → **Edit trust policy**
9. **Replace** the EC2 policy with the App Runner policy (from Step 2 above)
10. **Save**

## Quick Copy-Paste Trust Policy

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

This is the key part - it allows App Runner's build service to use this role.

