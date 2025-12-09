# AWS CLI Setup Guide

## Step 1: Generate AWS Access Keys

1. Go to AWS Console: https://console.aws.amazon.com
2. Search for "IAM" and open it
3. Click "Users" in the left sidebar
4. Click "Add users" (or select an existing user)
5. Enter a username (e.g., `apprunner-deploy`)
6. Select "Programmatic access" as the access type
7. Click "Next: Permissions"
8. Select "Attach policies directly"
9. Search for and select these policies:
   - `AmazonEC2ContainerRegistryFullAccess` (for ECR)
   - `AppRunnerFullAccess` (for App Runner)
   - Or use `PowerUserAccess` for broader permissions
10. Click "Next: Tags" (optional)
11. Click "Next: Review"
12. Click "Create user"
13. **IMPORTANT**: Copy both:
    - **Access Key ID** (starts with `AKIA...`)
    - **Secret Access Key** (long string of characters)
    
    ⚠️ **You can only see the Secret Access Key once!** Save it immediately.

## Step 2: Configure AWS CLI

Open PowerShell and run:

```powershell
aws configure
```

You'll be prompted for:

1. **AWS Access Key ID**: Paste your Access Key ID
2. **AWS Secret Access Key**: Paste your Secret Access Key
3. **Default region name**: Enter `us-east-1` (or your preferred region)
4. **Default output format**: Enter `json`

Example:
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

## Step 3: Verify Configuration

Test your AWS CLI setup:

```powershell
# Check your AWS identity
aws sts get-caller-identity

# List ECR repositories (should work if credentials are correct)
aws ecr describe-repositories --region us-east-1
```

## Step 4: Run Deployment Script

Once AWS CLI is configured, run:

```powershell
.\deploy_to_ecr.ps1
```

## Security Best Practices

1. **Never commit access keys to Git** - They're already in `.gitignore`
2. **Use IAM roles when possible** - For EC2/ECS/Lambda, use IAM roles instead of access keys
3. **Rotate keys regularly** - Change access keys every 90 days
4. **Use least privilege** - Only grant the minimum permissions needed
5. **Delete unused keys** - Remove access keys for users who no longer need them

## Troubleshooting

### "Unable to locate credentials"
- Run `aws configure` again
- Check that credentials are saved in `~/.aws/credentials`

### "Access Denied"
- Verify the IAM user has the correct permissions
- Check that the policies are attached to the user

### "Invalid credentials"
- Generate new access keys
- Make sure you copied the Secret Access Key correctly (no extra spaces)

