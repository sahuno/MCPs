#!/bin/bash

# Create transfer package for annOmics MCP Server
# Run this script on the cluster to prepare files for transfer

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧬 annOmics MCP Server - Transfer Package Creator${NC}"
echo "====================================================="

# Get current directory
CURRENT_DIR=$(pwd)
PROJECT_NAME="annOmics"
ARCHIVE_NAME="annomics-mcp-transfer.tar.gz"

echo -e "${YELLOW}📍 Current directory: ${CURRENT_DIR}${NC}"

# Verify we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "src/annomics_mcp" ]]; then
    echo -e "${RED}❌ Error: Not in annOmics project directory${NC}"
    echo "Please run this script from the annOmics project root directory"
    exit 1
fi

echo -e "${YELLOW}📦 Creating transfer package...${NC}"

# Create the archive excluding unnecessary files
tar -czf ${ARCHIVE_NAME} \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='mouse_results' \
    --exclude='test_output' \
    --exclude='*.log' \
    --exclude='.git' \
    --exclude='*.tmp' \
    --exclude='*.temp' \
    --exclude='output' \
    --exclude='htmlcov' \
    --exclude='.coverage' \
    --exclude='dist' \
    --exclude='build' \
    .

# Check if archive was created successfully
if [[ -f ${ARCHIVE_NAME} ]]; then
    echo -e "${GREEN}✅ Transfer package created successfully!${NC}"
    
    # Show archive details
    ARCHIVE_SIZE=$(ls -lh ${ARCHIVE_NAME} | awk '{print $5}')
    echo -e "${BLUE}📊 Archive details:${NC}"
    echo "   📁 Name: ${ARCHIVE_NAME}"
    echo "   📏 Size: ${ARCHIVE_SIZE}"
    echo "   📍 Location: ${CURRENT_DIR}/${ARCHIVE_NAME}"
    
    # Show contents summary
    echo -e "\n${BLUE}📋 Archive contents:${NC}"
    tar -tzf ${ARCHIVE_NAME} | head -20
    
    TOTAL_FILES=$(tar -tzf ${ARCHIVE_NAME} | wc -l)
    echo "   ... and $(($TOTAL_FILES - 20)) more files (${TOTAL_FILES} total)"
    
    echo -e "\n${GREEN}🚚 Transfer Instructions:${NC}"
    echo "1. Copy this file to your personal Linux machine:"
    echo "   ${YELLOW}scp ${CURRENT_DIR}/${ARCHIVE_NAME} user@your-machine:~/${NC}"
    echo ""
    echo "2. Or copy to external drive:"
    echo "   ${YELLOW}cp ${ARCHIVE_NAME} /path/to/external/drive/${NC}"
    echo ""
    echo "3. On your Linux machine, extract with:"
    echo "   ${YELLOW}tar -xzf ${ARCHIVE_NAME}${NC}"
    echo ""
    echo "4. Follow the CONTAINER_SETUP_GUIDE.md for complete setup instructions"
    
    echo -e "\n${GREEN}📝 Key files included:${NC}"
    echo "   ✅ Complete MCP server source code"
    echo "   ✅ Original R annotation script"  
    echo "   ✅ Comprehensive test suite (73 tests)"
    echo "   ✅ Docker configuration files"
    echo "   ✅ Complete documentation"
    echo "   ✅ Configuration templates"
    echo "   ✅ Setup and deployment scripts"
    
    echo -e "\n${GREEN}🎯 Next Steps:${NC}"
    echo "1. Transfer ${ARCHIVE_NAME} to your Linux machine"
    echo "2. Extract the archive"
    echo "3. Follow CONTAINER_SETUP_GUIDE.md"
    echo "4. Run: docker-compose up --build"
    echo "5. Test with: ./scripts/run_tests.sh"
    
else
    echo -e "${RED}❌ Error: Failed to create transfer package${NC}"
    exit 1
fi

# Verify archive integrity
echo -e "\n${YELLOW}🔍 Verifying archive integrity...${NC}"
if tar -tzf ${ARCHIVE_NAME} > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Archive integrity verified${NC}"
else
    echo -e "${RED}❌ Archive integrity check failed${NC}"
    exit 1
fi

# Show final summary
echo -e "\n${GREEN}🎉 Transfer package ready!${NC}"
echo -e "${BLUE}Package: ${ARCHIVE_NAME} (${ARCHIVE_SIZE})${NC}"
echo -e "${BLUE}Contents: ${TOTAL_FILES} files and directories${NC}"
echo ""
echo -e "${YELLOW}📖 Read CONTAINER_SETUP_GUIDE.md for complete setup instructions${NC}"
echo -e "${YELLOW}🐳 This package includes everything needed for Docker deployment${NC}"