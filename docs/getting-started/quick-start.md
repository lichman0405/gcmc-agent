# Quick Start

This guide will walk you through running your first molecular simulation with GCMC-Agent.

## Basic Usage

### 1. Import and Initialize

```python
from gcmc_agent import GlobalSupervisor

# Initialize the supervisor
supervisor = GlobalSupervisor()
```

### 2. Run a Simple Simulation

```python
# Request a simulation with existing force field
request = """
Run a CO2 adsorption simulation in ZIF-8 at 298K and 1 bar.
Use TraPPE force field for CO2.
Run 10,000 cycles.
"""

result = supervisor.process_request(request)
print(f"Status: {result['status']}")
print(f"Isotherm data: {result['isotherm']}")
```

### 3. View Results

The supervisor returns structured results:
```python
{
    "status": "success",
    "isotherm": {
        "temperature": 298.0,
        "pressures": [1.0],
        "loadings": [2.5],
        "loading_error": [0.1],
        "unit": "mol/kg"
    },
    "files": {
        "structure": "path/to/ZIF-8.cif",
        "forcefield": "path/to/force_field.def",
        "simulation": "path/to/simulation.input"
    }
}
```

## Complete Example

Here's a complete example that demonstrates the full pipeline:

```python
from gcmc_agent import GlobalSupervisor
from pathlib import Path

# Initialize supervisor
supervisor = GlobalSupervisor(
    workspace=Path("./workspace"),
    verbose=True
)

# Request simulation with literature extraction
request = """
Extract CO2 adsorption data from the paper by Dubbeldam et al. (2007).
Then set up and run the simulation to reproduce their results.
"""

# Process request
print("Processing request...")
result = supervisor.process_request(request)

# Check status
if result["status"] == "success":
    print("✓ Simulation completed successfully!")
    
    # Display results
    isotherm = result["isotherm"]
    print(f"\nResults at {isotherm['temperature']} K:")
    for p, loading, error in zip(
        isotherm["pressures"],
        isotherm["loadings"],
        isotherm["loading_error"]
    ):
        print(f"  {p:.1f} bar: {loading:.2f} ± {error:.2f} {isotherm['unit']}")
    
    # Compare with literature
    if "literature_data" in result:
        lit_data = result["literature_data"]
        print(f"\nLiterature values:")
        for p, loading in zip(lit_data["pressures"], lit_data["loadings"]):
            print(f"  {p:.1f} bar: {loading:.2f} {lit_data['unit']}")
else:
    print(f"✗ Simulation failed: {result.get('error', 'Unknown error')}")
```

## Advanced Usage

### Custom Configuration

```python
from gcmc_agent import GlobalSupervisor
from gcmc_agent.config import Config

# Create custom configuration
config = Config(
    llm_model="gpt-4",
    max_iterations=50,
    raspa_path="/custom/path/to/raspa",
    template_dir="/custom/templates"
)

supervisor = GlobalSupervisor(config=config)
```

### Multi-Component Systems

```python
request = """
Set up a binary mixture simulation:
- Components: CO2 and N2
- Mole fraction: 0.15 CO2, 0.85 N2
- Framework: MOF-5
- Temperature: 298K
- Pressure range: 1 to 100 bar (5 points)
- Force fields: TraPPE for both gases
"""

result = supervisor.process_request(request)
```

### Custom Force Fields

```python
request = """
Create a new force field for methane with the following parameters:
- Lennard-Jones epsilon: 148.0 K
- Lennard-Jones sigma: 3.73 Å
- Partial charges: none (neutral molecule)

Then run adsorption simulation in IRMOF-1 at 298K.
"""

result = supervisor.process_request(request)
```

## Using Individual Agents

You can also use individual agent teams directly:

### Research Team

```python
from gcmc_agent.research import ExtractionAgent

# Extract data from literature
agent = ExtractionAgent()
paper_data = agent.extract_from_paper(
    paper_id="arxiv:1234.5678",
    target="CO2 adsorption in ZIF-8"
)
```

### Setup Team

```python
from gcmc_agent.agents.forcefield import ForceFieldAgent
from gcmc_agent.agents.structure import StructureAgent

# Get structure
structure_agent = StructureAgent()
cif_file = structure_agent.get_structure("ZIF-8")

# Create force field
ff_agent = ForceFieldAgent()
ff_files = ff_agent.create_forcefield(
    molecule="CO2",
    framework="ZIF-8",
    method="TraPPE"
)
```

## Command Line Interface

GCMC-Agent also provides a CLI:

```bash
# Run simulation from command line
gcmc-agent simulate \
  --molecule CO2 \
  --framework ZIF-8 \
  --temperature 298 \
  --pressure 1 \
  --cycles 10000

# Extract data from literature
gcmc-agent extract \
  --paper "Dubbeldam 2007" \
  --target "CO2 adsorption"

# Run complete pipeline
gcmc-agent run \
  --request "Reproduce CO2 adsorption in ZIF-8 from Dubbeldam 2007"
```

## Next Steps

- [Configuration Guide](configuration.md) - Customize GCMC-Agent settings
- [Architecture Overview](../user-guide/architecture.md) - Understand the multi-agent system
- [Research Team Guide](../user-guide/research-team.md) - Learn about literature extraction
- [Setup Team Guide](../user-guide/setup-team.md) - Deep dive into simulation setup
- [API Reference](../api/global-supervisor.md) - Complete API documentation

## Example Scripts

See the `scripts/` directory for more examples:

- `quick_start.py` - Basic demonstration
- `research_pipeline_demo.py` - Complete literature extraction pipeline
- `view_logs.py` - Inspect agent logs and decision-making process
