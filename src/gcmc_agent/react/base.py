"""
ReAct (Reasoning + Acting) Agent Base Class

Implements the ReAct framework from Yao et al. 2023:
Thought -> Action -> Observation -> ... -> Final Answer
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..client import OpenAIChatClient


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    answer: str
    thought_action_history: List[Dict[str, Any]]
    error: Optional[str] = None


class ReActAgent:
    """
    Base class for ReAct agents.
    
    Example usage:
        agent = ReActAgent(
            name="StructureExpert",
            system_prompt="You are a structure expert...",
            llm_client=client,
            tools={"read_file": read_file_tool, ...}
        )
        result = agent.run("Find the CIF file for MOR_33")
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm_client: OpenAIChatClient,
        tools: Dict[str, Any],
        model: str = "deepseek-chat",
        max_iterations: int = 10,
        verbose: bool = False,
        log_file: Optional[Path] = None,
        llm_call_logger = None,  # LLMCallLogger instance
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.llm_client = llm_client
        self.tools = tools
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.log_file = log_file
        self.llm_call_logger = llm_call_logger
        
        # Setup logging
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            self.logger = self._setup_logger()
        else:
            self.logger = None
        
        # Connect LLM client to LLM call logger
        if llm_call_logger:
            self.llm_client.llm_logger = llm_call_logger
            self.llm_client.set_metadata(agent=name)

    def _setup_logger(self) -> logging.Logger:
        """Setup file logger for this agent."""
        logger = logging.getLogger(f"ReActAgent.{self.name}")
        logger.setLevel(logging.INFO)
        logger.handlers = []  # Clear existing handlers
        
        # File handler
        fh = logging.FileHandler(self.log_file, mode='w', encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _log(self, message: str):
        """Log message to file and optionally print."""
        if self.logger:
            self.logger.info(message)
        if self.verbose:
            print(message)

    def _format_tools_description(self) -> str:
        """Format tools for the system prompt."""
        tool_descriptions = []
        for name, tool in self.tools.items():
            desc = f"- {name}: {tool.get('description', 'No description')}"
            if "parameters" in tool:
                desc += f"\n  Parameters: {tool['parameters']}"
            tool_descriptions.append(desc)
        return "\n".join(tool_descriptions)

    def _build_prompt(self, task: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Build the full prompt including system, task, and history."""
        tools_desc = self._format_tools_description()
        
        system_content = f"""{self.system_prompt}

Available Tools:
{tools_desc}

You MUST follow this exact format:

Thought: <your reasoning about what to do next>
Action: <tool_name>
Action Input: <JSON object with tool parameters>

OR when you have the final answer:

Thought: <reasoning why you're done>
Final Answer: <your final response>

CRITICAL RULES:
1. Output EXACTLY one Thought followed by EXACTLY one Action OR Final Answer
2. Action Input MUST be valid JSON
3. Do not skip steps or combine multiple actions
4. If a tool fails, think about why and try a different approach
"""

        messages = [{"role": "system", "content": system_content}]
        messages.append({"role": "user", "content": f"Task: {task}"})
        
        # Add conversation history
        for entry in history:
            messages.append({"role": "assistant", "content": entry["assistant"]})
            if "observation" in entry:
                messages.append({"role": "user", "content": f"Observation: {entry['observation']}"})
        
        return messages

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract Thought, Action, Action Input, or Final Answer.
        
        Returns:
            {"type": "action", "thought": str, "action": str, "action_input": dict}
            or {"type": "final", "thought": str, "final_answer": str}
        """
        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|$)", response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # Check for Final Answer
        final_match = re.search(r"Final Answer:\s*(.+?)$", response, re.DOTALL)
        if final_match:
            return {
                "type": "final",
                "thought": thought,
                "final_answer": final_match.group(1).strip()
            }

        # Extract Action and Action Input
        action_match = re.search(r"Action:\s*(\w+)", response)
        # Improved regex: match balanced braces for multi-line JSON
        action_input_match = re.search(r"Action Input:\s*(\{.*\})", response, re.DOTALL)

        if action_match:
            action = action_match.group(1).strip()
            
            # Parse JSON input
            action_input = {}
            if action_input_match:
                try:
                    json_str = action_input_match.group(1)
                    # Try to find the actual end of JSON by counting braces
                    brace_count = 0
                    json_end = 0
                    for i, char in enumerate(json_str):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i + 1
                                break
                    
                    if json_end > 0:
                        json_str = json_str[:json_end]
                    
                    action_input = json.loads(json_str)
                except json.JSONDecodeError as e:
                    return {
                        "type": "error",
                        "thought": thought,
                        "error": f"Invalid JSON in Action Input: {e}"
                    }
            
            return {
                "type": "action",
                "thought": thought,
                "action": action,
                "action_input": action_input
            }

        return {
            "type": "error",
            "thought": thought,
            "error": "Could not parse Action or Final Answer from response"
        }

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool and return the observation."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"

        tool = self.tools[tool_name]
        func = tool.get("func")
        if not func:
            return f"Error: Tool '{tool_name}' has no function defined"

        try:
            result = func(**tool_input)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Run the ReAct agent on a task.
        
        Args:
            task: The task description
            context: Optional context dict (e.g., global memory, working_dir)
            
        Returns:
            AgentResult with success status and answer
        """
        self._log(f"{'='*60}")
        self._log(f"Agent: {self.name}")
        self._log(f"Task: {task}")
        self._log(f"{'='*60}\n")
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Agent: {self.name}")
            print(f"Task: {task}")
            print(f"{'='*60}\n")

        history = []
        
        for iteration in range(self.max_iterations):
            self._log(f"\n--- Iteration {iteration + 1} ---")
            
            if self.verbose:
                print(f"\n--- Iteration {iteration + 1} ---")

            # Build prompt and get LLM response
            messages = self._build_prompt(task, history)
            
            # Set metadata for this LLM call
            if self.llm_call_logger:
                self.llm_client.set_metadata(
                    agent=self.name,
                    iteration=iteration + 1,
                    task=task[:100]  # Truncate long tasks
                )
            
            try:
                response = self.llm_client.chat(
                    model=self.model,
                    messages=messages,
                    timeout=60
                )
                assistant_content = response["choices"][0]["message"]["content"]
                
                # Log LLM response
                self._log(f"\nLLM Response:\n{assistant_content}\n")
                
            except Exception as e:
                error_msg = f"LLM call failed: {str(e)}"
                self._log(f"❌ ERROR: {error_msg}")
                return AgentResult(
                    success=False,
                    answer="",
                    thought_action_history=history,
                    error=error_msg
                )

            if self.verbose:
                print(f"\nA:\n{assistant_content}")

            # Parse response
            parsed = self._parse_response(assistant_content)
            
            if parsed["type"] == "error":
                self._log(f"⚠️  Parse error: {parsed['error']}")
                
                if self.verbose:
                    print(f"⚠️  Parse error: {parsed['error']}")
                # Continue and let LLM correct itself
                history.append({
                    "assistant": assistant_content,
                    "observation": f"Parse Error: {parsed['error']}. Please follow the format exactly."
                })
                continue

            if parsed["type"] == "final":
                self._log(f"\n✅ Final Answer: {parsed['final_answer']}")
                self._log(f"Total iterations: {iteration + 1}")
                
                if self.verbose:
                    print(f"\n✅ Final Answer: {parsed['final_answer']}")
                return AgentResult(
                    success=True,
                    answer=parsed["final_answer"],
                    thought_action_history=history
                )

            # Execute action
            if parsed["type"] == "action":
                self._log(f"🔧 Tool: {parsed['action']}")
                self._log(f"   Input: {parsed['action_input']}")
                
                observation = self._execute_tool(parsed["action"], parsed["action_input"])
                
                self._log(f"   Observation: {observation[:500]}{'...' if len(observation) > 500 else ''}")
                
                if self.verbose:
                    print(f"\n🔧 Tool: {parsed['action']}")
                    print(f"   Input: {parsed['action_input']}")
                    print(f"   Observation: {observation[:200]}{'...' if len(observation) > 200 else ''}")

                history.append({
                    "assistant": assistant_content,
                    "observation": observation
                })

        # Max iterations reached
        error_msg = f"Max iterations ({self.max_iterations}) reached without Final Answer"
        self._log(f"\n❌ ERROR: {error_msg}")
        
        return AgentResult(
            success=False,
            answer="",
            thought_action_history=history,
            error=error_msg
        )
