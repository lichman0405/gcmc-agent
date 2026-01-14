# Contributing Guide

Thank you for your interest in contributing to GCMC-Agent!

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/lichman0405/gcmc-agent.git
cd gcmc-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- Main dependencies
- Testing tools (pytest, pytest-cov)
- Code quality tools (black, flake8, mypy)
- Documentation tools (mkdocs, mkdocs-material)

### 4. Install RASPA

See [Installation Guide](../getting-started/installation.md) for RASPA setup instructions.

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code, add tests, update documentation.

### 3. Run Tests

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test file
pytest tests/test_raspa_runner_unit.py

# Run with coverage
pytest --cov=src/gcmc_agent tests/
```

### 4. Format Code

```bash
# Auto-format with black
black src/ tests/

# Check style with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

Follow conventional commits format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `style:` Formatting
- `chore:` Maintenance

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Testing Guidelines

### Unit Tests

Test individual components in isolation:

```python
# tests/test_result_parser_unit.py
import pytest
from gcmc_agent.tools.result_parser import ResultParser

def test_parse_loading():
    parser = ResultParser()
    # Mock output file
    result = parser.parse_loading(mock_data)
    assert result == expected_value
```

### Integration Tests

Test component interactions:

```python
# tests/test_integration.py
def test_full_workflow():
    supervisor = GlobalSupervisor()
    result = supervisor.run("Setup CO2 in ZIF-8")
    assert result["status"] == "success"
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_raspa_runner_unit.py

# Specific test
pytest tests/test_raspa_runner_unit.py::test_check_installation

# With coverage
pytest --cov=src/gcmc_agent --cov-report=html

# Verbose output
pytest -v
```

## Code Style

### Python Style

Follow PEP 8 with these tools:

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type hints
mypy src/
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description with more details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When input is invalid
        
    Example:
        >>> my_function("test", 42)
        True
    """
    return True
```

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional
from pathlib import Path

def process_files(
    file_paths: List[Path],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process multiple files."""
    ...
```

## Documentation

### Building Documentation

```bash
# Install dependencies
pip install mkdocs mkdocs-material

# Serve locally
mkdocs serve

# Build static site
mkdocs build
```

### Adding Documentation

1. Create markdown file in `docs/`
2. Add to navigation in `mkdocs.yml`
3. Use proper formatting (see existing docs)

### Documentation Style

- Clear, concise language
- Code examples for all features
- Links to related documentation
- Include both basic and advanced examples

## Adding New Features

### 1. New Agent

```python
# src/gcmc_agent/agents/my_agent.py
from gcmc_agent.react.base import ReactAgent

class MyAgent(ReactAgent):
    """Description of agent."""
    
    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.register_tool("my_tool", self.my_tool_fn)
    
    def my_tool_fn(self, input: str) -> str:
        """Tool description."""
        # Implementation
        return result
```

### 2. New Tool

```python
# src/gcmc_agent/tools/my_tool.py
from pathlib import Path
from typing import Dict, Any

class MyTool:
    """Description of tool."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def execute(self, input: str) -> Dict[str, Any]:
        """Execute tool."""
        # Implementation
        return result
```

### 3. Tests

```python
# tests/test_my_feature.py
import pytest
from gcmc_agent.agents.my_agent import MyAgent

def test_my_agent():
    """Test my agent functionality."""
    agent = MyAgent(mock_client)
    result = agent.run("test task")
    assert result["status"] == "success"
```

### 4. Documentation

Add to `docs/api/` or `docs/user-guide/` as appropriate.

## Pull Request Guidelines

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted (black)
- [ ] No linting errors (flake8)
- [ ] Type hints added (mypy)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages follow convention

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code formatted
- [ ] CHANGELOG updated
```

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check existing docs first

## Code of Conduct

Please be respectful and constructive in all interactions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Additional Resources

- [Architecture Documentation](../user-guide/architecture.md)
- [API Reference](../api/agents.md)
