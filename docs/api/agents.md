# Agents API

GCMC-Agent includes specialized agents for different workflow tasks.

## Research Agents

### PaperSearchAgent

Search academic literature for relevant papers.

```python
from gcmc_agent.research import PaperSearchAgent
from gcmc_agent.client import OpenAIChatClient

client = OpenAIChatClient(config)
agent = PaperSearchAgent(client)

papers = agent.search(
    query="TraPPE force field CO2 zeolites",
    max_results=10
)
```

**Returns**:
```python
[
    {
        "title": "Molecular Simulation of Adsorption...",
        "authors": "Dubbeldam et al.",
        "year": 2007,
        "citations": 342,
        "pdf_url": "https://...",
        "abstract": "..."
    },
    ...
]
```

### ExtractionAgent

Extract simulation parameters from scientific papers.

```python
from gcmc_agent.research import ExtractionAgent

agent = ExtractionAgent(client)

data = agent.extract(
    paper_text="...",  # or pdf_path
    target_molecule="CO2",
    target_framework="ZIF-8"
)
```

**Returns**:
```python
{
    "molecule": "CO2",
    "framework": "ZIF-8",
    "force_field": {
        "type": "TraPPE",
        "parameters": {
            "C_co2": {"sigma": 2.80, "epsilon": 27.0, "charge": 0.70},
            "O_co2": {"sigma": 3.05, "epsilon": 79.0, "charge": -0.35}
        }
    },
    "simulation": {
        "temperature": 298,
        "pressure": 1e5,
        "cycles": 10000
    }
}
```

### ForceFieldWriterAgent

Convert extracted parameters to RASPA format.

```python
from gcmc_agent.research import ForceFieldWriterAgent

agent = ForceFieldWriterAgent(client)

files = agent.write_forcefield(
    parameters=extracted_data["force_field"],
    output_dir=Path("output")
)
```

**Generates**:
- `force_field.def`
- `pseudo_atoms.def`
- `force_field_mixing_rules.def`

## Setup Agents

### StructureExpert

Handle molecular framework structures.

```python
from gcmc_agent.agents.structure import StructureExpert

agent = StructureExpert(client)

# Find structure
result = agent.find_structure(
    name="ZIF-8",
    database="CoRE-MOF"  # or "IZA-zeolites"
)
```

**Returns**:
```python
{
    "cif_path": Path("structures/ZIF-8.cif"),
    "formula": "C8H10N4Zn",
    "space_group": "I-43m",
    "cell_parameters": {
        "a": 16.991, "b": 16.991, "c": 16.991,
        "alpha": 90, "beta": 90, "gamma": 90
    }
}
```

**Methods**:

#### `find_structure()`
```python
def find_structure(
    name: str,
    database: str = "auto"
) -> Dict[str, Any]
```

#### `validate_cif()`
```python
def validate_cif(
    cif_path: Path
) -> bool
```

#### `get_atoms()`
```python
def get_atoms(
    cif_path: Path
) -> List[Dict[str, Any]]
```

### ForceFieldExpert

Generate force field files.

```python
from gcmc_agent.agents.forcefield import ForceFieldExpert

agent = ForceFieldExpert(client)

result = agent.create_forcefield(
    molecule="CO2",
    framework="ZIF-8",
    method="TraPPE"  # or "UFF", "DREIDING", "custom"
)
```

**Methods**:

#### `create_forcefield()`
```python
def create_forcefield(
    molecule: str,
    framework: str,
    method: str = "TraPPE",
    custom_params: dict = None
) -> Dict[str, Path]
```

#### `validate_forcefield()`
```python
def validate_forcefield(
    ff_path: Path
) -> Tuple[bool, List[str]]
```

### SimulationInputExpert

Create RASPA simulation.input files.

```python
from gcmc_agent.agents.simulation_input import SimulationInputExpert

agent = SimulationInputExpert(client)

result = agent.create_input(
    framework="ZIF-8",
    molecule="CO2",
    temperature=298,
    pressure=1e5,
    cycles=10000
)
```

**Methods**:

#### `create_input()`
```python
def create_input(
    framework: str,
    molecule: str,
    temperature: float,
    pressure: float,
    cycles: int = 10000,
    simulation_type: str = "MonteCarlo"
) -> Path
```

