#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Optional Tailscale (invite-only remote Ollama via OLLAMA_HOST=http://100.x.x.x)
# Set TS_AUTHKEY in Railway Variables. Uses userspace networking (no TUN device).
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

    # Wait for the control socket
    for _ in $(seq 1 30); do
        if [ -S /var/run/tailscale/tailscaled.sock ]; then
            break
        fi
        sleep 1
    done

    tailscale up \
        --authkey="${TS_AUTHKEY}" \
        --hostname="${TS_HOSTNAME:-railway-portfolio}" \
        --accept-dns=false \
        --accept-routes

    # Route outbound traffic through Tailscale's HTTP proxy so Python urllib/openai
    # can reach Ollama on 100.x.x.x (userspace networking has no kernel TUN route).
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
    echo "TS_AUTHKEY not set — skipping Tailscale (simulation mode / local Ollama only)."
fi

# Start Streamlit in the background (inherits proxy env when Tailscale is active)
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
