# Contributing to GCMC-Agent

Thank you for your interest in contributing to GCMC-Agent! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lichman0405/gcmc-agent.git
   cd gcmc-agent
   ```

2. **Create a conda environment**:
   ```bash
   conda create -n gcmc-agent python=3.12
   conda activate gcmc-agent
   ```

3. **Install in development mode**:
   ```bash
   pip install -e ".[dev,docs]"
   ```

4. **Verify installation**:
   ```bash
   ./run_tests.sh fast
   ```

## Development Workflow

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking

Run all checks:
```bash
./run_tests.sh lint
./run_tests.sh type
```

Auto-format code:
```bash
black src/gcmc_agent tests
isort src/gcmc_agent tests
```

### Testing

We use pytest for automated testing. All tests are unit tests that run without external dependencies.

Test structure:
- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/test_result_parser_unit.py` - ResultParser unit tests (12 tests)
- `tests/test_raspa_runner_unit.py` - RaspaRunner unit tests (12 tests)

Run tests:
```bash
./run_tests.sh fast          # Run all tests (default)
./run_tests.sh coverage      # With coverage report
./run_tests.sh all           # Complete test suite with linting
pytest tests/ -v             # Direct pytest execution
```

Note: Some integration tests requiring RASPA installation are marked with `@pytest.mark.raspa` and will be skipped if RASPA is not available.

### Writing Tests

1. **Create test files** in `tests/` directory
2. **Mark tests appropriately**:
   ```python
   import pytest
   
   @pytest.mark.unit
   def test_something():
       assert True
   
   @pytest.mark.llm
   def test_with_llm():
       # Test requiring LLM API
       pass
   ```

3. **Use fixtures** from `tests/conftest.py`:
   ```python
   def test_with_fixture(temp_workspace, sample_cif_file):
       # temp_workspace provides temporary directory
       # sample_cif_file provides test CIF file
       pass
   ```

4. **Mock external dependencies**:
   ```python
   from unittest.mock import MagicMock
   
   @pytest.mark.unit
   def test_with_mock(mock_llm_response):
       # Use mock instead of real API call
       pass
   ```

### Type Hints

All new code should include type hints:

```python
from typing import List, Dict, Optional

def process_data(
    items: List[str],
    config: Dict[str, any],
    optional_param: Optional[int] = None
) -> Dict[str, List[str]]:
    """Process items with config."""
    result: Dict[str, List[str]] = {}
    # Implementation
    return result
```

Run type checker:
```bash
mypy src/gcmc_agent --ignore-missing-imports
```

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code style guidelines

3. **Add tests** for new functionality

4. **Run test suite**:
   ```bash
   ./scripts/run_tests.sh all
   ```

5. **Update documentation** if needed

6. **Commit with clear messages**:
   ```bash
   git commit -m "Add feature: brief description"
   ```

7. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Ensure CI passes** on GitHub Actions

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when applicable

Examples:
```
Add result parser for RASPA output files
Fix import error in global supervisor
Update documentation for research team
```

## Documentation

Documentation is built with MkDocs Material theme.

### Building Docs Locally

```bash
mkdocs serve
```

Visit `http://127.0.0.1:8000` to view documentation.

### Adding New Documentation

1. Create markdown files in appropriate `docs/` subdirectory
2. Update `mkdocs.yml` navigation section
3. Use proper markdown formatting:
   - Add language identifiers to code blocks
   - Use admonitions for notes/warnings
   - Include examples where helpful

### Documentation Style

- Write in clear, concise English
- Include code examples for features
- Add links to related sections
- Use proper heading hierarchy (h1 for page title, h2 for sections, etc.)

## Project Structure

```
gcmc-agent/
├── src/gcmc_agent/          # Main package
│   ├── agents/              # Agent implementations
│   ├── react/               # ReAct framework
│   ├── research/            # Research pipeline
│   └── tools/               # Tool implementations
├── tests/                   # Test suite
│   ├── conftest.py          # Pytest fixtures
│   └── test_*.py            # Test files
├── docs/                    # Documentation
├── templates/               # RASPA templates
└── evaluation/              # Benchmark scripts
```

## Need Help?

- Open an issue for bugs or feature requests
- Join discussions in GitHub Discussions
- Check existing issues before creating new ones
- Be respectful and constructive in all interactions

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
