#!/usr/bin/env python3
"""
Table 1 Evaluation Script - Experiment Setup Team

Tests the ability to generate correct RASPA simulation files for different scenarios.
Based on paper Table 1 with 7 test scenarios.
"""

from pathlib import Path
from typing import Dict, List, Any
import json
import time
from dotenv import load_dotenv

from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from gcmc_agent.agents.structure import StructureExpert
from gcmc_agent.agents.forcefield import ForceFieldExpert
from gcmc_agent.agents.simulation_input import SimulationInputExpert
from gcmc_agent.agents.coding import CodingExpert
from gcmc_agent.agents.evaluator import Evaluator


# Test scenarios from paper Table 1
TEST_SCENARIOS = [
    {
        "id": "1x1_isotherm",
        "name": "1 structure × 1 adsorbate - Isotherm",
        "n_structures": 1,
        "n_adsorbates": 1,
        "simulation_type": "isotherm",
        "structures": ["MOR"],
        "adsorbates": ["CO2"],
        "expected_success_rate": 1.00,
        "expected_execution_rate": 1.00
    },
    {
        "id": "1x3_isotherm",
        "name": "1 structure × 3 adsorbate - Isotherm",
        "n_structures": 1,
        "n_adsorbates": 3,
        "simulation_type": "isotherm",
        "structures": ["HKUST-1"],
        "adsorbates": ["CO2", "CH4", "N2"],
        "expected_success_rate": 1.00,
        "expected_execution_rate": 0.95
    },
    {
        "id": "500x1_isotherm",
        "name": "500 structure × 1 adsorbate - Isotherm",
        "n_structures": 500,
        "n_adsorbates": 1,
        "simulation_type": "isotherm",
        "structures": None,  # Would load from database
        "adsorbates": ["CO2"],
        "expected_success_rate": 0.98,
        "expected_execution_rate": 0.92,
        "note": "Requires 500 structure dataset"
    },
    {
        "id": "500x3_isotherm",
        "name": "500 structure × 3 adsorbate - Isotherm",
        "n_structures": 500,
        "n_adsorbates": 3,
        "simulation_type": "isotherm",
        "structures": None,
        "adsorbates": ["CO2", "CH4", "N2"],
        "expected_success_rate": 0.96,
        "expected_execution_rate": 0.88,
        "note": "Requires 500 structure dataset"
    },
    {
        "id": "1x1_hoa",
        "name": "1 structure × 1 adsorbate - HOA",
        "n_structures": 1,
        "n_adsorbates": 1,
        "simulation_type": "hoa",
        "structures": ["MOR"],
        "adsorbates": ["CO2"],
        "expected_success_rate": 1.00,
        "expected_execution_rate": 0.98
    },
    {
        "id": "500x1_hoa",
        "name": "500 structure × 1 adsorbate - HOA",
        "n_structures": 500,
        "n_adsorbates": 1,
        "simulation_type": "hoa",
        "structures": None,
        "adsorbates": ["CO2"],
        "expected_success_rate": 0.97,
        "expected_execution_rate": 0.90,
        "note": "Requires 500 structure dataset"
    },
    {
        "id": "500x3_hoa",
        "name": "500 structure × 3 adsorbate - HOA",
        "n_structures": 500,
        "n_adsorbates": 3,
        "simulation_type": "hoa",
        "structures": None,
        "adsorbates": ["CO2", "CH4", "N2"],
        "expected_success_rate": 0.94,
        "expected_execution_rate": 0.85,
        "note": "Requires 500 structure dataset"
    }
]


