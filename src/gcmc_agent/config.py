from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load .env when python-dotenv is available; otherwise rely on environment.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    pass


@dataclass
class DeepSeekConfig:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    chat_model: str = "deepseek-chat"
    reasoner_model: str = "deepseek-reasoner"
    timeout: Optional[int] = None

    @classmethod
    def from_env(cls) -> "DeepSeekConfig":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        base_url = os.getenv("DEEPSEEK_BASE_URL", cls.base_url).strip() or cls.base_url
        chat_model = os.getenv("DEEPSEEK_CHAT_MODEL", cls.chat_model).strip() or cls.chat_model
        reasoner_model = os.getenv("DEEPSEEK_REASONER_MODEL", cls.reasoner_model).strip() or cls.reasoner_model
        timeout_val = os.getenv("DEEPSEEK_TIMEOUT", "").strip()
        timeout: Optional[int] = int(timeout_val) if timeout_val.isdigit() else None

        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required; set it in the environment or .env")

        return cls(
            api_key=api_key,
            base_url=base_url,
            chat_model=chat_model,
            reasoner_model=reasoner_model,
            timeout=timeout,
        )


@dataclass
class AppConfig:
    deepseek: DeepSeekConfig
    workspace_root: Path

    @classmethod
    def load(cls, workspace_root: Optional[Path] = None) -> "AppConfig":
        root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[2]
        deepseek = DeepSeekConfig.from_env()
        return cls(deepseek=deepseek, workspace_root=root)
