# Verifying GitHub Secrets

## Method 1: Test Workflow (Recommended)

I've created a test workflow that you can run manually to verify your secrets.

### Steps:

1. **Push the test workflow**:
   ```powershell
   git add .github/workflows/test-credentials.yml
   git commit -m "Add credentials test workflow"
   git push origin main
   ```

2. **Run the workflow**:
   - Go to: `https://github.com/ttellner/portfolio/actions`
   - Click on "Test AWS Credentials" workflow
   - Click "Run workflow" button (top right)
   - Select branch: `main`
   - Click "Run workflow"

3. **Check results**:
   - Wait for workflow to complete (~30 seconds)
   - Click on the workflow run
   - Check the output - should show:
     - ✅ AWS account ID
     - ✅ User ARN
     - ✅ ECR access (or note if repos don't exist)

### What it tests:
- ✅ AWS credentials are valid
- ✅ Can authenticate with AWS
- ✅ Can access ECR (if repositories exist)

---

## Method 2: Test Locally (If Secrets Match Local Config)

If your GitHub secrets match your local AWS credentials:

```powershell
# Test locally
aws sts get-caller-identity
```

This should return the same account ID and user that GitHub Actions will use.

---

## Method 3: Verify Secret Names

Make sure the secret names in GitHub are **exactly**:
- `AWS_ACCESS_KEY_ID` (case-sensitive)
- `AWS_SECRET_ACCESS_KEY` (case-sensitive)

### To check:
1. Go to: `https://github.com/ttellner/portfolio/settings/secrets/actions`
2. Verify both secrets exist
3. Verify names match exactly (no typos, correct case)

---

## Method 4: Test with Main Deployment Workflow

You can also test by running the main deployment workflow:

1. **Trigger the workflow manually**:
   - Go to: `https://github.com/ttellner/portfolio/actions`
   - Click on "Deploy to AWS App Runner via ECR"
   - Click "Run workflow"
   - Select branch: `main`
   - Click "Run workflow"

2. **Watch the logs**:
   - If credentials are wrong, you'll see an error in the "Configure AWS credentials" step
   - If credentials are correct, it will proceed to "Login to Amazon ECR"

---

## Common Issues

### "InvalidClientTokenId" or "SignatureDoesNotMatch"
- **Cause**: Wrong access key ID or secret access key
- **Fix**: Double-check the values in GitHub Secrets

### "Access Denied"
- **Cause**: Credentials are valid but lack permissions
- **Fix**: Ensure IAM user has `AmazonEC2ContainerRegistryFullAccess` policy

### Secret not found
- **Cause**: Wrong secret name or typo
- **Fix**: Verify secret names match exactly: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

---

## Quick Verification Checklist

- [ ] Secrets added to GitHub: `https://github.com/ttellner/portfolio/settings/secrets/actions`
- [ ] Secret names are correct: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- [ ] Test workflow pushed to GitHub
- [ ] Test workflow run successfully
- [ ] Main deployment workflow can authenticate

---

## Expected Output from Test Workflow

If credentials are correct, you should see:

```
Testing AWS credentials...
{
    "UserId": "AIDARG7ZTKI6LQKRPUSEL",
    "Account": "083738448444",
    "Arn": "arn:aws:iam::083738448444:user/apprunner-deploy"
}
Testing ECR access...
✅ Credentials are valid!
```

---

## Next Steps

Once credentials are verified:

1. ✅ Run the test workflow to confirm
2. ✅ Push the main deployment workflow
3. ✅ Let it build and push to ECR
4. ✅ Configure App Runner to use the ECR image

The test workflow is safe - it only reads information, doesn't create or modify anything.