def run_single_setup(
    scenario: Dict,
    structure: str,
    adsorbate: str,
    output_dir: Path,
    llm_client: OpenAIChatClient,
    workspace_root: Path,
    run_id: int
) -> Dict[str, Any]:
    """
    Run a single simulation setup task.
    
    Returns:
        Dictionary with success metrics
    """
    run_name = f"{scenario['id']}_{structure}_{adsorbate}_run{run_id}"
    template_dir = output_dir / run_name / "template"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "run_name": run_name,
        "structure": structure,
        "adsorbate": adsorbate,
        "simulation_type": scenario["simulation_type"],
        "success": False,
        "execution_ready": False,
        "errors": [],
        "files_created": []
    }
    
    try:
        # Step 1: Structure Expert
        print(f"  📐 [{run_name}] StructureExpert...")
        structure_expert = StructureExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model="deepseek-chat",
            verbose=False
        )
        
        struct_result = structure_expert.run(
            structure_name=structure,
            template_folder=template_dir
        )
        
        if not struct_result.success:
            result["errors"].append(f"StructureExpert failed: {struct_result.error}")
            return result
        
        # Step 2: ForceField Expert
        print(f"  🔬 [{run_name}] ForceFieldExpert...")
        ff_expert = ForceFieldExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model="deepseek-chat",
            verbose=False
        )
        
        structure_file = template_dir / f"{structure}.cif"
        ff_result = ff_expert.run(
            structure_file=structure_file,
            adsorbate=adsorbate,
            template_folder=template_dir
        )
        
        if not ff_result.success:
            result["errors"].append(f"ForceFieldExpert failed: {ff_result.error}")
            return result
        
        # Step 3: SimulationInput Expert
        print(f"  ⚙️ [{run_name}] SimulationInputExpert...")
        siminput_expert = SimulationInputExpert(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model="deepseek-chat",
            verbose=False
        )
        
        siminput_result = siminput_expert.run(
            simulation_type=scenario["simulation_type"],
            structure_name=structure,
            adsorbate=adsorbate,
            template_folder=template_dir,
            parameters={
                "temperature": 298,
                "pressures": [1e4, 1e5, 1e6]
            }
        )
        
        if not siminput_result.success:
            result["errors"].append(f"SimulationInputExpert failed: {siminput_result.error}")
            return result
        
        # Step 4: Verify files
        required_files = [
            f"{structure}.cif",
            "pseudo_atoms.def",
            "force_field_mixing_rules.def",
            "force_field.def",
            "simulation.input"
        ]
        
        missing_files = []
        for fname in required_files:
            fpath = template_dir / fname
            if fpath.exists():
                result["files_created"].append(fname)
            else:
                missing_files.append(fname)
        
        if missing_files:
            result["errors"].append(f"Missing files: {missing_files}")
            return result
        
        # Step 5: Evaluator check
        print(f"  ✅ [{run_name}] Evaluator...")
        evaluator = Evaluator(
            llm_client=llm_client,
            workspace_root=workspace_root,
            model="deepseek-chat",
            verbose=False
        )
        
        eval_result = evaluator.run(
            template_folder=template_dir,
            agent_name="Experiment Setup Team",
            task_description=f"{structure}/{adsorbate} {scenario['simulation_type']} setup"
        )
        
        # Parse evaluation
        if eval_result.success and "PASS" in eval_result.answer.upper():
            result["success"] = True
            result["execution_ready"] = True
        elif eval_result.success and "FAIL" in eval_result.answer.upper():
            result["success"] = True  # Setup completed
            result["execution_ready"] = False  # But has issues
            result["errors"].append("Evaluator found issues")
        else:
            result["errors"].append(f"Evaluator failed: {eval_result.error}")
        
        return result
        
    except Exception as e:
        result["errors"].append(f"Exception: {str(e)}")
        return result


