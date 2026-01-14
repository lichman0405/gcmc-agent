"""
Supervisor Agent - coordinates the experiment setup team.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry
from ..logging_utils import RunLogger, LLMCallLogger

# Import the actual agent implementations
from .structure import StructureExpert
from .forcefield import ForceFieldExpert
from .simulation_input import SimulationInputExpert
from .coding import CodingExpert
from .evaluator import Evaluator


SUPERVISOR_PROMPT = """You are the Supervisor for the Experiment Setup Team.

Your role:
- Understand user requests for molecular simulations
- Break down the request into sub-tasks
- Delegate tasks to specialized agents
- Coordinate the workflow
- Ensure all tasks are completed

Available Agents:
1. StructureExpert - Finds and prepares structure files (.cif)
2. ForceFieldExpert - Selects and creates force field files
3. SimulationInputExpert - Creates simulation.input files
4. CodingExpert - Generates scripts for batch runs
5. Evaluator - Validates the setup quality

Typical workflow for adsorption isotherm:
1. StructureExpert: Find and copy structure file
2. ForceFieldExpert: Prepare force field for structure + adsorbate
3. SimulationInputExpert: Create simulation.input template
4. Evaluator: Check template quality
5. CodingExpert: Generate script for multiple pressures
6. Evaluator: Final validation

Your responsibilities:
- Parse the user request to extract: structure name, adsorbate, simulation type, conditions
- Plan the sequence of agent calls
- Delegate each sub-task to the appropriate agent
- Check Evaluator feedback and retry if needed
- Report final status and location of setup

Guidelines:
- Always start with StructureExpert
- Always run Evaluator after major steps
- If Evaluator reports FAIL, retry the failed agent
- Maximum 2 retries per agent
- Provide clear final summary

