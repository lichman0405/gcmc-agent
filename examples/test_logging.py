#!/usr/bin/env python3
"""
Test the enhanced logging system.

Demonstrates:
- LLM call logging
- Agent execution tracking  
- Workflow event logging
- Log analysis and replay
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcmc_agent.client import OpenAIChatClient
from gcmc_agent.config import DeepSeekConfig
from gcmc_agent.logging_utils import RunLogger, LLMCallLogger
from gcmc_agent.react.base import ReActAgent


def simple_tool(query: str) -> str:
    """A simple example tool."""
    return f"Tool result for: {query}"


def test_logging_system():
    """Test the complete logging system."""
    
    print("=" * 80)
    print("TESTING ENHANCED LOGGING SYSTEM")
    print("=" * 80)
    
    # 1. Initialize loggers
    run_logger = RunLogger(run_name="logging_test")
    llm_logger = LLMCallLogger(run_logger.run_dir / "llm_calls.jsonl")
    
    print(f"\n✓ Created run directory: {run_logger.run_dir}")
    print(f"✓ LLM calls will be logged to: {llm_logger.log_file}")
    
    # 2. Initialize LLM client with logging
    try:
        config = DeepSeekConfig.from_env()
        client = OpenAIChatClient(config, llm_logger=llm_logger)
        print(f"✓ LLM client initialized")
    except Exception as e:
        print(f"\n⚠️  Could not initialize LLM client: {e}")
        print("   This test requires valid API credentials")
        print("   Proceeding with logging structure test only...")
        run_logger.finish_run(overall_success=False)
        return run_logger.run_dir
    
    # 3. Record workflow events
    run_logger.record_workflow_event(
        event_type="initialization",
        description="Test run started",
        data={"test_type": "logging_system"}
    )
    
    # 4. Create and run a test agent
    tools = {
        "simple_tool": {
            "description": "A simple test tool",
            "parameters": {"query": "str"},
            "func": simple_tool
        }
    }
    
    agent = ReActAgent(
        name="TestAgent",
        system_prompt="You are a test agent. Use the simple_tool to answer questions.",
        llm_client=client,
        tools=tools,
        model="deepseek-chat",
        max_iterations=3,
        verbose=True,
        log_file=run_logger.get_agent_log_file("TestAgent"),
        llm_call_logger=llm_logger
    )
    
    run_logger.record_agent_start("TestAgent", "Test task: What is 2+2?")
    
    print("\n" + "=" * 80)
    print("RUNNING TEST AGENT")
    print("=" * 80)
    
    try:
        result = agent.run("What is 2 + 2? Use the simple_tool.")
        
        run_logger.record_agent_finish(
            "TestAgent",
            success=result.success,
            iterations=len(result.thought_action_history)
        )
        
        print(f"\n✓ Agent completed: {result.success}")
        print(f"✓ Answer: {result.answer}")
        
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        run_logger.record_agent_finish("TestAgent", success=False, iterations=0, error=str(e))
    
    # 5. Finish run
    run_logger.record_workflow_event(
        event_type="completion",
        description="Test run completed"
    )
    run_logger.finish_run(overall_success=True)
    
    # 6. Show summary
    print("\n" + "=" * 80)
    print("RUN SUMMARY")
    print("=" * 80)
    
    print(f"\nRun directory: {run_logger.run_dir}")
    print(f"LLM calls: {llm_logger.call_count}")
    print(f"Total tokens: {llm_logger.total_tokens}")
    print(f"Estimated cost: ${llm_logger.total_cost:.4f}")
    
    # 7. Analyze LLM calls
    if llm_logger.call_count > 0:
        print("\n" + "=" * 80)
        print("LLM CALL ANALYSIS")
        print("=" * 80)
        
        stats = LLMCallLogger.analyze_calls(llm_logger.log_file)
        print(f"\nTotal calls: {stats['total_calls']}")
        print(f"Total tokens: {stats['tokens']['total']:,}")
        print(f"Average tokens per call: {stats['tokens']['avg_per_call']:.1f}")
        print(f"Total cost: ${stats['cost']['total_usd']:.4f}")
        print(f"Total duration: {stats['timing']['total_seconds']:.2f}s")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"\nView logs:")
    print(f"  python scripts/view_logs.py")
    print(f"\nView LLM stats:")
    print(f"  python scripts/view_logs.py --llm-stats")
    print(f"\nReplay conversation:")
    print(f"  python scripts/view_logs.py --replay")
    print(f"\nExport HTML report:")
    print(f"  python scripts/view_logs.py --export report.html")
    
    return run_logger.run_dir


if __name__ == "__main__":
    run_dir = test_logging_system()
    print(f"\n✓ Test complete! Logs saved to: {run_dir}")
