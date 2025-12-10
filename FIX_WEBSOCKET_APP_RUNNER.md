# Fix: WebSocket Connection Failed in App Runner

## Status

✅ **Streamlit is running** (logs confirm)  
✅ **Health check passing**  
❌ **WebSocket connection failing** (frontend can't connect)

This is an App Runner WebSocket/proxy configuration issue.

## Solution: Update Streamlit Configuration

App Runner's load balancer may need specific WebSocket settings. Update your Dockerfile CMD:

### Current CMD (may need adjustment):
```dockerfile
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
```

### Updated CMD (try this):
```dockerfile
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--server.allowRunOnSave=false", "--server.fileWatcherType=none"]
```

## Alternative: Create streamlit config file

Create a `.streamlit/config.toml` file in your repo:

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
allowRunOnSave = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false
```

Then update Dockerfile to copy it:

```dockerfile
# Copy streamlit config
COPY .streamlit .streamlit

# Run Streamlit
CMD ["streamlit", "run", "Home.py"]
```

## Quick Fix: Update Dockerfile

Let me update your Dockerfile with better WebSocket settings:

