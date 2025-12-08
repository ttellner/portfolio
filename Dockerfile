# Use Ubuntu as base image (supports both Python and R)
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
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/python3.11 /usr/bin/python3

# Set working directory
WORKDIR /app

# Copy requirements file first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Install additional Python packages that might be needed
RUN pip3 install --no-cache-dir \
    nbconvert \
    nbformat \
    jupyter \
    ipython \
    scipy

# Install R packages commonly used in data science
# Install CRAN packages (including Seurat)
# Note: Seurat is a large package and will significantly increase build time (10-15 minutes)
# If you don't need Seurat, remove it from the list below
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'readxl', 'jsonlite', 'patchwork', 'Seurat'), \
    dependencies=TRUE, quiet=TRUE)" || echo "Some CRAN packages may have failed to install, but continuing..."

# Install Bioconductor packages (dependencies for some R packages)
RUN Rscript -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager', repos='https://cran.rstudio.com/'); \
    if (requireNamespace('BiocManager', quietly = TRUE)) { \
    BiocManager::install(c('BiocGenerics', 'S4Vectors', 'IRanges', 'GenomicRanges'), ask=FALSE, update=FALSE, quiet=TRUE) \
    }" || echo "Bioconductor packages installation skipped or failed"

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check for AWS App Runner
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]

