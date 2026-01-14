#!/usr/bin/env python3
"""
Test logging system with rich formatting.
"""

from pathlib import Path
import time
from src.gcmc_agent.logging_utils import RunLogger, LLMCallLogger


def test_run_logger():
    """Test RunLogger with rich output."""
    print("\n" + "="*80)
    print("Testing RunLogger with Rich Formatting")
    print("="*80 + "\n")
    
    # Initialize logger
    logger = RunLogger(run_name="test_demo")
    
    # Simulate agent workflow
    time.sleep(0.5)
    
    logger.record_agent_start("StructureExpert", "Find MOR.cif structure file")
    time.sleep(1)
    logger.record_agent_finish("StructureExpert", success=True, iterations=3)
    
    time.sleep(0.5)
    
    logger.record_agent_start("ForceFieldExpert", "Setup force field for CO2")
    time.sleep(1.5)
    logger.record_agent_finish("ForceFieldExpert", success=True, iterations=5)
    
    time.sleep(0.5)
    
    logger.record_agent_start("SimulationInputExpert", "Create isotherm template")
    time.sleep(1)
    logger.record_agent_finish("SimulationInputExpert", success=True, iterations=4)
    
    time.sleep(0.5)
    
    logger.record_agent_start("CodingExpert", "Generate batch scripts")
    time.sleep(0.8)
    logger.record_agent_finish("CodingExpert", success=False, iterations=2, error="Template not found")
    
    time.sleep(0.5)
    
    # Record workflow events
    logger.record_workflow_event(
        "team_handoff",
        "Research Team → Setup Team",
        {"papers": 5, "structure": "MOR", "adsorbate": "CO2"}
    )
    
    # Finish run
    logger.finish_run(overall_success=True)
    
    print(f"\n✅ Logs saved to: {logger.run_dir}")
    print(f"   - run_metadata.json")
    print(f"   - SUMMARY.txt")
    

def test_llm_logger():
    """Test LLMCallLogger."""
    print("\n" + "="*80)
    print("Testing LLMCallLogger")
    print("="*80 + "\n")
    
    log_dir = Path("logs/test_llm")
    log_dir.mkdir(parents=True, exist_ok=True)
    llm_logger = LLMCallLogger(log_file=log_dir / "llm_calls.jsonl")
    
    # Simulate LLM calls
    request1 = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Find MOR structure"}],
        "temperature": 0.7
    }
    response1 = {
        "choices": [{"message": {"content": "Found MOR.cif in database"}}],
        "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200}
    }
    llm_logger.log_call(request1, response1, None, 0.5, metadata={"agent_name": "StructureExpert"})
    
    time.sleep(0.2)
    
    request2 = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "Create force field for CO2"}],
        "temperature": 0.7
    }
    response2 = {
        "choices": [{"message": {"content": "Generated TraPPE force field"}}],
        "usage": {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}
    }
    llm_logger.log_call(request2, response2, None, 1.2, metadata={"agent_name": "ForceFieldExpert"})
    
    # Get summary
    summary = llm_logger.get_summary()
    print(f"✅ Total calls: {summary['total_calls']}")
    print(f"   Total tokens: {summary['total_tokens']}")
    print(f"   Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"   Log file: {llm_logger.log_file}")
    

if __name__ == "__main__":
    test_run_logger()
    test_llm_logger()
    
    print("\n" + "="*80)
    print("✨ All logging tests completed!")
    print("="*80 + "\n")
