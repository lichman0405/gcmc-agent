from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Mapping


def read_text(path: str | Path, encoding: str = "utf-8") -> str:
    return Path(path).read_text(encoding=encoding)


def write_text(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding=encoding)


def copy_file(src: str | Path, dst: str | Path) -> None:
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: str | Path, dst: str | Path) -> None:
    src_path = Path(src)
    dst_path = Path(dst)
    if dst_path.exists():
        shutil.rmtree(dst_path)
    shutil.copytree(src_path, dst_path)


def render_template(template: str, data: Mapping[str, Any]) -> str:
    """Very small placeholder renderer using str.format style."""
    return template.format(**data)
