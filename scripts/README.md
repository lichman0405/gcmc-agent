# Development Scripts

Utility scripts for development, testing, and debugging.

## Available Scripts

### run_tests.sh

Comprehensive test runner with multiple modes.

```bash
# Run all tests
./scripts/run_tests.sh all

# Fast tests only (no LLM/slow tests)
./scripts/run_tests.sh fast

# Unit tests only
./scripts/run_tests.sh unit

# With coverage report
./scripts/run_tests.sh coverage

# Linting only
./scripts/run_tests.sh lint

# Type checking only
./scripts/run_tests.sh type
```

### verify_publication.sh

Verify project is ready for GitHub publication.

```bash
./scripts/verify_publication.sh
```

Checks:
- Core project files (README, LICENSE, etc.)
- Documentation structure
- Test infrastructure
- CI/CD workflows
- Build artifacts cleanup
- Package structure
- Import verification

### check_environment.py

Verify all dependencies are correctly installed.

```bash
python scripts/check_environment.py
```

Checks:
- Core framework (openai, langchain, langgraph)
- Configuration (python-dotenv)
- Chemistry tools (pymatgen)
- Data processing (pandas, numpy)
- PDF processing (pypdf)

### view_logs.py

View and analyze agent execution logs.

```bash
python scripts/view_logs.py [log_directory]
```

Features:
- Parse agent thought-action traces
- Display decision-making process
- Show tool calls and results
- Analyze execution flow

## Usage

These scripts are for **development and debugging only**. For usage examples, see [../examples/](../examples/).
