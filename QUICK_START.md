# 🚀 Quick Start Guide - Get Running in Minutes

## 🎯 Two Approaches: Local vs Docker

The test suite revealed that **Docker build is slow** due to R package compilation. Here are **two bulletproof approaches**:

## ⚡ **Option 1: Local Installation (Fastest)**

### Step 1: Install R Packages
```bash
# Install R packages (one-time setup)
R -e "if (!requireNamespace('BiocManager', quietly = TRUE)) install.packages('BiocManager')"
R -e "BiocManager::install(c('annotatr', 'GenomicRanges'))"
R -e "install.packages(c('optparse', 'tidyverse', 'data.table', 'ggplot2'))"
```

### Step 2: Test & Run
```bash
# Test everything
python3 test_simple_setup.py

# Run the simple server directly
python3 src/annomics_mcp/simple_server.py
```

### Step 3: Use with Claude
Configure Claude Desktop to use the local server:
```json
{
  "mcpServers": {
    "annomics": {
      "command": "python3",
      "args": ["/full/path/to/MCPs/annOmics/src/annomics_mcp/simple_server.py"],
      "cwd": "/full/path/to/MCPs/annOmics"
    }
  }
}
```

## 🐳 **Option 2: Optimized Docker (Reliable)**

### Step 1: Pre-built R Image
```bash
# Use R image with pre-installed packages
docker run --rm -v $(pwd):/work -w /work rocker/tidyverse:latest \
  R -e "BiocManager::install(c('annotatr', 'GenomicRanges'))"
```

### Step 2: Build Optimized Container
```bash
# Build with cached R packages
docker build -f Dockerfile.optimized -t annomics-fast .
docker run -d --name annomics-server annomics-fast
```

### Step 3: Use with Claude
```json
{
  "mcpServers": {
    "annomics": {
      "command": "docker",
      "args": ["exec", "-i", "annomics-server", "python3", "/app/simple_server.py"]
    }
  }
}
```

## 🧪 **Testing Your Setup**

Always run the test suite first:
```bash
python3 test_simple_setup.py
```

**Expected results:**
- ✅ R Environment: All packages available
- ✅ R Script: Help working properly  
- ✅ Simple Server: Core functionality working
- ✅ Server Requests: MCP tools responding
- ✅ Docker Build: Container builds successfully (if using Docker)

## 🎯 **Recommended Approach**

**For Development/Testing**: Use **Option 1 (Local)** - fastest setup
**For Production/Sharing**: Use **Option 2 (Docker)** - most reliable

## 🔧 **Troubleshooting**

**R packages fail to install:**
```bash
# Check R installation
R --version

# Install system dependencies first (Ubuntu/Debian)
sudo apt-get install r-base-dev libcurl4-openssl-dev libssl-dev libxml2-dev

# Try installing packages one by one
R -e "install.packages('BiocManager')"
R -e "BiocManager::install('annotatr')"
```

**Docker build too slow:**
```bash
# Use local approach instead
# OR use pre-built base images with R packages
```

**Server not responding:**
```bash
# Check server logs
python3 src/annomics_mcp/simple_server.py --debug

# Test individual tools
echo '{"method":"tools/list"}' | python3 src/annomics_mcp/simple_server.py
```

---

**The beauty of this approach**: If one method doesn't work perfectly, you have a **proven backup**. The simple server architecture works the same way locally or in Docker! 🎯