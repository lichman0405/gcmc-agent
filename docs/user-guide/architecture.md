# System Architecture

GCMC-Agent is a multi-agent LLM framework that automates molecular simulation setup through coordinated teamwork.

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                   GlobalSupervisor                       │
│            (Coordinates both teams)                      │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
    ┌──────────▼─────────┐  ┌────────▼──────────┐
    │   Research Team    │  │  Setup Team       │
    ├────────────────────┤  ├───────────────────┤
    │ • PaperSearch      │  │ • StructureExpert │
    │ • Extraction       │  │ • ForceFieldExpert│
    │ • ForceFieldWriter │  │ • SimInputExpert  │
    │ • Verification     │  │ • CodingExpert    │
    └────────────────────┘  │ • Evaluator       │
                            └───────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   RaspaRunner       │
                          │ (Execute & Parse)   │
                          └─────────────────────┘
```

## Components

### 1. GlobalSupervisor

**Role**: Orchestrates the entire workflow

**Responsibilities**:
- Interprets user requests
- Decides which team to activate
- Coordinates between Research and Setup teams
- Manages workflow state
- Returns final results

**Key Methods**:
```python
supervisor.run(user_request, output_folder)
supervisor.process_request(request_text)
```

### 2. Research Team

**Purpose**: Extract simulation parameters from scientific literature

#### Components:

**PaperSearchAgent**
- Searches Semantic Scholar for relevant papers
- Filters by relevance and citation count
- Returns paper metadata and PDFs

**ExtractionAgent**
- Parses scientific papers (text/PDF)
- Extracts force field parameters
- Identifies simulation conditions
- Outputs structured data (JSON)

**ForceFieldWriterAgent**
- Converts extracted parameters to RASPA format
- Generates `force_field.def` files
- Validates parameter completeness

**VerificationAgent**
- Cross-checks extracted data
- Validates parameter ranges
- Ensures consistency

#### Workflow:
```
User Query → Search → Extract → Write → Verify → Parameters
```

### 3. Setup Team

**Purpose**: Generate complete RASPA simulation input files

#### Components:

**StructureExpert**
- Finds or generates CIF structure files
- Validates crystallographic data
- Handles structure transformations

**ForceFieldExpert**
- Selects appropriate force fields (TraPPE, UFF, etc.)
- Generates `force_field.def` and `pseudo_atoms.def`
- Handles mixing rules

**SimulationInputExpert**
- Creates `simulation.input` files
- Sets simulation parameters (cycles, temperature, pressure)
- Configures Monte Carlo moves

**CodingExpert**
- Generates batch simulation scripts
- Creates pressure/temperature sweep scripts
- Handles multi-condition workflows

**Evaluator**
- Validates generated files
- Checks parameter consistency
- Verifies file completeness

#### Workflow:
```
Request → Structure → ForceField → SimInput → Code → Validate → Files
```

### 4. Execution Layer

**RaspaRunner**
- Executes RASPA simulations
- Monitors progress
- Captures output
- Handles errors

**ResultParser**
- Parses RASPA output files
- Extracts isotherm data
- Computes statistics
- Generates plots

## Agent Communication

### ReAct Framework

All agents use the ReAct (Reasoning + Acting) pattern:

```python
while not task_complete:
    # Reasoning
    thought = agent.think(current_state)
    
    # Action selection
    action = agent.select_action(thought)
    
    # Tool execution
    observation = agent.use_tool(action)
    
    # Update state
    current_state = agent.update(observation)
```

### Tool Registry

Agents have access to specialized tools:

**Research Tools**:
- `search_papers(query)` - Semantic Scholar search
- `extract_from_pdf(file)` - PDF text extraction
- `parse_parameters(text)` - Parameter extraction

**Setup Tools**:
- `find_cif_file(name)` - Structure database search
- `read_atoms_from_cif(file)` - CIF parser
- `validate_forcefield(params)` - Force field validator
- `generate_simulation_input(config)` - Input file generator

**Execution Tools**:
- `run_simulation(directory)` - RASPA executor
- `parse_results(output_dir)` - Result parser
- `plot_isotherm(data)` - Visualization

## Workflow Patterns

### Pattern 1: Literature-Driven

```
User: "Reproduce CO2 adsorption from Smith 2020"
  ↓
Research Team:
  - Search for "Smith 2020 CO2 adsorption"
  - Extract force field parameters
  - Extract simulation conditions
  ↓
Setup Team:
  - Get structure (e.g., MOF-5)
  - Write force field files
  - Create simulation.input
  ↓
Execute:
  - Run RASPA
  - Parse results
  - Compare with literature
```

### Pattern 2: Direct Setup

```
User: "Setup CO2 in ZIF-8 at 298K, 1-10 bar"
  ↓
Setup Team:
  - Get ZIF-8 structure
  - Use TraPPE force field
  - Create 5-point pressure range
  - Generate batch script
  ↓
Execute:
  - Run simulations
  - Parse isotherms
  - Plot results
```

### Pattern 3: Custom Parameters

```
User: "Use custom LJ parameters: σ=3.7Å, ε=150K"
  ↓
Setup Team:
  - Parse custom parameters
  - Write force field file
  - Validate against RASPA format
  - Create simulation
  ↓
Execute & verify
```

## State Management

The supervisor maintains state through:

```python
class WorkflowState:
    request: str              # User input
    research_data: dict       # Extracted parameters
    setup_files: dict         # Generated files
    simulation_results: dict  # RASPA output
    status: str               # "running" | "success" | "failed"
    errors: List[str]         # Error messages
```

## Error Handling

Each agent implements error recovery:

1. **Retry with backoff** - Transient errors
2. **Alternative approaches** - Tool failures
3. **Human feedback** - Ambiguous requests
4. **Graceful degradation** - Partial results

## Extension Points

### Custom Agents

```python
from gcmc_agent.react.base import ReactAgent

class MyCustomAgent(ReactAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client)
        self.register_tool("my_tool", self.my_tool_fn)
    
    def my_tool_fn(self, input):
        # Custom logic
        return result
```

### Custom Tools

```python
from gcmc_agent.tools import register_tool

@register_tool
def custom_validator(params: dict) -> bool:
    """Custom validation logic"""
    # Implementation
    return is_valid
```

## Performance Considerations

- **Parallel execution**: Multiple simulations in parallel
- **Caching**: LLM responses and intermediate results
- **Lazy loading**: Load large models only when needed
- **Resource limits**: Timeout and retry mechanisms

## Security

- **API key management**: Environment variables only
- **Input validation**: Sanitize user inputs
- **File system isolation**: Workspace directories
- **No code execution**: From untrusted sources

See also:
- [Research Team Details](research-team.md)
- [Setup Team Details](setup-team.md)
- [RASPA Integration](raspa-integration.md)
