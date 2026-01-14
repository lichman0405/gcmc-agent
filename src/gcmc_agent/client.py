from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from openai import OpenAI

from .config import DeepSeekConfig


class LLMClient(Protocol):
    """Protocol for an OpenAI/Anthropic-compatible chat client."""

    def chat(self, *, model: str, messages: list[dict], timeout: int | None = None) -> dict:
        ...


class OpenAIChatClient(LLMClient):
    """Thin wrapper for OpenAI-compatible chat completions with logging support."""

    def __init__(self, cfg: DeepSeekConfig, llm_logger=None):
        self._client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        self._cfg = cfg
        self.llm_logger = llm_logger  # Optional LLMCallLogger instance
        self.metadata = {}  # Can be set by agents to add context

    def set_metadata(self, **kwargs):
        """Set metadata to be included in LLM call logs."""
        self.metadata.update(kwargs)

    def chat(
        self, 
        *, 
        model: str, 
        messages: List[Dict[str, Any]], 
        timeout: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat completion with automatic logging.
        
        Args:
            model: Model name
            messages: List of message dicts
            timeout: Request timeout
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Response dict from API
        """
        # Build request dict for logging
        request_dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.7,
            "max_tokens": max_tokens,
            "timeout": timeout or self._cfg.timeout,
        }
        request_dict.update(kwargs)
        
        # Call API with timing
        start_time = time.time()
        error = None
        response = None
        
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout or self._cfg.timeout,
                temperature=temperature if temperature is not None else 0.7,
                max_tokens=max_tokens,
                **kwargs
            )
            # Return a simple dict to keep callers decoupled from SDK objects.
            response = resp.model_dump() if hasattr(resp, "model_dump") else resp.to_dict()
            
        except Exception as e:
            error = str(e)
            raise
        
        finally:
            duration = time.time() - start_time
            
            # Log the call if logger is available
            if self.llm_logger:
                self.llm_logger.log_call(
                    request=request_dict,
                    response=response,
                    error=error,
                    duration=duration,
                    metadata=self.metadata.copy()
                )
        
        return response
