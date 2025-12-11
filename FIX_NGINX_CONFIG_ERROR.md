# Fix nginx Configuration Error

## Problem

Container exit code: 1 - nginx failed to start, likely due to configuration syntax error.

## Issue

The `if` statement in nginx location blocks can cause problems, especially when used with `proxy_set_header`. nginx has limitations with `if` statements in certain contexts.

## Fix Applied

I've removed the `if` statement and simplified the configuration to use the `$connection_upgrade` variable directly, which is the proper nginx way to handle WebSocket upgrades.

## What Changed

**Removed:**
```nginx
if ($http_upgrade != '') {
    proxy_set_header Connection "upgrade";
}
```

**Using instead:**
- The `$connection_upgrade` variable (already defined at the top)
- This automatically sets Connection to "upgrade" when Upgrade header is present
- This is the recommended nginx pattern for WebSocket

## Next Steps

### Step 1: Push Fixed nginx.conf

```powershell
git add nginx.conf
git commit -m "Fix nginx config - remove problematic if statement"
git push origin main
```

### Step 2: Wait for Build and Auto-Deploy

- GitHub Actions builds (~20 minutes)
- App Runner auto-deploys (~5-10 minutes)
- Check Activity tab for deployment status

### Step 3: Verify nginx Starts

After deployment, check logs:
- **App Runner → Your Service → Logs tab**
- Should see: `nginx: [notice] ... ready to handle connections`
- Should see: `You can now view your Streamlit app`

## Why This Happened

nginx's `if` directive has limitations:
- Can't always be used with `proxy_set_header` in location blocks
- Can cause unexpected behavior
- The `map` directive (which we already have) is the proper way to handle this

## Current Configuration

The `map` directive at the top:
```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

This automatically:
- Sets `$connection_upgrade` to "upgrade" when `$http_upgrade` is present
- Sets it to "close" when `$http_upgrade` is empty
- This is the correct nginx pattern for WebSocket

## Expected Result

After deploying the fix:
- ✅ Container starts successfully (no exit code 1)
- ✅ nginx starts and listens on port 8080
- ✅ Streamlit starts on port 8501
- ✅ Health check passes
- ✅ WebSocket should connect

The configuration is now simpler and follows nginx best practices!

