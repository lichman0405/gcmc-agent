# Configuration

GCMC-Agent can be configured through environment variables or configuration files.

## Environment Variables

Create a `.env` file in your project root:

```bash
# LLM API Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1  # Optional

# DeepSeek API (alternative)
DEEPSEEK_API_KEY=your-deepseek-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_CHAT_MODEL=deepseek-chat

# Semantic Scholar (optional, for literature search)
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key
```

## Configuration File

Alternatively, use a Python configuration:

```python
from gcmc_agent.config import Config

config = Config(
    llm_provider="openai",  # or "deepseek"
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.0,
    max_tokens=4000,
    timeout=120
)
```

## RASPA Configuration

Specify RASPA installation path:

```python
from gcmc_agent import GlobalSupervisor
from pathlib import Path

supervisor = GlobalSupervisor(
    raspa_path=Path("/usr/local/bin/simulate"),
    workspace_root=Path("./workspace")
)
```

Or set environment variable:

```bash
export RASPA_DIR=/path/to/raspa
```

## Template Configuration

Customize RASPA templates location:

```python
supervisor = GlobalSupervisor(
    template_dir=Path("./custom_templates")
)
```

Default template structure:
```
templates/raspa/
├── force_field_mixing_rules.def
├── pseudo_atoms.def
├── simulation.input.template
└── forcefields/
```

## Logging Configuration

Control verbosity:

```python
supervisor = GlobalSupervisor(verbose=True)  # Enable detailed logging
```

Or configure logging manually:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Advanced Options

### LLM Settings

```python
config = Config(
    temperature=0.0,      # Deterministic output
    max_tokens=4000,      # Response length
    timeout=120,          # API timeout (seconds)
    max_retries=3         # Retry failed requests
)
```

### Workspace Settings

```python
supervisor = GlobalSupervisor(
    workspace_root=Path("./workspace"),
    output_folder=Path("./output"),
    keep_intermediate=True  # Keep intermediate files
)
```

## Example: Complete Configuration

```python
from pathlib import Path
from gcmc_agent import GlobalSupervisor
from gcmc_agent.config import Config

# Configure LLM
config = Config.from_env()  # Load from .env file

# Initialize supervisor
supervisor = GlobalSupervisor(
    llm_config=config,
    workspace_root=Path("./workspace"),
    raspa_path=Path("/usr/local/bin/simulate"),
    template_dir=Path("./templates/raspa"),
    verbose=True
)

# Run simulation
result = supervisor.run(
    user_request="Setup CO2 adsorption in ZIF-8",
    output_folder=Path("./output")
)
```

## Troubleshooting

### API Connection Issues

```python
# Test API connection
from gcmc_agent.client import OpenAIChatClient
from gcmc_agent.config import Config

config = Config.from_env()
client = OpenAIChatClient(config)

# Test call
response = client.chat(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response)
```

### RASPA Not Found

```bash
# Check RASPA installation
which simulate

# Add to PATH
export PATH=/path/to/raspa/bin:$PATH
```

### Template Issues

Ensure templates directory has correct structure:

```bash
ls -R templates/raspa/
```

See [Installation Guide](installation.md) for more details.
