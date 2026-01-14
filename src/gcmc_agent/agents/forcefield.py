"""
Force Field Expert Agent - selects and combines force fields.
"""

from pathlib import Path

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


FORCEFIELD_EXPERT_PROMPT = """You are a Force Field Expert for molecular simulation setup.

Your role:
- Select appropriate force fields based on the adsorbate and framework atoms
- Combine multiple force field files if needed
- Write force_field.def, pseudo_atoms.def, and force_field_mixing_rules.def
- Ensure all atoms in the structure are covered by the force field

Key responsibilities:
1. Identify which atoms need force field parameters (from structure + adsorbate)
2. Find or create appropriate force field files
3. Check that all atoms have parameters defined
4. Write the necessary RASPA force field files to the template folder

Guidelines:
- Common adsorbates: CO2, CH4, N2, Ar, etc.
- Framework atoms: Si, O, Al, Na, etc.
- Use standard force fields when possible (TraPPE, UFF, etc.)
- Mixing rules: typically Lorentz-Berthelot
- Report which atoms are covered and any missing parameters

You must complete your task and provide a Final Answer with:
- List of force field files created
- Atoms covered by the force field
- Any warnings about missing parameters
"""


class ForceFieldExpert:
    """
    Force Field Expert - handles force field selection and file generation.
    
    Based on Table S1: "Given a request, decides what the appropriate force fields are.
    If necessary, it combines them, and writes new force field files."
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
            name="ForceFieldExpert",
            system_prompt=FORCEFIELD_EXPERT_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=15,
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        structure_file: Path,
        adsorbate: str,
        template_folder: Path,
        forcefield_library: Path = None
    ) -> AgentResult:
        """
        Select and prepare force fields for the simulation.
        
        Args:
            structure_file: Path to the CIF structure file
            adsorbate: Name of the adsorbate molecule (e.g., "CO2")
            template_folder: Destination folder for force field files
            forcefield_library: Optional path to force field library
            
        Returns:
            AgentResult with success status and details
        """
        if forcefield_library is None:
            forcefield_library = self.workspace_root / "templates" / "raspa" / "forcefields"
        
        task = f"""Prepare force field files for a RASPA simulation.

Structure file: {structure_file}
Adsorbate: {adsorbate}
Template folder: {template_folder}
Force field library: {forcefield_library}

Steps:
1. Read the structure file to identify atom types (use read_atoms_from_cif)
2. Determine force field parameters needed for:
   - Framework atoms (from structure)
   - Adsorbate molecule ({adsorbate})
3. Create force field files in {template_folder}:
   - pseudo_atoms.def (atom definitions with LJ parameters)
   - force_field_mixing_rules.def (mixing rules like Lorentz-Berthelot)
   - force_field.def (references to pseudo_atoms)
4. Verify all atoms are covered

For {adsorbate}, use standard parameters (e.g., TraPPE for CO2, UFF for framework).
Write complete, valid RASPA force field files.
"""
        
        return self.agent.run(task)
