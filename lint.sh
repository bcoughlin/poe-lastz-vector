#!/bin/bash

# Python Code Quality Check Script using Ruff

set -e

echo "🔍 Running Python code quality checks with Ruff..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run a command and capture its exit code
run_check() {
    local tool_name="$1"
    local command="$2"
    
    echo ""
    echo -e "${YELLOW}Running $tool_name...${NC}"
    echo "----------------------------------------"
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $tool_name passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $tool_name failed${NC}"
        return 1
    fi
}

# Install/update tools
echo "📦 Installing code quality tools..."
pip3 install ruff mypy

# Initialize counters
passed=0
failed=0

# Run Ruff linting
if run_check "Ruff (linting)" "ruff check ."; then
    ((passed++))
else
    ((failed++))
    echo "💡 Run 'ruff check . --fix' to auto-fix many issues"
fi

# Run Ruff formatting check
if run_check "Ruff (formatting)" "ruff format . --check"; then
    ((passed++))
else
    ((failed++))
    echo "💡 Run 'ruff format .' to auto-fix formatting"
fi

# Run MyPy (type checking)
if run_check "MyPy (type checking)" "mypy *.py"; then
    ((passed++))
else
    ((failed++))
fi

# Summary
echo ""
echo "=================================================="
echo "🏁 Code Quality Check Summary"
echo "=================================================="
echo -e "✅ Passed: ${GREEN}$passed${NC}"
echo -e "❌ Failed: ${RED}$failed${NC}"

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! Your code is ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some checks failed. Please review and fix the issues.${NC}"
    echo ""
    echo "Quick fixes:"
    echo "• ruff check . --fix  # Auto-fix linting issues"
    echo "• ruff format .       # Auto-fix formatting"
    echo "• Review mypy output above for type issues"
    exit 1
fi