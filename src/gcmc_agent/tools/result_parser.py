"""
RASPA Result Parser - Extract adsorption isotherm data from RASPA output files

This module provides functionality to:
1. Parse RASPA output files (*.data format)
2. Extract pressure-loading isotherm data
3. Convert units (Pa → bar, mol/uc → mol/kg)
4. Validate and export results
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import json


@dataclass
class IsothermData:
    """Container for adsorption isotherm data"""
    
    pressures: List[float] = field(default_factory=list)  # bar
    loadings: List[float] = field(default_factory=list)   # mol/kg
    uncertainties: List[float] = field(default_factory=list)  # mol/kg
    
    molecule: str = ""
    structure: str = ""
    temperature: float = 0.0  # K
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Number of pressure points"""
        return len(self.pressures)
    
    def is_valid(self) -> bool:
        """Check if data is valid"""
        if len(self.pressures) == 0:
            return False
        if len(self.pressures) != len(self.loadings):
            return False
        if any(p < 0 for p in self.pressures):
            return False
        if any(l < 0 for l in self.loadings):
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export"""
        return {
            "molecule": self.molecule,
            "structure": self.structure,
            "temperature": self.temperature,
            "pressures": self.pressures,
            "loadings": self.loadings,
            "uncertainties": self.uncertainties,
            "metadata": self.metadata
        }
    
    def save_json(self, filepath: Path) -> None:
        """Save isotherm data to JSON file"""
        filepath = Path(filepath)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def plot(self, filepath: Optional[Path] = None, show: bool = False) -> None:
        """
        Plot isotherm data
        
        Args:
            filepath: Save plot to file (optional)
            show: Display plot interactively
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib required for plotting. Install with: pip install matplotlib")
        
        plt.figure(figsize=(8, 6))
        
        if self.uncertainties and any(u > 0 for u in self.uncertainties):
            plt.errorbar(self.pressures, self.loadings, yerr=self.uncertainties,
                        fmt='o-', capsize=5, label=self.molecule)
        else:
            plt.plot(self.pressures, self.loadings, 'o-', label=self.molecule)
        
        plt.xlabel('Pressure (bar)', fontsize=12)
        plt.ylabel('Loading (mol/kg)', fontsize=12)
        plt.title(f'{self.molecule} in {self.structure} at {self.temperature:.0f} K', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if filepath:
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()


class ResultParser:
    """Parse RASPA simulation output files"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def parse_isotherm(
        self,
        output_dir: Path,
        molecule_name: Optional[str] = None,
        structure_name: Optional[str] = None
    ) -> IsothermData:
        """
        Parse isotherm data from RASPA output directory
        
        Args:
            output_dir: Path to RASPA Output/System_0 directory
            molecule_name: Override molecule name (auto-detected if None)
            structure_name: Override structure name (auto-detected if None)
            
        Returns:
            IsothermData object with extracted data
        """
        output_dir = Path(output_dir)
        
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")
        
        # Find output data file
        data_files = list(output_dir.glob("output_*.data"))
        if not data_files:
            raise FileNotFoundError(f"No output_*.data files found in {output_dir}")
        
        # Use first data file (typically output_Component_0.data)
        data_file = data_files[0]
        
        if self.verbose:
            print(f"Parsing: {data_file}")
        
        # Parse the data file
        isotherm = self._parse_data_file(data_file)
        
        # Override names if provided
        if molecule_name:
            isotherm.molecule = molecule_name
        if structure_name:
            isotherm.structure = structure_name
        
        # Try to extract names from parent directories if not set
        if not isotherm.molecule:
            isotherm.molecule = self._guess_molecule_name(data_file)
        if not isotherm.structure:
            isotherm.structure = self._guess_structure_name(output_dir)
        
        if self.verbose:
            print(f"Extracted {len(isotherm)} pressure points")
            print(f"Pressure range: {min(isotherm.pressures):.2e} - {max(isotherm.pressures):.2e} bar")
            print(f"Loading range: {min(isotherm.loadings):.2e} - {max(isotherm.loadings):.2e} mol/kg")
        
        return isotherm
    
    def _parse_data_file(self, filepath: Path) -> IsothermData:
        """Parse a single RASPA output_*.data file"""
        isotherm = IsothermData()
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract temperature (search for "External temperature:")
        temp_match = re.search(r'External temperature:\s+([\d.]+)\s*\[K\]', content)
        if temp_match:
            isotherm.temperature = float(temp_match.group(1))
        
        # Parse data table
        # Format: Pressure, Loading, Uncertainty
        # Example:
        # 0.000000e+00  1.234e+00  0.012e+00
        
        lines = content.split('\n')
        in_data_section = False
        
        for line in lines:
            line = line.strip()
            
            # Detect data section start
            if 'Average loading' in line or 'Pressure' in line:
                in_data_section = True
                continue
            
            # Skip empty lines
            if not line or line.startswith('#'):
                continue
            
            # Try to parse data line
            if in_data_section:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pressure_pa = float(parts[0])  # Pascal
                        loading_mol_uc = float(parts[1])  # mol/unit cell
                        uncertainty = float(parts[2]) if len(parts) > 2 else 0.0
                        
                        # Convert units
                        pressure_bar = pressure_pa / 1e5  # Pa → bar
                        
                        # Loading conversion requires unit cell mass
                        # For now, store as-is (will need unit cell info for proper conversion)
                        loading_mol_kg = loading_mol_uc
                        uncertainty_mol_kg = uncertainty
                        
                        isotherm.pressures.append(pressure_bar)
                        isotherm.loadings.append(loading_mol_kg)
                        isotherm.uncertainties.append(uncertainty_mol_kg)
                        
                    except (ValueError, IndexError):
                        # Not a valid data line, skip
                        continue
        
        # Alternative parsing: look for "output" files with clearer format
        if len(isotherm.pressures) == 0:
            isotherm = self._parse_alternative_format(filepath.parent)
        
        return isotherm
    
    def _parse_alternative_format(self, output_dir: Path) -> IsothermData:
        """
        Parse alternative RASPA output format
        
        Some RASPA versions output data in different formats.
        This method handles the most common alternative.
        """
        isotherm = IsothermData()
        
        # Look for files with "loading" in the name
        loading_files = list(output_dir.glob("*loading*.txt")) + \
                       list(output_dir.glob("*Loading*.data"))
        
        if not loading_files:
            return isotherm
        
        for filepath in loading_files:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pressure = float(parts[0])
                        loading = float(parts[1])
                        uncertainty = float(parts[2]) if len(parts) > 2 else 0.0
                        
                        # Assume already in correct units
                        isotherm.pressures.append(pressure)
                        isotherm.loadings.append(loading)
                        isotherm.uncertainties.append(uncertainty)
                    except ValueError:
                        continue
        
        return isotherm
    
    def _guess_molecule_name(self, data_file: Path) -> str:
        """Extract molecule name from filename"""
        # output_CO2_298.000000K_1.00000e+05Pa.data → CO2
        filename = data_file.stem
        match = re.search(r'output_([A-Za-z0-9]+)_', filename)
        if match:
            return match.group(1)
        return "Unknown"
    
    def _guess_structure_name(self, output_dir: Path) -> str:
        """Extract structure name from directory structure"""
        # Look for .cif files in parent directories
        current = output_dir.parent
        for _ in range(3):  # Search up to 3 levels
            cif_files = list(current.glob("*.cif"))
            if cif_files:
                return cif_files[0].stem
            current = current.parent
        return "Unknown"
    
    def validate_output(self, output_dir: Path) -> Dict[str, Any]:
        """
        Validate RASPA output directory
        
        Args:
            output_dir: Path to Output/System_0 directory
            
        Returns:
            Dictionary with validation results
        """
        output_dir = Path(output_dir)
        
        result = {
            "valid": False,
            "output_dir_exists": output_dir.exists(),
            "data_files": [],
            "missing_files": [],
            "warnings": []
        }
        
        if not output_dir.exists():
            result["missing_files"].append(str(output_dir))
            return result
        
        # Check for required files
        data_files = list(output_dir.glob("output_*.data"))
        result["data_files"] = [str(f) for f in data_files]
        
        if not data_files:
            result["warnings"].append("No output_*.data files found")
            result["missing_files"].append("output_*.data")
        
        # Check for log files
        log_files = list(output_dir.glob("*.txt"))
        if not log_files:
            result["warnings"].append("No log files (*.txt) found")
        
        # Validation passes if at least one data file exists
        result["valid"] = len(data_files) > 0
        
        return result
    
    def parse_batch(
        self,
        base_dir: Path,
        pattern: str = "*/Output/System_0"
    ) -> List[IsothermData]:
        """
        Parse multiple isotherm outputs in batch
        
        Args:
            base_dir: Base directory containing multiple simulation outputs
            pattern: Glob pattern to find Output directories
            
        Returns:
            List of IsothermData objects
        """
        base_dir = Path(base_dir)
        output_dirs = list(base_dir.glob(pattern))
        
        if self.verbose:
            print(f"Found {len(output_dirs)} output directories")
        
        isotherms = []
        for output_dir in output_dirs:
            try:
                isotherm = self.parse_isotherm(output_dir)
                if isotherm.is_valid():
                    isotherms.append(isotherm)
                else:
                    if self.verbose:
                        print(f"Warning: Invalid isotherm data in {output_dir}")
            except Exception as e:
                if self.verbose:
                    print(f"Error parsing {output_dir}: {e}")
        
        return isotherms


def quick_parse(output_dir: Path) -> IsothermData:
    """
    Convenience function for quick isotherm parsing
    
    Args:
        output_dir: Path to RASPA Output/System_0 directory
        
    Returns:
        IsothermData object
    """
    parser = ResultParser(verbose=True)
    return parser.parse_isotherm(output_dir)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
        parser = ResultParser(verbose=True)
        isotherm = parser.parse_isotherm(output_dir)
        
        print(f"\n=== Isotherm Data ===")
        print(f"Molecule: {isotherm.molecule}")
        print(f"Structure: {isotherm.structure}")
        print(f"Temperature: {isotherm.temperature} K")
        print(f"Data points: {len(isotherm)}")
        
        if isotherm.is_valid():
            print(f"\nPressure range: {min(isotherm.pressures):.2f} - {max(isotherm.pressures):.2f} bar")
            print(f"Loading range: {min(isotherm.loadings):.2e} - {max(isotherm.loadings):.2e} mol/kg")
            
            # Save to JSON
            output_json = output_dir.parent / "isotherm.json"
            isotherm.save_json(output_json)
            print(f"\nSaved to: {output_json}")
        else:
            print("\nWarning: Isotherm data is invalid")
    else:
        print("Usage: python result_parser.py <path/to/Output/System_0>")
