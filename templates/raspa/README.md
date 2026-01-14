# RASPA Template Files

This directory provides templates and force field libraries for agents to generate RASPA input and force field files.

## Directory Structure

```
templates/raspa/
├── README.md                              # This file
├── simulation.input.isotherm.template     # Adsorption isotherm template
├── simulation.input.hoa.template          # Heat of adsorption template
├── simulation.input.multigas.template     # Multi-component template
├── simulation.input.example               # Example simulation input
├── pseudo_atoms.def                       # Pseudo atoms template
├── force_field_mixing_rules.def          # Mixing rules template
└── forcefields/                           # Pre-defined force field library
    ├── README.md
    ├── TraPPE_CO2.def
    ├── TraPPE_CH4.def
    ├── TraPPE_N2.def
    ├── TraPPE_O2.def
    ├── TraPPE_CO.def
    └── UFF_Framework.def
```

## Template Files

### Simulation Input Templates

- **simulation.input.isotherm.template**: Adsorption isotherm simulations (GCMC at constant T, variable P)
- **simulation.input.hoa.template**: Heat of adsorption calculations
- **simulation.input.multigas.template**: Multi-component mixture simulations (up to 3 adsorbates)
- **simulation.input.example**: Reference example with framework configuration

### Force Field Templates

- **force_field_mixing_rules.def**: Lennard-Jones mixing rules template with placeholders `{n_interactions}` and `{interactions}`.
- **pseudo_atoms.def**: Pseudo atom definition template with placeholders `{n_atoms}` and `{atoms}`.

### Force Field Library

- **forcefields/**: Pre-defined force field parameters for common adsorbates and framework atoms
  - See [forcefields/README.md](forcefields/README.md) for details

## Placeholder Examples

### simulation.input.isotherm.template
- `n_cycles`, `n_init_cycles`, `print_every`
- `forcefield_name`, `cutoff`, `use_charges_from_cif`
- `unit_cells_a`, `unit_cells_b`, `unit_cells_c`
- `structure_name`
- `adsorbate_name`, `molecule_def`
- `pressure` (set per pressure point)

### simulation.input.hoa.template
- Same as isotherm, plus:
- `temperature` (variable for HOA)
- `write_every` (output frequency)

### simulation.input.multigas.template
- `adsorbate_1`, `molecule_def_1`
- `adsorbate_2`, `molecule_def_2`
- `adsorbate_3`, `molecule_def_3`
- Other parameters same as isotherm

### force_field_mixing_rules.def
- `n_interactions`: integer (number of interaction definitions)
- `interactions`: multi-line text, e.g.:
  ```
  CH4            lennard-jones    158.5     3.72
  CH4 CH4        none
  ```

### pseudo_atoms.def
- `n_atoms`: integer (number of atom types)
- `atoms`: multi-line text in RASPA pseudo_atoms.def format

## Paper Reproduction Support

### Table 1: Experiment Setup Team

**Supported Test Scenarios:**
- ✅ 1 structure × 1 adsorbate - Isotherm
- ✅ 1 structure × 3 adsorbate - Isotherm (use multigas template)
- ✅ 500 structure × 1 adsorbate - Isotherm
- ✅ 500 structure × 3 adsorbate - Isotherm (use multigas template)
- ✅ 1 structure × 1 adsorbate - HOA (use hoa template)
- ✅ 500 structure × 1 adsorbate - HOA (use hoa template)
- ✅ 500 structure × 3 adsorbate - HOA (use hoa + multigas)

**Status**: **Complete** - All 7 test scenarios supported

### Table 2: Research Team

**Supported Force Fields:**
- ✅ TraPPE CO2 (Garcia-Sanchez 2009)
- ✅ TraPPE CH4, N2, O2, CO
- ✅ UFF Framework atoms

**Status**: **Complete** - Reference force fields available for validation

## Usage by Agents

### Agent Workflow

1. **ForceFieldExpert**:
   - Reads pre-defined force fields from `forcefields/`
   - Combines adsorbate + framework parameters
   - Fills `pseudo_atoms.def` and `force_field_mixing_rules.def` templates
   - Generates `force_field.def`

2. **SimulationInputExpert**:
   - Selects appropriate template (isotherm/hoa/multigas)
   - Fills placeholders based on simulation requirements
   - Generates `simulation.input` file

3. **CodingExpert**:
   - Replicates template folder for multiple conditions
   - Creates run scripts for batch execution
   - Organizes output directories

### Example Usage

```python
# ForceFieldExpert uses pre-defined force fields
ff_expert.run(
    structure_file="MOR.cif",
    adsorbate="CO2",
    template_folder="runs/MOR_CO2/template"
)
# → Reads forcefields/TraPPE_CO2.def
# → Generates complete force field files

# SimulationInputExpert selects template
sim_expert.run(
    simulation_type="isotherm",  # Uses simulation.input.isotherm.template
    structure_name="MOR",
    adsorbate="CO2",
    template_folder="runs/MOR_CO2/template"
)

# For HOA
sim_expert.run(
    simulation_type="hoa",       # Uses simulation.input.hoa.template
    ...
)
```

## Template Selection Guide

| Simulation Type | Template | Use Case |
|----------------|----------|----------|
| Isotherm (1 gas) | `isotherm.template` | Standard adsorption isotherm |
| Isotherm (2-3 gases) | `multigas.template` | Mixture adsorption |
| Heat of Adsorption | `hoa.template` | HOA calculations |
| Custom | `example` | Reference for custom setups |

## Notes

- **Pre-defined force fields**: Agents can now use validated parameters from `forcefields/` instead of generating from scratch
- **Automatic selection**: SimulationInputExpert automatically selects template based on `simulation_type` parameter
- **Extensible**: Add new templates or force fields as needed for additional simulation types

