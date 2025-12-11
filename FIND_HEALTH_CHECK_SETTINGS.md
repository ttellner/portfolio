# How to Find Health Check Settings in App Runner

## Correct Location

According to AWS documentation, health check settings are in a **separate section**, not Service Settings:

### Step-by-Step:

1. **App Runner → Your Service** (click on the service name)
2. Click on **"Configuration"** tab (at the top)
3. Look for **"Health check"** section (separate from Service Settings)
4. Click **"Edit"** button in the Health check section
5. Change:
   - **Protocol:** `TCP` → `HTTP` ⚠️
   - **Path:** `/_stcore/health`
   - **Port:** `8080`
6. **Save**

## If You Don't See "Health check" Section

### Option 1: Check All Tabs

1. **Configuration tab** → Look for sub-sections:
   - Service
   - Health check ← Should be here
   - Security
   - Networking

2. **Scroll down** in Configuration tab - Health check might be below Service Settings

### Option 2: Use AWS CLI

If the UI doesn't show health check settings, use AWS CLI:

```powershell
# Get current configuration
aws apprunner describe-service --service-arn <your-service-arn> --region us-east-1

# Update health check (you'll need to update the entire service config)
# This is complex - see AWS CLI docs for full command
```

### Option 3: Check Service Creation vs Edit

**Health check protocol might only be settable during service creation:**

1. **Note all current settings:**
   - Image URI
   - Port: 8080
   - Access role
   - All other settings

2. **Delete current service**

3. **Create new service:**
   - During creation wizard, look for **Health check** step
   - Set protocol to **HTTP** during creation
   - Port: `8080`
   - Path: `/_stcore/health`

## Visual Guide

**App Runner Console Structure:**
```
Your Service
├── Overview tab
├── Configuration tab ← Click here
│   ├── Service (settings)
│   ├── Health check ← Look for this section
│   ├── Security
│   └── Networking
├── Activity tab
└── Logs tab
```

## What to Look For

In the **Configuration tab**, you should see:

1. **Service** section:
   - Port: 8080 ✅

2. **Health check** section (separate):
   - Protocol: TCP → Change to HTTP ⚠️
   - Path: `/_stcore/health`
   - Port: 8080

## If Still Can't Find It

**Try this:**
1. **App Runner → Your Service → Configuration tab**
2. Look for **"Edit"** button at the top right
3. Click **"Edit"**
4. This might show all sections including Health check

## Alternative: Check Service ARN and Use Documentation

1. **App Runner → Your Service → Configuration**
2. Note the **Service ARN** (at the top)
3. Check AWS documentation for your specific App Runner version:
   - https://docs.aws.amazon.com/apprunner/latest/dg/manage-configure-healthcheck.html

## Most Likely Solution

The health check section **should exist** in Configuration tab. If you truly can't find it:

1. **Delete the service**
2. **Create new service** from ECR
3. During creation, you'll see all configuration options including health check protocol
4. Set it to **HTTP** from the start

This ensures correct configuration from the beginning.

