"""
Coding Expert Agent - generates scripts to replicate simulation templates.
"""

from pathlib import Path

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


CODING_EXPERT_PROMPT = """You are a Coding Expert for molecular simulation automation.

Your role:
- Write Python scripts to replicate simulation template folders
- Fill in placeholders (pressure, temperature, etc.) for each run
- Create organized directory structures for batch simulations
- Generate executable scripts

Key responsibilities:
1. Understand the simulation template structure
2. Identify placeholders in simulation.input files
3. Write Python code to create multiple simulation folders
4. Each folder should be a complete, runnable simulation

Common patterns:
- Isotherm: Multiple folders for different pressures at constant T
- Temperature scan: Multiple folders for different temperatures
- Multi-component: Multiple folders for different mixtures

Guidelines:
- Use Python's pathlib and shutil for file operations
- Copy template folder for each condition
- Use string replacement or templating to fill placeholders
- Create clear directory names (e.g., P_10000Pa, T_298K)
- Write a README or log file with run details

You must complete your task and provide a Final Answer with:
- Path to the generated Python script
- Number of simulation folders to be created
- Description of what the script does
- Example command to run the script
"""


class CodingExpert:
    """
    Coding Expert - generates scripts to create multiple simulation runs.
    
    Based on Table S1: "Writes code to replicate the template folder for each
    necessary run. Needs to understand how the simulation template is set up."
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
            name="CodingExpert",
            system_prompt=CODING_EXPERT_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=15,
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        template_folder: Path,
        output_folder: Path,
        run_conditions: dict
    ) -> AgentResult:
        """
        Generate code to create multiple simulation runs.
        
        Args:
            template_folder: Source template folder to replicate
            output_folder: Base directory for simulation runs
            run_conditions: Dict with conditions like {"pressures": [1e4, 1e5], "temperature": 298}
            
        Returns:
            AgentResult with success status and details
        """
        task = f"""Write a Python script to create multiple RASPA simulation runs from a template.

Template folder: {template_folder}
Output base folder: {output_folder}
Run conditions: {run_conditions}

Steps:
1. Inspect the template folder structure (use list_directory)
2. Read the simulation.input file to understand placeholders (use read_file)
3. Write a Python script that:
   - Imports necessary modules (pathlib, shutil)
   - Defines the run conditions: {run_conditions}
   - Loops over each condition
   - Creates a folder for each run (e.g., P_10000Pa/)
   - Copies all files from template
   - Replaces placeholders in simulation.input
   - Saves the modified file
4. Save the script to: {output_folder / "generate_runs.py"}
5. Also execute the script to create the folders

The script should be well-commented and easy to modify.
"""
        
        return self.agent.run(task)
