"""
Force Field Writer Agent - converts extracted parameters to RASPA format.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json

from ..react import ReActAgent, AgentResult
from ..client import OpenAIChatClient
from ..tools.registry import create_tool_registry


FF_WRITER_PROMPT = """You are a Force Field Writer Agent specialized in RASPA force field format.

Your role:
- Take extracted force field parameters (JSON)
- Convert to RASPA format files:
  * pseudo_atoms.def - atom type definitions
  * force_field_mixing_rules.def - mixing rules and LJ parameters
- Handle unit conversions
- Apply mixing rules if needed

CRITICAL: RASPA format is FIXED-WIDTH columns. Follow examples EXACTLY!

1. pseudo_atoms.def FORMAT (EXACT spacing required):
```
#number of pseudo atoms
4
#type      print   as    chem  oxidation   mass        charge   polarization B-factor radii  connectivity anisotropic anisotropic-type   tinker-type
O          yes     O     O     0           15.9994     -1.025   0.0          1.0      0.68   0            0           relative           0
Si         yes     Si    Si    0           28.0855     2.05     0.0          1.0      0.7    0            0           relative           0
C_co2      yes     C     C     0           12.0        0.6512   0.0          1.0      0.720  0            0           relative           0
O_co2      yes     O     O     0           15.9994    -0.3256   0.0          1.0      0.68   0            0           relative           0
```

Rules:
- Line 2: Integer number of atoms
- Line 4+: Each atom on one line, space-separated
- Columns: type, print(yes/no), as(element), chem(element), oxidation(0), mass, charge, polarization(0.0), B-factor(1.0), radii(~0.7), connectivity(0), anisotropic(0), aniso-type(relative), tinker-type(0)

2. force_field_mixing_rules.def FORMAT:
```
# general rule for shifted vs truncated
shifted
# general rule tailcorrections
no
# number of defined interactions
4
# type interaction, parameters.    IMPORTANT: define shortest matches first
O              lennard-jones    93.53     3.033        // Garcia-Sanchez 2009
Si             lennard-jones    0.0       0.0          // Dummy atom
C_co2          lennard-jones    27.0      2.80         // TraPPE
O_co2          lennard-jones    79.0      3.05         // TraPPE
# general mixing rule for Lennard-Jones
Lorentz-Berthelot
```

Rules:
- Line 2: "shifted" or "truncated"
- Line 4: "yes" or "no" for tail corrections
- Line 6: Integer number of interactions
- Line 8+: type, "lennard-jones", epsilon(K), sigma(Å), // comment
- Last line: Mixing rule name

Unit conversions:
- Epsilon: Convert to Kelvin (K)
  * From kcal/mol: multiply by 503.22
  * From kJ/mol: multiply by 120.27
- Sigma: Convert to Angstrom
  * From nm: multiply by 10.0
- Charge: Keep in elementary charge units |e|

CRITICAL FORMATTING RULES:
1. Use SPACES for column alignment (NOT tabs)
2. Atom types should be left-aligned
3. Numbers should maintain precision (don't round excessively)
4. Comments use // (not #)
5. Blank lines only where shown in examples
6. First line MUST be a comment starting with #

Example task:
Input: {"atoms": [{"element": "O", "epsilon_K": 93.53, "sigma_A": 3.033, "charge": -1.025}]}
Output pseudo_atoms.def:
```
#number of pseudo atoms
1
#type      print   as    chem  oxidation   mass        charge   polarization B-factor radii  connectivity anisotropic anisotropic-type   tinker-type
O          yes     O     O     0           15.9994     -1.025   0.0          1.0      0.68   0            0           relative           0
```

Output force_field_mixing_rules.def:
```
# general rule for shifted vs truncated
shifted
# general rule tailcorrections
no
# number of defined interactions
1
# type interaction, parameters.
O              lennard-jones    93.53     3.033
# general mixing rule for Lennard-Jones
Lorentz-Berthelot
```

ALWAYS write both files using write_file tool. Never skip files.
"""


class ForceFieldWriterAgent:
    """
    Force Field Writer Agent - converts parameters to RASPA format.
    
    Uses LLM to:
    - Parse extracted parameter JSON
    - Perform unit conversions
    - Generate properly formatted RASPA files
    - Apply mixing rules if needed
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
        
        # Create tool registry (file writing tools)
        self.tools = create_tool_registry(workspace_root)
        
        self.agent = ReActAgent(
            name="ForceFieldWriterAgent",
            system_prompt=FF_WRITER_PROMPT,
            llm_client=llm_client,
            tools=self.tools.to_dict(),
            model=model,
            max_iterations=15,
            verbose=verbose,
            log_file=log_file,
        )
    
    def run(
        self,
        extracted_params: Dict[str, Any],
        output_folder: Path,
        mixing_rule: str = None
    ) -> AgentResult:
        """
        Convert extracted parameters to RASPA force field files.
        
        Args:
            extracted_params: JSON dict from PaperExtractionAgent
            output_folder: Where to write force field files
            mixing_rule: Override mixing rule (default: use from extracted_params)
            
        Returns:
            AgentResult with status and file locations
        """
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Format extracted params as readable text
        params_str = json.dumps(extracted_params, indent=2)
        
        mixing_hint = f"\nUse mixing rule: {mixing_rule}" if mixing_rule else ""
        
        task = f"""Convert these extracted force field parameters to RASPA format files.

EXTRACTED PARAMETERS:
```json
{params_str}
```

OUTPUT FOLDER: {output_folder}{mixing_hint}

Your conversion workflow:

1. Analyze the input JSON:
   - How many atoms?
   - What units are used?
   - Is mixing rule specified?
   - Are charges included?

2. Perform unit conversions:
   - Convert epsilon to Kelvin if needed
   - Convert sigma to Angstrom if needed
   - Keep charges in |e|

3. Create pseudo_atoms.def:
   - Use write_file tool
   - Path: {output_folder}/pseudo_atoms.def
   - Include header with count
   - One line per atom type
   - Use mass from JSON or default by element

4. Create force_field_mixing_rules.def:
   - Use write_file tool
   - Path: {output_folder}/force_field_mixing_rules.def
   - Specify mixing rule (from JSON or default to Lorentz-Berthelot)
   - Standard RASPA format

5. Create force_field.def:
   - Use write_file tool
   - Path: {output_folder}/force_field.def
   - Include self-interactions (atom-atom)
   - Use "lennard-jones" potential type
   - Parameters: epsilon (K), sigma (Angstrom)

6. Validate:
   - Check all files were written
   - Verify format matches RASPA requirements
   - Confirm numerical values are reasonable

7. Provide Final Answer with:
   - Success status
   - List of files created with paths
   - Summary of parameters written
   - Any warnings or assumptions made

Remember: RASPA is very strict about format - follow examples exactly!
"""
        
        return self.agent.run(task)
    
    def run_from_json_file(
        self,
        json_file: Path,
        output_folder: Path,
        mixing_rule: str = None
    ) -> AgentResult:
        """
        Convert parameters from a JSON file to RASPA format.
        
        Args:
            json_file: Path to JSON file with extracted parameters
            output_folder: Where to write force field files
            mixing_rule: Override mixing rule (optional)
            
        Returns:
            AgentResult with status
        """
        if not json_file.exists():
            from ..react import AgentResult
            return AgentResult(
                success=False,
                answer="",
                thought_action_history=[],
                error=f"JSON file not found: {json_file}"
            )
        
        with open(json_file, 'r') as f:
            extracted_params = json.load(f)
        
        return self.run(
            extracted_params=extracted_params,
            output_folder=output_folder,
            mixing_rule=mixing_rule
        )
