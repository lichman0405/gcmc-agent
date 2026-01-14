from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set


def get_all_force_field_descriptions(forcefield_root: str | Path) -> List[Dict[str, str]]:
    """List available force field folders with minimal metadata (name, path)."""
    root = Path(forcefield_root)
    results: List[Dict[str, str]] = []
    if not root.exists():
        return results
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            results.append({"name": entry.name, "path": str(entry)})
    return results


def get_atoms_in_ff_file(pseudo_atoms_path: str | Path) -> Set[str]:
    """Parse pseudo_atoms.def and return declared atom labels."""
    path = Path(pseudo_atoms_path)
    atoms: Set[str] = set()
    if not path.exists():
        return atoms
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 1 and parts[0].isalpha():
                atoms.add(parts[0])
    return atoms
