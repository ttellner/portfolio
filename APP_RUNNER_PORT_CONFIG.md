# App Runner Port Configuration

## Important: Update App Runner Port Setting

After deploying with nginx, you **MUST** update the App Runner port configuration:

1. Go to **App Runner → Your Service → Configuration → Service**
2. Find **Port** setting
3. Change from `8501` to **`8080`**
4. Click **Save** and **Deploy**

## Why?

- **Streamlit** runs on port `8501` (internal, localhost only)
- **nginx** runs on port `8080` (exposed to App Runner)
- **App Runner** must connect to port `8080` (nginx), not `8501` (Streamlit)

nginx properly handles WebSocket upgrades that App Runner's load balancer might not support directly.

## Architecture

```
App Runner Load Balancer → nginx (port 8080) → Streamlit (port 8501, localhost)
```

nginx handles:
- WebSocket upgrade headers
- Connection keep-alive
- Proper proxy headers
- Health checks