You must provide a Final Answer with:
- Status: SUCCESS or FAILURE
- Location of simulation setup
- Summary of what was created
- Any warnings or issues
- Next steps (how to run the simulation)
"""


class Supervisor:
    """
    Supervisor - coordinates multi-agent simulation setup.
    
    Based on Table S1: "Responsible for understanding the user request, and developing
    a plan of actions needed to be performed to set up a simulation. Delegates to the
    various agents according to its plan."
    """
    
    def __init__(
        self,
        llm_client: OpenAIChatClient,
        workspace_root: Path,
        model: str = "deepseek-chat",
        verbose: bool = False,
        log_file: Path = None,
        run_logger: Optional[RunLogger] = None,
    ):
        self.workspace_root = workspace_root
        self.llm_client = llm_client
        self.model = model
        self.verbose = verbose
        
        # Initialize run logger if not provided
        if run_logger is None:
            self.run_logger = RunLogger(run_name="setup_team")
        else:
            self.run_logger = run_logger
        
        # Log supervisor initialization
        self.run_logger.record_workflow_event(
            "supervisor_init",
            "Setup Team Supervisor initialized",
            {"workspace": str(workspace_root), "model": model}
        )
        
        # Initialize the actual agents
        self.structure_expert = StructureExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
        )
        
        self.forcefield_expert = ForceFieldExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
        )
        
        self.siminput_expert = SimulationInputExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
        )
        
        self.coding_expert = CodingExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
        )
        
        self.evaluator = Evaluator(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
        )
        
        # Create a special tool registry for supervisor
        # Supervisor doesn't use all tools, just delegation and file inspection
        self.tools = create_tool_registry(workspace_root)
        
        # Add delegation tools (these would be placeholders that describe how to call agents)
        self._add_delegation_tools()
        
        self.agent = ReActAgent(
            name="Supervisor",
            system_prompt=SUPERVISOR_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=30,  # Supervisor may need more iterations
            verbose=verbose,
            log_file=log_file,
        )
    
    def _add_delegation_tools(self):
        """Add tools for delegating to other agents."""
        
        def delegate_to_structure_expert(structure_name: str, template_folder: str) -> str:
            """Delegate structure finding to StructureExpert."""
            try:
                self.run_logger.record_agent_start("StructureExpert", f"Find {structure_name}")
                result = self.structure_expert.run(
                    structure_name=structure_name,
                    template_folder=Path(template_folder)
                )
                self.run_logger.record_agent_finish(
                    "StructureExpert",
                    success=result.success,
                    iterations=getattr(result, 'iterations', 0)
                )
                if result.success:
                    return f"SUCCESS: {result.answer}"
                else:
                    return f"FAILED: {result.error or result.answer}"
            except Exception as e:
                self.run_logger.record_agent_finish("StructureExpert", success=False, iterations=0, error=str(e))
                return f"ERROR: {str(e)}"
        
        def delegate_to_forcefield_expert(structure_file: str, adsorbate: str, template_folder: str, custom_force_field_dir: str = None) -> str:
            """Delegate force field setup to ForceFieldExpert."""
            try:
                self.run_logger.record_agent_start("ForceFieldExpert", f"Setup FF for {adsorbate}")
                result = self.forcefield_expert.run(
                    structure_file=Path(structure_file),
                    adsorbate=adsorbate,
                    template_folder=Path(template_folder),
                    forcefield_library=Path(custom_force_field_dir) if custom_force_field_dir else None
                )
                self.run_logger.record_agent_finish(
                    "ForceFieldExpert",
                    success=result.success,
                    iterations=getattr(result, 'iterations', 0)
                )
                if result.success:
                    return f"SUCCESS: {result.answer}"
                else:
                    return f"FAILED: {result.error or result.answer}"
            except Exception as e:
                self.run_logger.record_agent_finish("ForceFieldExpert", success=False, iterations=0, error=str(e))
                return f"ERROR: {str(e)}"
        
        def delegate_to_siminput_expert(simulation_type: str, structure_name: str, adsorbate: str, template_folder: str, temperature: float = 298.0) -> str:
            """Delegate simulation input creation to SimulationInputExpert."""
            try:
                self.run_logger.record_agent_start("SimulationInputExpert", f"Create {simulation_type} input")
                result = self.siminput_expert.run(
                    simulation_type=simulation_type,
                    structure_name=structure_name,
                    adsorbate=adsorbate,
                    template_folder=Path(template_folder),
                    parameters={"temperature": temperature}
                )
                self.run_logger.record_agent_finish(
                    "SimulationInputExpert",
                    success=result.success,
                    iterations=getattr(result, 'iterations', 0)
                )
                if result.success:
                    return f"SUCCESS: {result.answer}"
                else:
                    return f"FAILED: {result.error or result.answer}"
            except Exception as e:
                self.run_logger.record_agent_finish("SimulationInputExpert", success=False, iterations=0, error=str(e))
                return f"ERROR: {str(e)}"
        
        def delegate_to_coding_expert(template_folder: str, output_folder: str, pressures: str) -> str:
            """Delegate code generation to CodingExpert."""
            try:
                # Parse pressures from string like "10, 30, 100, 300, 1000"
                pressure_list = [float(p.strip()) for p in pressures.split(',')]
                
                self.run_logger.record_agent_start("CodingExpert", f"Generate scripts for {len(pressure_list)} pressures")
                result = self.coding_expert.run(
                    template_folder=Path(template_folder),
                    output_folder=Path(output_folder),
                    run_conditions={"pressures": pressure_list}
                )
                self.run_logger.record_agent_finish(
                    "CodingExpert",
                    success=result.success,
                    iterations=getattr(result, 'iterations', 0)
                )
                if result.success:
                    return f"SUCCESS: {result.answer}"
                else:
                    return f"FAILED: {result.error or result.answer}"
            except Exception as e:
                self.run_logger.record_agent_finish("CodingExpert", success=False, iterations=0, error=str(e))
                return f"ERROR: {str(e)}"
        
        def delegate_to_evaluator(template_folder: str, check_type: str = "structure") -> str:
            """Delegate validation to Evaluator."""
            try:
                self.run_logger.record_agent_start("Evaluator", f"Check {check_type}")
                result = self.evaluator.run(
                    template_folder=Path(template_folder),
                    agent_name="Supervisor",
                    task_description=f"Validate {check_type} setup"
                )
                self.run_logger.record_agent_finish(
                    "Evaluator",
                    success=result.success,
                    iterations=getattr(result, 'iterations', 0)
                )
                if result.success:
                    return f"PASS: {result.answer}"
                else:
                    return f"FAIL: {result.error or result.answer}"
            except Exception as e:
                self.run_logger.record_agent_finish("Evaluator", success=False, iterations=0, error=str(e))
                return f"ERROR: {str(e)}"
        
        self.tools.register_function(
            name="delegate_structure_expert",
            description="Delegate structure file finding and copying to StructureExpert",
            func=delegate_to_structure_expert,
            parameters={
                "structure_name": "string - name of structure to find (e.g., 'MOR', 'MFI')",
                "template_folder": "string - absolute path to destination folder"
            }
        )
        
        self.tools.register_function(
            name="delegate_forcefield_expert",
            description="Delegate force field preparation to ForceFieldExpert",
            func=delegate_to_forcefield_expert,
            parameters={
                "structure_file": "string - absolute path to structure CIF file",
                "adsorbate": "string - adsorbate molecule name (e.g., 'CO2', 'CH4')",
                "template_folder": "string - absolute path to destination folder",
                "custom_force_field_dir": "string - (optional) path to custom force field directory"
            }
        )
        
        self.tools.register_function(
            name="delegate_siminput_expert",
            description="Delegate simulation.input creation to SimulationInputExpert",
            func=delegate_to_siminput_expert,
            parameters={
                "simulation_type": "string - type of simulation ('isotherm', 'single_point', etc)",
                "structure_name": "string - structure name (e.g., 'MOR')",
                "adsorbate": "string - adsorbate molecule (e.g., 'CO2')",
                "template_folder": "string - absolute path to destination folder",
                "temperature": "float - (optional) temperature in K, default 298.0"
            }
        )
        
        self.tools.register_function(
            name="delegate_coding_expert",
            description="Delegate batch run script generation to CodingExpert",
            func=delegate_to_coding_expert,
            parameters={
                "template_folder": "string - absolute path to source template folder",
                "output_folder": "string - absolute path to base folder for runs",
                "pressures": "string - comma-separated pressure values in Pa (e.g., '10, 30, 100, 300')"
            }
        )
        
        self.tools.register_function(
            name="delegate_evaluator",
            description="Delegate quality validation to Evaluator",
            func=delegate_to_evaluator,
            parameters={
                "template_folder": "string - absolute path to folder to evaluate",
                "check_type": "string - type of check ('structure', 'forcefield', 'simulation', 'complete')"
            }
        )
    
    def run(self, user_request: str) -> AgentResult:
        """
        Process user request and coordinate simulation setup.
        
        Args:
            user_request: User's simulation request in natural language
            
        Returns:
            AgentResult with final status and setup location
        """
        self.run_logger.record_workflow_event(
            "supervisor_run_start",
            "Supervisor processing user request",
            {"request": user_request[:200]}
        )
        
        task = f"""Process this user request and set up a molecular simulation.

