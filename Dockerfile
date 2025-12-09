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

# Install additional Python packages that might be needed
RUN pip3 install --no-cache-dir \
    nbconvert \
    nbformat \
    jupyter \
    ipython \
    scipy

# Install R packages commonly used in data science
# Install basic CRAN packages first
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    install.packages(c('rmarkdown', 'knitr', 'ggplot2', 'dplyr', 'tidyr', 'readr', 'readxl', 'jsonlite', 'patchwork'), \
    dependencies=TRUE, quiet=TRUE)" || echo "Basic R packages installation had issues, but continuing..."

# Install Seurat separately with better error handling
# Note: Seurat is a large package and will significantly increase build time (10-15 minutes)
# If build fails here, try Dockerfile.simple first (without Seurat)
RUN Rscript -e "options(repos = c(CRAN = 'https://cran.rstudio.com/')); \
    tryCatch({ \
        install.packages('Seurat', dependencies=TRUE, quiet=TRUE); \
        cat('Seurat installed successfully\n'); \
    }, error = function(e) { \
        cat('Seurat installation failed:', conditionMessage(e), '\n'); \
        cat('Continuing without Seurat - bioinfoprojects R Markdown may not work\n'); \
    })" || echo "Seurat installation failed, but continuing..."

# Install Bioconductor packages (dependencies for some R packages)
# These are optional and won't break the build if they fail
RUN Rscript -e "if (!requireNamespace('BiocManager', quietly = TRUE)) { \
        install.packages('BiocManager', repos='https://cran.rstudio.com/', quiet=TRUE); \
    }; \
    if (requireNamespace('BiocManager', quietly = TRUE)) { \
        tryCatch({ \
            BiocManager::install(c('BiocGenerics', 'S4Vectors', 'IRanges', 'GenomicRanges'), ask=FALSE, update=FALSE, quiet=TRUE); \
            cat('Bioconductor packages installed\n'); \
        }, error = function(e) { \
            cat('Bioconductor packages failed:', conditionMessage(e), '\n'); \
        }); \
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

