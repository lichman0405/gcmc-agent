#!/usr/bin/env python3
"""
Enhanced Log Viewer - analyze agent logs, LLM calls, and workflow execution.

Features:
- View run summaries
- Analyze LLM API usage and costs
- Replay agent conversations
- Filter and search logs
- Export to HTML report
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcmc_agent.logging_utils import (
    get_latest_run_dir,
    print_run_summary,
    LLMCallLogger
)


def list_runs(base_dir: Path = Path("logs")) -> List[Path]:
    """List all run directories."""
    if not base_dir.exists():
        return []
    return sorted([d for d in base_dir.iterdir() if d.is_dir()], 
                   key=lambda x: x.stat().st_mtime, reverse=True)


def show_summary(run_dir: Path):
    """Show run summary."""
    print("\n" + "=" * 80)
    print("RUN SUMMARY")
    print("=" * 80)
    print_run_summary(run_dir)


def show_llm_stats(run_dir: Path):
    """Show LLM API usage statistics."""
    llm_log = run_dir / "llm_calls.jsonl"
    
    if not llm_log.exists():
        print("\n⚠️  No LLM call logs found")
        return
    
    stats = LLMCallLogger.analyze_calls(llm_log)
    
    print("\n" + "=" * 80)
    print("LLM API USAGE STATISTICS")
    print("=" * 80)
    
    print(f"\n📊 Call Statistics:")
    print(f"   Total calls:      {stats['total_calls']}")
    print(f"   Successful:       {stats['successful_calls']}")
    print(f"   Failed:           {stats['failed_calls']}")
    
    print(f"\n💰 Token Usage:")
    print(f"   Total tokens:     {stats['tokens']['total']:,}")
    print(f"   Prompt tokens:    {stats['tokens']['prompt']:,}")
    print(f"   Completion tokens:{stats['tokens']['completion']:,}")
    print(f"   Avg per call:     {stats['tokens']['avg_per_call']:.1f}")
    
    print(f"\n💵 Estimated Cost:")
    print(f"   Total cost:       ${stats['cost']['total_usd']:.4f}")
    print(f"   Avg per call:     ${stats['cost']['avg_per_call_usd']:.6f}")
    
    print(f"\n⏱️  Timing:")
    print(f"   Total duration:   {stats['timing']['total_seconds']:.2f}s")
    print(f"   Avg per call:     {stats['timing']['avg_seconds']:.3f}s")
    
    if stats.get('errors'):
        print(f"\n❌ Errors:")
        for err in stats['errors'][:5]:  # Show first 5
            print(f"   Call #{err['call']}: {err['error'][:60]}")


def replay_conversation(run_dir: Path, agent_name: str = None):
    """Replay agent conversation from LLM logs."""
    llm_log = run_dir / "llm_calls.jsonl"
    
    if not llm_log.exists():
        print("\n⚠️  No LLM call logs found")
        return
    
    calls = LLMCallLogger.load_calls(llm_log)
    
    # Filter by agent if specified
    if agent_name:
        calls = [c for c in calls if c.get('metadata', {}).get('agent') == agent_name]
        if not calls:
            print(f"\n⚠️  No calls found for agent: {agent_name}")
            return
    
    print("\n" + "=" * 80)
    if agent_name:
        print(f"CONVERSATION REPLAY: {agent_name}")
    else:
        print("CONVERSATION REPLAY: ALL AGENTS")
    print("=" * 80)
    
    for i, call in enumerate(calls, 1):
        metadata = call.get('metadata', {})
        agent = metadata.get('agent', 'Unknown')
        iteration = metadata.get('iteration', '?')
        
        print(f"\n{'─' * 80}")
        print(f"Call #{i} | Agent: {agent} | Iteration: {iteration} | "
              f"Tokens: {call['tokens']['total']} | "
              f"Time: {call['duration_seconds']:.2f}s")
        print(f"{'─' * 80}")
        
        # Show last user message (the task/observation)
        messages = call['request']['messages']
        if messages:
            last_user_msg = [m for m in messages if m['role'] == 'user']
            if last_user_msg:
                print(f"\n👤 USER:")
                print(f"{last_user_msg[-1]['content'][:300]}")
                if len(last_user_msg[-1]['content']) > 300:
                    print("   ...")
        
        # Show assistant response
        if call.get('response') and call['response'].get('content'):
            print(f"\n🤖 ASSISTANT:")
            content = call['response']['content']
            print(f"{content[:500]}")
            if len(content) > 500:
                print("   ...")
        
        if call.get('error'):
            print(f"\n❌ ERROR: {call['error']}")


def search_logs(run_dir: Path, query: str):
    """Search for text in log files."""
    print(f"\n🔍 Searching for: '{query}'")
    print("=" * 80)
    
    found_count = 0
    for log_file in run_dir.glob("*.log"):
        matches = []
        lines = log_file.read_text(encoding='utf-8').splitlines()
        
        for line_num, line in enumerate(lines, 1):
            if query.lower() in line.lower():
                matches.append((line_num, line))
        
        if matches:
            print(f"\n📄 {log_file.name}:")
            for line_num, line in matches[:5]:  # Show first 5 matches
                print(f"   Line {line_num}: {line.strip()[:80]}")
            if len(matches) > 5:
                print(f"   ... and {len(matches) - 5} more matches")
            found_count += len(matches)
    
    print(f"\n✓ Found {found_count} matches")


def export_html_report(run_dir: Path, output_file: Path):
    """Export run to HTML report."""
    print(f"\n📝 Generating HTML report: {output_file}")
    
    # Read metadata
    metadata_file = run_dir / "run_metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
    
    # Read LLM stats
    llm_stats = {}
    llm_log = run_dir / "llm_calls.jsonl"
    if llm_log.exists():
        llm_stats = LLMCallLogger.analyze_calls(llm_log)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GCMC-Agent Run Report: {run_dir.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }}
        .stat {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-left: 4px solid #4CAF50; }}
        .stat-label {{ font-weight: bold; color: #666; }}
        .stat-value {{ font-size: 1.2em; color: #333; }}
        .success {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        .agent-card {{ background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 GCMC-Agent Run Report</h1>
        <p><strong>Run ID:</strong> {run_dir.name}</p>
        <p><strong>Start Time:</strong> {metadata.get('start_time', 'N/A')}</p>
        <p><strong>End Time:</strong> {metadata.get('end_time', 'N/A')}</p>
        <p><strong>Status:</strong> <span class="{'success' if metadata.get('overall_success') else 'failed'}">
            {'✅ SUCCESS' if metadata.get('overall_success') else '❌ FAILED'}
        </span></p>
        
        <h2>📊 LLM API Usage</h2>
"""
    
    if llm_stats:
        html += f"""
        <div class="stat">
            <span class="stat-label">Total API Calls:</span> 
            <span class="stat-value">{llm_stats.get('total_calls', 0)}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Total Tokens:</span> 
            <span class="stat-value">{llm_stats.get('tokens', {}).get('total', 0):,}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Estimated Cost:</span> 
            <span class="stat-value">${llm_stats.get('cost', {}).get('total_usd', 0):.4f}</span>
        </div>
        <div class="stat">
            <span class="stat-label">Total Duration:</span> 
            <span class="stat-value">{llm_stats.get('timing', {}).get('total_seconds', 0):.2f}s</span>
        </div>
"""
    
    html += """
        <h2>👥 Agents</h2>
"""
    
    for agent_name, info in metadata.get('agents', {}).items():
        status_class = 'success' if info.get('status') == 'success' else 'failed'
        status_icon = '✅' if info.get('status') == 'success' else '❌'
        html += f"""
        <div class="agent-card">
            <h3>{status_icon} {agent_name}</h3>
            <p><strong>Task:</strong> {info.get('task', 'N/A')}</p>
            <p><strong>Iterations:</strong> {info.get('iterations', 'N/A')}</p>
            <p><strong>Status:</strong> <span class="{status_class}">{info.get('status', 'N/A').upper()}</span></p>
"""
        if info.get('error'):
            html += f"""<p><strong>Error:</strong> <span class="failed">{info['error']}</span></p>"""
        html += """
        </div>
"""
    
    html += """
    </div>
</body>
</html>
"""
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding='utf-8')
    print(f"✓ Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="View and analyze GCMC-Agent logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show latest run summary
  python view_logs.py
  
  # Show LLM usage stats
  python view_logs.py --llm-stats
  
  # Replay conversation
  python view_logs.py --replay
  
  # Replay specific agent
  python view_logs.py --replay --agent StructureExpert
  
  # Search logs
  python view_logs.py --search "error"
  
  # Export HTML report
  python view_logs.py --export report.html
  
  # List all runs
  python view_logs.py --list
        """
    )
    
    parser.add_argument('--list', action='store_true',
                       help='List all run directories')
    parser.add_argument('--run', type=str,
                       help='Specify run directory (default: latest)')
    parser.add_argument('--llm-stats', action='store_true',
                       help='Show LLM API usage statistics')
    parser.add_argument('--replay', action='store_true',
                       help='Replay agent conversations')
    parser.add_argument('--agent', type=str,
                       help='Filter by agent name (use with --replay)')
    parser.add_argument('--search', type=str,
                       help='Search for text in logs')
    parser.add_argument('--export', type=str,
                       help='Export HTML report to file')
    
    args = parser.parse_args()
    
    base_dir = Path("logs")
    
    # List runs
    if args.list:
        runs = list_runs(base_dir)
        print("\n" + "=" * 80)
        print("AVAILABLE RUNS")
        print("=" * 80)
        for i, run in enumerate(runs, 1):
            metadata_file = run / "run_metadata.json"
            status = "?"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    data = json.load(f)
                    status = "✅" if data.get('overall_success') else "❌"
            print(f"{i}. {status} {run.name}")
        return
    
    # Get run directory
    if args.run:
        run_dir = base_dir / args.run
        if not run_dir.exists():
            print(f"❌ Run not found: {run_dir}")
            sys.exit(1)
    else:
        run_dir = get_latest_run_dir(base_dir)
        if not run_dir:
            print("❌ No run logs found")
            print("   Run experiments to generate logs")
            sys.exit(1)
    
    print(f"\n📁 Viewing run: {run_dir.name}")
    
    # Execute requested action
    if args.llm_stats:
        show_llm_stats(run_dir)
    elif args.replay:
        replay_conversation(run_dir, args.agent)
    elif args.search:
        search_logs(run_dir, args.search)
    elif args.export:
        export_html_report(run_dir, Path(args.export))
    else:
        show_summary(run_dir)
        
        # Also show quick stats if available
        llm_log = run_dir / "llm_calls.jsonl"
        if llm_log.exists():
            print("\n💡 Tip: Use --llm-stats to see detailed LLM usage")
            print("        Use --replay to see conversation history")


if __name__ == "__main__":
    main()
