#!/bin/bash
# Week 1 Verification Script

echo "=== MemNexus Week 1 Verification ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Function to check and report
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

# 1. Check branch
echo "1. Checking branch..."
git branch | grep -q "* feature/code-memory"
check "On feature/code-memory branch"

# 2. Check experimental markers
echo ""
echo "2. Checking experimental markers..."
grep -q "EXPERIMENTAL" src/memnexus/memory/advanced_rag.py
check "advanced_rag.py marked as experimental"

[ -f "src/memnexus/memory/layers/README.md" ] && grep -q "EXPERIMENTAL" src/memnexus/memory/layers/README.md
check "layers/ marked as experimental"

# 3. Check new files exist
echo ""
echo "3. Checking new files..."
[ -f "src/memnexus/memory/git.py" ]
check "git.py created"

[ -f "src/memnexus/memory/code.py" ]
check "code.py created"

# 4. Check CLI commands
echo ""
echo "4. Checking CLI commands..."
grep -q "def init(" src/memnexus/cli.py
check "init command added"

grep -q "def status(" src/memnexus/cli.py
check "status command added"

# 5. Check documentation
echo ""
echo "5. Checking documentation..."
[ -f "docs/VISION.md" ]
check "VISION.md exists"

[ -f "docs/ROADMAP.md" ]
check "ROADMAP.md exists"

grep -q "Code Memory" README.md
check "README updated with new positioning"

# 6. Check simplified exports
echo ""
echo "6. Checking simplified exports..."
grep -q "GitMemoryExtractor" src/memnexus/memory/__init__.py
check "GitMemoryExporter in exports"

grep -q "CodeMemoryExtractor" src/memnexus/memory/__init__.py
check "CodeMemoryExtractor in exports"

# Summary
echo ""
echo "=================================="
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Week 1 completed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run 'uv sync' to install dependencies"
    echo "  2. Test 'memnexus init' in a project directory"
    echo "  3. Start Week 2: Git Integration"
else
    echo -e "${YELLOW}⚠ Some checks failed. Review above.${NC}"
fi
