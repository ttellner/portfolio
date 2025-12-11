# Creating New App Runner Service - FAQ

## Question 1: Can I Create a New Service Without Deleting the Current One?

**Answer: YES! ✅**

You can create multiple App Runner services. They are independent and don't conflict.

### Benefits of Keeping Both:

1. **Test the new service** before deleting the old one
2. **Compare configurations** side-by-side
3. **No downtime** - old service keeps running while you test new one
4. **Easy rollback** - if new service has issues, just delete it and keep using old one

### What Happens:

- **Old service:** Keeps running on its current URL
- **New service:** Gets a new default URL (different from old one)
- **Both can run simultaneously** - they're completely separate

### After New Service Works:

1. **Test new service** thoroughly
2. **Update custom domain** to point to new service (if you have one)
3. **Then delete old service** (optional - you can keep both if you want)

## Question 2: Can I Reuse the IAM Role?

**Answer: YES! ✅**

The IAM role (`AppRunner-ECR-AccessRole`) can be used by **multiple App Runner services**.

### How to Use Existing Role:

1. **App Runner → Create service**
2. **Source:** Container registry → Amazon ECR
3. **Image URI:** `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
4. **Deployment Settings → Access role:**
   - Select: **"Use existing service role"**
   - Choose: **`AppRunner-ECR-AccessRole`** (the one you created)
5. **Service Settings:**
   - **Port:** `8080`
   - **Health check protocol:** `HTTP` ← Set this during creation!
   - **Health check path:** `/_stcore/health`
   - **Health check port:** `8080`
6. **Create and deploy**

### Role Permissions:

The role has `AmazonEC2ContainerRegistryReadOnly` policy, which allows:
- ✅ Multiple services to use the same role
- ✅ All services to pull images from ECR
- ✅ No conflicts or permission issues

## Step-by-Step: Create New Service

### Step 1: Start Creation

1. **App Runner → Create service**
2. **Source type:** Container registry
3. **Provider:** Amazon ECR

### Step 2: Configure Source

1. **Container image URI:**
   - Browse and select: `portfolio-streamlit:latest`
   - Or type: `083738448444.dkr.ecr.us-east-1.amazonaws.com/portfolio-streamlit:latest`
2. **Deployment trigger:** Automatic (or Manual)

### Step 3: Configure Service

1. **Service name:** `portfolio-streamlit-v2` (or any name)
2. **Virtual CPU:** 1 vCPU
3. **Memory:** 2 GB
4. **Port:** `8080` ⚠️ Important!

### Step 4: Configure Health Check (During Creation)

**Look for Health check section in the creation wizard:**

1. **Protocol:** Select **`HTTP`** (not TCP) ⚠️ CRITICAL!
2. **Path:** `/_stcore/health`
3. **Port:** `8080` (or may default to service port)

**If you don't see health check during creation:**
- It might be set after service creation
- Or might be in "Advanced settings"

### Step 5: Configure Security

1. **Access role:** 
   - Select **"Use existing service role"**
   - Choose: **`AppRunner-ECR-AccessRole`**
2. **Instance role:** Leave default (not needed)

### Step 6: Review and Create

1. **Review all settings:**
   - Port: 8080 ✅
   - Health check: HTTP, port 8080, path `/_stcore/health` ✅
   - Access role: `AppRunner-ECR-AccessRole` ✅
2. **Create & deploy**

## Comparison: Old vs New Service

| Setting | Old Service | New Service |
|---------|-------------|-------------|
| **Name** | `portfolio-streamlit` | `portfolio-streamlit-v2` |
| **URL** | `xxxxx.us-east-1.awsapprunner.com` | `yyyyy.us-east-1.awsapprunner.com` |
| **Port** | 8501 (wrong) | 8080 (correct) |
| **Health Check** | TCP (wrong) | HTTP (correct) |
| **Access Role** | `AppRunner-ECR-AccessRole` | `AppRunner-ECR-AccessRole` (same) |

## After New Service is Running

### Option A: Keep Both

- Use new service for production
- Keep old service as backup
- Update custom domain to new service

### Option B: Delete Old Service

1. **Test new service** thoroughly
2. **Update custom domain** (if you have one) to point to new service
3. **Delete old service** (App Runner → Old service → Delete)

## Custom Domain (If You Have One)

If you have a custom domain (`ttellnerai.com`):

1. **New service** will have a different default URL
2. **Update custom domain** to point to new service:
   - App Runner → New service → Custom domains
   - Add your domain
   - Update DNS records if needed
3. **Remove custom domain** from old service (optional)

## Cost Note

- **Both services run simultaneously** = you pay for both
- **Delete old service** once new one is confirmed working to avoid double costs
- App Runner charges per service instance

## Summary

✅ **Yes, create new service** - old one can stay running  
✅ **Yes, reuse the IAM role** - `AppRunner-ECR-AccessRole`  
✅ **Set health check to HTTP** during creation  
✅ **Test new service** before deleting old one  
✅ **Update custom domain** to new service when ready

This is the safest approach - no risk, easy rollback!

