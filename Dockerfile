# Simplified Dockerfile for testing (without Seurat to reduce build time)
# Use this to test if basic setup works, then switch to main Dockerfile
# Updated: 2025-01-13 - Force rebuild to fix ggplot2 installation
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
# Build cache buster - change this to force rebuild
ARG BUILD_DATE=2025-01-13
ENV BUILD_DATE=${BUILD_DATE}

# Install system dependencies (including nginx for WebSocket proxy)
# Add system libraries needed for R graphics packages (ggplot2, isoband, etc.)
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
# Install ONLY rmarkdown with required dependencies (not suggested packages)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('rmarkdown', dependencies=c('Depends', 'Imports'), quiet=TRUE)" && \
    Rscript -e "if (!require('rmarkdown', quietly=TRUE)) { stop('rmarkdown not installed') }"

# Install packages required by the R Markdown files
# Install dplyr with required dependencies (needed for bioinformatics projects)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('dplyr', dependencies=c('Depends', 'Imports'), quiet=TRUE)" && \
    Rscript -e "if (!require('dplyr', quietly=TRUE)) { stop('dplyr not installed') }"

# Install ggplot2 with required dependencies (needed for visualization)
# Install all dependencies first, then ggplot2 in a separate step for better error visibility
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    cat('Installing ggplot2 dependencies...\\n'); \
    install.packages(c('farver', 'labeling', 'RColorBrewer', 'viridisLite'), \
    dependencies=FALSE, quiet=FALSE)" && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    cat('Installing more ggplot2 dependencies...\\n'); \
    install.packages(c('gtable', 'S7', 'scales'), dependencies=FALSE, quiet=FALSE)" && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    cat('R library paths:', paste(.libPaths(), collapse=': '), '\\n'); \
    cat('Installing ggplot2...\\n'); \
    result <- tryCatch({ \
        install.packages('ggplot2', dependencies=FALSE, quiet=FALSE, repos='https://cran.rstudio.com/') \
    }, error=function(e) { \
        cat('ERROR during ggplot2 installation:', as.character(e$message), '\\n'); \
        stop(e) \
    }, warning=function(w) { \
        cat('WARNING during ggplot2 installation:', as.character(w$message), '\\n') \
    }); \
    if (is.null(result)) { stop('ggplot2 installation returned NULL') }; \
    cat('ggplot2 installation result:', paste(result, collapse=', '), '\\n'); \
    cat('Checking immediately after install...\\n'); \
    installed_now <- rownames(installed.packages()); \
    cat('ggplot2 in installed packages?', 'ggplot2' %in% installed_now, '\\n')" && \
    Rscript -e "installed <- rownames(installed.packages()); \
    cat('Checking for ggplot2 in', length(installed), 'installed packages...\\n'); \
    if (!'ggplot2' %in% installed) { \
        cat('ERROR: ggplot2 not found. First 20 installed:', paste(head(installed, 20), collapse=', '), '...\\n'); \
        stop('ggplot2 verification failed') \
    } else { \
        cat('SUCCESS: ggplot2 found in installed packages\\n') \
    }" && \
    Rscript -e "library(ggplot2); cat('SUCCESS: ggplot2 version', as.character(packageVersion('ggplot2')), 'installed and loaded\\n')" && \
    Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('isoband', dependencies=FALSE, quiet=TRUE)" || echo "isoband optional - ggplot2 installed successfully"

# Install patchwork (optional - used for combining plots)
# Try to install, but don't fail the build if it doesn't work
# The R Markdown file can render without it (some plot combining features may be limited)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages('patchwork', dependencies=FALSE, quiet=TRUE)" || echo "patchwork installation failed - continuing without it"

# Install other optional packages (skip if they fail)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('jsonlite', 'readr', 'tidyr'), \
    dependencies=FALSE, quiet=TRUE)" || echo "Optional R packages had issues, but continuing..."

# Note: Seurat is NOT installed - it's too large and complex for this build
# Users will need to install it separately if needed, or use a different approach

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

