# Simplified Dockerfile for testing (without Seurat to reduce build time)
# Use this to test if basic setup works, then switch to main Dockerfile
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies
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
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

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
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'jsonlite', 'patchwork'), \
    dependencies=TRUE, quiet=TRUE)" || echo "R packages installation had some issues, but continuing..."

# Copy application code
COPY . .

# Ensure .streamlit directory exists (create if it doesn't)
RUN mkdir -p .streamlit

# Expose Streamlit port
EXPOSE 8501

# Health check for AWS App Runner
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit with WebSocket-friendly settings for App Runner
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=true", "--server.enableXsrfProtection=false", "--server.allowRunOnSave=false", "--server.fileWatcherType=none"]

