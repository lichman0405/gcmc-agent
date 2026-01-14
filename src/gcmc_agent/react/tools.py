"""Tool registry and conversion utilities for ReAct agents."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


class Tool:
    """
    Wrapper for a tool that can be used by ReAct agents.
    
    Example:
        def read_file(path: str) -> str:
            with open(path) as f:
                return f.read()
        
        tool = Tool(
            name="read_file",
            description="Read contents of a file",
            parameters={"path": "string - absolute file path"},
            func=read_file
        )
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format for ReActAgent."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "func": self.func,
        }


class ToolRegistry:
    """Registry for managing tools available to agents."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def register_function(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Optional[Dict[str, str]] = None,
    ):
        """Register a function as a tool."""
        tool = Tool(name=name, description=description, func=func, parameters=parameters)
        self.register(tool)

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert all tools to dict format for ReActAgent."""
        return {name: tool.to_dict() for name, tool in self._tools.items()}
