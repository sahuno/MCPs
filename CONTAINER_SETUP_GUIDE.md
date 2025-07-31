# annOmics MCP Server - Container Setup Guide

## 📋 Overview

This guide helps you transfer the annOmics MCP server from the cluster to your personal Linux machine and set it up using Docker containers (since Docker is not available on the cluster).

## 📦 Step 1: Prepare Files for Transfer

### Create Transfer Package on Cluster

```bash
# Navigate to the project directory
cd /data1/greenbab/users/ahunos/apps/annOmics

# Create a compressed archive with all necessary files
tar -czf annomics-mcp-transfer.tar.gz \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='mouse_results' \
  --exclude='test_output' \
  .

# Verify the archive contents
tar -tzf annomics-mcp-transfer.tar.gz | head -20

# Check archive size
ls -lh annomics-mcp-transfer.tar.gz
```

### Essential Files Included

The archive contains:
```
annOmics/
├── src/annomics_mcp/              # MCP server code
├── scripts/annotate_genomic_segments.R  # Core R script
├── tests/                         # Complete test suite
├── config/                        # Configuration files
├── pyproject.toml                 # Project dependencies
├── uv.lock                        # Dependency lock file
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Multi-service setup
├── README_MCP.md                  # Documentation
├── MCP_USAGE_GUIDE.md            # User guide
├── DEPLOYMENT_GUIDE.md           # Deployment instructions
└── CONTAINER_SETUP_GUIDE.md      # This guide
```

## 🚚 Step 2: Transfer to Personal Linux Machine

### Option A: Direct SCP Transfer
```bash
# From your personal Linux machine, run:
scp your_username@cluster_address:/data1/greenbab/users/ahunos/apps/annOmics/annomics-mcp-transfer.tar.gz ~/Downloads/

# Or if you have the file locally, upload to your Linux machine:
scp annomics-mcp-transfer.tar.gz user@your-linux-machine:~/
```

### Option B: USB/External Drive
```bash
# On cluster: Copy to external drive
cp annomics-mcp-transfer.tar.gz /path/to/external/drive/

# On your Linux machine: Copy from external drive
cp /media/external/drive/annomics-mcp-transfer.tar.gz ~/
```

### Option C: Cloud Storage
```bash
# Upload to cloud (e.g., Google Drive, Dropbox)
# Then download on your Linux machine
```

## 🖥️ Step 3: Setup on Personal Linux Machine

### Prerequisites Check

```bash
# Check if Docker is installed
docker --version
docker-compose --version

# If not installed, install Docker:
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io docker-compose

# CentOS/RHEL:
sudo yum install docker docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, avoids sudo)
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker
```

### Extract and Setup Project

```bash
# Create project directory
mkdir -p ~/genomics-tools
cd ~/genomics-tools

# Extract the archive
tar -xzf ~/annomics-mcp-transfer.tar.gz
cd annOmics

# Verify extraction
ls -la
```

## 🐳 Step 4: Container Deployment

### Method 1: Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up --build

# This will:
# 1. Build the Docker image with R + Python + all dependencies
# 2. Start the MCP server
# 3. Mount directories for data input/output
# 4. Set up health monitoring
```

### Method 2: Manual Docker Build

```bash
# Build the image
docker build -t annomics-mcp .

# Run the container
docker run -it \
  --name annomics-mcp-server \
  -v $(pwd)/data:/app/data:ro \
  -v $(pwd)/output:/app/output:rw \
  -v $(pwd)/config:/app/config:ro \
  annomics-mcp
```

### Verify Container is Running

```bash
# Check container status
docker ps

# Check logs
docker logs annomics-mcp-server

# Test the installation
docker exec annomics-mcp-server python -c "
from annomics_mcp.schemas.genome_builds import SupportedGenomes
print('✅ MCP server ready!')
print(f'Supported genomes: {SupportedGenomes.list_genomes()}')
"
```

## 🧪 Step 5: Test the Setup

### Run Comprehensive Tests

```bash
# Run all tests inside the container
docker exec annomics-mcp-server ./scripts/run_tests.sh

# Or run specific test suites
docker exec annomics-mcp-server ./scripts/run_tests.sh unit
docker exec annomics-mcp-server ./scripts/run_tests.sh positive
```

### Test R Environment

```bash
# Verify R and packages are working
docker exec annomics-mcp-server Rscript -e "
library(annotatr)
library(GenomicRanges)
library(tidyverse)
print('✅ R environment fully functional!')
"

# Test the annotation script directly
docker exec annomics-mcp-server Rscript scripts/annotate_genomic_segments.R --help
```

### Test with Sample Data

```bash
# Create test data directory
mkdir -p data/test

# Create a sample BED file
cat > data/test/sample.bed << 'EOF'
chr1	1000	2000	region1	100	+
chr1	3000	4000	region2	200	-
chr2	5000	6000	region3	150	+
EOF

# Test annotation
docker exec annomics-mcp-server Rscript scripts/annotate_genomic_segments.R \
  -i /app/data/test/sample.bed \
  -g mm10 \
  -o /app/output/test_results \
  -n sample_test \
  --formats pdf,png

# Check results
ls -la output/test_results/
```

## 🔧 Step 6: Configure for Your Use

### Setup Data Directories

```bash
# Create organized directory structure
mkdir -p {data,output,logs}
mkdir -p data/{chipseq,atacseq,rnaseq}
mkdir -p output/{annotations,plots,summaries}

