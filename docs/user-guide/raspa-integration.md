# RASPA Integration

GCMC-Agent integrates with RASPA for molecular simulation execution and result parsing.

## Overview

RASPA (Rapid Simulation Package for Adsorption) is a molecular simulation code for computing adsorption and diffusion in nanoporous materials.

GCMC-Agent provides:
- Automatic RASPA installation detection
- Input file generation
- Simulation execution and monitoring
- Output parsing and visualization

## RASPA Installation

### Linux

```bash
# Install dependencies
sudo apt-get install build-essential gfortran cmake

# Download RASPA2
git clone https://github.com/iRASPA/RASPA2.git
cd RASPA2

# Build and install
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### macOS

```bash
# Install with Homebrew
brew install cmake gfortran

# Download and build
git clone https://github.com/iRASPA/RASPA2.git
cd RASPA2
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### Verify Installation

```bash
simulate --version
# or just run:
which simulate
```

## RaspaRunner

The `RaspaRunner` class handles RASPA execution.

### Basic Usage

```python
from gcmc_agent.tools.raspa_runner import RaspaRunner
from pathlib import Path

# Initialize runner
runner = RaspaRunner(
    raspa_executable=Path("/usr/local/bin/simulate"),
    verbose=True
)

# Check installation
if runner.check_installation():
    print("✓ RASPA found and ready")

# Run simulation
result = runner.run(
    simulation_dir=Path("./simulation"),
    input_file="simulation.input"
)

# Check results
if result.success:
    print(f"Simulation completed in {result.execution_time:.1f}s")
    print(f"Output files: {result.output_files}")
else:
    print(f"Error: {result.error_message}")
```

### RaspaResult Object

```python
@dataclass
class RaspaResult:
    success: bool              # Did simulation complete?
    output_dir: Path           # Where are outputs?
    stdout: str                # Standard output
    stderr: str                # Error output
    execution_time: float      # Runtime in seconds
    error_message: str         # Error details
    output_files: List[Path]   # Generated files
```

### Validation

Validate setup before running:

```python
validation = runner.validate_setup(simulation_dir)

if not validation["valid"]:
    print("Issues found:")
    for issue in validation["issues"]:
        print(f"  - {issue}")
else:
    print("✓ Setup is valid")
    print(f"CIF files: {validation['cif_files']}")
```

## ResultParser

Parse RASPA output and extract isotherm data.

### Basic Parsing

```python
from gcmc_agent.tools.result_parser import ResultParser

parser = ResultParser()

# Parse simulation output
isotherm = parser.parse_isotherm(
    output_dir=Path("Output/System_0"),
    component="CO2"
)

# Access data
print(f"Temperature: {isotherm.temperature} K")
print(f"Pressures: {isotherm.pressures}")
print(f"Loadings: {isotherm.loadings} {isotherm.unit}")
```

### IsothermData Object

```python
@dataclass
class IsothermData:
    temperature: float           # K
    pressures: List[float]       # Pa
    loadings: List[float]        # mol/kg or mol/uc
    loading_error: List[float]   # Uncertainties
    unit: str                    # "mol/kg" or "mol/uc"
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        
    def save_json(self, path: Path):
        """Save to JSON file"""
    
    def plot(self, save_path: Path):
        """Generate isotherm plot"""
```

### Visualization

```python
# Generate plot
isotherm.plot("isotherm.png")

# Or customize:
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
plt.errorbar(
    isotherm.pressures,
    isotherm.loadings,
    yerr=isotherm.loading_error,
    marker='o', capsize=5
)
plt.xlabel("Pressure (Pa)")
plt.ylabel(f"Loading ({isotherm.unit})")
plt.title(f"CO2 Adsorption at {isotherm.temperature} K")
plt.tight_layout()
plt.savefig("custom_plot.png", dpi=300)
```

## Complete Workflow

### From Setup to Results

```python
from gcmc_agent import GlobalSupervisor
from gcmc_agent.tools.raspa_runner import RaspaRunner
from gcmc_agent.tools.result_parser import ResultParser
from pathlib import Path

# 1. Generate simulation files
supervisor = GlobalSupervisor()
setup_result = supervisor.run(
    user_request="Setup CO2 in ZIF-8 at 298K, 1-10 bar",
    output_folder=Path("setup")
)

# 2. Run RASPA
runner = RaspaRunner()
raspa_result = runner.run(Path("setup/template"))

# 3. Parse results
if raspa_result.success:
    parser = ResultParser()
    isotherm = parser.parse_isotherm(
        raspa_result.output_dir / "System_0"
    )
    
    # 4. Visualize
    isotherm.plot("isotherm.png")
    isotherm.save_json("results.json")
```

## Advanced Features

### Parallel Execution

Run multiple simulations in parallel:

```python
from concurrent.futures import ProcessPoolExecutor

def run_single(sim_dir):
    runner = RaspaRunner()
    return runner.run(sim_dir)

simulation_dirs = [
    Path("run_1bar"),
    Path("run_5bar"),
    Path("run_10bar")
]

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(run_single, simulation_dirs))
```

### Progress Monitoring

Monitor long-running simulations:

```python
import time

result = runner.run(
    simulation_dir=Path("long_run"),
    input_file="simulation.input"
)

# For background execution, use subprocess directly:
import subprocess

process = subprocess.Popen(
    ["simulate", "simulation.input"],
    cwd="long_run",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

while process.poll() is None:
    # Check progress
    time.sleep(10)
    print("Still running...")

stdout, stderr = process.communicate()
```

### Error Recovery

Handle common RASPA errors:

```python
result = runner.run(simulation_dir)

if not result.success:
    if "segmentation fault" in result.stderr.lower():
        print("RASPA crashed - check force field parameters")
    elif "cannot open" in result.stderr.lower():
        print("File not found - check paths")
    elif "convergence" in result.stderr.lower():
        print("Simulation didn't converge - increase cycles")
```

## Output File Structure

RASPA generates:

```
Output/
└── System_0/
    ├── output_*.data         # Thermodynamic data
    ├── Framework_0_*.cif     # Framework structure
    ├── Movies/               # Trajectory files
    │   └── Movie_*.pdb
    ├── Restart/              # Restart files
    │   └── restart_*.dat
    └── VTK/                  # Visualization files
```

## Performance Tips

1. **Use multiple cores**: Set `NumberOfThreads` in simulation.input
2. **Optimize cycles**: Start small (1k), scale to 100k+ for production
3. **Use restart files**: Continue crashed simulations
4. **Monitor memory**: Large systems need more RAM
5. **Batch small jobs**: Better than few large jobs

## Troubleshooting

### RASPA Not Found

```bash
# Add to PATH
export PATH=/path/to/raspa/bin:$PATH

# Or specify in code
runner = RaspaRunner(
    raspa_executable=Path("/custom/path/to/simulate")
)
```

### Simulation Fails

Check validation first:

```python
issues = runner.validate_setup(sim_dir)
if issues["issues"]:
    for issue in issues["issues"]:
        print(f"Fix: {issue}")
```

### Parsing Errors

```python
try:
    isotherm = parser.parse_isotherm(output_dir)
except FileNotFoundError:
    print("Output files missing - simulation may have failed")
except ValueError as e:
    print(f"Data parsing error: {e}")
```

## See Also

- [RASPA Documentation](https://iraspa.org/raspa/)
- [Setup Team Guide](setup-team.md)
- [API: RaspaRunner](../api/tools.md#rasparunner)
- [API: ResultParser](../api/tools.md#resultparser)
