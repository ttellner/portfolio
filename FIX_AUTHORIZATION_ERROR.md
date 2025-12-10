# Fix: "Invalid character in header content ["Authorization"]"

## Error Message

```
Error: Invalid character in header content ["Authorization"]
```

This error means your GitHub Secrets contain invalid characters (whitespace, newlines, or special characters) that break the HTTP Authorization header.

## ✅ Solution: Re-add Secrets Correctly

### Step 1: Get Clean Credentials

**Important**: Copy your credentials carefully without any extra characters.

1. **Get your AWS Access Key ID**:
   - Should look like: `AKIAIOSFODNN7EXAMPLE`
   - Should be exactly 20 characters
   - No spaces, no newlines, no quotes

2. **Get your AWS Secret Access Key**:
   - Should be a long string (40 characters)
   - No spaces, no newlines, no quotes
   - Example: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

### Step 2: Delete Old Secrets

1. Go to: https://github.com/ttellner/portfolio/settings/secrets/actions
2. **Delete** both secrets:
   - Click on `AWS_ACCESS_KEY_ID` → Click "Delete"
   - Click on `AWS_SECRET_ACCESS_KEY` → Click "Delete"

### Step 3: Re-add Secrets (Very Carefully)

**Critical**: When adding secrets, be very careful:

1. **Add AWS_ACCESS_KEY_ID**:
   - Click "New repository secret"
   - **Name**: `AWS_ACCESS_KEY_ID` (exactly, case-sensitive)
   - **Value**: 
     - Open a text editor (Notepad)
     - Paste your Access Key ID
     - **Select all** (Ctrl+A)
     - **Copy** (Ctrl+C) - this ensures no hidden characters
     - Paste into GitHub secret value field
     - **Verify**: No spaces before/after, no quotes, no newlines
   - Click "Add secret"

2. **Add AWS_SECRET_ACCESS_KEY**:
   - Click "New repository secret"
   - **Name**: `AWS_SECRET_ACCESS_KEY` (exactly, case-sensitive)
   - **Value**:
     - Open a text editor (Notepad)
     - Paste your Secret Access Key
     - **Select all** (Ctrl+A)
     - **Copy** (Ctrl+C)
     - Paste into GitHub secret value field
     - **Verify**: No spaces before/after, no quotes, no newlines
   - Click "Add secret"

### Step 4: Verify Format

Before adding to GitHub, verify your credentials in a text editor:

**Access Key ID should look like**:
```
AKIAIOSFODNN7EXAMPLE
```
- Exactly 20 characters
- No spaces
- No quotes
- No newlines

**Secret Access Key should look like**:
```
wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```
- Long string (40 characters)
- No spaces
- No quotes
- No newlines
- May contain `/` and `+` characters (this is normal)

## Common Mistakes

### ❌ Wrong: Copying with quotes
```
"AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE"
```
Remove the quotes!

### ❌ Wrong: Copying with newlines
```
AKIAIOSFODNN7EXAMPLE
```
If there's a newline, remove it!

### ❌ Wrong: Copying with spaces
```
AKIA IOSFODNN7EXAMPLE
```
Remove all spaces!

### ❌ Wrong: Copying from AWS Console with extra text
```
Access Key ID: AKIAIOSFODNN7EXAMPLE
```
Only copy the key itself, not the label!

### ✅ Correct: Clean value only
```
AKIAIOSFODNN7EXAMPLE
```
Just the key, nothing else!

## Test Credentials Locally First

Before adding to GitHub, test that your credentials work:

```powershell
# Set environment variables temporarily
$env:AWS_ACCESS_KEY_ID = "your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY = "your-secret-access-key"

# Test
aws sts get-caller-identity
```

If this works, the same credentials (without the env vars) will work in GitHub Actions.

## Alternative: Use AWS CLI to Get Credentials

If you're not sure about the format, get them from AWS CLI:

```powershell
# View your configured credentials
aws configure list

# Or get them from the config file
Get-Content ~/.aws/credentials
```

Then copy the values carefully (just the values, not the keys).

## After Fixing

1. **Wait 1-2 minutes** after adding secrets
2. **Re-run the workflow**:
   - Go to: https://github.com/ttellner/portfolio/actions
   - Click on the failed workflow
   - Click "Re-run all jobs"

3. **Or trigger new run**:
   - Go to Actions → "Deploy to AWS App Runner via ECR"
   - Click "Run workflow"

## Verify Secret Format

You can't view secrets after adding, but you can verify the workflow uses them correctly. The workflow should show:

```
✓ Configure AWS credentials
```

And in the logs, you should see your AWS account ID (not the key itself, but proof it worked).

## Still Getting Error?

If you still get the error after carefully re-adding:

1. **Generate new AWS credentials**:
   - Go to AWS IAM → Users → Your user
   - Security credentials tab
   - Create new access key
   - Copy immediately (you can only see it once)

2. **Add new credentials to GitHub** (following steps above)

3. **Test locally first**:
   ```powershell
   aws configure
   # Enter new credentials
   aws sts get-caller-identity
   ```

4. **Then add to GitHub Secrets**

## Quick Checklist

- [ ] Deleted old secrets from GitHub
- [ ] Copied credentials to text editor first
- [ ] Selected all and copied again (removes hidden chars)
- [ ] Pasted into GitHub (no quotes, no spaces, no newlines)
- [ ] Verified Access Key ID is exactly 20 characters
- [ ] Verified Secret Access Key is long string (40 chars)
- [ ] Tested credentials locally first
- [ ] Waited 1-2 minutes after adding
- [ ] Re-ran workflow

The key is: **clean values only, no extra characters!**

