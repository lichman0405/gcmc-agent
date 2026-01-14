# Welcome to GCMC-Agent Documentation

GCMC-Agent is a sophisticated multi-agent system for automating Grand Canonical Monte Carlo (GCMC) molecular simulations using RASPA2.

## What is GCMC-Agent?

GCMC-Agent implements a complete multi-agent workflow that:

1. **Understands** natural language requests for molecular simulations
2. **Extracts** force field parameters from scientific literature
3. **Generates** complete RASPA simulation input files
4. **Executes** simulations and validates results
5. **Analyzes** and visualizes simulation outputs

## Key Features

### 🤖 Multi-Agent Architecture

Two specialized teams work together under a global supervisor:

- **Research Team**: Searches papers, extracts force fields, generates RASPA files
- **Setup Team**: Prepares structures, configures simulations, validates outputs

### 📚 Intelligent Literature Mining

- Automatic paper search via Semantic Scholar
- Force field parameter extraction from PDFs
- Generation of RASPA-format force field files

### 🔬 Full Automation

- End-to-end workflow from natural language to executable simulations
- Support for 17 molecules and 240+ zeolite frameworks
- RASPA2 integration with error handling

### 📊 Result Analysis

- Automatic parsing of RASPA output files
- Pressure-loading isotherm extraction
- Data visualization and export

## Quick Example

```python
from pathlib import Path
from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from gcmc_agent.global_supervisor import GlobalSupervisor

# Initialize supervisor
config = DeepSeekConfig.from_env()
client = OpenAIChatClient(config)
supervisor = GlobalSupervisor(llm_client=client, workspace_root=Path.cwd())

# Run complete workflow
result = supervisor.run(
    user_request="Set up CO2 adsorption isotherm in MFI at 298K, 0.1-10 bar",
    output_folder=Path("output")
)
```

## Paper Implementation

This project implements the complete framework described in:

> "Towards Fully Automated Molecular Simulations"  
> arXiv:2509.10210v1

We achieve **100% coverage** of the paper's Appendix C coordinated workflow.

## Getting Started

New to GCMC-Agent? Start here:

1. [Installation Guide](getting-started/installation.md) - Set up your environment
2. [Quick Start](getting-started/quick-start.md) - Run your first simulation
3. [Configuration](getting-started/configuration.md) - Configure API keys and settings

## User Guides

Learn how to use different components:

- [Architecture Overview](user-guide/architecture.md) - System design and components
- [Research Team](user-guide/research-team.md) - Literature mining workflow
- [Setup Team](user-guide/setup-team.md) - Simulation file generation
- [End-to-End Workflow](user-guide/end-to-end.md) - Complete examples
- [RASPA Integration](user-guide/raspa-integration.md) - Execution and parsing

## API Reference

Detailed API documentation for developers:

- [GlobalSupervisor](api/global-supervisor.md) - Main coordination layer
- [Research Agents](api/research-agents.md) - Paper search and extraction
- [Setup Agents](api/setup-agents.md) - Simulation file generation
- [Tools](api/tools.md) - RASPA runner and result parser

## Evaluation

Reproduction of paper results:

- [Paper Reproduction](evaluation/reproduction.md) - Overall results
- [Table 1 Evaluation](evaluation/table1.md) - Success and execution rates
- [Table 2 Evaluation](evaluation/table2.md) - Force field extraction IoU

## Development

Contributing to GCMC-Agent:

- [Contributing Guide](development/contributing.md) - How to contribute
- [Testing Guide](development/testing.md) - Running and writing tests
- [Code Style](development/code-style.md) - Coding standards

## Support

Need help?

- **Issues**: [GitHub Issues](https://github.com/lichman0405/gcmc-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/lichman0405/gcmc-agent/discussions)
- **Paper**: [arXiv:2509.10210](https://arxiv.org/abs/2509.10210)

## License

This project is licensed under the MIT License. See [License](about/license.md) for details.
