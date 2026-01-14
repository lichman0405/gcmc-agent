# Tools API

GCMC-Agent provides specialized tools for RASPA simulation and result processing.

## RaspaRunner

Execute RASPA simulations.

### Class Definition

```python
from gcmc_agent.tools.raspa_runner import RaspaRunner
from pathlib import Path

runner = RaspaRunner(
    raspa_executable: Path = None,
    verbose: bool = False
)
```

### Methods

#### `check_installation()`

Verify RASPA is installed and accessible.

```python
def check_installation() -> bool
```

**Example**:
```python
runner = RaspaRunner()
if runner.check_installation():
    print("✓ RASPA ready")
else:
    print("✗ RASPA not found")
```

#### `run()`

Execute a RASPA simulation.

```python
def run(
    simulation_dir: Path,
    input_file: str = "simulation.input",
    timeout: int = 3600
) -> RaspaResult
```

**Parameters**:
- `simulation_dir`: Directory containing simulation files
- `input_file`: Name of input file
- `timeout`: Maximum runtime in seconds

**Returns**: `RaspaResult` object

```python
result = runner.run(
    simulation_dir=Path("./run_1bar"),
    timeout=1800  # 30 minutes
)

if result.success:
    print(f"Completed in {result.execution_time:.1f}s")
else:
    print(f"Error: {result.error_message}")
```

#### `validate_setup()`

Check if simulation directory has all required files.

```python
def validate_setup(
    simulation_dir: Path
) -> Dict[str, Any]
```

**Returns**:
```python
{
    "valid": True,
    "issues": [],
    "cif_files": ["ZIF-8.cif"],
    "force_field_files": ["force_field.def"],
    "input_file": "simulation.input"
}
```

**Example**:
```python
validation = runner.validate_setup(Path("./simulation"))

if not validation["valid"]:
    for issue in validation["issues"]:
        print(f"Issue: {issue}")
```

### RaspaResult

Dataclass containing simulation results.

```python
@dataclass
class RaspaResult:
    success: bool
    output_dir: Path
    stdout: str
    stderr: str
    execution_time: float
    error_message: str
    output_files: List[Path]
```

**Attributes**:
- `success`: Whether simulation completed without errors
- `output_dir`: Path to output directory
- `stdout`: Standard output from RASPA
- `stderr`: Error output from RASPA
- `execution_time`: Runtime in seconds
- `error_message`: Error description (if failed)
- `output_files`: List of generated output files

## ResultParser

Parse RASPA output files and extract data.

### Class Definition

```python
from gcmc_agent.tools.result_parser import ResultParser

parser = ResultParser()
```

### Methods

#### `parse_isotherm()`

Extract adsorption isotherm data.

```python
def parse_isotherm(
    output_dir: Path,
    component: str = "CO2"
) -> IsothermData
```

**Parameters**:
- `output_dir`: RASPA output directory (e.g., `Output/System_0`)
- `component`: Molecule name

**Returns**: `IsothermData` object

**Example**:
```python
parser = ResultParser()
isotherm = parser.parse_isotherm(
    output_dir=Path("Output/System_0"),
    component="CO2"
)

print(f"Temperature: {isotherm.temperature} K")
print(f"Pressures: {isotherm.pressures}")
print(f"Loadings: {isotherm.loadings}")
```

#### `parse_output_file()`

Parse a specific RASPA output file.

```python
def parse_output_file(
    file_path: Path
) -> Dict[str, Any]
```

**Returns**: Dictionary with extracted data

```python
data = parser.parse_output_file(
    Path("Output/System_0/output_ZIF-8_298.000000_1000000.data")
)
```

#### `extract_final_loading()`

Get final loading from output.

```python
def extract_final_loading(
    output_dir: Path,
    component: str
) -> Tuple[float, float]
```

**Returns**: `(loading, error)` tuple

