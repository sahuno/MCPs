# annOmics MCP Server - Deployment Guide

## Quick Start

### 1. Local Development Setup

```bash
# Clone repository
git clone <repository-url>
cd annOmics

# Install with uv (recommended)
uv sync --dev

# Verify R environment
Rscript -e "library(annotatr); library(GenomicRanges); print('R environment ready')"

# Run tests
./scripts/run_tests.sh

# Start server
uv run annomics-mcp
```

### 2. Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run manually
docker build -t annomics-mcp .
docker run -v ./data:/app/data -v ./output:/app/output annomics-mcp
```

## Production Deployment

### System Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB (plus space for annotation databases)
- Python 3.11+
- R 4.0+ with Bioconductor packages

**Recommended**:
- CPU: 4+ cores  
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: High-speed for database downloads

### Installation Methods

#### Method 1: uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repository-url>
cd annOmics
uv sync

# Install R dependencies
Rscript -e "
if (!requireNamespace('BiocManager', quietly = TRUE))
    install.packages('BiocManager')
BiocManager::install(c('annotatr', 'GenomicRanges'))
install.packages(c('tidyverse', 'data.table', 'ggplot2', 'optparse'))
"

# Start server
uv run annomics-mcp
```

#### Method 2: Docker (Production)

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or manual Docker setup
docker build -t annomics-mcp .
docker run -d \
  --name annomics-mcp-server \
  -v /data/genomics:/app/data:ro \
  -v /data/results:/app/output:rw \
  --restart unless-stopped \
  annomics-mcp
```

#### Method 3: System Installation

```bash
# Build wheel
uv build

# Install globally
pip install dist/annomics_mcp-*.whl

# Create systemd service
sudo cp deployment/annomics-mcp.service /etc/systemd/system/
sudo systemctl enable annomics-mcp
sudo systemctl start annomics-mcp
```

### Configuration

#### Environment Variables

```bash
# Core settings
export ANNOMICS_CONFIG_FILE="/path/to/config.json"
export ANNOMICS_LOG_LEVEL="INFO"
export ANNOMICS_OUTPUT_DIR="/data/results"

# R environment
export R_LIBS_USER="/usr/local/lib/R/site-library"
export R_MAX_MEMORY="8G"

# Performance tuning
export ANNOMICS_MAX_CONCURRENT_JOBS=3
export ANNOMICS_CACHE_TTL=24  # hours
```

#### Configuration File

Create `/etc/annomics/config.json`:

```json
{
  "server": {
    "name": "annomics-mcp-prod",
    "log_level": "INFO",
    "max_file_size_mb": 500,
    "timeout_seconds": 1800
  },
  "r_environment": {
    "memory_limit": "16G",
    "timeout_seconds": 3600
  },
  "performance": {
    "max_concurrent_jobs": 5,
    "memory_limit_mb": 8192,
    "enable_caching": true
  }
}
```

### Monitoring and Logging

#### Health Checks

```bash
# Basic health check
curl -X POST http://localhost:8000/health

# Or for stdio mode
echo '{"method": "ping"}' | annomics-mcp

# Check R environment
Rscript -e "library(annotatr); print('OK')"
```

#### Log Management

```bash
# View logs
journalctl -u annomics-mcp -f

# Or with Docker
docker logs -f annomics-mcp-server

