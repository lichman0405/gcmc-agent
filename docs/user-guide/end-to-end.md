---
title: End-to-End Workflow
description: Complete guide to using GCMC-Agent's end-to-end automation features
---

# End-to-End Workflow

## Overview

This guide explains the complete end-to-end automation workflow as described in the paper Appendix C. The workflow consists of 4 phases:

```
User Request
    ↓
PHASE 1: Research Team (if paper reference in request)
    - PaperSearchAgent: Search Semantic Scholar
    - PaperExtractionAgent: Extract force field parameters
    - ForceFieldWriterAgent: Generate RASPA format files
    ↓
PHASE 2: Experiment Setup Team
    - StructureExpert: Prepare .cif structure file
    - ForceFieldExpert: Integrate force field files
    - SimulationInputExpert: Create simulation.input
    - CodingExpert: Generate pressure point directories
    - Evaluator: Validate all outputs
    ↓
PHASE 3: Simulator
    - RaspaRunner: Execute RASPA simulations
    ↓
PHASE 4: Result Parser
    - ResultParser: Extract isotherm data from output
    ↓
Complete Results
```

## Components

### 1. GlobalSupervisor
- **Purpose**: Coordinates all 4 phases of the workflow
- **Location**: `src/gcmc_agent/global_supervisor.py`
- **Implementation**: Paper Appendix C coordinated workflow

### 2. RaspaRunner
- **Purpose**: Execute and validate RASPA simulations
- **Location**: `src/gcmc_agent/tools/raspa_runner.py`
- **Features**: Auto-detection, validation, error handling

### 3. ResultParser
- **Purpose**: Extract adsorption data from RASPA output
- **Location**: `src/gcmc_agent/tools/result_parser.py`
- **Features**: Isotherm data extraction, unit conversion, plotting

## Quick Start

### Option 1: End-to-End Example (Recommended)
```bash
# Run complete workflow from paper Appendix C
python examples/end_to_end.py
```

This runs the exact workflow from the paper:
- User Request: CO2 isotherm in MOR, force field from Garcia-Sanchez 2009
- Research Team: Searches Semantic Scholar, extracts parameters
- Setup Team: Prepares all simulation files
- Simulator: Executes RASPA (if installed)
- Result Parser: Extracts isotherm data

### Option 2: Python API
```python
from pathlib import Path
from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from gcmc_agent.global_supervisor import GlobalSupervisor

# Initialize
config = DeepSeekConfig.from_env()
client = OpenAIChatClient(config)
supervisor = GlobalSupervisor(
    llm_client=client,
    workspace_root=Path.cwd(),
    verbose=True
)

# Run complete 4-phase workflow
result = supervisor.run(
    user_request="""
    Set up an adsorption isotherm simulation for MOR zeolite with CO2,
    evaluated at 10, 30, 100, 300, 1000, 3000 and 10000 Pa.
    The force field should be taken from Garcia-Sanchez et al. 2009.
    """,
    output_folder=Path("./output")
)

if result.success:
    print(result.answer)
```

### Option 3: RASPA Execution Only
```python
from gcmc_agent.tools.raspa_runner import RaspaRunner

runner = RaspaRunner(verbose=True)

# Validate setup without execution
validation = runner.validate_setup("/path/to/simulation/folder")
print(f"Valid: {validation['valid']}")

# Execute simulation
result = runner.run("/path/to/simulation.input", timeout=3600)
if result.success:
    print(f"Completed in {result.execution_time:.1f}s")
    print(f"Output files: {result.output_files}")
```

### Option 4: Result Parsing
```python
from gcmc_agent.tools.result_parser import ResultParser

parser = ResultParser()

# Extract isotherm data
isotherm = parser.parse_isotherm("/path/to/Output/System_0")
print(f"Pressure points: {len(isotherm.pressures)}")
print(f"Loading range: {min(isotherm.loadings):.2f} - {max(isotherm.loadings):.2f} mol/kg")

# Save results
isotherm.save_json("isotherm.json")
isotherm.plot("isotherm.png")
```

