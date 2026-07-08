# Simplified Dockerfile for testing (without Seurat to reduce build time)
# Use this to test if basic setup works, then switch to main Dockerfile
# Updated: 2026-07-07 - Install R from CRAN (jammy-cran40) instead of Ubuntu 22.04 default R 4.1.2
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
# Build cache buster - change this to force rebuild
ARG BUILD_DATE=2026-07-08-tailscale-userspace
ENV BUILD_DATE=${BUILD_DATE}

# Install system dependencies (including nginx for WebSocket proxy)
# Add system libraries needed for R graphics packages (ggplot2, isoband, etc.)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    curl \
    wget \
    git \
    build-essential \
    pandoc \
    nginx \
    software-properties-common \
    dirmngr \
    gnupg \
    ca-certificates \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libfribidi-dev \
    libharfbuzz-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff5-dev \
    libcairo2-dev \
    libpango1.0-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libuv1-dev \
    cmake \
    libgit2-dev \
    && wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc \
    | gpg --dearmor -o /usr/share/keyrings/r-project.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/r-project.gpg] https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/" \
    > /etc/apt/sources.list.d/r-project.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends r-base r-base-dev \
    && Rscript -e "if (getRversion() < '4.3.0') { cat('ERROR: R version too old:', R.version.string, '\n'); quit(status=1, save='no') }" \
    && Rscript -e "cat('Installed', R.version.string, '\n')" \
    && echo 'options(repos = c(CRAN = "https://packagemanager.posit.co/cran/__linux__/jammy/latest"))' \
    >> /etc/R/Rprofile.site \
    && rm -rf /var/lib/apt/lists/* \
    && which pandoc || (echo "ERROR: pandoc not found after installation" && exit 1) \
    && pandoc --version || (echo "ERROR: pandoc not working" && exit 1)

# Create symlinks for python and pip (remove existing if they exist)
RUN rm -f /usr/bin/python /usr/bin/python3 && \
    ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/python3.11 /usr/bin/python3

# Set working directory
WORKDIR /app

# Copy requirements file first (for better Docker layer caching)
COPY requirements.txt .

# Use a virtualenv so pip does not conflict with Ubuntu apt Python packages (e.g. blinker)
RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install additional Python packages
RUN pip install --no-cache-dir \
    nbconvert \
    nbformat \
    jupyter \
    ipython \
    scipy

# Limit parallel R package compilation to reduce OOM risk on small builders
ENV MAKEFLAGS=-j1

# Install R packages for bioinformatics / gamedatascience pages
COPY scripts/docker-install-r-packages.R /tmp/docker-install-r-packages.R
RUN Rscript /tmp/docker-install-r-packages.R

# Note: Seurat is NOT installed - it's too large and complex for this build
# Users will need to install it separately if needed, or use a different approach

# Copy application code
COPY . .

# Install Tailscale (userspace networking at runtime for Railway → home Ollama)
RUN curl -fsSL https://tailscale.com/install.sh | sh && \
    mkdir -p /var/run/tailscale /var/lib/tailscale

# Copy nginx configuration for WebSocket support
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Ensure .streamlit directory exists (create if it doesn't)
RUN mkdir -p .streamlit

# Expose nginx port (App Runner will connect to this)
EXPOSE 8080

# Health check for AWS App Runner (through nginx)
# App Runner uses HTTP health checks, not TCP
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Start both Streamlit (in background) and nginx (foreground)
# nginx will proxy WebSocket connections properly to handle App Runner's load balancer
CMD ["/app/start.sh"]

