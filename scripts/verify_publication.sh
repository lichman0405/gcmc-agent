#!/bin/bash
# Final verification script before GitHub publication

echo "=================================="
echo "  GCMC-Agent Publication Check"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

check_pass() {
    echo -e "${GREEN}✓ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((CHECKS_WARNING++))
}

echo "1. Checking core project files..."
echo ""

if [ -f "README.md" ]; then check_pass "README.md exists"; else check_fail "README.md missing"; fi
if [ -f "LICENSE" ]; then check_pass "LICENSE exists"; else check_fail "LICENSE missing"; fi
if [ -f "CONTRIBUTING.md" ]; then check_pass "CONTRIBUTING.md exists"; else check_fail "CONTRIBUTING.md missing"; fi
if [ -f ".gitignore" ]; then check_pass ".gitignore exists"; else check_fail ".gitignore missing"; fi
if [ -f "setup.py" ]; then check_pass "setup.py exists"; else check_fail "setup.py missing"; fi
if [ -f "pyproject.toml" ]; then check_pass "pyproject.toml exists"; else check_fail "pyproject.toml missing"; fi
if [ -f "mkdocs.yml" ]; then check_pass "mkdocs.yml exists"; else check_fail "mkdocs.yml missing"; fi

echo ""
echo "2. Checking documentation..."
echo ""

if [ -f "docs/index.md" ]; then check_pass "docs/index.md exists"; else check_fail "docs/index.md missing"; fi
if [ -f "docs/getting-started/installation.md" ]; then check_pass "Installation guide exists"; else check_fail "Installation guide missing"; fi
if [ -f "docs/getting-started/quick-start.md" ]; then check_pass "Quick start exists"; else check_fail "Quick start missing"; fi
if [ -d "docs/_archive" ]; then check_pass "Old docs archived"; else check_warn "Archive directory not found"; fi

echo ""
echo "3. Checking test infrastructure..."
echo ""

if [ -f "tests/conftest.py" ]; then check_pass "Pytest fixtures exist"; else check_fail "Pytest fixtures missing"; fi
if [ -f "tests/test_result_parser_unit.py" ]; then check_pass "ResultParser tests exist"; else check_fail "ResultParser tests missing"; fi
if [ -f "tests/test_raspa_runner_unit.py" ]; then check_pass "RaspaRunner tests exist"; else check_fail "RaspaRunner tests missing"; fi
if [ -f ".flake8" ]; then check_pass "Flake8 config exists"; else check_fail "Flake8 config missing"; fi
if [ -f "scripts/run_tests.sh" ]; then check_pass "Test runner script exists"; else check_fail "Test runner script missing"; fi

echo ""
echo "4. Checking CI/CD workflows..."
echo ""

[ -f ".github/workflows/tests.yml" ] && check_pass "Test workflow exists" || check_fail "Test workflow missing"
[ -f ".github/workflows/docs.yml" ] && check_pass "Docs workflow exists" || check_fail "Docs workflow missing"

echo ""
echo "5. Checking for build artifacts..."
echo ""

if find . -type d -name "__pycache__" | grep -q .; then
    check_warn "Found __pycache__ directories"
else
    check_pass "No __pycache__ directories"
fi

if find . -type d -name "*.egg-info" | grep -q .; then
    check_warn "Found .egg-info directories"
else
    check_pass "No .egg-info directories"
fi

if find . -type f -name "*.pyc" | grep -q .; then
    check_warn "Found .pyc files"
else
    check_pass "No .pyc files"
fi

echo ""
echo "6. Checking Python package structure..."
echo ""

[ -d "src/gcmc_agent" ] && check_pass "Package directory exists" || check_fail "Package directory missing"
[ -f "src/gcmc_agent/__init__.py" ] && check_pass "Package __init__.py exists" || check_fail "Package __init__.py missing"
[ -f "src/gcmc_agent/global_supervisor.py" ] && check_pass "GlobalSupervisor exists" || check_fail "GlobalSupervisor missing"
[ -f "src/gcmc_agent/tools/raspa_runner.py" ] && check_pass "RaspaRunner exists" || check_fail "RaspaRunner missing"
[ -f "src/gcmc_agent/tools/result_parser.py" ] && check_pass "ResultParser exists" || check_fail "ResultParser missing"

echo ""
echo "7. Testing package import..."
echo ""

if python -c "import sys; sys.path.insert(0, 'src'); import gcmc_agent" 2>/dev/null; then
    check_pass "Package imports successfully"
else
    check_fail "Package import failed"
fi

echo ""
echo "8. Checking critical documentation content..."
echo ""

if grep -q "# GCMC-Agent" README.md; then
    check_pass "README has title"
else
    check_fail "README missing title"
fi

if grep -q "Installation" README.md; then
    check_pass "README has installation section"
else
    check_warn "README missing installation section"
fi

if grep -q "arXiv" README.md; then
    check_pass "README references paper"
else
    check_warn "README missing paper reference"
fi

echo ""
echo "=================================="
echo "  Summary"
echo "=================================="
echo ""
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
echo -e "${YELLOW}Warnings: $CHECKS_WARNING${NC}"
echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Project is ready for GitHub publication!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Format code: black src/gcmc_agent tests"
    echo "  2. Sort imports: isort src/gcmc_agent tests"
    echo "  3. Run tests: ./run_tests.sh fast"
    echo "  4. Build docs: mkdocs build --clean"
    echo "  5. Git init and push to GitHub"
    echo "  6. Deploy docs: mkdocs gh-deploy"
    exit 0
else
    echo -e "${RED}✗ Please fix failed checks before publishing${NC}"
    exit 1
fi
