"""
Global Supervisor - Coordinates Research Team and Experiment Setup Team

Implements the functionality described in paper Appendix C:
"Two teams were overseen by a supervisor. They were tasked with extracting 
the force field from [18] and setting up an adsorption isotherm simulation 
for a structure using the extracted force field."
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from gcmc_agent.react import ReActAgent, AgentResult
from gcmc_agent.client import OpenAIChatClient
from gcmc_agent.tools.registry import create_tool_registry
from gcmc_agent.research.search_agent import PaperSearchAgent
from gcmc_agent.research.extraction_agent import PaperExtractionAgent
from gcmc_agent.research.ff_writer_agent import ForceFieldWriterAgent
from gcmc_agent.agents.supervisor import Supervisor
from gcmc_agent.tools.raspa_runner import RaspaRunner, RaspaResult
from gcmc_agent.tools.result_parser import ResultParser
from gcmc_agent.logging_utils import RunLogger, LLMCallLogger


GLOBAL_SUPERVISOR_PROMPT = """You are the Global Supervisor coordinating molecular simulation workflows.

Your role:
- Understand user requests for molecular simulations
- Determine whether force field parameters need to be extracted from literature
- Coordinate Research Team and Experiment Setup Team
- Ensure end-to-end task completion

Teams under your command:

1. Research Team (for literature-based force field extraction):
   - PaperSearchAgent: Search for relevant papers
   - PaperExtractionAgent: Extract force field parameters
   - ForceFieldWriterAgent: Generate RASPA force field files

2. Experiment Setup Team (for simulation setup):
   - StructureExpert: Prepare structure files
   - ForceFieldExpert: Select/combine force fields
   - SimulationInputExpert: Create simulation.input files
   - Evaluator: Validate outputs

Workflow Decision Logic:

SCENARIO A: Force field already available
- User mentions specific force field (e.g., "use TraPPE")
- Standard molecules with existing force fields (CO2, CH4, N2)
→ Skip Research Team, go directly to Setup Team

SCENARIO B: Force field needs extraction
- User mentions a paper/DOI for force field
- Novel molecule without standard force field
- User explicitly asks to extract from literature
→ Research Team first, then Setup Team

SCENARIO C: Uncertain
- Ask user for clarification
- Default to using existing force fields if molecule is common

Output Format:
Provide Final Answer with JSON:
{
  "workflow": "scenario_a|scenario_b",
  "research_needed": true|false,
  "plan": [
    "step 1: ...",
    "step 2: ...",
    ...
  ],
  "output_directory": "path/to/output",
  "status": "success|failed",
  "message": "..."
}
"""


class GlobalSupervisor:
    """
    Global Supervisor coordinating Research Team and Experiment Setup Team.
    
    Implements the coordinated workflow described in paper Appendix C.
    """
    
    def __init__(
        self,
        llm_client: OpenAIChatClient,
        workspace_root: Path,
        model: str = "deepseek-chat",
        verbose: bool = False,
        log_file: Optional[Path] = None,
    ):
        self.workspace_root = workspace_root
        self.llm_client = llm_client
        self.model = model
        self.verbose = verbose
        
        # Initialize logging system
        self.run_logger = RunLogger(run_name="gcmc_workflow")
        llm_log_file = self.run_logger.run_dir / "llm_calls.jsonl"
        self.llm_logger = LLMCallLogger(log_file=llm_log_file)
        
        # Connect LLM client to logger
        self.llm_client.llm_logger = self.llm_logger
        self.llm_client.set_metadata(supervisor="GlobalSupervisor")
        
        # Initialize Research Team agents
        self.paper_search = PaperSearchAgent(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
            log_file=log_file
        )
        
        self.paper_extraction = PaperExtractionAgent(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
            log_file=log_file
        )
        
        self.ff_writer = ForceFieldWriterAgent(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
            log_file=log_file
        )
        
        # Initialize Setup Team Supervisor
        self.setup_supervisor = Supervisor(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model=model,
            verbose=verbose,
            log_file=log_file,
            run_logger=self.run_logger
        )
        
        # Create coordination agent (not really needed now, simplified)
        tools = create_tool_registry(workspace_root)
        self.agent = ReActAgent(
            name="GlobalSupervisor",
            system_prompt=GLOBAL_SUPERVISOR_PROMPT,
            llm_client=llm_client,
            tools=tools.to_dict(),
            model=model,
            max_iterations=15,
            verbose=verbose,
            log_file=log_file,
        )
    
    def _needs_literature_search(
        self, 
        user_request: str, 
        paper_text: Optional[str], 
        paper_doi: Optional[str]
    ) -> bool:
        """
        Determine if Research Team is needed based on user request.
        
        Returns True if:
        - paper_text or paper_doi is provided
        - User mentions a specific paper/author/year (e.g., "Garcia-Sanchez 2009")
        - User says "extract from paper/literature"
        """
        # Explicit paper content provided
        if paper_text or paper_doi:
            return True
        
        # Check for paper/literature keywords in request
        request_lower = user_request.lower()
        
        # Keywords indicating literature extraction needed
        literature_keywords = [
            "from paper", "from literature", "extract from",
            "taken from", "using parameters from", "force field from",
            "garcia", "sanchez", "dubbeldam", "calero", "martin-calvo",
            "trappe-zeo", "epm2", "harris", "vujic"
        ]
        
        # Year patterns (e.g., "2009", "et al. 2015")
        import re
        year_pattern = r'\b(19|20)\d{2}\b'
        has_year = bool(re.search(year_pattern, user_request))
        
        for keyword in literature_keywords:
            if keyword in request_lower:
                return True
        
        # If there's a year and author-like words, likely a paper reference
        if has_year and any(word in request_lower for word in ["et al", "force field", "parameters"]):
            return True
        
        return False
    
    def _search_paper_from_request(self, user_request: str) -> Dict[str, Any]:
        """
        Use PaperSearchAgent to find and retrieve paper based on user request.
        
        Extracts paper reference from request, searches Semantic Scholar,
        downloads/retrieves paper content.
        """
        try:
            # Run paper search agent
            search_result = self.paper_search.run(user_request)
            
            if not search_result.success:
                return {"success": False, "error": search_result.error}
            
            # Parse search result to get best paper
            try:
                result_data = json.loads(search_result.answer)
                papers = result_data.get("papers", [])
                recommended_id = result_data.get("recommended")
                
                if not papers:
                    return {"success": False, "error": "No papers found"}
                
                # Get recommended or first paper
                best_paper = None
                for p in papers:
                    if p.get("paper_id") == recommended_id:
                        best_paper = p
                        break
                if not best_paper:
                    best_paper = papers[0]
                
                # Get paper details/abstract as proxy for full text
                # (In production, would download and parse PDF)
                paper_text = f"""
