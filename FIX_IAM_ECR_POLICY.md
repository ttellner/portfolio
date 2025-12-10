# Fix: Finding AmazonEC2ContainerRegistryReadOnly Policy

## Issue
Can't find `AmazonEC2ContainerRegistryReadOnly` in IAM.

## Solution 1: Search for the Policy

1. Go to **IAM → Policies**
2. In the search box, type: `ECR`
3. Look for: **AmazonEC2ContainerRegistryReadOnly**
4. It's an **AWS managed policy** (should show "AWS" as the type)

**Alternative search terms:**
- Search for: `ContainerRegistry`
- Search for: `ECR ReadOnly`
- Filter by: **AWS managed** policies only

## Solution 2: Use the Exact ARN

If you can't find it by name, use the ARN directly:

**ARN:** `arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly`

**To attach using ARN:**
1. Go to **IAM → Roles**
2. Find your App Runner role (e.g., `AppRunner-ECR-AccessRole-xxxxx`)
3. Click on the role
4. Click **Add permissions → Attach policies**
5. In the search box, paste: `arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly`
6. Select it and click **Add permissions**

## Solution 3: Create Custom Policy (If Still Can't Find It)

If the managed policy still doesn't show up, create a custom policy:

1. Go to **IAM → Policies → Create policy**
2. Click **JSON** tab
3. Paste this:

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
                "ecr:BatchGetImage"
            ],
            "Resource": "*"
        }
    ]
}
```

4. Click **Next**
5. Name it: `AppRunnerECRAccess`
6. Click **Create policy**
7. Go back to your App Runner role
8. Attach this custom policy

## Solution 4: Let App Runner Create the Role (Easiest)

If you're still having trouble, the **easiest solution** is to let App Runner create the role automatically:

1. Go to **App Runner → Your Service → Edit**
2. Go to **Security** section
3. Under **Access role**, select **"Create new service role"**
4. App Runner will automatically:
   - Create the role
   - Attach the correct permissions
   - Configure everything properly

**This is the recommended approach** if you're having permission issues!

## Verify Permissions

After attaching the policy, verify it worked:

1. Go to **IAM → Roles**
2. Find your App Runner role
3. Click on it
4. Check **Permissions** tab
5. You should see either:
   - `AmazonEC2ContainerRegistryReadOnly` (AWS managed)
   - OR your custom policy with the 4 ECR permissions

## Required Permissions Summary

The role needs these 4 permissions:
- ✅ `ecr:GetAuthorizationToken`
- ✅ `ecr:BatchCheckLayerAvailability`
- ✅ `ecr:GetDownloadUrlForLayer`
- ✅ `ecr:BatchGetImage`

## Quick Test

After fixing permissions, try deploying again in App Runner. The "Failed to copy image" error should be resolved.

