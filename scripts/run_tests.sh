#!/bin/bash
# Test runner script with different test suites

set -e  # Exit on error

echo "=================================="
echo "  GCMC-Agent Test Suite"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_section() {
    echo ""
    echo -e "${GREEN}===================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}===================================${NC}"
    echo ""
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    print_error "Must run from project root directory"
    exit 1
fi

# Activate conda environment if exists
if command -v conda &> /dev/null; then
    if conda env list | grep -q "gcmc-agent"; then
        print_success "Activating gcmc-agent conda environment"
        eval "$(conda shell.bash hook)"
        conda activate gcmc-agent
    fi
fi

# Parse command line arguments
TEST_SUITE=${1:-"all"}

case $TEST_SUITE in
    "unit")
        print_section "Running Unit Tests Only"
        pytest tests/ -m unit -v
        ;;
    
    "integration")
        print_section "Running Integration Tests"
        pytest tests/ -m integration -v
        ;;
    
    "fast")
        print_section "Running Fast Tests (excluding LLM and slow tests)"
        pytest tests/ -m "not llm and not slow" -v
        ;;
    
    "lint")
        print_section "Code Quality Checks"
        
        echo "Running black..."
        black src/gcmc_agent tests --check || print_warning "Black formatting issues found. Run 'black src/gcmc_agent tests' to fix."
        
        echo "Running isort..."
        isort src/gcmc_agent tests --check-only || print_warning "Import sorting issues found. Run 'isort src/gcmc_agent tests' to fix."
        
        echo "Running flake8..."
        flake8 src/gcmc_agent tests || print_warning "Flake8 issues found"
        
        print_success "Linting complete"
        ;;
    
    "type")
        print_section "Type Checking with mypy"
        mypy src/gcmc_agent --ignore-missing-imports || print_warning "Type checking issues found"
        ;;
    
    "coverage")
        print_section "Running Tests with Coverage"
        pytest tests/ --cov=gcmc_agent --cov-report=html --cov-report=term-missing
        print_success "Coverage report generated in htmlcov/index.html"
        ;;
    
    "all")
        print_section "Running Complete Test Suite"
        
        echo "Step 1/5: Code formatting..."
        black src/gcmc_agent tests --check || {
            print_warning "Formatting issues found"
            black src/gcmc_agent tests
            print_success "Auto-formatted code"
        }
        
        echo ""
        echo "Step 2/5: Import sorting..."
        isort src/gcmc_agent tests --check-only || {
            print_warning "Import sorting issues found"
            isort src/gcmc_agent tests
            print_success "Auto-sorted imports"
        }
        
        echo ""
        echo "Step 3/5: Linting with flake8..."
        flake8 src/gcmc_agent tests || print_warning "Linting issues found (non-blocking)"
        
        echo ""
        echo "Step 4/5: Type checking..."
        mypy src/gcmc_agent --ignore-missing-imports || print_warning "Type checking issues found (non-blocking)"
        
        echo ""
        echo "Step 5/5: Running all tests with coverage..."
        pytest tests/ -m "not llm and not slow" --cov=gcmc_agent --cov-report=html --cov-report=term
        
        print_success "All tests complete!"
        print_success "Coverage report: htmlcov/index.html"
        ;;
    
    *)
        echo "Usage: ./run_tests.sh [unit|integration|fast|lint|type|coverage|all]"
        echo ""
        echo "Options:"
        echo "  unit         - Run only unit tests"
        echo "  integration  - Run only integration tests"
        echo "  fast         - Run tests excluding LLM and slow tests"
        echo "  lint         - Run code quality checks"
        echo "  type         - Run type checking"
        echo "  coverage     - Run tests with coverage report"
        echo "  all          - Run complete test suite (default)"
        exit 1
        ;;
esac

echo ""
print_success "Test suite '$TEST_SUITE' completed successfully!"
