#!/bin/bash

# Test runner script for annOmics MCP Server
# Usage: ./scripts/run_tests.sh [test-type]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧬 annOmics MCP Server Test Suite${NC}"
echo "=================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install uv first.${NC}"
    exit 1
fi

# Activate virtual environment
export UV_PROJECT_ENVIRONMENT=.venv
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Parse test type argument
TEST_TYPE=${1:-"all"}

case $TEST_TYPE in
    "unit")
        echo -e "${YELLOW}🔬 Running unit tests...${NC}"
        uv run pytest tests/unit/ -v
        ;;
    "integration") 
        echo -e "${YELLOW}🔗 Running integration tests...${NC}"
        uv run pytest tests/integration/ -v
        ;;
    "positive")
        echo -e "${YELLOW}✅ Running positive test cases...${NC}"
        uv run pytest tests/test_positive_cases.py -v
        ;;
    "negative")
        echo -e "${YELLOW}❌ Running negative test cases...${NC}"
        uv run pytest tests/test_negative_cases.py -v
        ;;
    "quick")
        echo -e "${YELLOW}⚡ Running quick tests (excluding slow tests)...${NC}"
        uv run pytest -v -m "not slow"
        ;;
    "slow")
        echo -e "${YELLOW}🐌 Running slow tests only...${NC}"
        uv run pytest -v -m "slow"
        ;;
    "coverage")
        echo -e "${YELLOW}📊 Running tests with coverage...${NC}"
        uv add --dev pytest-cov
        uv run pytest --cov=annomics_mcp --cov-report=html --cov-report=term
        echo -e "${GREEN}📈 Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "all"|*)
        echo -e "${YELLOW}🚀 Running all tests...${NC}"
        
        echo -e "\n${YELLOW}Step 1: Unit tests${NC}"
        uv run pytest tests/unit/ -v
        
        echo -e "\n${YELLOW}Step 2: Integration tests${NC}"
        uv run pytest tests/integration/ -v
        
        echo -e "\n${YELLOW}Step 3: Positive cases${NC}"
        uv run pytest tests/test_positive_cases.py -v
        
        echo -e "\n${YELLOW}Step 4: Negative cases${NC}"
        uv run pytest tests/test_negative_cases.py -v
        
        echo -e "\n${GREEN}✅ All tests completed!${NC}"
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed successfully!${NC}"
else
    echo -e "\n${RED}💥 Some tests failed. Please check the output above.${NC}"
    exit 1
fi

# Optional: Run linting if ruff is available
if command -v ruff &> /dev/null; then
    echo -e "\n${YELLOW}🧹 Running code formatting check...${NC}"
    uv run ruff check src/ tests/
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Code formatting looks good!${NC}"
    else
        echo -e "${YELLOW}⚠️  Code formatting issues found. Run 'uv run ruff format src/ tests/' to fix.${NC}"
    fi
fi

# Optional: Run type checking if mypy is available
if command -v mypy &> /dev/null; then
    echo -e "\n${YELLOW}🔍 Running type checking...${NC}"
    uv run mypy src/annomics_mcp/ --ignore-missing-imports
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Type checking passed!${NC}"
    else
        echo -e "${YELLOW}⚠️  Type checking issues found.${NC}"
    fi
fi

echo -e "\n${GREEN}🏁 Test run complete!${NC}"