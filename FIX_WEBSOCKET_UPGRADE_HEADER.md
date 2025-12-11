# Fix "Can Upgrade only to WebSocket" Error

## What This Error Means

The message "Can 'Upgrade' only to 'WebSocket'" when accessing `/_stcore/stream` means:

✅ **Good news:**
- nginx is receiving the request
- WebSocket upgrade is being attempted
- Headers are being passed

❌ **Problem:**
- The `Connection` header might not be set correctly
- Or App Runner's load balancer is modifying headers
- The WebSocket handshake isn't completing

## Root Cause

The `Connection` header needs to be exactly `"upgrade"` (lowercase) when the `Upgrade` header is present. The nginx `$connection_upgrade` variable should handle this, but App Runner's load balancer might be interfering.

## Fix Applied

I've updated `nginx.conf` to:

1. **Use `$connection_upgrade` variable** - This properly handles the Connection header based on Upgrade header
2. **Added conditional Connection header** - Forces "upgrade" if Upgrade header is present
3. **Better header normalization** - Ensures headers are in correct format

## Next Steps

### Step 1: Push Updated nginx.conf

```powershell
git add nginx.conf
git commit -m "Fix WebSocket Connection header for App Runner"
git push origin main
```

### Step 2: Wait for Build and Deploy

- GitHub Actions builds (~20 minutes)
- Deploy new image to App Runner
- Wait for deployment (~5-10 minutes)

### Step 3: Test

1. **Clear browser cache**
2. **Visit service URL** (not the /_stcore/stream endpoint directly)
3. **Check browser console** - WebSocket should connect

## Why Direct Access to /_stcore/stream Shows Error

When you access `/_stcore/stream` directly in a browser:
- Browser sends HTTP request (not WebSocket)
- nginx tries to upgrade, but browser doesn't complete handshake
- You see the error message

**This is normal!** The WebSocket endpoint is meant to be accessed by JavaScript, not directly in a browser.

## What to Test

**Don't test `/_stcore/stream` directly in browser.**

Instead:
1. **Visit your main service URL** (e.g., `https://xxxxx.awsapprunner.com`)
2. **Open browser console** (F12)
3. **Look for WebSocket connection** in Network tab → WS filter
4. **Check for errors** in Console tab

## Expected Result

After deploying the fix:
- ✅ Main page loads (no "glowing boxes")
- ✅ WebSocket connects successfully
- ✅ App functions normally
- ❌ Direct access to `/_stcore/stream` still shows error (this is normal)

## If Still Failing

If WebSocket still fails after this fix, the issue might be:

### App Runner Load Balancer Limitation

App Runner's load balancer might be stripping or modifying WebSocket headers before they reach nginx.

**Solutions:**
1. **Check App Runner logs** - See if headers are being modified
2. **Try different deployment platform** - ECS/Fargate, Elastic Beanstalk, Railway, Render
3. **Contact AWS Support** - Ask about WebSocket support in App Runner

### Alternative: Check Browser Network Tab

1. **F12 → Network tab**
2. **Filter: WS** (WebSocket)
3. **Click on the failed connection**
4. **Check Headers:**
   - Request headers: Should have `Upgrade: websocket` and `Connection: Upgrade`
   - Response headers: Should have `101 Switching Protocols`
5. **Share the headers** - This will show exactly what's happening

## Summary

The error you're seeing is actually a **good sign** - it means nginx is working and trying to upgrade. The fix I applied should normalize the Connection header properly. Deploy the updated config and test the main app URL (not the stream endpoint directly).

