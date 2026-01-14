# GlobalSupervisor API

The `GlobalSupervisor` is the main entry point for GCMC-Agent's end-to-end workflow.

It coordinates 4 phases:
1. **Research Team**: Search papers, extract force field parameters
2. **Setup Team**: Prepare structure, force field, simulation.input
3. **Simulator**: Execute RASPA simulations
4. **Result Parser**: Extract isotherm data

## Class Definition

```python
from gcmc_agent.global_supervisor import GlobalSupervisor
from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from pathlib import Path

config = DeepSeekConfig.from_env()
client = OpenAIChatClient(config)

supervisor = GlobalSupervisor(
    llm_client=client,
    workspace_root=Path("./workspace"),
    model="deepseek-chat",
    verbose=False
)
```

## Constructor Parameters

### `llm_client`
- **Type**: `OpenAIChatClient`
- **Required**: Yes
- **Description**: LLM client for agent communication

```python
from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient

config = DeepSeekConfig.from_env()  # Uses DEEPSEEK_API_KEY
client = OpenAIChatClient(config)
supervisor = GlobalSupervisor(llm_client=client, ...)
```

### `workspace_root`
- **Type**: `Path`
- **Required**: Yes
- **Description**: Project root directory containing templates, structures, etc.

### `model`
- **Type**: `str`
- **Default**: `"deepseek-chat"`
- **Description**: Model name for LLM calls

### `verbose`
- **Type**: `bool`
- **Default**: `False`
- **Description**: Enable detailed output showing agent reasoning

### `log_file`
- **Type**: `Path` or `None`
- **Default**: `None`
- **Description**: Optional log file path for supervisor logs

## Main Methods

### `run()`

Execute the complete 4-phase workflow from user request to results.

```python
def run(
    user_request: str,
    output_folder: Path,
    paper_text: Optional[str] = None,
    paper_doi: Optional[str] = None
) -> AgentResult
```

**Parameters**:
- `user_request` (str): Natural language description of task (e.g., "Set up CO2 isotherm in MOR using Garcia-Sanchez 2009 force field")
- `output_folder` (Path): Directory for output files
- `paper_text` (str, optional): Explicit paper text for extraction
- `paper_doi` (str, optional): Explicit DOI for paper lookup

**Note**: If `paper_text` and `paper_doi` are not provided, GlobalSupervisor will analyze the user_request to detect paper references (e.g., "Garcia-Sanchez 2009") and automatically search Semantic Scholar.

**Returns**: `AgentResult` object

```python
result.success    # bool: True if workflow completed
result.answer     # str: Summary of workflow execution
result.error      # str or None: Error message if failed
```

**Example Output** (result.answer):
```
=== Global Supervisor - Workflow Complete ===

Output Directory: /path/to/output

Phases Executed:
  ✅ Research Team: Force field extracted from literature
  ✅ Setup Team: Simulation files generated
  ✅ Simulator: 7/7 simulations completed
  ✅ Result Parser: 7 isotherm(s) extracted

✅ End-to-end workflow completed!
```

**Example**:
```python
from gcmc_agent import GlobalSupervisor
from pathlib import Path

supervisor = GlobalSupervisor()

result = supervisor.run(
    user_request="Setup CO2 adsorption in ZIF-8 at 298K",
    output_folder=Path("output")
)

if result["status"] == "success":
    print(f"Generated files: {result['files']}")
```

### `process_request()`

Process request without running simulation.

```python
def process_request(
    request: str
) -> Dict[str, Any]
```

**Use case**: Generate files only, don't execute

```python
result = supervisor.process_request(
    "Create force field for CO2 using TraPPE"
)
# Returns parameter data without running RASPA
```

## State Management

### `get_state()`

Get current workflow state.

```python
def get_state() -> WorkflowState
```

**Returns**:
```python
@dataclass
class WorkflowState:
    request: str
    research_data: dict
    setup_files: dict
    simulation_results: dict
    status: str
    errors: List[str]
```

### `reset()`

Reset supervisor to initial state.

```python
def reset() -> None
```

## Team Access

### `research_team`

Access Research Team for literature extraction.

```python
research_result = supervisor.research_team.extract_from_paper(
    paper_query="Dubbeldam 2007 CO2 TraPPE"
)
```

### `setup_team`

Access Setup Team for file generation.

```python
setup_result = supervisor.setup_team.generate_files(
    structure="ZIF-8",
    molecule="CO2",
    temperature=298,
    pressures=[1e4, 1e5, 1e6]
)
```

## Error Handling

```python
try:
    result = supervisor.run(user_request, output_folder)
except ValueError as e:
    print(f"Invalid request: {e}")
except FileNotFoundError as e:
    print(f"File error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Complete Example

```python
from gcmc_agent import GlobalSupervisor
from gcmc_agent.config import Config
from pathlib import Path

# Configure
config = Config.from_env()
supervisor = GlobalSupervisor(
    llm_config=config,
    workspace_root=Path("./workspace"),
    raspa_path=Path("/usr/local/bin/simulate"),
    verbose=True
)

# Execute workflow
request = """
Setup CO2 adsorption isotherm in MOF-5:
- Temperature: 298K
- Pressure: 0.1 to 10 bar (5 points)
- Use TraPPE force field
- 10,000 MC cycles
"""

result = supervisor.run(
    user_request=request,
    output_folder=Path("output/mof5_co2")
)

# Process results
if result["status"] == "success":
    print("✓ Simulation completed")
    
    # Access files
    for file_type, path in result["files"].items():
        print(f"  {file_type}: {path}")
    
    # Access data
    if "simulation_results" in result:
        isotherm = result["simulation_results"]["isotherm"]
        print(f"  Loading: {isotherm.loadings[-1]:.2f} {isotherm.unit}")
else:
    print("✗ Workflow failed")
    for error in result["errors"]:
        print(f"  - {error}")
```

## Advanced Usage

### Custom Templates

```python
supervisor = GlobalSupervisor(
    template_dir=Path("./my_templates")
)

# my_templates/ should contain:
# ├── force_field_mixing_rules.def
# ├── pseudo_atoms.def
# └── simulation.input.template
```

### Manual Team Coordination

```python
# Step 1: Extract from literature
research_data = supervisor.research_team.run(
    "Extract CO2 parameters from Harris 1995"
)

# Step 2: Use extracted data
setup_result = supervisor.setup_team.run(
    structure="zeolite-13X",
    force_field_data=research_data["force_field"]
)

# Step 3: Execute simulation
from gcmc_agent.tools.raspa_runner import RaspaRunner
runner = RaspaRunner()
sim_result = runner.run(setup_result["output_dir"])
```

## See Also

- [Architecture Overview](../user-guide/architecture.md)
- [Configuration Guide](../getting-started/configuration.md)
- [API: Agents](agents.md)
- [API: Tools](tools.md)