# Set permissions
chmod 755 data output
chmod 644 data/*/*  # For your BED files
```

### Customize Configuration

```bash
# Edit server configuration
nano config/server_config.json

# Key settings to adjust:
{
  "server": {
    "timeout_seconds": 600,        # Increase for large files
    "max_file_size_mb": 200       # Increase for large datasets
  },
  "r_environment": {
    "memory_limit": "16G",        # Adjust based on your RAM
    "timeout_seconds": 1800       # Increase for large datasets
  },
  "performance": {
    "max_concurrent_jobs": 2      # Adjust based on CPU cores
  }
}
```

### Environment Variables

```bash
# Create environment file
cat > .env << 'EOF'
ANNOMICS_LOG_LEVEL=INFO
ANNOMICS_MAX_MEMORY=8G
ANNOMICS_OUTPUT_DIR=/app/output
ANNOMICS_CACHE_TTL=24
EOF

# Update docker-compose.yml to use .env file
echo "env_file: .env" >> docker-compose.yml
```

## 🚀 Step 7: Running Your Analysis

### Start the Server

```bash
# Start in background
docker-compose up -d

# Monitor logs
docker-compose logs -f
```

### Use with Claude Desktop

Add to Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "annomics": {
      "command": "docker",
      "args": [
        "exec", 
        "annomics-mcp-server", 
        "python", 
        "-m", 
        "annomics_mcp.server"
      ]
    }
  }
}
```

### Direct MCP Tool Usage

```bash
# Test MCP tools directly
docker exec -i annomics-mcp-server python -c "
import asyncio
from annomics_mcp.server import handle_list_supported_genomes

async def test():
    result = await handle_list_supported_genomes({})
    print(result[0].text)

asyncio.run(test())
"
```

## 📊 Step 8: Production Usage Examples

### Example 1: ChIP-seq Peak Annotation

```bash
# Copy your BED files to data directory
cp /path/to/your/chipseq_peaks.bed data/chipseq/

# Run annotation via container
docker exec annomics-mcp-server python -c "
import asyncio
from annomics_mcp.server import handle_annotate_genomic_regions

async def annotate():
    result = await handle_annotate_genomic_regions({
        'input_files': '/app/data/chipseq/chipseq_peaks.bed',
        'genome_build': 'hg38',
        'output_directory': '/app/output/chipseq_analysis',
        'sample_name': 'my_chipseq_sample',
        'plot_formats': ['pdf', 'png'],
        'include_cpg': True,
        'include_genic': True
    })
    print(result[0].text)

asyncio.run(annotate())
"

# Check results
ls -la output/chipseq_analysis/
```

### Example 2: Batch Processing Multiple Samples

```bash
# Prepare multiple BED files
cp sample1.bed sample2.bed sample3.bed data/batch/

# Run batch annotation
docker exec annomics-mcp-server python -c "
import asyncio
from annomics_mcp.server import handle_annotate_genomic_regions

async def batch_annotate():
    result = await handle_annotate_genomic_regions({
        'input_files': ['/app/data/batch/sample1.bed', 
                       '/app/data/batch/sample2.bed', 
                       '/app/data/batch/sample3.bed'],
        'genome_build': 'mm10',
        'output_directory': '/app/output/batch_analysis',
        'combine_analysis': True,
        'plot_formats': ['pdf']
    })
    print(result[0].text)

asyncio.run(batch_annotate())
"
```

## 🔍 Troubleshooting

### Container Issues

```bash
# Check container logs
docker logs annomics-mcp-server

# Enter container for debugging
docker exec -it annomics-mcp-server /bin/bash

# Restart container
docker-compose restart

# Rebuild if needed
docker-compose down
docker-compose up --build
```

### R Environment Issues

```bash
# Test R installation in container
docker exec annomics-mcp-server R --version

# Check R packages
docker exec annomics-mcp-server Rscript -e "installed.packages()[,c('Package','Version')]"

# Reinstall packages if needed
docker exec annomics-mcp-server Rscript -e "BiocManager::install('annotatr', force=TRUE)"
```

### Performance Issues

```bash
# Monitor resource usage
docker stats annomics-mcp-server

# Increase memory limits in docker-compose.yml:
services:
  annomics-mcp:
    mem_limit: 8g
    memswap_limit: 8g
```

### File Permission Issues

```bash
# Fix ownership of output files
sudo chown -R $USER:$USER output/

# Set proper permissions
chmod -R 755 output/
```

## 🎯 Success Indicators

### ✅ Successful Setup Checklist

- [ ] Container builds without errors
- [ ] Container starts and runs
- [ ] R environment loads successfully
- [ ] All tests pass (`./scripts/run_tests.sh`)
- [ ] Sample annotation completes
- [ ] Output files are generated
- [ ] Plots are created in specified formats

### ✅ Ready for Production

When you see:
```
✅ MCP server ready!
✅ R environment fully functional!
✅ All tests passed successfully!
✅ Sample annotation completed!
```

Your annOmics MCP server is ready for genomic analysis with Claude integration! 🧬🤖

## 📞 Getting Help

If you encounter issues:

1. **Check logs**: `docker logs annomics-mcp-server`
2. **Run tests**: `docker exec annomics-mcp-server ./scripts/run_tests.sh`
3. **Verify R**: `docker exec annomics-mcp-server Rscript -e "library(annotatr)"`
4. **Test simple case**: Use the sample BED file example above

The container approach ensures all dependencies are properly installed and configured, making this the most reliable deployment method for your personal Linux machine!