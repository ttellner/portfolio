# No-Code / Low-Code Deployment Options

Since you're having network issues pushing Docker images, here are **much simpler** deployment options that connect directly to your GitHub repo and handle everything automatically.

## 🚀 Option 1: Streamlit Community Cloud (Easiest - You Already Used This!)

**This is the simplest option** - you mentioned it worked before! It's specifically designed for Streamlit apps.

### Setup:
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `ttellner/portfolio`
5. Main file: `Home.py`
6. Click "Deploy"

**That's it!** Streamlit Cloud handles:
- ✅ Automatic builds on every push
- ✅ Free hosting
- ✅ No Docker needed (it builds for you)
- ✅ Handles Python/R dependencies automatically

**Note**: For R support, you may need to add a `packages.txt` file listing R packages, or the R projects might need to use the fallback HTML display.

---

## 🚂 Option 2: Railway (Very Easy - No-Code)

Railway automatically detects your app and deploys it. Great for Docker apps.

### Setup:
1. Go to https://railway.app/
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `ttellner/portfolio`
5. Railway will auto-detect your Dockerfile
6. Click "Deploy"

**Features:**
- ✅ Auto-detects Dockerfile
- ✅ Free tier: $5/month credit
- ✅ Automatic deployments on push
- ✅ Built-in monitoring

**Cost**: ~$5-10/month for small apps

---

## 🎨 Option 3: Render (Very Easy - No-Code)

Similar to Railway, very simple setup.

### Setup:
1. Go to https://render.com/
2. Sign in with GitHub
3. Click "New" → "Web Service"
4. Connect your repo: `ttellner/portfolio`
5. Settings:
   - **Name**: `portfolio-streamlit`
   - **Environment**: Docker
   - **Dockerfile Path**: `Dockerfile`
   - **Start Command**: (leave empty, uses Dockerfile CMD)
6. Click "Create Web Service"

**Features:**
- ✅ Free tier available (with limitations)
- ✅ Auto-deploys on push
- ✅ Custom domains
- ✅ SSL certificates included

**Cost**: Free tier (sleeps after inactivity) or $7/month for always-on

---

## ✈️ Option 4: Fly.io (Good for Docker)

Fly.io is great for Docker apps and has a generous free tier.

### Setup:
1. Install Fly CLI: `powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"`
2. Sign up: `fly auth signup`
3. In your repo directory: `fly launch`
4. Follow prompts (it auto-detects Dockerfile)
5. Deploy: `fly deploy`

**Features:**
- ✅ Generous free tier
- ✅ Global edge network
- ✅ Auto-deploys via GitHub Actions (can set up)

**Cost**: Free tier includes 3 shared VMs

---

## 🔧 Option 5: GitHub Actions + AWS App Runner (Low-Code)

Automate the build/push process using GitHub Actions. This solves your network issue by building in GitHub's infrastructure.

### Setup:

1. **Create `.github/workflows/deploy.yml`** in your repo:

```yaml
name: Deploy to AWS App Runner

on:
  push:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: portfolio-streamlit
  AWS_ACCOUNT_ID: 083738448444

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
      
    - name: Build, tag, and push image to Amazon ECR
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: latest
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

2. **Add GitHub Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add `AWS_ACCESS_KEY_ID`
   - Add `AWS_SECRET_ACCESS_KEY`

3. **Push to GitHub** - That's it! Every push will automatically build and push to ECR.

**Benefits:**
- ✅ Builds in GitHub's network (no local network issues)
- ✅ Automatic on every push
- ✅ Free for public repos
- ✅ Then App Runner auto-deploys from ECR

---

## 📊 Comparison

| Platform | Difficulty | Cost | Auto-Deploy | Docker Support |
|----------|-----------|------|-------------|----------------|
| **Streamlit Cloud** | ⭐ Easiest | Free | ✅ Yes | ❌ No (but not needed) |
| **Railway** | ⭐⭐ Easy | $5-10/mo | ✅ Yes | ✅ Yes |
| **Render** | ⭐⭐ Easy | Free/$7/mo | ✅ Yes | ✅ Yes |
| **Fly.io** | ⭐⭐⭐ Medium | Free tier | ⚠️ Manual/CI | ✅ Yes |
| **GitHub Actions + App Runner** | ⭐⭐⭐ Medium | Free + AWS | ✅ Yes | ✅ Yes |

---

## 🎯 My Recommendation

**For your situation, I'd recommend:**

1. **Try Streamlit Community Cloud first** - It's the easiest and you said it worked before. Just need to handle R dependencies.

2. **If you need Docker/R support**: Use **Railway** or **Render** - both are very simple, connect to GitHub, and handle Docker automatically.

3. **If you want to stick with AWS**: Use **GitHub Actions** (Option 5) - this solves your network issue by building in GitHub's infrastructure, then App Runner deploys automatically.

---

## Quick Start: Streamlit Cloud

Since this is the easiest, here's the exact steps:

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Fill in:
   - **Repository**: `ttellner/portfolio`
   - **Branch**: `main`
   - **Main file path**: `Home.py`
5. Click "Deploy"

If R is needed, you can add a `packages.txt` file in your repo root with R packages, or the R projects will use their HTML fallback (which you already implemented).

**This takes 2 minutes and requires zero code changes!**

