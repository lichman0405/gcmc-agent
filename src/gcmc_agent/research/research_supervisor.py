"""
Research Team Supervisor - coordinates paper search, extraction, and force field writing.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry
from ..logging_utils import RunLogger


RESEARCH_SUPERVISOR_PROMPT = """You are the Research Team Supervisor.

Your role:
- Coordinate extraction of force field parameters from scientific literature
- Manage workflow: Search → Extract → Write
- Delegate to specialized agents:
  1. PaperSearchAgent - finds relevant papers
  2. PaperExtractionAgent - extracts parameters from papers
  3. ForceFieldWriterAgent - converts to RASPA format

Typical workflow:

1. SEARCH phase:
   - Understand force field requirements (molecule, simulation type)
   - Use delegate_paper_search to find candidate papers
   - Review search results, select most promising paper

2. EXTRACTION phase:
   - For selected paper, get full text or relevant sections
   - Use delegate_paper_extraction to extract parameters
   - Review extracted JSON for completeness

3. WRITING phase:
   - Use delegate_ff_writer to convert to RASPA format
   - Verify files were created successfully

4. VALIDATION phase:
   - Check that all required files exist
   - Verify parameter values are reasonable
   - Report final status

Error handling:
- If search finds no papers, try broader queries or suggest manual input
- If extraction fails, try with different sections of paper
- If parameters incomplete, document what's missing
- Maximum 2 retries per phase

