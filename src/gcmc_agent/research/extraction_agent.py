"""
Paper Extraction Agent - extracts force field parameters from papers using LLM.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


PAPER_EXTRACTION_PROMPT = """You are a Paper Extraction Agent specialized in extracting force field parameters.

Your role:
- Read scientific papers (text format)
- Identify force field parameter tables
- Extract Lennard-Jones parameters (epsilon, sigma)
- Extract partial charges if available
- Handle different table formats and unit conventions

Common formats to recognize:
1. TraPPE format: atom type, epsilon (K), sigma (Å)
2. OPLS format: atom type, epsilon (kcal/mol), sigma (Å)
3. Table with multiple columns: may include mass, charge, epsilon, sigma
4. Section format: parameters grouped by atom type

Unit conversions:
- Epsilon: K, kcal/mol, kJ/mol (note which unit is used)
- Sigma: Å, nm (note which unit is used)
- Charge: |e| (elementary charge)

Atom naming:
- Understand chemical notation (C_co2, O_co2, etc.)
- Map to chemical elements
- Preserve original atom type names

Output format:
Your Final Answer MUST be valid JSON in this exact format:
{
  "source": "paper title or DOI",
  "force_field_name": "TraPPE / OPLS / etc",
  "atoms": [
    {
      "atom_type": "...",
      "element": "...",
      "mass": ...,
      "charge": ...,
      "epsilon": ...,
      "epsilon_unit": "K / kcal/mol / kJ/mol",
      "sigma": ...,
      "sigma_unit": "Angstrom / nm"
    }
  ],
  "mixing_rules": "Lorentz-Berthelot / geometric / ...",
  "notes": "any special comments",
  "extraction_confidence": "high / medium / low"
}

CRITICAL: Output the JSON directly as your Final Answer. Do NOT use write_file tool.

Guidelines:
- Be precise with numbers (don't round)
- Preserve scientific notation if used
- Note any assumptions made
- Flag ambiguous cases
- If parameters span multiple tables, combine them
- Check for parameter updates in supplementary material
"""


class PaperExtractionAgent:
    """
    Paper Extraction Agent - extracts force field parameters using LLM.
    
    Uses LLM to:
    - Parse tables in different formats
    - Handle unit conversions
    - Understand atom naming conventions
    - Extract complete parameter sets
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
        
        self.agent = ReActAgent(
            name="PaperExtractionAgent",
            system_prompt=PAPER_EXTRACTION_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=30,  # Increased for complex table parsing workflows
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        paper_text: str,
        adsorbate: str = None,
        paper_title: str = "",
        target_force_field: str = None
    ) -> AgentResult:
        """
        Extract force field parameters from paper text.
        
        Args:
            paper_text: Full text or relevant sections of the paper
            adsorbate: Target molecule (optional, helps focus extraction)
            paper_title: Paper title for reference
            target_force_field: Specific force field name to look for (optional)
            
        Returns:
            AgentResult with JSON containing extracted parameters
        """
        adsorbate_hint = f" Focus on parameters for {adsorbate}." if adsorbate else ""
        ff_hint = f" Look specifically for {target_force_field} parameters." if target_force_field else ""
        title_info = f"\nPaper: {paper_title}" if paper_title else ""
        
        # For very long papers, we might need to provide the text in chunks
        # For now, pass it directly (consider chunking strategy later)
        text_preview = paper_text[:2000] if len(paper_text) > 2000 else paper_text
        has_more = len(paper_text) > 2000
        
        task = f"""Extract force field parameters from this scientific paper.{title_info}{adsorbate_hint}{ff_hint}

PAPER TEXT ({"first 2000 chars, full text available via read_file" if has_more else "complete"}):
```
{text_preview}
```

Your extraction workflow:
1. Scan the text for force field parameter tables
   - Look for keywords: "force field", "Lennard-Jones", "LJ parameters", "epsilon", "sigma", "TraPPE", "OPLS"
   - Tables often in Methods section or Supplementary Material
   
2. Identify table structure:
   - Column headers (atom type, epsilon, sigma, charge, mass, etc.)
   - Units (K, kcal/mol, Angstrom, etc.)
   - Note any footnotes or special notations
   
3. Extract parameters systematically:
   - For each atom type, record all available parameters
   - Preserve exact numerical values
   - Note the units used
   
4. Check for mixing rules:
   - Usually stated as "Lorentz-Berthelot", "geometric mean", etc.
   - Often in Methods section
   
5. Validate completeness:
   - Do we have all atoms for the molecule?
   - Are epsilon and sigma present for each?
   - Any missing critical information?

6. Output Final Answer directly:
   - Provide complete JSON following the format in system prompt
   - Do NOT write to file and then read it back for verification
   - Output the JSON directly in your Final Answer

Remember: Accuracy is critical - these parameters will be used in simulations!
"""
        
        # Store full text in a temporary file if needed
        if has_more:
            temp_file = self.workspace_root / "temp_paper.txt"
            temp_file.write_text(paper_text, encoding='utf-8')
            if self.verbose:
                print(f"[PaperExtractionAgent] Stored full paper text in {temp_file}")
        
        return self.agent.run(task)
    
    def run_from_file(
        self,
        paper_file: Path,
        adsorbate: str = None,
        target_force_field: str = None
    ) -> AgentResult:
        """
        Extract force field parameters from a paper file.
        
        Args:
            paper_file: Path to paper text file
            adsorbate: Target molecule (optional)
            target_force_field: Specific force field name (optional)
            
        Returns:
            AgentResult with extracted parameters
        """
        if not paper_file.exists():
            from ..react import AgentResult
            return AgentResult(
                success=False,
                answer="",
                thought_action_history=[],
                error=f"Paper file not found: {paper_file}"
            )
        
        paper_text = paper_file.read_text(encoding='utf-8', errors='ignore')
        paper_title = paper_file.stem
        
        return self.run(
            paper_text=paper_text,
            adsorbate=adsorbate,
            paper_title=paper_title,
            target_force_field=target_force_field
        )
