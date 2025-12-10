#!/bin/bash
set -e

# Start Streamlit in the background
streamlit run Home.py \
    --server.port=8501 \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --server.enableCORS=true \
    --server.enableXsrfProtection=false \
    --server.allowRunOnSave=false \
    --server.fileWatcherType=none \
    --server.runOnSave=false &

# Wait a moment for Streamlit to start
sleep 3

# Start nginx in the foreground (so Docker doesn't exit)
exec nginx -g "daemon off;"

