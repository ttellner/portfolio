# Simplified Dockerfile for testing (without Seurat to reduce build time)
# Use this to test if basic setup works, then switch to main Dockerfile
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies (including nginx for WebSocket proxy)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    r-base \
    r-base-dev \
    curl \
    wget \
    git \
    build-essential \
    pandoc \
    nginx \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
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

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Install additional Python packages
RUN pip3 install --no-cache-dir \
    nbconvert \
    nbformat \
    jupyter \
    ipython \
    scipy

# Install basic R packages (without Seurat for faster builds)
# Split into multiple RUN commands for better caching and to avoid timeout
# Install minimal core packages first
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('jsonlite', 'yaml', 'evaluate', 'highr', 'markdown', 'stringr', 'xfun'), \
    dependencies=FALSE, quiet=TRUE)" || true

# Install data manipulation packages (with dependencies to avoid build failures)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('readr', dependencies=TRUE, quiet=TRUE)" || true && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('dplyr', dependencies=TRUE, quiet=TRUE)" || true && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('tidyr', dependencies=TRUE, quiet=TRUE)" || true

# Install visualization packages
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('ggplot2', dependencies=TRUE, quiet=TRUE)" || true && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('patchwork', dependencies=FALSE, quiet=TRUE)" || true

# Install knitr (required for rmarkdown)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('knitr', dependencies=TRUE, quiet=TRUE)" || true

# Install rmarkdown - it should work now that all dependencies are installed
# Use dependencies=FALSE since we've already installed the required packages
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('rmarkdown', dependencies=FALSE, quiet=TRUE)" && \
    Rscript -e "if (!require('rmarkdown', quietly=TRUE)) { stop('rmarkdown not installed') }"

# Copy application code
COPY . .

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

