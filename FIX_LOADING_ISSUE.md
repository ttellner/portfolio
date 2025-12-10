# Fix: App Runner Shows Only Loading Boxes (Nothing Renders)

## Symptoms

- ✅ Service is running
- ✅ Page loads (no 404 error)
- ❌ Only see shaded/throbbing boxes (loading indicators)
- ❌ No content renders
- ❌ Page appears stuck

## Common Causes & Solutions

### Solution 1: Check App Runner Logs (Most Important!)

**This will tell you what's actually wrong:**

1. Go to AWS App Runner Console
2. Click on your service: `portfolio-streamlit`
3. Click **"Logs"** tab
4. Look for errors, especially:
   - Python errors
   - Import errors
   - File not found errors
   - Port binding errors

**Common errors you might see:**
- `ModuleNotFoundError` - Missing Python package
- `FileNotFoundError` - Missing file
- `Port already in use` - Port conflict
- `Streamlit configuration error`

### Solution 2: Verify Streamlit is Running

Check if Streamlit started correctly:

1. **In App Runner Logs**, look for:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   Network URL: http://0.0.0.0:8501
   ```

2. **If you don't see this**, Streamlit didn't start properly

### Solution 3: Check Port Configuration

Verify the port matches:

1. **Dockerfile** should have:
   ```dockerfile
   EXPOSE 8501
   CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", ...]
   ```

2. **App Runner** should have:
   - Port: `8501`

3. **Environment variables** (if set):
   - `STREAMLIT_SERVER_PORT=8501`
   - `STREAMLIT_SERVER_ADDRESS=0.0.0.0`

### Solution 4: Check for Import Errors

The app might be failing to import modules. Check logs for:

- `ImportError`
- `ModuleNotFoundError`
- Missing dependencies in `requirements.txt`

### Solution 5: Verify Home.py Exists and is Correct

1. **Check Dockerfile** copies the file:
   ```dockerfile
   COPY . .
   ```
   This should copy `Home.py`

2. **Check Home.py** is in the root directory

3. **Check Home.py** has no syntax errors:
   ```powershell
   python -m py_compile Home.py
   ```

### Solution 6: Check Browser Console

1. Open your browser's Developer Tools (F12)
2. Go to **Console** tab
3. Look for JavaScript errors
4. Go to **Network** tab
5. Check if resources are loading (CSS, JS files)

### Solution 7: Test Health Endpoint

Check if the app is responding:

1. Try accessing: `https://your-app-runner-url/_stcore/health`
2. Should return: `{"status": "healthy"}`
3. If this fails, the app isn't running

### Solution 8: Check CORS Settings

Your Dockerfile has:
```dockerfile
--server.enableCORS=false
```

This should be fine, but if you see CORS errors in browser console, the app might be blocking requests.

### Solution 9: Verify All Dependencies Installed

Check if all Python packages are installed:

1. **In App Runner Logs**, look for pip install output
2. Check for any package installation failures
3. Verify `requirements.txt` includes all needed packages

### Solution 10: Check File Paths

Since you're using dynamic paths (`Path(__file__).parent`), verify:

1. Files are being copied correctly in Docker
2. Paths resolve correctly in the container
3. No hardcoded Windows paths remain

## Debugging Steps

### Step 1: Check Logs First

**This is the most important step!**

1. App Runner → Your service → Logs tab
2. Look at the most recent logs
3. Copy any error messages
4. Share them for further diagnosis

### Step 2: Test Locally

Test if the Docker image works locally:

```powershell
# Build image
docker build -t portfolio-streamlit .

# Run locally
docker run -p 8501:8501 portfolio-streamlit

# Access at http://localhost:8501
```

If it works locally but not in App Runner, it's an App Runner configuration issue.

### Step 3: Simplify to Test

Create a minimal test to verify Streamlit works:

1. Create `test.py`:
   ```python
   import streamlit as st
   st.write("Hello World")
   ```

2. Update Dockerfile CMD temporarily:
   ```dockerfile
   CMD ["streamlit", "run", "test.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
   ```

3. Rebuild and redeploy
4. If this works, the issue is in `Home.py` or dependencies

## Most Likely Issues

Based on your symptoms (loading boxes but nothing renders):

1. **Python error in Home.py** - Check logs for traceback
2. **Missing dependency** - Check logs for ImportError
3. **File path issue** - Check logs for FileNotFoundError
4. **Streamlit not starting** - Check logs for startup errors

## Quick Fixes to Try

### Fix 1: Check Logs (Do This First!)

```powershell
# Or check in App Runner console
# App Runner → Service → Logs tab
```

### Fix 2: Verify Requirements

Make sure `requirements.txt` has all dependencies, especially:
- `streamlit`
- `pandas`
- `numpy`
- Any other packages used in `Home.py`

### Fix 3: Check Home.py for Errors

Look for:
- Import errors
- Syntax errors
- File path issues
- Missing files

### Fix 4: Test Health Endpoint

Visit: `https://your-app-runner-url/_stcore/health`

Should return: `{"status": "healthy"}`

## Next Steps

1. **Check App Runner Logs** - This will show the actual error
2. **Share the error message** from logs
3. **Test health endpoint** - Verify app is running
4. **Check browser console** - Look for JavaScript errors

## What to Share for Further Help

If you need more help, share:

1. **App Runner Logs** (last 50-100 lines)
2. **Browser Console errors** (F12 → Console tab)
3. **Health endpoint response** (`/_stcore/health`)
4. **Any error messages** you see

The logs will tell us exactly what's wrong!