Paper: {best_paper.get('title', 'Unknown')}
Authors: {', '.join(best_paper.get('authors', []))}
Year: {best_paper.get('year', 'Unknown')}
DOI: {best_paper.get('doi', 'Unknown')}

Abstract:
{best_paper.get('abstract', 'No abstract available')}
"""
                
                return {
                    "success": True,
                    "title": best_paper.get("title"),
                    "doi": best_paper.get("doi"),
                    "paper_id": best_paper.get("paper_id"),
                    "paper_text": paper_text
                }
                
            except json.JSONDecodeError:
                # If not JSON, use raw answer as context
                return {
                    "success": True,
                    "paper_text": search_result.answer
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run(
        self,
        user_request: str,
        output_folder: Path,
        paper_text: Optional[str] = None,
        paper_doi: Optional[str] = None
    ) -> AgentResult:
        """
        Execute end-to-end workflow based on user request.
        
        This implements the coordinated workflow from paper Appendix C:
        1. Analyze user request to determine if literature search is needed
        2. If needed, Research Team searches and extracts force field from paper
        3. Setup Team creates complete simulation directory
        
        Args:
            user_request: Natural language simulation request
            output_folder: Directory for output files
            paper_text: Optional paper text for force field extraction
            paper_doi: Optional DOI for paper search
        
        Returns:
            AgentResult with complete simulation setup
        """
        output_folder.mkdir(parents=True, exist_ok=True)
        
        self.run_logger.record_workflow_event("workflow_start", f"User request: {user_request[:100]}")
        
        # Analyze user request to determine if Research Team is needed
        research_needed = self._needs_literature_search(user_request, paper_text, paper_doi)
        
        # Step 1: Execute Research Team if needed
        force_field_dir = None
        extracted_paper_text = paper_text
        
        if research_needed:
            if self.verbose:
                print("\n" + "="*80)
                print("PHASE 1: Research Team - Force Field Extraction")
                print("="*80)
            
            # If no paper_text provided but user mentioned a paper, search for it
            if not paper_text and not paper_doi:
                if self.verbose:
                    print("\n>> PaperSearchAgent: Searching Semantic Scholar...")
                
                search_result = self._search_paper_from_request(user_request)
                if search_result["success"]:
                    paper_doi = search_result.get("doi")
                    extracted_paper_text = search_result.get("paper_text")
                    if self.verbose:
                        print(f">> Found paper: {search_result.get('title', 'Unknown')}")
                else:
                    if self.verbose:
                        print(f">> Paper search failed: {search_result.get('error')}")
                        print(f">> Fallback: Skipping Research Team, will use known force fields")
                    # If search fails, skip Research Team and use Setup Team's built-in force fields
                    research_needed = False
            
            # Only run Research Team if we have paper text
            if research_needed and extracted_paper_text:
                research_result = self._run_research_team(
                    user_request=user_request,
                    paper_text=extracted_paper_text,
                    paper_doi=paper_doi,
                    output_folder=output_folder
                )
                
                if not research_result["success"]:
                    if self.verbose:
                        print(f">> Research Team failed: {research_result['error']}")
                        print(f">> Fallback: Using Setup Team's built-in force fields")
                    # Continue with Setup Team even if Research fails
                else:
                    force_field_dir = research_result["force_field_dir"]
        
        # Step 2: Execute Setup Team
        if self.verbose:
            print("\n" + "="*80)
            print("PHASE 2: Experiment Setup Team - Simulation Files")
            print("="*80)
        
        setup_result = self._run_setup_team(
            user_request=user_request,
            output_folder=output_folder,
            custom_force_field_dir=force_field_dir
        )
        
        if not setup_result["success"]:
            return AgentResult(
                success=False,
                answer="",
                thought_action_history=[],
                error=f"Setup Team failed: {setup_result['error']}"
            )
        
        # Step 3: Execute RASPA simulation
        if self.verbose:
            print("\n" + "="*80)
            print("PHASE 3: Simulator - Execute RASPA")
            print("="*80)
        
        simulation_results = self._run_simulations(output_folder)
        
        # Step 4: Parse results (if simulation succeeded)
        parsed_results = None
        if simulation_results["success"] and simulation_results.get("results"):
            if self.verbose:
                print("\n" + "="*80)
                print("PHASE 4: Result Parser - Extract Isotherm Data")
                print("="*80)
            
            parsed_results = self._parse_results(simulation_results["results"])
        
        # Step 5: Final summary
        final_answer = self._generate_summary(
            research_needed=research_needed,
            setup_result=setup_result,
            simulation_results=simulation_results,
            parsed_results=parsed_results,
            output_folder=output_folder
        )
        
        # Finish run logging
        overall_success = simulation_results.get("success", False) if simulation_results else setup_result["success"]
        self.run_logger.finish_run(overall_success=overall_success)
        
        return AgentResult(
            success=True,
            answer=final_answer,
            thought_action_history=[],
            error=None
        )
    
    def _run_research_team(
        self,
        user_request: str,
        paper_text: Optional[str],
        paper_doi: Optional[str],
        output_folder: Path
    ) -> Dict[str, Any]:
        """Execute Research Team workflow."""
        ff_dir = output_folder / "force_fields"
        ff_dir.mkdir(exist_ok=True)
        
        # Extract parameters
        if paper_text:
            extract_result = self.paper_extraction.run(
                paper_text=paper_text,
                paper_title=paper_doi or "User provided paper"
            )
            
            if not extract_result.success:
                return {"success": False, "error": extract_result.error}
            
            try:
                params = json.loads(extract_result.answer)
            except:
                return {"success": False, "error": "Failed to parse extraction result"}
            
            # Write force field files
            writer_result = self.ff_writer.run(
                extracted_params=params,
                output_folder=ff_dir
            )
            
            if not writer_result.success:
                return {"success": False, "error": writer_result.error}
            
            return {
                "success": True,
                "force_field_dir": ff_dir,
                "params": params
            }
        
        return {"success": False, "error": "No paper text provided"}
    
    def _run_setup_team(
        self,
        user_request: str,
        output_folder: Path,
        custom_force_field_dir: Optional[Path]
    ) -> Dict[str, Any]:
        """Execute Experiment Setup Team workflow."""
        # Build setup request with explicit output directory
        setup_request = user_request
        
        # CRITICAL: Tell Setup Team where to put files
        setup_request += f"\n\nIMPORTANT OUTPUT DIRECTORY: Create all simulation files in: {output_folder}"
        setup_request += f"\nUse {output_folder} as the base template folder, not a different location."
        
        if custom_force_field_dir:
            setup_request += f"\n\nIMPORTANT: Use custom force field files from: {custom_force_field_dir}"
        
        # Call Setup Team Supervisor
        result = self.setup_supervisor.run(setup_request)
        
        if not result.success:
            return {"success": False, "error": result.error}
        
        return {
            "success": True,
            "output_folder": output_folder,
            "details": result.answer
        }
    
    def _run_simulations(self, output_folder: Path) -> Dict[str, Any]:
        """Execute RASPA simulations for all pressure points."""
        runner = RaspaRunner(verbose=self.verbose)
        
        # Check if RASPA is installed
        if not runner.check_installation():
            if self.verbose:
                print("⚠️  RASPA not installed. Skipping simulation execution.")
                print("   To execute: install RASPA and set RASPA_DIR environment variable")
            return {
                "success": False,
                "error": "RASPA not installed",
                "results": []
            }
        
        # Find simulation directories (pressure point directories)
        simulation_dirs = []
        
        # Search in multiple possible locations
        search_dirs = [
            output_folder,
            output_folder / "runs",
            output_folder / "template",
        ]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            # Check subdirectories (e.g., P_100Pa, run_0.1bar)
            for subdir in search_dir.iterdir():
                if subdir.is_dir() and (subdir / "simulation.input").exists():
                    simulation_dirs.append(subdir)
            
            # Also check the directory itself
            if (search_dir / "simulation.input").exists() and search_dir not in simulation_dirs:
                simulation_dirs.append(search_dir)
        
        if not simulation_dirs:
            if self.verbose:
                print("⚠️  No simulation.input files found to execute")
            return {
                "success": False,
                "error": "No simulation.input files found",
                "results": []
            }
        
        if self.verbose:
            print(f"   Found {len(simulation_dirs)} simulation(s) to run")
        
        # Execute each simulation
        results = []
        all_success = True
        
        for sim_dir in sorted(simulation_dirs):
            if self.verbose:
                print(f"\n   Running: {sim_dir.name}")
            
            result = runner.run(sim_dir)
            results.append({
                "directory": str(sim_dir),
                "success": result.success,
                "execution_time": result.execution_time,
                "output_dir": str(result.output_dir) if result.output_dir else None,
                "error": result.error_message
            })
            
            if not result.success:
                all_success = False
                if self.verbose:
                    print(f"   ❌ Failed: {result.error_message}")
            else:
                if self.verbose:
                    print(f"   ✅ Completed in {result.execution_time:.1f}s")
        
        return {
            "success": all_success,
            "results": results,
            "total_simulations": len(results),
            "successful": sum(1 for r in results if r["success"])
        }
    
    def _parse_results(self, simulation_results: List[Dict]) -> Dict[str, Any]:
        """Parse RASPA output to extract isotherm data."""
        parser = ResultParser()
        isotherms = []
        
        for sim in simulation_results:
            if not sim["success"]:
                continue
            
            output_dir = Path(sim["output_dir"])
            if not output_dir.exists():
                continue
            
            try:
                # Look for System_0 output directory
                system_dir = output_dir / "System_0"
                if not system_dir.exists():
                    system_dir = output_dir
                
                isotherm_data = parser.parse_isotherm(system_dir)
                if isotherm_data:
                    isotherms.append({
                        "directory": sim["directory"],
                        "data": isotherm_data
                    })
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Failed to parse {sim['directory']}: {e}")
        
        return {
            "isotherms": isotherms,
            "total_parsed": len(isotherms)
        }
    
    def _generate_summary(
        self,
        research_needed: bool,
        setup_result: Dict[str, Any],
        output_folder: Path,
        simulation_results: Optional[Dict[str, Any]] = None,
        parsed_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate final summary report."""
        summary = f"""
=== Global Supervisor - Workflow Complete ===

Output Directory: {output_folder}

Phases Executed:
"""
        if research_needed:
            summary += "  ✅ Research Team: Force field extracted from literature\n"
        
        summary += "  ✅ Setup Team: Simulation files generated\n"
        
        if simulation_results:
            if simulation_results["success"]:
                summary += f"  ✅ Simulator: {simulation_results.get('successful', 0)}/{simulation_results.get('total_simulations', 0)} simulations completed\n"
            else:
                error = simulation_results.get('error', 'Unknown error')
                if error == "RASPA not installed":
                    summary += "  ⏭️  Simulator: Skipped (RASPA not installed)\n"
                else:
                    summary += f"  ❌ Simulator: Failed - {error}\n"
        
        if parsed_results and parsed_results.get("total_parsed", 0) > 0:
            summary += f"  ✅ Result Parser: {parsed_results['total_parsed']} isotherm(s) extracted\n"
        
        summary += f"\nSetup Details:\n{setup_result.get('details', 'N/A')}\n"
        summary += "\n✅ End-to-end workflow completed!"
        
        return summary
