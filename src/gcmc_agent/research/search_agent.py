"""
Paper Search Agent - searches for force field papers using Semantic Scholar.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry
from .semantic_scholar import SemanticScholarClient


PAPER_SEARCH_PROMPT = """You are a Paper Search Agent for molecular simulation force fields.

Your role:
- Understand the user's force field requirements (adsorbate, structure type, simulation conditions)
- Search for relevant scientific papers using Semantic Scholar
- Evaluate paper relevance based on:
  * Mentions of the specific adsorbate molecule
  * Force field parameters (Lennard-Jones, charges, etc.)
  * Applicability to the simulation type (GCMC, MD, etc.)
- Return a ranked list of papers with DOI, title, and relevance reasoning

Search strategy:
1. Start with specific queries: "[adsorbate] force field parameters"
2. Broaden if needed: "[adsorbate] molecular simulation", "[adsorbate] adsorption"
3. Look for well-cited papers from reputable journals
4. Prefer papers with tables of parameters in abstract/metadata
5. IMPORTANT: After getting details for 3-5 relevant papers, STOP and provide Final Answer

Output format:
Provide Final Answer with JSON containing:
{
  "papers": [
    {
      "title": "...",
      "doi": "...",
      "paper_id": "...",  
      "relevance": "...",
      "year": ...,
      "citations": ...
    }
  ],
  "recommended": "[paper_id of most relevant]",
  "reasoning": "..."
}

Guidelines:
- Search at least 3 different query variations
- Return top 5 most relevant papers
- If no good papers found, explain why and suggest alternatives
- Check if full text is available (PDF link)
"""


class PaperSearchAgent:
    """
    Paper Search Agent - finds force field papers using Semantic Scholar.
    
    Uses LLM to:
    - Formulate effective search queries
    - Evaluate paper relevance
    - Select most appropriate papers
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
        
        # Create tool registry with semantic scholar tools
        self.tools = create_tool_registry(workspace_root)
        self._add_search_tools()
        
        self.agent = ReActAgent(
            name="PaperSearchAgent",
            system_prompt=PAPER_SEARCH_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=20,  # Increased for multiple search queries and paper detail lookups
            verbose=verbose,
            log_file=log_file,
        )
    
    def _add_search_tools(self):
        """Add Semantic Scholar search tools."""
        import os
        
        # Initialize Semantic Scholar client
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.s2_client = SemanticScholarClient(api_key=api_key)
        
        def search_papers(query: str, limit: int = 5) -> str:
            """
            Search for papers on Semantic Scholar.
            
            Args:
                query: Search query string
                limit: Maximum number of results (default 5)
                
            Returns:
                JSON string with search results
            """
            try:
                results = self.s2_client.search(query=query, limit=limit)
                
                if not results:
                    return f"No papers found for query: '{query}'"
                
                # Format results
                papers = []
                for r in results:
                    paper = {
                        "paper_id": r.get("paperId", ""),
                        "title": r.get("title", ""),
                        "year": r.get("year"),
                        "authors": [a.get("name") for a in r.get("authors", [])],
                        "venue": r.get("venue", ""),
                        "doi": r.get("externalIds", {}).get("DOI", ""),
                        "abstract": r.get("abstract", "")[:500] + "..." if r.get("abstract") else "",
                        "url": r.get("url", "")
                    }
                    papers.append(paper)
                
                import json
                return json.dumps({"query": query, "count": len(papers), "papers": papers}, indent=2)
                
            except Exception as e:
                return f"Error searching papers: {str(e)}"
        
        def get_paper_details(paper_id: str) -> str:
            """
            Get detailed information about a specific paper.
            
            Args:
                paper_id: Semantic Scholar paper ID or DOI
                
            Returns:
                JSON string with paper details
            """
            try:
                paper = self.s2_client.paper(paper_id=paper_id)
                
                import json
                return json.dumps({
                    "paper_id": paper.get("paperId", ""),
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "year": paper.get("year"),
                    "venue": paper.get("venue", ""),
                    "authors": [a.get("name") for a in paper.get("authors", [])],
                    "doi": paper.get("externalIds", {}).get("DOI", ""),
                    "arxiv": paper.get("externalIds", {}).get("ArXiv", ""),
                    "url": paper.get("url", "")
                }, indent=2)
                
            except Exception as e:
                return f"Error getting paper details: {str(e)}"
        
        self.tools.register_function(
            name="search_papers",
            description="Search for scientific papers on Semantic Scholar",
            func=search_papers,
            parameters={
                "query": "string - search query",
                "limit": "integer - max results (default 5)"
            }
        )
        
        self.tools.register_function(
            name="get_paper_details",
            description="Get detailed information about a specific paper",
            func=get_paper_details,
            parameters={
                "paper_id": "string - Semantic Scholar paper ID or DOI"
            }
        )
    
    def run(
        self,
        adsorbate: str,
        structure_type: str = None,
        simulation_type: str = "adsorption",
        additional_requirements: str = ""
    ) -> AgentResult:
        """
        Search for force field papers.
        
        Args:
            adsorbate: Target molecule (e.g., "CO2", "CH4")
            structure_type: Type of structure (e.g., "zeolite", "MOF")
            simulation_type: Simulation type (e.g., "adsorption", "diffusion")
            additional_requirements: Any additional search requirements
            
        Returns:
            AgentResult with JSON containing recommended papers
        """
        structure_info = f" in {structure_type}" if structure_type else ""
        add_info = f"\n{additional_requirements}" if additional_requirements else ""
        
        task = f"""Find force field parameters for {adsorbate}{structure_info} molecular simulation ({simulation_type}).

Requirements:
- Search for papers containing Lennard-Jones parameters (epsilon, sigma)
- Prefer papers with tabulated force field parameters  
- Look for TraPPE, EPM2, or other standard force fields for {adsorbate}
- Papers should be suitable for GCMC/Monte Carlo simulations{add_info}

Steps:
1. Search with query variations (try 2-3 queries):
   - "{adsorbate} force field parameters"
   - "{adsorbate} Lennard-Jones parameters"
   - "TraPPE {adsorbate}"
   
2. From search results, select top 3-5 papers based on:
   - Abstract mentions force field parameters
   - Year (prefer recent, but classic papers OK)
   - Citations (well-established work)
   
3. Get details for ONLY the 3-5 most promising papers using get_paper_details
   (DO NOT get details for every paper - be selective)

4. After getting details for 3-5 papers, IMMEDIATELY provide Final Answer with JSON containing:
   - List of top papers with paper_id, title, DOI, relevance reasoning
   - Recommended paper_id (the best one)
   - Overall assessment

CRITICAL: Do not endlessly search. After checking 3-5 paper details, output your Final Answer.

Remember: We need actual numerical parameters, not just theory papers.
"""
        
        return self.agent.run(task)
