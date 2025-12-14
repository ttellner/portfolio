#!/bin/bash
set -e

# Install missing R packages on startup (workaround if Dockerfile installation failed)
echo "Checking for required R packages..."
Rscript -e "
required_packages <- c('dplyr', 'ggplot2')
missing <- character(0)
for (pkg in required_packages) {
    if (!require(pkg, character.only=TRUE, quietly=TRUE)) {
        missing <- c(missing, pkg)
    }
}
if (length(missing) > 0) {
    cat('Installing missing R packages:', paste(missing, collapse=', '), '\\n')
    options(repos = c(CRAN = 'https://cran.rstudio.com/'))
    for (pkg in missing) {
        if (pkg == 'ggplot2') {
            # Install ggplot2 dependencies first
            install.packages(c('farver', 'labeling', 'RColorBrewer', 'viridisLite', 'gtable', 'S7', 'scales'), 
                           dependencies=FALSE, quiet=TRUE, repos='https://cran.rstudio.com/')
        }
        install.packages(pkg, dependencies=FALSE, quiet=TRUE, repos='https://cran.rstudio.com/')
    }
    cat('R packages installation complete\\n')
} else {
    cat('All required R packages are already installed\\n')
}
" || echo "R package check had issues, continuing..."

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