def run_scenario_evaluation(
    scenario: Dict,
    output_dir: Path,
    llm_client: OpenAIChatClient,
    workspace_root: Path,
    num_runs: int = 5
) -> Dict[str, Any]:
    """
    Run evaluation for a single scenario.
    
    Returns:
        Results dictionary with metrics
    """
    print(f"\n{'='*80}")
    print(f"Scenario: {scenario['name']}")
    print(f"{'='*80}")
    
    # Check if scenario requires large dataset
    if scenario.get("note") and "500 structure" in scenario["note"]:
        print(f"⚠️  SKIPPED - {scenario['note']}")
        return {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "skipped": True,
            "reason": scenario["note"],
            "expected_success_rate": scenario["expected_success_rate"],
            "expected_execution_rate": scenario["expected_execution_rate"]
        }
    
    all_results = []
    
    # Run tests
    for run_id in range(num_runs):
        for structure in scenario["structures"]:
            for adsorbate in scenario["adsorbates"]:
                print(f"\n  Run {run_id+1}/{num_runs}: {structure} + {adsorbate}")
                
                result = run_single_setup(
                    scenario=scenario,
                    structure=structure,
                    adsorbate=adsorbate,
                    output_dir=output_dir,
                    llm_client=llm_client,
                    workspace_root=workspace_root,
                    run_id=run_id
                )
                
                all_results.append(result)
                
                # Brief status
                status = "✅" if result["success"] else "❌"
                exec_status = "🟢" if result["execution_ready"] else "🟡"
                print(f"    Setup: {status}  Executable: {exec_status}")
                
                time.sleep(1)  # Rate limiting
    
    # Calculate metrics
    total = len(all_results)
    successful = sum(1 for r in all_results if r["success"])
    executable = sum(1 for r in all_results if r["execution_ready"])
    
    success_rate = successful / total if total > 0 else 0
    execution_rate = executable / total if total > 0 else 0
    
    print(f"\n📊 Results:")
    print(f"  Success Rate: {success_rate:.2%} (expected: {scenario['expected_success_rate']:.2%})")
    print(f"  Execution Rate: {execution_rate:.2%} (expected: {scenario['expected_execution_rate']:.2%})")
    
    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "skipped": False,
        "num_tests": total,
        "successful": successful,
        "executable": executable,
        "success_rate": success_rate,
        "execution_rate": execution_rate,
        "expected_success_rate": scenario["expected_success_rate"],
        "expected_execution_rate": scenario["expected_execution_rate"],
        "individual_results": all_results
    }


def main():
    """Run Table 1 evaluation."""
    load_dotenv()
    
    # Setup
    output_dir = Path("evaluation/table1_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    workspace_root = Path.cwd()
    
    # Initialize LLM
    cfg = DeepSeekConfig.from_env()
    llm_client = OpenAIChatClient(cfg)
    
    print("="*80)
    print("TABLE 1 EVALUATION - EXPERIMENT SETUP TEAM")
    print("="*80)
    print(f"\nOutput directory: {output_dir}")
    print(f"Number of scenarios: {len(TEST_SCENARIOS)}")
    print(f"Runs per scenario: 5\n")
    
    all_scenario_results = []
    
    # Run each scenario
    for scenario in TEST_SCENARIOS:
        result = run_scenario_evaluation(
            scenario=scenario,
            output_dir=output_dir,
            llm_client=llm_client,
            workspace_root=workspace_root,
            num_runs=5
        )
        all_scenario_results.append(result)
    
    # Save results
    results_file = Path("evaluation/table1_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenarios": all_scenario_results,
            "summary": {
                "total_scenarios": len(TEST_SCENARIOS),
                "completed_scenarios": sum(1 for r in all_scenario_results if not r.get("skipped")),
                "skipped_scenarios": sum(1 for r in all_scenario_results if r.get("skipped")),
            }
        }, f, indent=2)
    
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\nResults saved to: {results_file}")
    
    # Print comparison table
    print(f"\n{'Scenario':<30} {'Success':<15} {'Execution':<15} {'Status'}")
    print("-"*80)
    for r in all_scenario_results:
        if r.get("skipped"):
            print(f"{r['scenario_id']:<30} {'SKIPPED':<15} {'SKIPPED':<15} {r.get('reason', '')}")
        else:
            success_str = f"{r['success_rate']:.1%} ({r['expected_success_rate']:.1%})"
            exec_str = f"{r['execution_rate']:.1%} ({r['expected_execution_rate']:.1%})"
            
            # Check if meets expectations
            success_ok = r['success_rate'] >= r['expected_success_rate'] - 0.05
            exec_ok = r['execution_rate'] >= r['expected_execution_rate'] - 0.05
            status = "✅" if (success_ok and exec_ok) else "⚠️"
            
            print(f"{r['scenario_id']:<30} {success_str:<15} {exec_str:<15} {status}")
    
    print(f"\n✅ Evaluation complete!")


if __name__ == "__main__":
    main()
