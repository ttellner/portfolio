# Install R packages needed by bioinformatics and gamedatascience portfolio pages.
cran_repo <- "https://packagemanager.posit.co/cran/__linux__/jammy/latest"
options(repos = c(CRAN = cran_repo))

install_required <- function(pkgs) {
  install.packages(pkgs, dependencies = c("Depends", "Imports"))
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing) > 0) {
    stop("Missing required R packages: ", paste(missing, collapse = ", "))
  }
}

cat("Using CRAN repo:", cran_repo, "\n")
cat("R version:", R.version.string, "\n")

# rmarkdown stack (install compiled deps explicitly for clearer failures)
install_required(c("fs", "sass", "bslib", "rmarkdown", "knitr"))

# dplyr / visualization stack used by portfolio R Markdown pages
install_required(c("dplyr", "ggplot2", "jsonlite", "readr", "tidyr"))

install_optional <- function(pkg) {
  tryCatch(
    {
      install.packages(pkg, dependencies = FALSE)
      cat("Installed optional package:", pkg, "\n")
    },
    error = function(e) {
      cat("Skipping optional package ", pkg, ": ", conditionMessage(e), "\n", sep = "")
    }
  )
}

install_optional("isoband")
install_optional("patchwork")

cat("R package installation complete.\n")
