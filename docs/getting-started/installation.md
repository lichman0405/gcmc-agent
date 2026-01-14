# Installation

This guide will help you install GCMC-Agent and its dependencies.

## Prerequisites

- Python 3.10 or higher
- Conda (recommended) or pip
- RASPA 2.0 (for running molecular simulations)
- OpenAI API key or compatible LLM API

## Quick Installation

### Using Conda (Recommended)

```bash
# Create and activate conda environment
conda create -n gcmc-agent python=3.12
conda activate gcmc-agent

# Clone repository
git clone https://github.com/lichman0405/gcmc-agent.git
cd gcmc-agent

# Install package
pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Clone repository
git clone https://github.com/lichman0405/gcmc-agent.git
cd gcmc-agent

# Install package
pip install -e .
```

## Installing RASPA

GCMC-Agent requires RASPA 2.0 for running molecular simulations.

### Linux

```bash
# Install dependencies
sudo apt-get install build-essential gfortran

# Download and compile RASPA
git clone https://github.com/iRASPA/RASPA2.git
cd RASPA2
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### macOS

```bash
# Install with Homebrew
brew install cmake gfortran

# Download and compile RASPA
git clone https://github.com/iRASPA/RASPA2.git
cd RASPA2
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

Verify installation:
```bash
simulate --help
```

## Setting Up API Keys

GCMC-Agent requires an LLM API key (OpenAI or compatible).

### OpenAI

Create `.env` file in project root:
```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1  # Optional, for custom endpoints
```

### Azure OpenAI

```bash
OPENAI_API_KEY=your-azure-api-key
OPENAI_API_BASE=https://your-resource.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
```

### Other Compatible APIs

```bash
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=https://your-custom-endpoint.com/v1
```

## Development Installation

For contributing to GCMC-Agent:

```bash
# Install with development dependencies
pip install -e ".[dev,docs]"

# Verify installation
./run_tests.sh fast
```

This installs additional tools:
- pytest, pytest-cov, pytest-mock (testing)
- mypy (type checking)
- black, flake8, isort (code formatting and linting)
- mkdocs, mkdocs-material (documentation)

## Verifying Installation

Run the quick start example:

```python
from gcmc_agent import GlobalSupervisor

supervisor = GlobalSupervisor()
print("✓ GCMC-Agent installed successfully!")
```

Or run the test suite:
```bash
./run_tests.sh fast
```

## Troubleshooting

### Import Errors

If you see import errors:
```bash
# Ensure you're in the right conda environment
conda activate gcmc-agent

# Reinstall package
pip install -e .
```

### RASPA Not Found

If `simulate` command is not found:
```bash
# Add RASPA to PATH (Linux/macOS)
export PATH=/path/to/RASPA/bin:$PATH

# Or set in .bashrc/.zshrc for persistence
echo 'export PATH=/path/to/RASPA/bin:$PATH' >> ~/.bashrc
```

### API Key Issues

If LLM calls fail:
1. Check `.env` file exists in project root
2. Verify API key is correct
3. Test API endpoint manually:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

## Next Steps

- [Quick Start Guide](quick-start.md) - Run your first simulation
- [Configuration](configuration.md) - Customize GCMC-Agent
- [Architecture Overview](../user-guide/architecture.md) - Understand the system
