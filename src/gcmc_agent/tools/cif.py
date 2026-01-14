from __future__ import annotations

from pathlib import Path


def _load_structure(cif_path: Path):
    try:
        from pymatgen.core import Structure
    except ImportError as exc:  # pragma: no cover
        raise ImportError("pymatgen is required for CIF utilities; install via pip.") from exc
    return Structure.from_file(cif_path)


def count_atom_type_in_cif(cif_path: str | Path, atom_label: str) -> int:
    """Count occurrences of atom species (case-insensitive) in a CIF file."""
    cif_path = Path(cif_path)
    structure = _load_structure(cif_path)
    target = atom_label.strip().lower()
    count = 0
    for site in structure.sites:
        label = site.species_string.lower()
        if label == target:
            count += 1
    return count


def get_unit_cell_size(cif_path: str | Path) -> tuple[float, float, float]:
    """Return lattice parameters (a, b, c) in angstroms."""
    cif_path = Path(cif_path)
    structure = _load_structure(cif_path)
    lattice = structure.lattice
    return lattice.a, lattice.b, lattice.c
