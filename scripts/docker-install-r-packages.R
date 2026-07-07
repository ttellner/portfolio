# Install R packages needed by bioinformatics and gamedatascience portfolio pages.
cran_repo <- "https://packagemanager.posit.co/cran/__linux__/jammy/latest"
options(repos = c(CRAN = cran_repo))

install_required <- function(pkgs) {
  install.packages(pkgs, dependencies = c("Depends", "Imports", "LinkingTo"))
  missing <- pkgs[!vapply(pkgs, requireNamespace, quietly = TRUE, FUN.VALUE = logical(1))]
  if (length(missing) > 0) {
    stop("Missing required R packages: ", paste(missing, collapse = ", "))
  }
}

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

cat("Using CRAN repo:", cran_repo, "\n")
cat("R version:", R.version.string, "\n")

# Header-only / lightweight deps required before tzdb, isoband, vroom, tidyr
cat("Installing R package foundations...\n")
install_required(c("cpp11", "progress"))

cat("Installing rmarkdown stack...\n")
install_required(c("fs", "sass", "bslib", "rmarkdown", "knitr"))

cat("Installing ggplot2/readr prerequisites...\n")
install_required(c("tzdb", "isoband", "vroom"))

cat("Installing dplyr / visualization / IO stack...\n")
install_required(c("dplyr", "ggplot2", "jsonlite", "readr", "tidyr"))

install_optional("patchwork")

cat("R package installation complete.\n")
