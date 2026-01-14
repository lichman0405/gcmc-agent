"""
Evaluator Agent - checks generated files and provides feedback.
"""

from pathlib import Path

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


EVALUATOR_PROMPT = """You are an Evaluator for molecular simulation setup validation.

Your role:
- Inspect generated files for correctness and completeness
- Verify all required files exist
- Check that parameters are reasonable
- Identify potential errors or issues
- Provide specific feedback for corrections

Key responsibilities:
1. Check file existence (structure, force field, simulation.input, molecules)
2. Validate force field coverage (all atoms have parameters)
3. Verify simulation.input syntax and parameters
4. Check for common errors (missing files, wrong paths, invalid values)
5. Provide actionable feedback

Common checks:
- Structure file (.cif) exists and is readable
- Force field files exist: pseudo_atoms.def, force_field_mixing_rules.def
- All atoms in structure have force field parameters
- simulation.input has required keywords
- Cutoff < half of smallest unit cell dimension
- Temperature and pressure are reasonable
- MC move probabilities sum correctly

Guidelines:
- Be specific about what's wrong and how to fix it
- Distinguish between errors (must fix) and warnings (should improve)
- For each issue, state the file and line/parameter
- If everything is correct, clearly state PASS

You must provide a Final Answer with:
- PASS or FAIL status
- List of specific issues found (if any)
- Recommendations for improvement
"""


class Evaluator:
    """
    Evaluator Agent - validates simulation setup quality.
    
    Based on Table S1: "Evaluates the task performance of each agent by inspecting
    files created during their execution and flags any potential mistakes it finds."
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
            name="Evaluator",
            system_prompt=EVALUATOR_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=20,
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        template_folder: Path,
        agent_name: str = "Unknown",
        task_description: str = ""
    ) -> AgentResult:
        """
        Evaluate the quality of generated simulation files.
        
        Args:
            template_folder: Folder to evaluate
            agent_name: Name of the agent that created the files
            task_description: Description of what was supposed to be created
            
        Returns:
            AgentResult with PASS/FAIL and specific feedback
        """
        task = f"""Evaluate the simulation setup in the template folder.

Agent: {agent_name}
Task: {task_description}
Folder to evaluate: {template_folder}

Perform these checks:

1. File existence:
   - List directory contents (use list_directory)
   - Verify structure file (.cif) exists
   - Verify force field files exist (pseudo_atoms.def, force_field_mixing_rules.def, force_field.def)
   - Verify simulation.input exists

2. Structure validation:
   - Read structure file to check it's valid (use read_atoms_from_cif)
   - Get unit cell dimensions (use get_unit_cell)

3. Force field validation:
   - Read pseudo_atoms.def (use read_file)
   - Check that structure atoms are covered
   - Verify parameters look reasonable (no zeros, negative values)

4. Simulation input validation:
   - Read simulation.input (use read_file)
   - Check for required keywords: SimulationType, NumberOfCycles, Framework, Component
   - Verify temperature and pressure are reasonable (T > 0, P > 0)
   - Check cutoff < half of smallest cell dimension

5. Overall assessment:
   - Are all files present and valid?
   - Are there any obvious errors?
   - Is this setup ready to run?

Provide specific feedback with:
- STATUS: PASS or FAIL
- ERRORS: List of critical issues (if any)
- WARNINGS: List of potential improvements (if any)
- RECOMMENDATIONS: Specific actions to fix issues
"""
        
        return self.agent.run(task)