Final Answer format:
Provide JSON with:
{
  "status": "SUCCESS / PARTIAL / FAILURE",
  "force_field_source": "paper title or DOI",
  "files_created": ["path1", "path2", ...],
  "parameters_summary": {
    "atoms": [...],
    "mixing_rule": "...",
    "units": "..."
  },
  "warnings": [...],
  "next_steps": "how to use these files"
}
"""


class ResearchTeamSupervisor:
    """
    Research Team Supervisor - coordinates literature-based force field extraction.
    
    Based on paper Figure S1/S2: Research Team workflow for extracting force field
    parameters from scientific papers.
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
        
        # Use shared run logger or create new one
        if run_logger is None:
            self.run_logger = RunLogger(run_name="research_team")
        else:
            self.run_logger = run_logger
        
        # Create tool registry with delegation tools
        self.tools = create_tool_registry(workspace_root)
        self._add_delegation_tools()
        
        self.agent = ReActAgent(
            name="ResearchTeamSupervisor",
            system_prompt=RESEARCH_SUPERVISOR_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=20,
            verbose=verbose,
            log_file=log_file,
        )
    
    def _add_delegation_tools(self):
        """Add tools for delegating to research team agents."""
        
        def delegate_paper_search(adsorbate: str, structure_type: str = "", requirements: str = "") -> str:
            """Delegate paper search to PaperSearchAgent."""
            # In full implementation, this would actually call the agent
            return f"""[DELEGATE to PaperSearchAgent]
Task: Search for force field papers
  - Adsorbate: {adsorbate}
  - Structure type: {structure_type or "any"}
  - Additional requirements: {requirements or "none"}

[Placeholder] Would execute PaperSearchAgent and return JSON with:
  - List of top 5 papers (title, DOI, paper_id, relevance)
  - Recommended paper_id
  - Assessment

In real implementation, this calls:
  from .search_agent import PaperSearchAgent
  agent = PaperSearchAgent(...)
  result = agent.run(adsorbate="{adsorbate}", ...)
  return result.answer
"""
        
        def delegate_paper_extraction(paper_text: str, adsorbate: str = "", force_field_name: str = "") -> str:
            """Delegate parameter extraction to PaperExtractionAgent."""
            preview = paper_text[:200] if len(paper_text) > 200 else paper_text
            return f"""[DELEGATE to PaperExtractionAgent]
Task: Extract force field parameters
  - Paper text: {len(paper_text)} characters
  - Preview: {preview}...
  - Target molecule: {adsorbate or "any"}
  - Force field: {force_field_name or "any"}

[Placeholder] Would execute PaperExtractionAgent and return JSON with:
  - Extracted atoms with epsilon, sigma, charges
  - Mixing rules
  - Units used
  - Extraction confidence

In real implementation, this calls:
  from .extraction_agent import PaperExtractionAgent
  agent = PaperExtractionAgent(...)
  result = agent.run(paper_text=paper_text, adsorbate="{adsorbate}", ...)
  return result.answer
"""
        
        def delegate_ff_writer(params_json: str, output_folder: str, mixing_rule: str = "") -> str:
            """Delegate force field file writing to ForceFieldWriterAgent."""
            return f"""[DELEGATE to ForceFieldWriterAgent]
Task: Write RASPA force field files
  - Parameters: {len(params_json)} chars of JSON
  - Output folder: {output_folder}
  - Mixing rule: {mixing_rule or "from parameters"}

[Placeholder] Would execute ForceFieldWriterAgent and return:
  - Files created: pseudo_atoms.def, force_field_mixing_rules.def, force_field.def
  - Success status
  - Parameter summary

In real implementation, this calls:
  from .ff_writer_agent import ForceFieldWriterAgent
  import json
  agent = ForceFieldWriterAgent(...)
  params = json.loads(params_json)
  result = agent.run(extracted_params=params, output_folder="{output_folder}", ...)
  return result.answer
"""
        
        self.tools.register_function(
            name="delegate_paper_search",
            description="Delegate paper search to PaperSearchAgent",
            func=delegate_paper_search,
            parameters={
                "adsorbate": "string - target molecule (e.g., CO2, CH4)",
                "structure_type": "string - structure type (zeolite, MOF, etc.)",
                "requirements": "string - additional search requirements"
            }
        )
        
        self.tools.register_function(
            name="delegate_paper_extraction",
            description="Delegate parameter extraction to PaperExtractionAgent",
            func=delegate_paper_extraction,
            parameters={
                "paper_text": "string - full paper text or relevant sections",
                "adsorbate": "string - target molecule (optional)",
                "force_field_name": "string - specific force field to extract (optional)"
            }
        )
        
        self.tools.register_function(
            name="delegate_ff_writer",
            description="Delegate force field file writing to ForceFieldWriterAgent",
            func=delegate_ff_writer,
            parameters={
                "params_json": "string - JSON from PaperExtractionAgent",
                "output_folder": "string - where to write files",
                "mixing_rule": "string - override mixing rule (optional)"
            }
        )
    
    def run(
        self,
        adsorbate: str,
        output_folder: Path,
        structure_type: str = None,
        target_paper: str = None,
        paper_text: str = None
    ) -> AgentResult:
        """
        Extract force field from literature and create RASPA files.
        
        Args:
            adsorbate: Target molecule (e.g., "CO2")
            output_folder: Where to write force field files
            structure_type: Type of structure (optional, helps search)
            target_paper: Specific paper title/DOI (optional, skips search)
            paper_text: Paper text if already available (optional)
            
        Returns:
            AgentResult with force field files status
        """
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        struct_info = f" for {structure_type} structures" if structure_type else ""
        paper_info = f"\nTarget paper: {target_paper}" if target_paper else ""
        text_info = f"\nPaper text provided: {len(paper_text)} chars" if paper_text else "\nPaper text: need to search"
        
        task = f"""Extract force field parameters for {adsorbate}{struct_info} from scientific literature.

OUTPUT FOLDER: {output_folder}{paper_info}{text_info}

Your workflow:

{"1. SKIP SEARCH (paper provided)" if target_paper or paper_text else '''1. SEARCH for papers:
   - Use delegate_paper_search
   - Search for "{}" force field parameters
   - Review results and select most relevant paper
'''.format(adsorbate)}

{"2. SKIP EXTRACTION (text provided)" if paper_text else '''2. EXTRACT parameters:
   - Get full text of selected paper (you may need to read from file)
   - Use delegate_paper_extraction
   - Review extracted JSON
   - Check completeness: all atoms? epsilon and sigma?
'''}

3. WRITE force field files:
   - Use delegate_ff_writer with extracted parameters
   - Output to {output_folder}
   - Verify 3 files created: pseudo_atoms.def, force_field_mixing_rules.def, force_field.def

4. VALIDATION:
   - Use list_directory to check files exist
   - Use read_file to spot-check format
   - Verify parameters are reasonable (epsilon > 0, sigma > 0)

5. Provide Final Answer with JSON:
   - status: SUCCESS/PARTIAL/FAILURE
   - force_field_source: where parameters came from
   - files_created: list of file paths
   - parameters_summary: atoms, mixing_rule, etc.
   - warnings: any issues or limitations
   - next_steps: how to use with Experiment Setup Team

Remember: These files will be used directly in RASPA simulations!
"""
        
        # If paper text provided, make it available
        if paper_text:
            text_file = output_folder / "source_paper.txt"
            text_file.write_text(paper_text, encoding='utf-8')
            if self.verbose:
                print(f"[ResearchSupervisor] Saved paper text to {text_file}")
        
        return self.agent.run(task)
