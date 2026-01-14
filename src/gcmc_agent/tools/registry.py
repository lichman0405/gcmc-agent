"""
Tool registry with all GCMC-agent tools for ReAct agents.
"""

from pathlib import Path
from typing import List, Set

from ..react import ToolRegistry
from ..tools import files, cif, forcefield


def create_tool_registry(workspace_root: Path) -> ToolRegistry:
    """
    Create and populate tool registry with all available tools.
    
    Args:
        workspace_root: Root directory of the project
        
    Returns:
        ToolRegistry with all tools registered
    """
    registry = ToolRegistry()
    
    # ============================================================
    # File Tools
    # ============================================================
    
    def read_file(path: str) -> str:
        """Read text file contents."""
        try:
            return files.read_text(path)
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="read_file",
        description="Read the contents of a text file",
        func=read_file,
        parameters={"path": "string - absolute path to the file"}
    )
    
    def write_file(path: str, content: str) -> str:
        """Write content to a file."""
        try:
            files.write_text(path, content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="write_file",
        description="Write content to a file (creates parent directories if needed)",
        func=write_file,
        parameters={
            "path": "string - absolute path to the file",
            "content": "string - content to write"
        }
    )
    
    def copy_file(src: str, dst: str) -> str:
        """Copy a file from src to dst."""
        try:
            files.copy_file(src, dst)
            return f"Successfully copied {src} to {dst}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="copy_file",
        description="Copy a file from source to destination",
        func=copy_file,
        parameters={
            "src": "string - absolute path to source file",
            "dst": "string - absolute path to destination file"
        }
    )
    
    def list_directory(path: str) -> str:
        """List contents of a directory."""
        try:
            p = Path(path)
            if not p.exists():
                return f"Error: Directory {path} does not exist"
            if not p.is_dir():
                return f"Error: {path} is not a directory"
            
            items = sorted(p.iterdir())
            result = []
            for item in items:
                if item.is_dir():
                    result.append(f"[DIR]  {item.name}")
                else:
                    size = item.stat().st_size
                    result.append(f"[FILE] {item.name} ({size} bytes)")
            return "\n".join(result) if result else "(empty directory)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="list_directory",
        description="List all files and subdirectories in a directory",
        func=list_directory,
        parameters={"path": "string - absolute path to directory"}
    )
    
    # ============================================================
    # CIF Tools
    # ============================================================
    
    def count_atom_in_cif(cif_path: str, atom_label: str) -> str:
        """Count specific atom type in CIF file."""
        try:
            count = cif.count_atom_type_in_cif(cif_path, atom_label)
            return f"Found {count} atoms of type '{atom_label}' in {Path(cif_path).name}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="count_atom_in_cif",
        description="Count how many atoms of a specific type are in a CIF file",
        func=count_atom_in_cif,
        parameters={
            "cif_path": "string - absolute path to CIF file",
            "atom_label": "string - atom type to count (e.g., 'Si', 'O', 'Na')"
        }
    )
    
    def get_unit_cell(cif_path: str) -> str:
        """Get unit cell dimensions from CIF file."""
        try:
            a, b, c = cif.get_unit_cell_size(cif_path)
            return f"Unit cell dimensions: a={a:.3f} Å, b={b:.3f} Å, c={c:.3f} Å"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="get_unit_cell",
        description="Get the unit cell lattice parameters (a, b, c) from a CIF file",
        func=get_unit_cell,
        parameters={"cif_path": "string - absolute path to CIF file"}
    )
    
    def read_atoms_from_cif(cif_path: str) -> str:
        """Get list of all atom types in CIF."""
        try:
            from pymatgen.core import Structure
            structure = Structure.from_file(cif_path)
            atom_types = set()
            for site in structure.sites:
                atom_types.add(site.species_string)
            return f"Atom types in {Path(cif_path).name}: {', '.join(sorted(atom_types))}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="read_atoms_from_cif",
        description="Get the list of all atom types present in a CIF file",
        func=read_atoms_from_cif,
        parameters={"cif_path": "string - absolute path to CIF file"}
    )
    
    # ============================================================
    # Force Field Tools
    # ============================================================
    
    def list_force_fields(ff_root: str) -> str:
        """List available force field directories."""
        try:
            ffs = forcefield.get_all_force_field_descriptions(ff_root)
            if not ffs:
                return f"No force fields found in {ff_root}"
            result = [f"Found {len(ffs)} force field(s):"]
            for ff in ffs:
                result.append(f"  - {ff['name']}")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="list_force_fields",
        description="List all available force field directories",
        func=list_force_fields,
        parameters={"ff_root": "string - absolute path to force field root directory"}
    )
    
    def get_ff_atoms(pseudo_atoms_path: str) -> str:
        """Get atoms defined in pseudo_atoms.def."""
        try:
            atoms = forcefield.get_atoms_in_ff_file(pseudo_atoms_path)
            if not atoms:
                return f"No atoms found in {pseudo_atoms_path}"
            return f"Atoms defined in force field: {', '.join(sorted(atoms))}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="get_ff_atoms",
        description="Get the list of atom types defined in a pseudo_atoms.def file",
        func=get_ff_atoms,
        parameters={"pseudo_atoms_path": "string - absolute path to pseudo_atoms.def file"}
    )
    
    # ============================================================
    # Workspace Navigation
    # ============================================================
    
    def find_cif_files(search_dir: str) -> str:
        """Find all CIF files in a directory tree."""
        try:
            p = Path(search_dir)
            if not p.exists():
                return f"Error: Directory {search_dir} does not exist"
            
            cif_files = sorted(p.rglob("*.cif"))
            if not cif_files:
                return f"No CIF files found in {search_dir}"
            
            result = [f"Found {len(cif_files)} CIF file(s):"]
            for cif_file in cif_files[:20]:  # Limit to first 20
                rel_path = cif_file.relative_to(p) if cif_file.is_relative_to(p) else cif_file
                result.append(f"  - {rel_path}")
            
            if len(cif_files) > 20:
                result.append(f"  ... and {len(cif_files) - 20} more")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="find_cif_files",
        description="Search for all CIF files in a directory and its subdirectories",
        func=find_cif_files,
        parameters={"search_dir": "string - absolute path to directory to search"}
    )
    
    # ============================================================
    # Structure Database Tools
    # ============================================================
    
    def download_cif_from_iza(structure_code: str, save_dir: str) -> str:
        """
        Download CIF file from IZA zeolite database.
        
        Args:
            structure_code: 3-letter IZA code (e.g., 'MOR', 'MFI', 'LTA')
            save_dir: Directory to save the downloaded file
            
        Returns:
            Success message with file path or error message
        """
        try:
            import requests
            
            # Ensure save directory exists
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # IZA database URL
            code = structure_code.upper()
            url = f"https://europe.iza-structure.org/IZA-SC/cif/{code}.cif"
            
            # Download
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                output_file = save_path / f"{code}.cif"
                output_file.write_text(response.text, encoding='utf-8')
                return f"Successfully downloaded {code}.cif from IZA database to {output_file}"
            elif response.status_code == 404:
                return f"Error: Structure '{code}' not found in IZA database (404). Check the structure code."
            else:
                return f"Error: HTTP {response.status_code} when downloading {code}.cif"
                
        except requests.exceptions.Timeout:
            return f"Error: Timeout when connecting to IZA database"
        except requests.exceptions.RequestException as e:
            return f"Error: Network error - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    registry.register_function(
        name="download_cif_from_iza",
        description="Download zeolite structure CIF file from IZA database by 3-letter code (e.g., MOR, MFI, LTA, FAU, CHA)",
        func=download_cif_from_iza,
        parameters={
            "structure_code": "string - 3-letter IZA structure code (e.g., 'MOR', 'MFI', 'LTA')",
            "save_dir": "string - absolute path to directory where CIF file should be saved"
        }
    )
    
    return registry
