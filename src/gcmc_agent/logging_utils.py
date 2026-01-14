"""
Logging utilities for GCMC Agent.

Provides centralized logging management with automatic run ID generation,
structured log directories, and progress tracking with rich formatting.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


class RunLogger:
    """
    Manages logging for a single run across multiple agents.
    
    Creates a unique directory for each run with timestamp and ID,
    and provides log file paths for each agent.
    """
    
    def __init__(self, base_dir: Path = None, run_name: str = None):
        """
        Initialize run logger.
        
        Args:
            base_dir: Base directory for logs (default: logs/)
            run_name: Optional name for this run (default: auto-generated)
        """
        if base_dir is None:
            base_dir = Path("logs")
        
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Rich console
        self.console = Console() if RICH_AVAILABLE else None
        
        # Generate run ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if run_name:
            self.run_id = f"{timestamp}_{run_name}"
        else:
            self.run_id = timestamp
        
        # Create run directory
        self.run_dir = self.base_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata
        self.metadata = {
            "run_id": self.run_id,
            "start_time": datetime.now().isoformat(),
            "agents": {},
            "phases": []
        }
        
        self._save_metadata()
        
        # Print startup
        if self.console:
            self.console.print(Panel(
                f"[bold cyan]Run ID:[/] {self.run_id}\n"
                f"[bold cyan]Log Dir:[/] {self.run_dir}",
                title="[bold green]🚀 GCMC-Agent Run Started[/]",
                border_style="green"
            ))
        else:
            print(f"\n{'='*80}")
            print(f"🚀 GCMC-Agent Run Started")
            print(f"Run ID: {self.run_id}")
            print(f"Log Dir: {self.run_dir}")
            print(f"{'='*80}\n")
    
    def get_agent_log_file(self, agent_name: str) -> Path:
        """Get log file path for a specific agent."""
        return self.run_dir / f"{agent_name}.log"
    
    def record_agent_start(self, agent_name: str, task: str):
        """Record when an agent starts."""
        self.metadata["agents"][agent_name] = {
            "start_time": datetime.now().isoformat(),
            "task": task,
            "status": "running"
        }
        self._save_metadata()
        
        # Beautiful output
        if self.console:
            self.console.print(f"\n[bold blue]▶ {agent_name}[/] started")
            self.console.print(f"  [dim]Task:[/] {task}")
        else:
            print(f"\n▶ {agent_name} started")
            print(f"  Task: {task}")
    
    def record_team_handoff(self, from_team: str, to_team: str, data: Dict[str, Any]):
        """Record handoff between teams (e.g., Research -> Setup)."""
        if "handoffs" not in self.metadata:
            self.metadata["handoffs"] = []
        
        self.metadata["handoffs"].append({
            "timestamp": datetime.now().isoformat(),
            "from_team": from_team,
            "to_team": to_team,
            "data_summary": {
                "keys": list(data.keys()) if isinstance(data, dict) else str(type(data)),
                "size_bytes": len(str(data))
            }
        })
        self._save_metadata()
    
    def record_workflow_event(self, event_type: str, description: str, data: Optional[Dict[str, Any]] = None):
        """Record general workflow events (decision points, state changes)."""
        if "events" not in self.metadata:
            self.metadata["events"] = []
        
        self.metadata["events"].append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "data": data or {}
        })
        self._save_metadata()
    
    def record_agent_finish(self, agent_name: str, success: bool, iterations: int, error: str = None):
        """Record when an agent finishes."""
        if agent_name in self.metadata["agents"]:
            self.metadata["agents"][agent_name].update({
                "end_time": datetime.now().isoformat(),
                "status": "success" if success else "failed",
                "iterations": iterations,
                "error": error
            })
        self._save_metadata()
        
        # Beautiful output
        status_icon = "✅" if success else "❌"
        if self.console:
            self.console.print(f"[bold {'green' if success else 'red'}]{status_icon} {agent_name}[/] finished ({iterations} iterations)")
            if error:
                self.console.print(f"  [red]Error:[/] {error}")
        else:
            print(f"{status_icon} {agent_name} finished ({iterations} iterations)")
            if error:
                print(f"  Error: {error}")
    
    def finish_run(self, overall_success: bool):
        """Mark the run as finished."""
        self.metadata["end_time"] = datetime.now().isoformat()
        self.metadata["overall_success"] = overall_success
        self._save_metadata()
        
        # Create summary
        self._create_summary()
        
        # Beautiful final summary
        if self.console:
            status = "[bold green]✅ SUCCESS[/]" if overall_success else "[bold red]❌ FAILED[/]"
            self.console.print(Panel(
                f"[bold cyan]Status:[/] {status}\n"
                f"[bold cyan]Run ID:[/] {self.run_id}\n"
                f"[bold cyan]Logs:[/] {self.run_dir}",
                title="[bold]🏁 Run Complete[/]",
                border_style="green" if overall_success else "red"
            ))
        else:
            status_icon = "✅ SUCCESS" if overall_success else "❌ FAILED"
            print(f"\n{'='*80}")
            print(f"🏁 Run Complete: {status_icon}")
            print(f"Run ID: {self.run_id}")
            print(f"Logs: {self.run_dir}")
            print(f"{'='*80}\n")
    
    def _save_metadata(self):
        """Save metadata to JSON file."""
        metadata_file = self.run_dir / "run_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, indent=2, fp=f)
    
    def _create_summary(self):
        """Create human-readable summary."""
        summary_file = self.run_dir / "SUMMARY.txt"
        
        lines = []
        lines.append("=" * 80)
        lines.append(f"Run Summary: {self.run_id}")
        lines.append("=" * 80)
        lines.append(f"Start: {self.metadata.get('start_time', 'N/A')}")
        lines.append(f"End:   {self.metadata.get('end_time', 'N/A')}")
        lines.append(f"Status: {'✅ SUCCESS' if self.metadata.get('overall_success') else '❌ FAILED'}")
        lines.append("")
        lines.append("Agents:")
        lines.append("-" * 80)
        
        for agent_name, info in self.metadata.get("agents", {}).items():
            status_icon = "✅" if info.get("status") == "success" else "❌"
            lines.append(f"{status_icon} {agent_name}")
            lines.append(f"   Task: {info.get('task', 'N/A')[:60]}")
            lines.append(f"   Iterations: {info.get('iterations', 'N/A')}")
            if info.get('error'):
                lines.append(f"   Error: {info['error']}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append(f"Logs saved in: {self.run_dir}")
        lines.append("=" * 80)
        
        with open(summary_file, 'w') as f:
            f.write('\n'.join(lines))
        
        # Also print to console
        print('\n'.join(lines))


def get_latest_run_dir(base_dir: Path = None) -> Optional[Path]:
    """Get the most recent run directory."""
    if base_dir is None:
        base_dir = Path("logs")
    
    if not base_dir.exists():
        return None
    
    run_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        return None
    
    # Sort by modification time
    latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
    return latest


def print_run_summary(run_dir: Path):
    """Print summary of a run."""
    summary_file = run_dir / "SUMMARY.txt"
    if summary_file.exists():
        print(summary_file.read_text())
    else:
        print(f"No summary found for {run_dir}")


class LLMCallLogger:
    """
    Logger for LLM API calls with detailed request/response tracking.
    
    Records each LLM call in JSON Lines format for easy analysis:
    - Complete request (messages, model, parameters)
    - Complete response (content, metadata)
    - Token usage statistics
    - Timing information
    - Error tracking
    """
    
    def __init__(self, log_file: Path):
        """
        Initialize LLM call logger.
        
        Args:
            log_file: Path to JSON Lines log file
        """
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.call_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0  # Estimated cost
        
    def log_call(
        self,
        request: Dict[str, Any],
        response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a single LLM API call.
        
        Args:
            request: Request dict with model, messages, parameters
            response: Response dict from LLM API
            error: Error message if call failed
            duration: Call duration in seconds
            metadata: Additional metadata (agent name, iteration, etc.)
        """
        self.call_count += 1
        
        # Extract token usage
        tokens_used = 0
        prompt_tokens = 0
        completion_tokens = 0
        
        if response and "usage" in response:
            usage = response["usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = usage.get("total_tokens", 0)
            self.total_tokens += tokens_used
        
        # Estimate cost (rough approximation for GPT-4)
        # You can adjust these rates based on actual model
        cost_per_1k_prompt = 0.03  # $0.03 per 1K prompt tokens
        cost_per_1k_completion = 0.06  # $0.06 per 1K completion tokens
        estimated_cost = (prompt_tokens / 1000 * cost_per_1k_prompt +
                         completion_tokens / 1000 * cost_per_1k_completion)
        self.total_cost += estimated_cost
        
        # Build log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "call_number": self.call_count,
            "duration_seconds": round(duration, 3),
            "request": {
                "model": request.get("model", "unknown"),
                "messages": request.get("messages", []),
                "temperature": request.get("temperature"),
                "max_tokens": request.get("max_tokens"),
                "top_p": request.get("top_p"),
            },
            "response": None,
            "error": error,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": tokens_used
            },
            "estimated_cost_usd": round(estimated_cost, 6),
            "metadata": metadata or {}
        }
        
        # Add response content if available
        if response:
            try:
                content = response["choices"][0]["message"]["content"]
                log_entry["response"] = {
                    "content": content,
                    "finish_reason": response["choices"][0].get("finish_reason"),
                    "model": response.get("model"),
                }
            except (KeyError, IndexError):
                log_entry["response"] = {"raw": response}
        
        # Write to JSON Lines file (one JSON object per line)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_prompt_tokens": 0,  # Not tracked separately in current implementation
            "total_completion_tokens": 0,  # Not tracked separately in current implementation
            "total_duration": 0.0,  # Not tracked separately in current implementation
            "total_cost_usd": round(self.total_cost, 4)
        }
    
    @staticmethod
    def load_calls(log_file: Path) -> List[Dict[str, Any]]:
        """Load all LLM calls from a log file."""
        if not log_file.exists():
            return []
        
        calls = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        calls.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return calls
    
    @staticmethod
    def analyze_calls(log_file: Path) -> Dict[str, Any]:
        """Analyze LLM calls and provide statistics."""
        calls = LLMCallLogger.load_calls(log_file)
        
        if not calls:
            return {"error": "No calls found"}
        
        total_calls = len(calls)
        total_tokens = sum(c["tokens"]["total"] for c in calls)
        total_cost = sum(c.get("estimated_cost_usd", 0) for c in calls)
        total_duration = sum(c.get("duration_seconds", 0) for c in calls)
        
        errors = [c for c in calls if c.get("error")]
        
        # Token distribution
        prompt_tokens = sum(c["tokens"]["prompt"] for c in calls)
        completion_tokens = sum(c["tokens"]["completion"] for c in calls)
        
        return {
            "total_calls": total_calls,
            "successful_calls": total_calls - len(errors),
            "failed_calls": len(errors),
            "tokens": {
                "total": total_tokens,
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "avg_per_call": round(total_tokens / total_calls, 1) if total_calls > 0 else 0
            },
            "cost": {
                "total_usd": round(total_cost, 4),
                "avg_per_call_usd": round(total_cost / total_calls, 6) if total_calls > 0 else 0
            },
            "timing": {
                "total_seconds": round(total_duration, 2),
                "avg_seconds": round(total_duration / total_calls, 3) if total_calls > 0 else 0
            },
            "errors": [{"call": c["call_number"], "error": c["error"]} for c in errors]
        }
