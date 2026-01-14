#!/usr/bin/env python3
"""
End-to-End Workflow Example

Demonstrates the complete workflow from paper Appendix C:
  User Request → Global Supervisor → Research Team → Setup Team → Simulator → Results

Complete phases:
1. Research Team: Search paper → Extract parameters → Write force field files
2. Setup Team: Prepare structure → Integrate force field → Create simulation.input
3. Simulator: Execute RASPA simulations
4. Result Parser: Extract isotherm data

Usage:
    python end_to_end.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from gcmc_agent.global_supervisor import GlobalSupervisor


def main():
    # User request - exactly like paper Appendix C
    user_request = """
    Set up an adsorption isotherm simulation for MOR zeolite with CO2,
    evaluated at 10, 30, 100, 300, 1000, 3000 and 10000 Pa.
    The force field should be taken from 'Transferable force field for 
    carbon dioxide adsorption in zeolites' (2009), by Garcia-Sanchez et al.
    """
    
    print("="*80)
    print("GCMC-Agent: End-to-End Workflow")
    print("="*80)
    print(f"\nUser Request:\n{user_request.strip()}")
    print("\n" + "="*80)
    
    # Initialize
    config = DeepSeekConfig.from_env()
    client = OpenAIChatClient(config)
    
    workspace = Path(__file__).parent.parent
    output_dir = workspace / "runs" / "MOR_CO2_GarciaSanchez2009"
    
    supervisor = GlobalSupervisor(
        llm_client=client,
        workspace_root=workspace,
        verbose=True
    )
    
    # Run complete workflow
    # Phase 1: Research Team - search paper, extract force field
    # Phase 2: Setup Team - prepare structure, create input files
    # Phase 3: Simulator - execute RASPA (if installed)
    # Phase 4: Result Parser - extract isotherm data
    result = supervisor.run(
        user_request=user_request,
        output_folder=output_dir
    )
    
    # Report
    print("\n" + "="*80)
    if result.success:
        print("✓ Workflow Complete")
        print("="*80)
        print(result.answer)
    else:
        print("✗ Workflow Failed")
        print("="*80)
        print(f"Error: {result.error}")
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
