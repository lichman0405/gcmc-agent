"""
Structure Expert Agent - finds and copies CIF structure files.

This is the first real ReAct agent implementation following the paper's design.
"""

from pathlib import Path

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


# System prompt based on Table S1 from the paper
STRUCTURE_EXPERT_PROMPT = """You are a Structure Expert for molecular simulation setup.

Your role:
- Find the appropriate CIF structure file based on the user's request
- Download from IZA database if not found locally
- Copy the structure file to the simulation template folder
- Verify the structure properties (unit cell, atom types)

Key responsibilities:
1. Search for the requested structure in available CIF repositories
2. If not found locally, download from IZA database using download_cif_from_iza tool
3. Validate the structure file exists and is readable
4. Copy it to the correct location in the simulation workspace
5. Report back the structure details (atoms, unit cell size)

Guidelines:
- Structure names may have variations (e.g., MOR, MOR_33, MOR-type)
- For standard zeolites (3-letter codes like MOR, MFI, LTA), use IZA database
- Always verify the file exists before copying
- Report any issues with missing or invalid structures
- Provide clear information about what was found and copied

Available tools:
- find_cif_files: Search for CIF files in directories
- download_cif_from_iza: Download zeolite structures from IZA database (3-letter codes)
- copy_file: Copy structure to destination
- read_file: Verify structure content

You must complete your task and provide a Final Answer with:
- Path to the copied structure file
- Atom types present
- Unit cell dimensions
- Any warnings or notes
"""


class StructureExpert:
    """
    Structure Expert Agent - handles finding and preparing structure files.
    
    Based on Table S1: "Finds the appropriate (placeholder) structure, 
    and places a copy in the simulation folder."
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
        
        # Create tool registry
        self.tools = create_tool_registry(workspace_root)
        
        # Create ReAct agent
        self.agent = ReActAgent(
            name="StructureExpert",
            system_prompt=STRUCTURE_EXPERT_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=15,  # Increased from 10 to allow file copy
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        structure_name: str,
        template_folder: Path,
        cif_search_paths: list[Path] = None
    ) -> AgentResult:
        """
        Find and copy a structure file to the template folder.
        
        Args:
            structure_name: Name of the structure to find (e.g., "MOR_33")
            template_folder: Destination folder for the structure file
            cif_search_paths: Optional list of directories to search
            
        Returns:
            AgentResult with success status and details
        """
        # Default search paths
        if cif_search_paths is None:
            cif_search_paths = [
                self.workspace_root / "cifs",
                self.workspace_root / "structures",
            ]
        
        # Build task description
        search_paths_str = ", ".join([str(p) for p in cif_search_paths])
        
        task = f"""Find the CIF structure file for '{structure_name}' and copy it to the simulation template folder.

Search locations: {search_paths_str}
Destination folder: {template_folder}

Workflow:
1. Search for CIF files in the provided directories using find_cif_files
2. Look for files matching '{structure_name}' (may have .cif extension or similar naming)

3. If NOT found locally:
   - Extract the 3-letter structure code from '{structure_name}' (e.g., 'MOR' from 'MOR_33')
   - Use download_cif_from_iza to download from IZA zeolite database
   - Save to the first search directory: {cif_search_paths[0]}
   
4. Once you have the file (either found or downloaded):
   - Read the structure using read_file to get atom types and unit cell dimensions
   - Copy the file to: {template_folder}/{structure_name}.cif
   
5. Provide Final Answer with:
   - Success/failure status
   - Path to the copied file
   - Structure details (atom types, unit cell)
   - Whether it was found locally or downloaded

If the structure cannot be found or downloaded, report that clearly.
"""
        
        return self.agent.run(task)
