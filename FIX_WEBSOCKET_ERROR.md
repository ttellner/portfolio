# Fix: WebSocket Connection Failed - Streamlit Not Connecting

## Error

```
WebSocket connection to 'wss://ttellnerai.com/_stcore/stream' failed
```

This means Streamlit's frontend can't connect to the backend via WebSocket.

## Root Cause

The WebSocket connection failure usually means:
1. **Streamlit isn't running** - Python error on startup
2. **Streamlit crashed** - Error during execution
3. **Configuration issue** - WebSocket settings incorrect
4. **Port/network issue** - App Runner configuration problem

## ✅ Solution: Check App Runner Logs (Critical!)

**This is the most important step** - the logs will show why Streamlit isn't connecting:

1. Go to **AWS App Runner Console**
2. Click your service: `portfolio-streamlit`
3. Click **"Logs"** tab
4. Look for:
   - Python errors (traceback)
   - `ModuleNotFoundError`
   - `ImportError`
   - `FileNotFoundError`
   - Streamlit startup messages

**What to look for:**
- ✅ Good: `You can now view your Streamlit app in your browser.`
- ❌ Bad: Any Python error or traceback
- ❌ Bad: `ModuleNotFoundError: No module named 'theme'`
- ❌ Bad: `FileNotFoundError`

## Common Fixes

### Fix 1: Missing `theme.py` Module

Your `Home.py` imports:
```python
from theme import apply_theme
```

**Check if `theme.py` exists:**
1. Verify `theme.py` is in your repo root
2. Check Dockerfile copies it: `COPY . .`
3. Check App Runner logs for: `ModuleNotFoundError: No module named 'theme'`

**If missing, create it or remove the import.**

### Fix 2: Streamlit Configuration

Your Dockerfile has:
```dockerfile
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
```

**Try adding WebSocket settings:**
```dockerfile
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.enableWebsocketCompression=false"]
```

### Fix 3: Check App Runner Port Configuration

1. Go to App Runner → Your service → Configuration
2. Verify **Port** is set to `8501`
3. Verify it matches your Dockerfile `EXPOSE 8501`

### Fix 4: Test Health Endpoint

Visit: `https://ttellnerai.com/_stcore/health`

- ✅ If returns `{"status": "healthy"}` → Streamlit is running, WebSocket issue
- ❌ If fails → Streamlit isn't running, check logs for Python errors

### Fix 5: Check for Python Errors on Startup

The most common cause is a Python error when `Home.py` tries to run.

**Check App Runner logs for:**
- Import errors
- Syntax errors
- File not found errors
- Any traceback

## Debugging Steps

### Step 1: Check Logs (Do This First!)

**App Runner → Service → Logs tab**

Look for the last 50-100 lines. Share any errors you see.

### Step 2: Verify theme.py Exists

```powershell
# Check locally
Test-Path theme.py
```

If it doesn't exist, either:
- Create a minimal `theme.py` file
- Or remove the import from `Home.py`

### Step 3: Test Locally

Test if the Docker image works locally:

```powershell
# Build
docker build -t portfolio-streamlit .

# Run
docker run -p 8501:8501 portfolio-streamlit

# Access http://localhost:8501
```

If it works locally but not in App Runner, it's a configuration issue.

### Step 4: Create Minimal Test

Create a simple test to verify Streamlit works:

1. Create `test.py`:
   ```python
   import streamlit as st
   st.write("Hello World - Streamlit is working!")
   ```

2. Temporarily update Dockerfile:
   ```dockerfile
   CMD ["streamlit", "run", "test.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
   ```

3. Rebuild and redeploy
4. If this works, the issue is in `Home.py` or dependencies

## Most Likely Issues

Based on the WebSocket error:

1. **Python error on startup** (90% likely)
   - Check App Runner logs
   - Look for `ModuleNotFoundError`, `ImportError`, etc.

2. **Missing theme.py** (likely)
   - `Home.py` imports `from theme import apply_theme`
   - If `theme.py` doesn't exist, Streamlit crashes on startup

3. **Missing dependencies** (possible)
   - Check if all packages in `requirements.txt` are installed
   - Check logs for `ModuleNotFoundError`

## Quick Fixes to Try

### Fix A: Remove theme.py Import (If File Missing)

If `theme.py` doesn't exist:

1. Edit `Home.py`
2. Comment out or remove:
   ```python
   from theme import apply_theme
   ```
3. Comment out any calls to `apply_theme()`
4. Rebuild and redeploy

### Fix B: Create Minimal theme.py

If `theme.py` is missing, create it:

```python
# theme.py
import streamlit as st

def apply_theme():
    # Minimal theme - can be empty or add custom CSS
    pass
```

### Fix C: Update Dockerfile CMD

Try adding WebSocket compression setting:

```dockerfile
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.enableWebsocketCompression=false", "--server.allowRunOnSave=false"]
```

## What to Share

To get more specific help, share:

1. **App Runner Logs** (last 50-100 lines)
2. **Health endpoint response**: `https://ttellnerai.com/_stcore/health`
3. **Whether `theme.py` exists** in your repo

The logs will tell us exactly what's wrong!