## Workflow Scenarios

### Scenario A: Using Existing Force Fields
```python
# Request specifies force field
user_request = "CO2 adsorption in MFI using TraPPE force field at 300K"

# GlobalSupervisor automatically:
# 1. Skips Research Team
# 2. Directs to Setup Team
# 3. Uses existing TraPPE parameters
```

### Scenario B: Literature Extraction
```python
# Request includes paper reference
user_request = "CH4 adsorption in MOR using parameters from Garcia-Sanchez 2009"

# GlobalSupervisor automatically:
# 1. Activates Research Team
#    - PaperSearchAgent finds paper
#    - PaperExtractionAgent extracts parameters
#    - ForceFieldWriterAgent creates force_field.def
# 2. Passes to Setup Team
#    - StructureExpert prepares MOR.cif
#    - ForceFieldExpert integrates extracted parameters
#    - SimulationInputExpert creates simulation.input
#    - Evaluator validates all files
```

## Output Structure

```
output/
├── simulation.input          # Main RASPA input file
├── force_field.def          # Force field parameters
├── pseudo_atoms.def         # Atom type definitions
├── force_field_mixing_rules.def  # Mixing rules
├── MOR.cif                  # Structure file
├── Output/                  # RASPA output (after execution)
│   └── System_0/
│       ├── output_*.data    # Isotherm data
│       └── *.txt           # Log files
└── isotherm.json           # Parsed results (after parsing)
```

## Performance Metrics

| Workflow Component | Time | LLM Calls | Approx. Cost |
|-------------------|------|-----------|--------------|
| Research Team     | 30-60s | 3-5 | $0.15-0.25 |
| Setup Team        | 40-80s | 4-6 | $0.20-0.30 |
| **End-to-End**    | **70-140s** | **7-11** | **~$0.35-0.55** |
| RASPA Execution   | 60-600s | 0 | $0 |
| Result Parsing    | <1s | 0 | $0 |

## Troubleshooting

### RASPA Not Found
```python
# Manually specify RASPA path
import os
os.environ['RASPA_DIR'] = '/path/to/RASPA2'

# Or check installation
from gcmc_agent.tools.raspa_runner import RaspaRunner
runner = RaspaRunner()
print(runner.check_installation())
```

### Simulation Execution Failed
```python
# Check error details
result = runner.run("simulation.input")
if not result.success:
    print(f"Error: {result.error_message}")
    print(f"Stderr:\n{result.stderr}")
```

### Timeout Issues
```python
# Increase timeout for long simulations
result = runner.run("simulation.input", timeout=7200)  # 2 hours
```

### Result Parsing Failed
```python
# Validate output files exist
parser = ResultParser()
validation = parser.validate_output("/path/to/Output/System_0")
if not validation['valid']:
    print(f"Missing: {validation['missing_files']}")
```

## Integration Examples

### Batch Processing
```python
structures = ["MFI", "MOR", "FAU"]
molecules = ["CO2", "CH4", "N2"]

for structure in structures:
    for molecule in molecules:
        request = f"{molecule} adsorption in {structure} at 298K"
        result = supervisor.run(request, Path(f"output/{structure}_{molecule}"))
```

### With RASPA Execution
```python
# Full workflow with execution
result = supervisor.run(user_request, output_folder)

# Execute simulation
if result['success']:
    runner = RaspaRunner()
    exec_result = runner.run(output_folder / "simulation.input")
    
    # Parse results
    if exec_result.success:
        parser = ResultParser()
        isotherm = parser.parse_isotherm(exec_result.output_dir / "System_0")
        isotherm.plot(output_folder / "isotherm.png")
```

## Future Enhancements

1. **Multi-component isotherms**: Support gas mixtures
2. **Temperature series**: Automated temperature sweeps
3. **Web interface**: Graphical workflow builder
4. **Cluster integration**: Submit to HPC schedulers

## References

- Paper: arXiv:2509.10210v1
- RASPA Manual: https://github.com/iRASPA/RASPA2
- Project Documentation: `docs/`
