# Setup Team

The Setup Team generates complete RASPA simulation input files.

## Overview

The Setup Team transforms user requests or research data into ready-to-run RASPA simulations.

**Outputs**:
- CIF structure files
- Force field definitions  
- Simulation input files
- Batch execution scripts

## Agents

### StructureExpert

Handles molecular framework structures.

**Capabilities**:
- Search structure databases (CoRE MOF, IZA zeolites)
- Validate CIF files
- Transform coordinates
- Optimize unit cells

**Tools**:
- `find_cif_file(name)` - Database search
- `read_atoms_from_cif(path)` - CIF parser
- `get_unit_cell(path)` - Cell parameters
- `validate_structure(path)` - Structure validation

**Example**:
```python
from gcmc_agent.agents.structure import StructureExpert

agent = StructureExpert(llm_client)
result = agent.find_structure("ZIF-8")

# Result
{
    "cif_path": "structures/ZIF-8.cif",
    "formula": "C8H10N4Zn",
    "space_group": "I-43m",
    "cell": {
        "a": 16.991, "b": 16.991, "c": 16.991,
        "alpha": 90, "beta": 90, "gamma": 90
    }
}
```

### ForceFieldExpert

Generates force field files.

**Supported Force Fields**:
- TraPPE (transferable potentials)
- UFF (universal force field)
- DREIDING
- Custom parameters

**Generates**:
```python
# force_field.def
CH4  lennard-jones  148.0  3.73
CO2  lennard-jones  27.0   2.80
...

# pseudo_atoms.def
CH4  yes  C  12.0  0.0
CO2  yes  C  12.0  0.70
...

# force_field_mixing_rules.def  
Lorentz-Berthelot
```

**Example**:
```python
from gcmc_agent.agents.forcefield import ForceFieldExpert

agent = ForceFieldExpert(llm_client)
result = agent.create_forcefield(
    molecule="CO2",
    framework="ZIF-8",
    method="TraPPE"
)

# Generated files
{
    "force_field": "force_field.def",
    "pseudo_atoms": "pseudo_atoms.def",
    "mixing_rules": "force_field_mixing_rules.def"
}
```

### SimulationInputExpert

Creates RASPA simulation.input files.

**Supported Simulation Types**:
- `MonteCarlo` - GCMC adsorption isotherms
- `MolecularDynamics` - MD simulations
- `Minimization` - Energy minimization

**Key Parameters**:
```python
simulation_config = {
    "type": "MonteCarlo",
    "cycles": 10000,
    "initialization_cycles": 5000,
    "temperature": 298,  # K
    "pressure": 1e5,     # Pa
    "molecules": ["CO2"],
    "framework": "ZIF-8"
}
```

**Generated File**:
```
SimulationType                MonteCarlo
NumberOfCycles                10000
NumberOfInitializationCycles  5000
PrintEvery                    1000
RestartFile                   no

Framework 0
FrameworkName                 ZIF-8
UnitCells                     1 1 1

Component 0 MoleculeName      CO2
            MoleculeDefinition TraPPE
            TranslationProbability   1.0
            RotationProbability      1.0
            ReinsertionProbability   1.0
            SwapProbability          2.0
            CreateNumberOfMolecules  0
```

### CodingExpert

Generates batch simulation scripts.

**Capabilities**:
- Pressure sweeps
- Temperature sweeps
- Multi-component mixtures
- Parallel execution

**Example**:
```python
from gcmc_agent.agents.coding import CodingExpert

agent = CodingExpert(llm_client)
script = agent.generate_batch_script(
    template_dir="templates/",
    pressures=[1e4, 5e4, 1e5, 5e5, 1e6],
    temperatures=[273, 298, 323]
)
```

**Generated Script** (`run_isotherm.py`):
```python
#!/usr/bin/env python3
import subprocess
from pathlib import Path

pressures = [1e4, 5e4, 1e5, 5e5, 1e6]
template = Path("template/simulation.input")

for p in pressures:
    run_dir = Path(f"run_{p:.0e}")
    run_dir.mkdir(exist_ok=True)
    
    # Modify pressure in simulation.input
    input_text = template.read_text()
    input_text = input_text.replace("__PRESSURE__", str(p))
    
    # Run simulation
    subprocess.run(["simulate", "simulation.input"], cwd=run_dir)
```

### Evaluator

Validates all generated files.

**Checks**:
- File existence
- Syntax correctness
- Parameter consistency
- RASPA compatibility

**Example**:
```python
from gcmc_agent.agents.evaluator import Evaluator

evaluator = Evaluator(llm_client)
result = evaluator.validate_setup(workspace_dir)

# Result
{
    "valid": True,
    "issues": [],
    "files": {
        "structure": "ZIF-8.cif",
        "force_field": "force_field.def",
        "simulation": "simulation.input"
    }
}
```

## Complete Workflow

### Example: CO2 Adsorption Isotherm

```python
from gcmc_agent import GlobalSupervisor

supervisor = GlobalSupervisor(llm_client)

request = """
Set up CO2 adsorption isotherm in ZIF-8:
- Temperature: 298K
- Pressure range: 0.1 to 10 bar (5 points)
- Use TraPPE force field
- 10,000 MC cycles
"""

result = supervisor.run(request, output_folder=Path("output"))

# Generated files in output/:
# ├── ZIF-8.cif
# ├── force_field.def
# ├── pseudo_atoms.def
# ├── force_field_mixing_rules.def
# ├── simulation.input
# └── run_isotherm.py
```

## Advanced Features

### Multi-Component Mixtures

```python
request = """
Binary mixture: 15% CO2, 85% N2 in MOF-5
Temperature: 298K, Pressure: 1 bar
"""
```

Generates configuration for both components with correct mole fractions.

### Custom Force Fields

```python
request = """
Use custom LJ parameters:
- CO2 C: σ=2.80Å, ε/k=27K, q=+0.70
- CO2 O: σ=3.05Å, ε/k=79K, q=-0.35
"""
```

Creates force field file from user-specified parameters.

### Temperature/Pressure Sweeps

```python
request = """
Temperature sweep: 273, 298, 323, 348K
Pressure sweep: 0.1, 1, 10, 100 bar
Generate batch script
"""
```

Creates 4×4 = 16 simulation directories with batch execution script.

## Integration with Research Team

Setup Team can use Research Team outputs:

```python
# Research extracts parameters
research_result = research_team.extract_from_paper("Dubbeldam 2007")

# Setup uses them
setup_result = setup_team.generate_files(
    structure="ZIF-8",
    force_field_data=research_result["force_field"],
    conditions=research_result["simulation"]
)
```

## Best Practices

1. **Start simple**: Single component, single condition first
2. **Validate parameters**: Check force field ranges
3. **Test small**: Run short simulations first (1000 cycles)
4. **Scale up**: Increase cycles for production runs (100k+)
5. **Parallelize**: Use batch scripts for parameter sweeps

## Common Issues

### Structure Not Found
```
Error: ZIF-8 structure not found

Solution: 
- Check structure name spelling
- Provide custom CIF file
- Search alternative databases
```

### Force Field Mismatch
```
Error: TraPPE not available for CH4 in ZIF-8

Solution:
- Use UFF (more general)
- Provide custom parameters
- Check literature for appropriate FF
```

### Simulation Won't Converge
```
Warning: Equilibration not reached

Solution:
- Increase initialization cycles
- Check temperature (too high?)
- Verify force field parameters
```

## See Also

- [Research Team](research-team.md) - Extracting parameters
- [RASPA Integration](raspa-integration.md) - Running simulations
- [API Reference](../api/setup-agents.md) - Detailed API
