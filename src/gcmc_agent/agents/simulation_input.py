"""
Simulation Input Expert Agent - creates simulation.input files.
"""

from pathlib import Path

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


SIMULATION_INPUT_EXPERT_PROMPT = """You are a Simulation Input Expert for RASPA molecular simulations.

Your role:
- Create appropriate simulation.input files based on simulation type
- Set correct parameters (temperature, pressure, MC moves, cutoffs, etc.)
- Choose appropriate keywords for the simulation type
- Ensure consistency with structure and force field

Key responsibilities:
1. Determine simulation type (isotherm, HOA, single-point, etc.)
2. Select appropriate RASPA keywords and values
3. Set Monte Carlo move probabilities
4. Configure Ewald summation, cutoffs, unit cells
5. Write complete simulation.input file

Common simulation types:
- Adsorption Isotherm: Multiple pressures at constant T
- Heat of Adsorption: Variable temperature
- Single-point: One state point

Key parameters:
- NumberOfCycles, NumberOfInitializationCycles
- Cutoff (typically 12 Å)
- Movies: Yes/No
- ExternalTemperature, ExternalPressure
- Framework: name, unitcells, ChargeMethod
- Component: molecule name, moves (Translation, Rotation, WidomInsertion, etc.)

Guidelines:
- Use example files as templates when available
- Widom insertion for GCMC
- Proper Ewald for charged systems
- UnitCells: ensure minimum image convention (3x cutoff)

You must complete your task and provide a Final Answer with:
- Path to simulation.input file created
- Key parameters set
- Simulation type
"""


class SimulationInputExpert:
    """
    Simulation Input Expert - creates RASPA simulation.input files.
    
    Based on Table S1: "Creates a simulation.input file, depending on the requirements
    of the simulation. Needs to decide which keywords are appropriate."
    """
    
    def __init__(
        self,
        llm_client: OpenAIChatClient,
        workspace_root: Path,
        model: str = "deepseek-chat",
        verbose: bool = False,
        log_file: Path = None,
    ):
        self.workspace_root = workspace_root
        self.llm_client = llm_client
        self.model = model
        self.verbose = verbose
        
        self.tools = create_tool_registry(workspace_root)
        
        self.agent = ReActAgent(
            name="SimulationInputExpert",
            system_prompt=SIMULATION_INPUT_EXPERT_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=15,
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        simulation_type: str,
        structure_name: str,
        adsorbate: str,
        template_folder: Path,
        parameters: dict = None
    ) -> AgentResult:
        """
        Create simulation.input file for RASPA.
        
        Args:
            simulation_type: Type of simulation (e.g., "isotherm", "HOA")
            structure_name: Name of the structure
            adsorbate: Adsorbate molecule name
            template_folder: Destination folder for simulation.input
            parameters: Optional dict with temperature, pressures, etc.
            
        Returns:
            AgentResult with success status and details
        """
        params = parameters or {}
        temperature = params.get("temperature", 298)
        pressures = params.get("pressures", [1e4, 1e5, 1e6])  # Pa
        
        task = f"""Create a simulation.input file for RASPA.

Simulation type: {simulation_type}
Structure: {structure_name}
Adsorbate: {adsorbate}
Temperature: {temperature} K
Pressures: {pressures} Pa
Template folder: {template_folder}

Steps:
1. Look for example simulation.input files in {self.workspace_root / "templates" / "raspa"}
2. Read an appropriate example as a template (use read_file)
3. Modify the template for this specific simulation:
   - Set SimulationType: MonteCarlo
   - Set NumberOfCycles: 50000 (production), NumberOfInitializationCycles: 10000
   - Set ExternalTemperature: {temperature}
   - Set Framework: {structure_name}.cif
   - Set Component: {adsorbate}
   - Set appropriate MC moves (Translation, Rotation, WidomInsertion for GCMC)
   - Set Cutoff: 12.0 (Angstrom)
   - Set UnitCells: auto-calculate based on structure size
4. Write the file to: {template_folder / "simulation.input"}

For {simulation_type}, ensure correct keywords.
If isotherm: this is a template, pressure will be set per-run.
"""
        
        return self.agent.run(task)