USER REQUEST:
{user_request}

Your workflow:
1. Parse the request to extract:
   - Structure name (e.g., "MOR", "MFI", "LTA", etc.)
   - Adsorbate molecule (e.g., "CO2", "CH4", etc.)
   - Simulation type (e.g., "isotherm", "HOA", "single-point")
   - Conditions (temperature, pressures, etc.)

2. Create a workspace folder: {self.workspace_root / "runs"}/[structure]_[adsorbate]_[type]

3. Delegate to agents in sequence:
   - Use delegate_structure_expert to find and copy structure file
   - Use delegate_forcefield_expert to prepare force field files
   - Use delegate_siminput_expert to create simulation.input template
   - Use delegate_evaluator to validate the setup
   - Use delegate_coding_expert to generate batch run scripts for multiple pressures
   - Use delegate_evaluator for final check

4. Each delegation will return SUCCESS/FAILED/PASS/FAIL with details.
   If a step fails, you can retry or report the failure.

5. Provide Final Answer with:
   - Status: SUCCESS or FAILURE
   - Location of simulation files
   - Summary of what was created
   - Any issues or warnings
   - Next steps (how to run the simulation)

Remember: All agents will execute real actions. Check their results carefully.
"""
        
        result = self.agent.run(task)
        
        self.run_logger.record_workflow_event(
            "supervisor_run_complete",
            f"Supervisor {'succeeded' if result.success else 'failed'}",
            {"success": result.success, "iterations": getattr(result, 'iterations', 0)}
        )
        
        return result