#### `create_isotherm_input()`
```python
def create_isotherm_input(
    framework: str,
    molecule: str,
    temperature: float,
    pressures: List[float],
    cycles: int = 10000
) -> List[Path]
```

### CodingExpert

Generate batch simulation scripts.

```python
from gcmc_agent.agents.coding import CodingExpert

agent = CodingExpert(client)

script = agent.generate_batch_script(
    template_dir=Path("template"),
    pressures=[1e4, 1e5, 1e6],
    temperatures=[273, 298, 323]
)
```

**Methods**:

#### `generate_batch_script()`
```python
def generate_batch_script(
    template_dir: Path,
    pressures: List[float] = None,
    temperatures: List[float] = None,
    molecules: List[str] = None
) -> Path
```

#### `generate_analysis_script()`
```python
def generate_analysis_script(
    results_dir: Path,
    output_file: Path = Path("analysis.py")
) -> Path
```

### Evaluator

Validate generated simulation files.

```python
from gcmc_agent.agents.evaluator import Evaluator

agent = Evaluator(client)

result = agent.validate_setup(
    workspace_dir=Path("simulation")
)
```

**Returns**:
```python
{
    "valid": True,
    "issues": [],
    "files": {
        "structure": "ZIF-8.cif",
        "force_field": "force_field.def",
        "simulation": "simulation.input"
    },
    "warnings": [
        "Consider increasing cycles for better statistics"
    ]
}
```

**Methods**:

#### `validate_setup()`
```python
def validate_setup(
    workspace_dir: Path
) -> Dict[str, Any]
```

#### `check_consistency()`
```python
def check_consistency(
    force_field: Path,
    simulation_input: Path
) -> List[str]
```

## Base Agent Classes

### ReactAgent

Base class for all agents using ReAct pattern.

```python
from gcmc_agent.react.base import ReactAgent

class CustomAgent(ReactAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.register_tool("custom_tool", self.custom_fn)
    
    def custom_fn(self, input: str) -> str:
        """Custom tool implementation"""
        return result
```

**Methods**:

#### `register_tool()`
```python
def register_tool(
    name: str,
    function: Callable
) -> None
```

#### `run()`
```python
def run(
    task: str,
    max_iterations: int = 10
) -> Dict[str, Any]
```

## Complete Example

### Custom Workflow with Multiple Agents

```python
from gcmc_agent import GlobalSupervisor
from gcmc_agent.agents.structure import StructureExpert
from gcmc_agent.agents.forcefield import ForceFieldExpert
from gcmc_agent.agents.simulation_input import SimulationInputExpert
from gcmc_agent.agents.evaluator import Evaluator
from pathlib import Path

# Initialize agents
supervisor = GlobalSupervisor()
structure_agent = StructureExpert(supervisor.llm_client)
ff_agent = ForceFieldExpert(supervisor.llm_client)
input_agent = SimulationInputExpert(supervisor.llm_client)
evaluator = Evaluator(supervisor.llm_client)

# Step 1: Get structure
struct_result = structure_agent.find_structure("ZIF-8")
print(f"Structure: {struct_result['cif_path']}")

# Step 2: Create force field
ff_result = ff_agent.create_forcefield(
    molecule="CO2",
    framework="ZIF-8",
    method="TraPPE"
)
print(f"Force field: {ff_result['force_field']}")

# Step 3: Create simulation input
input_result = input_agent.create_isotherm_input(
    framework="ZIF-8",
    molecule="CO2",
    temperature=298,
    pressures=[1e4, 5e4, 1e5, 5e5, 1e6],
    cycles=10000
)
print(f"Created {len(input_result)} input files")

# Step 4: Validate
validation = evaluator.validate_setup(Path("simulation"))
if validation["valid"]:
    print("✓ Setup validated")
else:
    print("Issues found:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
```

## See Also

- [Architecture Overview](../user-guide/architecture.md)
- [Research Team Guide](../user-guide/research-team.md)
- [Setup Team Guide](../user-guide/setup-team.md)
- [GlobalSupervisor API](global-supervisor.md)
