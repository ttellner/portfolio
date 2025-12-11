# Health Check Port Setting - Why It's Not There

## This is Normal! ✅

**The health check port defaults to the service port automatically.**

If you set the **service port to 8080**, the health check will use **port 8080** automatically.

## What You Need to Set in Health Section

In the **Health** section, you should see:

1. **Protocol:** 
   - Dropdown or option
   - **Select: `HTTP`** ⚠️ CRITICAL (not TCP)

2. **Path:**
   - Text field
   - **Enter: `/_stcore/health`** (or `/`)

3. **Port:** 
   - ❌ **NOT visible** - This is normal!
   - ✅ **Automatically uses service port** (8080)

## How It Works

- **Service port (Service Settings):** `8080` → This is what you set
- **Health check port:** Automatically uses service port (`8080`)
- **Health check protocol:** Must be set to `HTTP` in Health section
- **Health check path:** Must be set to `/_stcore/health` in Health section

## Complete Configuration

### Service Settings:
- **Port:** `8080` ✅

### Health Section:
- **Protocol:** `HTTP` ⚠️ (change from TCP if needed)
- **Path:** `/_stcore/health` ✅
- **Port:** (Not shown - uses service port automatically) ✅

## Why This Design?

App Runner assumes:
- Health checks should use the **same port** as your service
- This prevents port mismatches
- Simpler configuration

## What to Do

1. **Service Settings:**
   - Set **Port:** `8080` ✅

2. **Health Section:**
   - Set **Protocol:** `HTTP` ⚠️ (most important!)
   - Set **Path:** `/_stcore/health` ✅
   - **Don't worry about port** - it uses 8080 automatically ✅

3. **Continue with service creation**

## Verification

After service is created, you can verify:
- **App Runner → Your Service → Configuration → Health check**
- Should show:
  - Protocol: HTTP ✅
  - Path: /_stcore/health ✅
  - Port: 8080 (inherited from service port) ✅

## Summary

✅ **No port setting in Health section is normal**  
✅ **Health check uses service port automatically**  
⚠️ **Just set Protocol to HTTP and Path to /_stcore/health**  
✅ **Make sure service port is 8080**

You're good to continue! The important part is setting **Protocol to HTTP** in the Health section.

