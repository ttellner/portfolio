#!/bin/bash

STREAMLIT_LOG=/var/log/streamlit.log
STREAMLIT_HEALTH_URL="http://127.0.0.1:8501/_stcore/health"
STREAMLIT_START_TIMEOUT="${STREAMLIT_START_TIMEOUT:-120}"

mkdir -p /var/log

# ---------------------------------------------------------------------------
# Optional Tailscale (invite-only remote Ollama via OLLAMA_HOST=http://100.x.x.x)
# Set TS_AUTHKEY in Railway Variables. Uses userspace networking (no TUN device).
# Tailscale failures must not prevent Streamlit from starting.
# ---------------------------------------------------------------------------
if [ -n "${TS_AUTHKEY:-}" ]; then
    echo "Starting Tailscale (userspace networking)..."
    mkdir -p /var/run/tailscale /var/lib/tailscale

    tailscaled \
        --state=/var/lib/tailscale/tailscaled.state \
        --socket=/var/run/tailscale/tailscaled.sock \
        --tun=userspace-networking \
        --socks5-server=localhost:1055 \
        --outbound-http-proxy-listen=localhost:1056 \
        &

    for _ in $(seq 1 30); do
        if [ -S /var/run/tailscale/tailscaled.sock ]; then
            break
        fi
        sleep 1
    done

    if tailscale up \
        --authkey="${TS_AUTHKEY}" \
        --hostname="${TS_HOSTNAME:-railway-portfolio}" \
        --accept-dns=false \
        --accept-routes; then
        export HTTP_PROXY="http://127.0.0.1:1056"
        export HTTPS_PROXY="http://127.0.0.1:1056"
        export ALL_PROXY="socks5://127.0.0.1:1055"
        export http_proxy="${HTTP_PROXY}"
        export https_proxy="${HTTPS_PROXY}"
        export all_proxy="${ALL_PROXY}"
        export NO_PROXY="localhost,127.0.0.1,::1"
        export no_proxy="${NO_PROXY}"
        echo "Tailscale is up: $(tailscale ip -4 2>/dev/null || echo 'ip pending')"
    else
        echo "WARNING: Tailscale up failed; continuing in simulation mode."
    fi
else
    echo "TS_AUTHKEY not set — skipping Tailscale (simulation mode / local Ollama only)."
fi

echo "Starting Streamlit..."
streamlit run Home.py \
    --server.port=8501 \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --server.enableCORS=true \
    --server.enableXsrfProtection=false \
    --server.allowRunOnSave=false \
    --server.fileWatcherType=none \
    --server.runOnSave=false \
    >> "${STREAMLIT_LOG}" 2>&1 &

STREAMLIT_PID=$!
echo "Streamlit PID: ${STREAMLIT_PID}"

for i in $(seq 1 "${STREAMLIT_START_TIMEOUT}"); do
    if curl -sf "${STREAMLIT_HEALTH_URL}" >/dev/null 2>&1; then
        echo "Streamlit ready after ${i}s"
        break
    fi

    if ! kill -0 "${STREAMLIT_PID}" 2>/dev/null; then
        echo "ERROR: Streamlit exited during startup."
        tail -n 80 "${STREAMLIT_LOG}" || true
        exit 1
    fi

    sleep 1
done

if ! curl -sf "${STREAMLIT_HEALTH_URL}" >/dev/null 2>&1; then
    echo "ERROR: Streamlit did not become healthy within ${STREAMLIT_START_TIMEOUT}s."
    tail -n 80 "${STREAMLIT_LOG}" || true
    exit 1
fi

echo "Starting nginx..."
exec nginx -g "daemon off;"
