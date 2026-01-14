"""
RASPA Runner - 执行RASPA模拟并验证结果

功能:
1. 检查RASPA安装
2. 执行模拟
3. 捕获输出
4. 验证成功
5. 解析结果
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import re


@dataclass
class RaspaResult:
    """RASPA execution result."""
    success: bool
    output_dir: Path
    stdout: str
    stderr: str
    execution_time: float
    error_message: Optional[str] = None
    output_files: List[Path] = None
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []


class RaspaRunner:
    """
    Execute RASPA simulations and parse results.
    
    Usage:
        runner = RaspaRunner()
        result = runner.run(simulation_dir)
        if result.success:
            print(f"Simulation complete: {result.output_files}")
    """
    
    def __init__(
        self,
        raspa_executable: Optional[str] = None,
        timeout: int = 3600,
        verbose: bool = False
    ):
        """
        Initialize RASPA runner.
        
        Args:
            raspa_executable: Path to RASPA simulate executable
            timeout: Maximum execution time in seconds
            verbose: Print detailed output
        """
        self.timeout = timeout
        self.verbose = verbose
        
        # Find RASPA executable
        if raspa_executable:
            self.raspa_exe = Path(raspa_executable)
        else:
            self.raspa_exe = self._find_raspa()
        
        if not self.raspa_exe:
            print("⚠️  RASPA not found. Set RASPA_DIR environment variable or provide path.")
    
    def _find_raspa(self) -> Optional[Path]:
        """Locate RASPA executable."""
        # Check environment variable
        raspa_dir = os.getenv("RASPA_DIR")
        if raspa_dir:
            exe = Path(raspa_dir) / "bin" / "simulate"
            if exe.exists():
                return exe
        
        # Check common locations (prioritize software/installed versions)
        common_paths = [
            Path.home() / "software" / "raspa2" / "raspa" / "bin" / "simulate",
            Path("/usr/local/bin/simulate"),
            Path("/opt/raspa/bin/simulate"),
            Path.home() / "RASPA" / "bin" / "simulate",
            Path.home() / "RASPA2" / "src" / ".libs" / "simulate",
            Path.home() / "RASPA2" / "src" / "simulate",
        ]
        
        for path in common_paths:
            if path.exists():
                return path
        
        # Check if in PATH
        exe = shutil.which("simulate")
        if exe:
            return Path(exe)
        
        return None
    
    def check_installation(self) -> bool:
        """Check if RASPA is properly installed."""
        if not self.raspa_exe or not self.raspa_exe.exists():
            return False
        
        # RASPA doesn't support --version flag reliably
        # Just check if executable exists and is executable
        return self.raspa_exe.is_file() and os.access(self.raspa_exe, os.X_OK)
    
    def run(
        self,
        simulation_dir: Path,
        input_file: str = "simulation.input"
    ) -> RaspaResult:
        """
        Execute RASPA simulation.
        
        Args:
            simulation_dir: Directory containing simulation.input
            input_file: Name of input file (default: simulation.input)
        
        Returns:
            RaspaResult with execution details
        """
        import time
        start_time = time.time()
        
        # Validate setup
        if not self.raspa_exe:
            return RaspaResult(
                success=False,
                output_dir=simulation_dir,
                stdout="",
                stderr="",
                execution_time=0,
                error_message="RASPA executable not found"
            )
        
        input_path = simulation_dir / input_file
        if not input_path.exists():
            return RaspaResult(
                success=False,
                output_dir=simulation_dir,
                stdout="",
                stderr="",
                execution_time=0,
                error_message=f"Input file not found: {input_path}"
            )
        
        # Prepare execution
        output_dir = simulation_dir / "Output"
        output_dir.mkdir(exist_ok=True)
        
        if self.verbose:
            print(f"\n🚀 Running RASPA simulation...")
            print(f"   Executable: {self.raspa_exe}")
            print(f"   Input: {input_path}")
            print(f"   Output: {output_dir}")
        
        # Execute RASPA
        try:
            result = subprocess.run(
                [str(self.raspa_exe), input_file],
                cwd=simulation_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            # Check success
            success = self._check_success(result.stdout, result.stderr, result.returncode)
            
            # Find output files
            output_files = self._find_output_files(output_dir)
            
            if self.verbose:
                if success:
                    print(f"✅ Simulation completed in {execution_time:.1f}s")
                    print(f"   Output files: {len(output_files)}")
                else:
                    print(f"❌ Simulation failed after {execution_time:.1f}s")
            
            error_msg = None if success else self._extract_error(result.stdout, result.stderr)
            
            return RaspaResult(
                success=success,
                output_dir=output_dir,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=execution_time,
                error_message=error_msg,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            return RaspaResult(
                success=False,
                output_dir=output_dir,
                stdout="",
                stderr="",
                execution_time=self.timeout,
                error_message=f"Simulation timeout after {self.timeout}s"
            )
        
        except Exception as e:
            return RaspaResult(
                success=False,
                output_dir=output_dir,
                stdout="",
                stderr="",
                execution_time=time.time() - start_time,
                error_message=f"Execution error: {str(e)}"
            )
    
    def _check_success(self, stdout: str, stderr: str, returncode: int) -> bool:
        """Determine if simulation succeeded."""
        # Check return code
        if returncode != 0:
            return False
        
        # Check for error keywords in output
        error_keywords = [
            "ERROR",
            "FATAL",
            "Segmentation fault",
            "core dumped",
            "failed to",
        ]
        
        combined_output = stdout + stderr
        for keyword in error_keywords:
            if keyword in combined_output:
                return False
        
        # Check for success indicators
        success_keywords = [
            "Simulation finished",
            "Number of finished Adsorbate-moves",
            "Average Widom Rosenbluth-weight",
        ]
        
        for keyword in success_keywords:
            if keyword in stdout:
                return True
        
        # If no clear indicator, consider it failed
        return False
    
    def _extract_error(self, stdout: str, stderr: str) -> str:
        """Extract error message from output."""
        # Look for error lines
        error_lines = []
        for line in (stdout + "\n" + stderr).split('\n'):
            if any(kw in line for kw in ["ERROR", "Error", "error", "FATAL"]):
                error_lines.append(line.strip())
        
        if error_lines:
            return "\n".join(error_lines[:5])  # First 5 error lines
        
        return "Simulation failed (no specific error message)"
    
    def _find_output_files(self, output_dir: Path) -> List[Path]:
        """Find all output files generated."""
        if not output_dir.exists():
            return []
        
        output_files = []
        for pattern in ["*.data", "*.dat", "*.txt", "*.output"]:
            output_files.extend(output_dir.glob(f"**/{pattern}"))
        
        return sorted(output_files)
    
    def validate_setup(self, simulation_dir: Path) -> Dict[str, Any]:
        """
        Validate simulation setup without running.
        
        Checks:
        - simulation.input exists
        - Structure files exist
        - Force field files exist
        - Basic syntax validity
        
        Returns:
            dict with validation results
        """
        issues = []
        
        # Check simulation.input
        input_file = simulation_dir / "simulation.input"
        if not input_file.exists():
            issues.append("simulation.input not found")
        else:
            # Basic syntax check
            try:
                content = input_file.read_text()
                if "SimulationType" not in content:
                    issues.append("simulation.input missing SimulationType")
                if "NumberOfCycles" not in content:
                    issues.append("simulation.input missing NumberOfCycles")
            except Exception as e:
                issues.append(f"Cannot read simulation.input: {e}")
        
        # Check for structure files
        cif_files = list(simulation_dir.glob("*.cif"))
        if not cif_files:
            issues.append("No .cif structure files found")
        
        # Check for force field files
        ff_file = simulation_dir / "force_field.def"
        if not ff_file.exists():
            issues.append("force_field.def not found")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "cif_files": [f.name for f in cif_files]
        }


def quick_test():
    """Quick test of RASPA installation."""
    runner = RaspaRunner(verbose=True)
    
    print("="*80)
    print("RASPA Installation Check")
    print("="*80)
    
    if runner.raspa_exe:
        print(f"✅ RASPA executable found: {runner.raspa_exe}")
    else:
        print("❌ RASPA executable not found")
        print("\nTo install RASPA:")
        print("  1. Download from: https://github.com/iRASPA/RASPA2")
        print("  2. Set RASPA_DIR environment variable")
        return
    
    if runner.check_installation():
        print("✅ RASPA installation verified")
    else:
        print("❌ RASPA installation check failed")
    
    print("="*80)


if __name__ == "__main__":
    quick_test()
