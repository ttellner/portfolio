# Fix: Git Push SSL Connection Timeout

## Error
```
fatal: unable to access 'https://github.com/ttellner/portfolio.git/': SSL connection timeout
```

This indicates a network connectivity issue preventing access to GitHub.

## Quick Fixes

### Solution 1: Check Internet Connection

```powershell
# Test connectivity to GitHub
Test-NetConnection -ComputerName github.com -Port 443
```

If this fails, you have a network connectivity issue.

### Solution 2: Try SSH Instead of HTTPS

If HTTPS is timing out, switch to SSH:

1. **Check if you have SSH keys**:
   ```powershell
   Test-Path ~/.ssh/id_rsa.pub
   ```

2. **If no SSH key, generate one**:
   ```powershell
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

3. **Add SSH key to GitHub**:
   - Copy public key: `Get-Content ~/.ssh/id_ed25519.pub`
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the key

4. **Change remote URL to SSH**:
   ```powershell
   git remote set-url origin git@github.com:ttellner/portfolio.git
   ```

5. **Try pushing again**:
   ```powershell
   git push origin main
   ```

### Solution 3: Increase Git Timeout

```powershell
# Increase timeout to 300 seconds (5 minutes)
git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 300
```

Then try pushing again:
```powershell
git push origin main
```

### Solution 4: Use GitHub CLI (Alternative)

If Git push keeps failing, use GitHub CLI:

1. **Install GitHub CLI** (if not installed):
   ```powershell
   winget install GitHub.cli
   ```

2. **Authenticate**:
   ```powershell
   gh auth login
   ```

3. **Push using GitHub CLI**:
   ```powershell
   gh repo sync
   ```

### Solution 5: Check Proxy/Firewall

If you're behind a corporate firewall or proxy:

1. **Configure Git to use proxy** (if you have proxy settings):
   ```powershell
   git config --global http.proxy http://proxy.example.com:8080
   git config --global https.proxy https://proxy.example.com:8080
   ```

2. **Or disable proxy if not needed**:
   ```powershell
   git config --global --unset http.proxy
   git config --global --unset https.proxy
   ```

### Solution 6: Disable VPN Temporarily

If you're using a VPN:
1. Temporarily disable it
2. Try pushing
3. Re-enable after push

### Solution 7: Try Different Network

- Switch to a different Wi-Fi network
- Use mobile hotspot
- Try from a different location

## Manual Upload (Last Resort)

If Git push continues to fail, you can upload files manually:

1. **Create a ZIP of your changes**:
   ```powershell
   # Create archive of new/changed files
   git archive -o changes.zip HEAD $(git diff --name-only HEAD~1)
   ```

2. **Or upload specific files via GitHub web interface**:
   - Go to: https://github.com/ttellner/portfolio
   - Click "Add file" → "Upload files"
   - Upload the workflow files:
     - `.github/workflows/deploy.yml`
     - `.github/workflows/test-credentials.yml`
   - Commit directly on GitHub

## For the Workflow Files Specifically

Since you just need to push the workflow files for GitHub Actions:

### Option A: Upload via GitHub Web Interface

1. Go to: https://github.com/ttellner/portfolio
2. Navigate to `.github/workflows/` folder
3. Click "Add file" → "Create new file"
4. Name: `deploy.yml`
5. Paste the contents of `.github/workflows/deploy.yml`
6. Click "Commit new file"
7. Repeat for `test-credentials.yml` if needed

### Option B: Use GitHub Desktop

If you have GitHub Desktop installed:
1. Open GitHub Desktop
2. It may handle network issues better than command line
3. Commit and push through the GUI

## Verify Network Connectivity

Run these tests:

```powershell
# Test GitHub connectivity
Test-NetConnection -ComputerName github.com -Port 443

# Test DNS resolution
Resolve-DnsName github.com

# Test with curl
curl -I https://github.com
```

## Temporary Workaround: Use GitHub Actions Web Editor

If you can access GitHub in a browser:

1. Go to: https://github.com/ttellner/portfolio
2. Click on `.github/workflows/deploy.yml`
3. Click "Edit" (pencil icon)
4. If file doesn't exist, click "Add file" → "Create new file"
5. Paste the workflow content
6. Commit directly on GitHub

This bypasses Git push entirely!

## Summary

**Quick fixes to try:**
1. ✅ Switch to SSH (most reliable)
2. ✅ Increase Git timeout
3. ✅ Check proxy/VPN settings
4. ✅ Upload via GitHub web interface (bypasses Git)

**For immediate deployment:**
- Upload workflow file via GitHub web interface
- GitHub Actions will work once the file is in the repo
- No need to push via Git if web interface works

The most reliable long-term solution is switching to SSH for Git operations.

