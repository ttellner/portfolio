# Fix Health Check Still Using TCP on Port 8501

## Problem

Even after changing port to 8080, App Runner is still:
- Using **TCP** protocol (should be **HTTP**)
- Checking port **8501** (should be **8080**)

## Root Cause

App Runner has **separate settings** for:
1. **Service port** (where App Runner connects)
2. **Health check port** (where health checks run)
3. **Health check protocol** (TCP vs HTTP)

You may have changed the service port but not the health check settings.

## Fix: Update Health Check Settings

### Step 1: Go to Service Settings

1. **App Runner → Your Service → Edit**
2. Scroll to **Service Settings** section

### Step 2: Update Port

1. **Port:** Must be **`8080`** (not 8501)
2. This is the **service port** (where App Runner connects)

### Step 3: Update Health Check (CRITICAL!)

Look for **Health check** section (may be in same section or separate):

1. **Health check protocol:** Change from `TCP` to **`HTTP`** ⚠️
2. **Health check path:** `/_stcore/health` (or `/`)
3. **Health check port:** Must be **`8080`** (should match service port)

**If you don't see separate health check settings:**
- The health check port might default to the service port
- But the **protocol** must be explicitly set to **HTTP**

### Step 4: Save and Deploy

1. **Save** all changes
2. **Deploy** (or it may auto-deploy)
3. Wait 5-10 minutes

## Alternative: Check All Settings

Some App Runner configurations have health check in a **separate section**:

1. **App Runner → Your Service → Edit**
2. Look for:
   - **Service Settings** → Port: `8080`
   - **Health check** section (separate) → Protocol: `HTTP`, Port: `8080`, Path: `/_stcore/health`
3. **Save**

## Verify Settings Before Deploying

Before clicking Deploy, verify:

- [ ] **Service port:** `8080` ✅
- [ ] **Health check protocol:** `HTTP` (NOT TCP) ✅
- [ ] **Health check port:** `8080` (or matches service port) ✅
- [ ] **Health check path:** `/_stcore/health` or `/` ✅

## Why This Happens

App Runner may have:
- **Default health check** settings that override your changes
- **Separate health check configuration** that you need to update
- **Cached settings** from previous deployment

**Solution:** Explicitly set ALL health check settings to HTTP on port 8080.

## If Still Not Working

If health check still shows TCP on 8501 after saving:

1. **Delete the App Runner service**
2. **Create a new one** with correct settings from the start:
   - Source: ECR → `portfolio-streamlit:latest`
   - Port: `8080`
   - Health check: **HTTP**, port `8080`, path `/_stcore/health`
   - Access role: `AppRunner-ECR-AccessRole`
3. **Deploy**

This ensures clean configuration.

## Quick Checklist

Before deploying, double-check:

| Setting | Value | Location |
|---------|-------|----------|
| **Service Port** | `8080` | Service Settings |
| **Health Check Protocol** | `HTTP` | Health Check section |
| **Health Check Port** | `8080` | Health Check section |
| **Health Check Path** | `/_stcore/health` | Health Check section |

**All must be set correctly!**