# Log rotation (add to logrotate)
/var/log/annomics/*.log {
    daily
    rotate 30
    compress
    notifempty
    create 644 annomics annomics
}
```

#### Monitoring Setup

```bash
# System metrics
top -p $(pgrep -f annomics-mcp)
iostat -x 1
free -h

# Custom metrics script
#!/bin/bash
# Monitor annotation jobs
echo "Active jobs: $(ps aux | grep -c 'Rscript.*annotate_genomic_segments')"
echo "Memory usage: $(ps -o pid,vsz,rss,comm -p $(pgrep -f annomics-mcp))"
echo "Disk usage: $(df -h /data/results)"
```

### Security Considerations

#### File System Security

```bash
# Create dedicated user
sudo useradd -r -s /bin/false annomics
sudo mkdir -p /var/lib/annomics /var/log/annomics
sudo chown annomics:annomics /var/lib/annomics /var/log/annomics

# Set file permissions
sudo chmod 750 /var/lib/annomics
sudo chmod 755 /usr/local/bin/annomics-mcp
```

#### Network Security

```bash
# If using HTTP mode, setup reverse proxy
# nginx.conf
server {
    listen 80;
    server_name annomics.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Setup SSL with Let's Encrypt
certbot --nginx -d annomics.yourdomain.com
```

### Performance Optimization

#### System Tuning

```bash
# Increase file limits
echo "annomics soft nofile 65536" >> /etc/security/limits.conf
echo "annomics hard nofile 65536" >> /etc/security/limits.conf

# Optimize R performance
echo "R_MAX_VSIZE=32Gb" >> /etc/R/Renviron
echo "options(mc.cores=parallel::detectCores())" >> /etc/R/Rprofile.site

# SSD optimization for databases
echo "deadline" > /sys/block/sda/queue/scheduler
```

#### Database Optimization

```bash
# Pre-download annotation databases
Rscript -e "
library(annotatr)
for(genome in c('hg38', 'mm10')) {
  build_annotations(genome, paste0(genome, '_cpgs'))
  build_annotations(genome, paste0(genome, '_genes_promoters'))
}
"

# Create database cache directory
mkdir -p /var/lib/annomics/cache
chown annomics:annomics /var/lib/annomics/cache
```

## Integration with Claude

### MCP Client Setup

#### For Claude Desktop

Add to Claude Desktop settings:

```json
{
  "mcpServers": {
    "annomics": {
      "command": "annomics-mcp",
      "args": [],
      "env": {
        "ANNOMICS_CONFIG_FILE": "/path/to/config.json"
      }
    }
  }
}
```

#### For Custom Integration

```python
import asyncio
from mcp.client import stdio_client

async def use_annomics():
    async with stdio_client("annomics-mcp") as client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])
        
        # Annotate regions
        result = await client.call_tool("annotate_genomic_regions", {
            "input_files": "peaks.bed",
            "genome_build": "hg38",
            "output_directory": "results"
        })
        print("Result:", result)

asyncio.run(use_annomics())
```

### Example Workflows

#### Workflow 1: ChIP-seq Analysis

```
User: "I have ChIP-seq peaks from a transcription factor study. 
       Please annotate them with hg38 and show me the genomic distribution."

Claude: I'll annotate your ChIP-seq peaks and analyze their distribution.

[Calls annotate_genomic_regions tool]

Your peaks show:
- 45% in promoter regions
- 23% in gene bodies  
- 18% in intergenic regions
- 14% near CpG islands

This suggests your TF prefers active promoter regions...
```

#### Workflow 2: Multi-sample Comparison

```  
User: "Compare the genomic annotations between control and treatment samples"

Claude: I'll process both samples and create a comparison analysis.

[Calls annotate_genomic_regions with combine_analysis=true]

Comparison shows:
- Treatment has 2x more promoter binding
- Control shows more intergenic binding
- CpG island overlap increased 3-fold in treatment
```

## Troubleshooting

### Common Issues

#### 1. R Package Installation Fails

```bash
# Install system dependencies
sudo apt-get install libcurl4-openssl-dev libssl-dev libxml2-dev

# Install packages manually
R -e "BiocManager::install('annotatr', force=TRUE)"
```

#### 2. Memory Issues

```bash
# Increase R memory limit
export R_MAX_VSIZE=16Gb

# Process files in smaller batches
# Use combine_analysis=false for large datasets
```

#### 3. Permission Errors

```bash
# Fix file permissions
sudo chown -R annomics:annomics /var/lib/annomics
sudo chmod -R 755 /var/lib/annomics
```

#### 4. Docker Issues

```bash
# Check container logs
docker logs annomics-mcp-server

# Rebuild with no cache
docker-compose build --no-cache

# Check volume mounts
docker inspect annomics-mcp-server | grep Mounts -A 10
```

### Performance Issues

#### Slow Annotation

```bash
# Check system resources
htop
iotop

# Monitor R processes
ps aux | grep Rscript

# Check database downloads
ls -la ~/.cache/R/
```

#### High Memory Usage

```bash
# Monitor memory
watch -n 1 'free -h && ps aux --sort=-%mem | head -10'

# Tune garbage collection
echo "options(expressions=50000)" >> ~/.Rprofile
```

### Log Analysis

```bash
# Common error patterns
grep -i "error\|failed\|exception" /var/log/annomics/server.log

# Performance analysis
grep "completed in" /var/log/annomics/server.log | \
  awk '{print $NF}' | sort -n

# Resource usage
grep "memory\|cpu" /var/log/annomics/server.log
```

## Backup and Recovery

### Database Backup

```bash
# Backup R packages and databases
tar -czf annomics-backup-$(date +%Y%m%d).tar.gz \
  /usr/local/lib/R/site-library \
  ~/.cache/R/ \
  /var/lib/annomics/

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/annomics"
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "$BACKUP_DIR/annomics-$DATE.tar.gz" \
  /var/lib/annomics/ \
  /etc/annomics/
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Recovery

```bash
# Restore from backup
tar -xzf annomics-backup-20240101.tar.gz -C /

# Restart services
sudo systemctl restart annomics-mcp

# Verify installation
annomics-mcp --version
```

## Scaling and High Availability

### Horizontal Scaling

```yaml
# docker-compose.yml for multiple instances
version: '3.8'
services:
  annomics-mcp-1:
    build: .
    ports: ["8001:8000"]
  annomics-mcp-2: 
    build: .
    ports: ["8002:8000"]
  
  nginx:
    image: nginx
    ports: ["80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Load Balancing

```nginx
# nginx.conf
upstream annomics_backend {
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://annomics_backend;
    }
}
```

## Support

### Getting Help

- **Documentation**: Check README_MCP.md and MCP_USAGE_GUIDE.md
- **Issues**: Report bugs on GitHub issues
- **Discussions**: Use GitHub discussions for questions

### Contributing

```bash
# Development setup
git clone <repo>
cd annOmics
uv sync --dev

# Run tests before contributing
./scripts/run_tests.sh

# Format code
uv run ruff format src/ tests/

# Submit PR with tests
```