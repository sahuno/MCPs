# Dockerfile for annOmics MCP Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for R and graphics
RUN apt-get update && apt-get install -y \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libcairo2-dev \
    libxt-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages
RUN R -e "install.packages(c('optparse', 'tidyverse', 'data.table', 'ggplot2'), repos='https://cran.rstudio.com/')"
RUN R -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager'); BiocManager::install(c('annotatr', 'GenomicRanges'))"

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
COPY scripts/ scripts/
COPY config/ config/

# Install Python dependencies
RUN uv pip install --system -e .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONPATH=/app/src
ENV R_LIBS_USER=/usr/local/lib/R/site-library

# Expose port (if needed for HTTP mode)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from annomics_mcp.schemas.genome_builds import SupportedGenomes; print('OK')"

# Run server
CMD ["python", "-m", "annomics_mcp.server"]