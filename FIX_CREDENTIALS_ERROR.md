# Fix: "Credentials could not be loaded" Error

## Error Message

```
Credentials could not be loaded, please check your action inputs: Could not load credentials from any providers
```

This means the GitHub Actions workflow is running, but it can't find your AWS credentials in GitHub Secrets.

## ✅ Solution: Verify GitHub Secrets

### Step 1: Check Secrets Exist

1. Go to: https://github.com/ttellner/portfolio/settings/secrets/actions
2. Verify you see **both** of these secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### Step 2: Verify Secret Names (Case-Sensitive!)

The names must be **exactly** (case-sensitive):
- `AWS_ACCESS_KEY_ID` (not `aws_access_key_id` or `AWS_ACCESS_KEY`)
- `AWS_SECRET_ACCESS_KEY` (not `aws_secret_access_key` or `AWS_SECRET_KEY`)

### Step 3: Verify Secret Values

**Important**: You can't view the secret values after adding them, but you can verify:

1. **Check your local AWS credentials** (if they match what you added):
   ```powershell
   aws configure list
   ```

2. **Or test locally**:
   ```powershell
   aws sts get-caller-identity
   ```
   This should work if your credentials are valid.

### Step 4: Re-add Secrets (If Needed)

If secrets are missing or incorrectly named:

1. Go to: https://github.com/ttellner/portfolio/settings/secrets/actions
2. **Delete** any incorrectly named secrets
3. Click **"New repository secret"**
4. Add **first secret**:
   - **Name**: `AWS_ACCESS_KEY_ID` (exactly, case-sensitive)
   - **Value**: Your AWS Access Key ID (starts with `AKIA...`)
   - Click **"Add secret"**
5. Click **"New repository secret"** again
6. Add **second secret**:
   - **Name**: `AWS_SECRET_ACCESS_KEY` (exactly, case-sensitive)
   - **Value**: Your AWS Secret Access Key (long string)
   - Click **"Add secret"**

### Step 5: Verify Workflow References

The workflow file should reference them like this:

```yaml
aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

Make sure the workflow file matches these exact names.

## Common Issues

### Issue 1: Secret Names Don't Match

❌ **Wrong**:
- `aws_access_key_id` (lowercase)
- `AWS_ACCESS_KEY` (missing `_ID`)
- `AWS_SECRET_KEY` (missing `ACCESS_`)

✅ **Correct**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Issue 2: Secrets Not Set

If you see "0 secrets" on the secrets page, you need to add them.

### Issue 3: Wrong Repository

Make sure you're adding secrets to the correct repository:
- `ttellner/portfolio`

### Issue 4: Secrets in Wrong Location

Secrets must be in:
- **Repository secrets** (not organization secrets)
- **Actions secrets** (not Dependabot secrets)

## Test After Fixing

1. **Re-run the workflow**:
   - Go to: https://github.com/ttellner/portfolio/actions
   - Click on the failed workflow run
   - Click **"Re-run all jobs"**

2. **Or trigger manually**:
   - Go to Actions tab
   - Click "Deploy to AWS App Runner via ECR"
   - Click "Run workflow"
   - Select branch: `main`
   - Click "Run workflow"

3. **Check the logs**:
   - The "Configure AWS credentials" step should now succeed
   - You should see your AWS account ID in the logs

## Verify Credentials Are Valid

Before adding to GitHub, test locally:

```powershell
# Test AWS credentials
aws sts get-caller-identity
```

This should return:
```json
{
    "UserId": "...",
    "Account": "083738448444",
    "Arn": "..."
}
```

If this works locally, the same credentials will work in GitHub Actions.

## Quick Checklist

- [ ] Secrets page shows 2 secrets
- [ ] Secret names are exactly: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- [ ] Secret values are correct (can't verify after adding, but test locally first)
- [ ] Workflow file references: `${{ secrets.AWS_ACCESS_KEY_ID }}` and `${{ secrets.AWS_SECRET_ACCESS_KEY }}`
- [ ] Secrets are in the correct repository (`ttellner/portfolio`)
- [ ] Secrets are in "Actions secrets" (not Dependabot)

## Still Not Working?

If you've verified everything above:

1. **Delete and re-add secrets** (sometimes GitHub needs a refresh)
2. **Wait 1-2 minutes** after adding secrets before running workflow
3. **Check workflow file** for any typos in secret references
4. **Verify AWS credentials** are still valid (not expired/rotated)

## Expected Success Output

After fixing, the workflow should show:

```
✓ Configure AWS credentials
✓ Login to Amazon ECR
✓ Build, tag, and push image to Amazon ECR
```

And you should see your AWS account ID in the logs.

