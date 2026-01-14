# Examples

This directory contains example scripts demonstrating how to use GCMC-Agent.

## ⭐ End-to-End Workflow (Recommended)

**[end_to_end.py](end_to_end.py)** - Complete 4-phase workflow from paper Appendix C

Demonstrates the full automated pipeline:
```
User Request
    ↓
PHASE 1: Research Team
    - Search Semantic Scholar for Garcia-Sanchez 2009
    - Extract CO2 force field parameters
    - Generate RASPA format files
    ↓
PHASE 2: Setup Team
    - Prepare MOR.cif structure
    - Integrate force field
    - Create simulation.input
    - Generate pressure point directories
    ↓
PHASE 3: Simulator  
    - Execute RASPA simulations (if installed)
    ↓
PHASE 4: Result Parser
    - Extract isotherm data from output
    ↓
Complete Results
```

Run:
```bash
python examples/end_to_end.py
```

---

## 🎯 Quick Start

**[quick_start.py](quick_start.py)** - System components demonstration

Shows basic usage of:
- Data structures (IsothermData)
- RASPA runner
- Result parser

Run:
```bash
python examples/quick_start.py
```

##  Logging Demo

**[test_logging.py](test_logging.py)** - Logging system demonstration

Shows:
- RunLogger for workflow tracking
- LLMCallLogger for API call tracing
- Log analysis and replay

Run:
```bash
python examples/test_logging.py
```

## More Examples

### Structure Agent

```python
from gcmc_agent.agents.structure import StructureAgent
from gcmc_agent.client import OpenAIChatClient
from gcmc_agent.config import Config

config = Config.from_env()
client = OpenAIChatClient(config)

agent = StructureAgent(llm_client=client)
result = agent.find_structure("ZIF-8")
print(f"CIF file: {result.cif_path}")
```

### Force Field Agent

```python
from gcmc_agent.agents.forcefield import ForceFieldAgent

agent = ForceFieldAgent(llm_client=client)
result = agent.create_forcefield(
    molecule="CO2",
    framework="ZIF-8",
    method="TraPPE"
)
print(f"Force field files: {result.ff_files}")
```

### Research Pipeline

```python
from gcmc_agent.research import ExtractionAgent

agent = ExtractionAgent(llm_client=client)
data = agent.extract_from_paper(
    paper_id="arxiv:1234.5678",
    target="CO2 adsorption in MOFs"
)
print(f"Extracted data: {data}")
```

### Complete Workflow

```python
from gcmc_agent import GlobalSupervisor

supervisor = GlobalSupervisor()

# User request
request = """
Extract CO2 adsorption data from paper by Smith et al. (2020)
and reproduce their simulation in MOF-5 at 298K.
"""

# Process
result = supervisor.process_request(request)

# Results
if result["status"] == "success":
    print(f"Simulation complete!")
    print(f"Isotherm: {result['isotherm']}")
```

## Development Tools

See [../scripts/](../scripts/) for development utilities:
- `check_environment.py` - Verify dependencies
- `view_logs.py` - Inspect agent logs

## Benchmarks

See [../evaluation/](../evaluation/) for paper reproduction benchmarks:
- Table 1: Setup team evaluation (7 scenarios)
- Table 2: Literature extraction evaluation (6 papers)