```python
loading, error = parser.extract_final_loading(
    Path("Output/System_0"),
    component="CO2"
)
print(f"Loading: {loading} ± {error} mol/kg")
```

### IsothermData

Dataclass containing isotherm data.

```python
@dataclass
class IsothermData:
    temperature: float
    pressures: List[float]
    loadings: List[float]
    loading_error: List[float]
    unit: str
```

**Methods**:

##### `to_dict()`

Convert to dictionary.

```python
def to_dict() -> dict
```

```python
data = isotherm.to_dict()
# {'temperature': 298, 'pressures': [...], ...}
```

##### `save_json()`

Save to JSON file.

```python
def save_json(path: Path) -> None
```

```python
isotherm.save_json(Path("results.json"))
```

##### `plot()`

Generate isotherm plot.

```python
def plot(
    save_path: Path,
    title: str = None,
    xlabel: str = None,
    ylabel: str = None
) -> None
```

```python
isotherm.plot(
    save_path=Path("isotherm.png"),
    title="CO2 Adsorption in ZIF-8",
    xlabel="Pressure (bar)",
    ylabel="Loading (mol/kg)"
)
```

## File Utilities

### CIF Tools

Read and manipulate CIF structure files.

```python
from gcmc_agent.tools.cif_utils import (
    read_cif,
    get_unit_cell,
    validate_cif
)

# Read CIF
atoms = read_cif(Path("ZIF-8.cif"))

# Get cell parameters
cell = get_unit_cell(Path("ZIF-8.cif"))
# {'a': 16.991, 'b': 16.991, 'c': 16.991, ...}

# Validate
is_valid = validate_cif(Path("structure.cif"))
```

### Force Field Tools

```python
from gcmc_agent.tools.forcefield_utils import (
    parse_forcefield,
    validate_parameters,
    write_forcefield
)

# Parse existing force field
params = parse_forcefield(Path("force_field.def"))

# Validate parameters
is_valid = validate_parameters(params)

# Write new force field
write_forcefield(
    path=Path("new_ff.def"),
    parameters=params
)
```

## Complete Example

### Run Simulation and Plot Results

```python
from gcmc_agent.tools.raspa_runner import RaspaRunner
from gcmc_agent.tools.result_parser import ResultParser
from pathlib import Path

# Initialize tools
runner = RaspaRunner(
    raspa_executable=Path("/usr/local/bin/simulate"),
    verbose=True
)
parser = ResultParser()

# Validate setup
simulation_dir = Path("simulation")
validation = runner.validate_setup(simulation_dir)

if not validation["valid"]:
    print("Setup issues found:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
    exit(1)

# Run simulation
print("Running RASPA simulation...")
result = runner.run(simulation_dir, timeout=1800)

if not result.success:
    print(f"Simulation failed: {result.error_message}")
    exit(1)

print(f"✓ Completed in {result.execution_time:.1f}s")

# Parse results
output_dir = result.output_dir / "System_0"
isotherm = parser.parse_isotherm(output_dir, component="CO2")

# Save and visualize
isotherm.save_json(Path("isotherm.json"))
isotherm.plot(
    save_path=Path("isotherm.png"),
    title=f"CO2 Adsorption at {isotherm.temperature}K"
)

print(f"Results saved to isotherm.json and isotherm.png")
```

## Error Handling

```python
from gcmc_agent.tools.raspa_runner import RaspaRunner
from gcmc_agent.tools.result_parser import ResultParser

runner = RaspaRunner()
parser = ResultParser()

try:
    result = runner.run(Path("simulation"))
    
    if result.success:
        isotherm = parser.parse_isotherm(
            result.output_dir / "System_0"
        )
    else:
        print(f"Simulation error: {result.error_message}")
        
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Parsing error: {e}")
except TimeoutError:
    print("Simulation timeout")
```

## See Also

- [RASPA Integration Guide](../user-guide/raspa-integration.md)
- [GlobalSupervisor API](global-supervisor.md)
- [Agents API](agents.md)
