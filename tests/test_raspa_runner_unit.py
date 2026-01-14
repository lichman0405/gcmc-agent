"""
Unit tests for RaspaRunner.

Tests RASPA execution and validation functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from gcmc_agent.tools.raspa_runner import RaspaRunner, RaspaResult


class TestRaspaResult:
    """Tests for RaspaResult dataclass."""

    def test_successful_result(self):
        """Test creation of successful result."""
        result = RaspaResult(
            success=True,
            output_dir=Path("/tmp/output"),
            stdout="Simulation finished",
            stderr="",
            execution_time=120.5
        )
        
        assert result.success
        assert result.execution_time == 120.5
        assert result.error_message is None

    def test_failed_result(self):
        """Test creation of failed result."""
        result = RaspaResult(
            success=False,
            output_dir=Path("/tmp/output"),
            stdout="",
            stderr="ERROR: Invalid input",
            execution_time=5.0,
            error_message="Simulation failed"
        )
        
        assert not result.success
        assert result.error_message == "Simulation failed"


class TestRaspaRunner:
    """Tests for RaspaRunner class."""

    def test_initialization_no_raspa(self):
        """Runner should initialize even without RASPA."""
        with patch.object(RaspaRunner, '_find_raspa', return_value=None):
            runner = RaspaRunner(verbose=False)
            assert runner.raspa_exe is None

    def test_check_installation_not_found(self):
        """Check should return False if RASPA not found."""
        with patch.object(RaspaRunner, '_find_raspa', return_value=None):
            runner = RaspaRunner(verbose=False)
            assert not runner.check_installation()

    @pytest.mark.raspa
    def test_check_installation_found(self):
        """Check should return True if RASPA found (requires RASPA installation)."""
        runner = RaspaRunner(verbose=False)
        # This test requires actual RASPA installation
        # Skip if RASPA not found
        if runner.raspa_exe is None:
            pytest.skip("RASPA not installed")
        assert runner.check_installation()

    def test_validate_setup_missing_input(self, temp_workspace):
        """Validation should fail if simulation.input missing."""
        runner = RaspaRunner(verbose=False)
        result = runner.validate_setup(temp_workspace)
        
        assert not result["valid"]
        assert "simulation.input not found" in result["issues"]

    def test_validate_setup_missing_cif(self, temp_workspace):
        """Validation should fail if no CIF files present."""
        # Create simulation.input
        (temp_workspace / "simulation.input").write_text("dummy content")
        
        runner = RaspaRunner(verbose=False)
        result = runner.validate_setup(temp_workspace)
        
        assert not result["valid"]
        assert "No .cif structure files found" in result["issues"]

    def test_validate_setup_success(self, temp_workspace, sample_cif_file):
        """Validation should pass with all required files."""
        runner = RaspaRunner(verbose=False)
        
        # Create proper simulation.input with required fields
        sim_input = temp_workspace / "simulation.input"
        sim_input.write_text("""SimulationType    MonteCarlo
NumberOfCycles    1000
NumberOfInitializationCycles 100
PrintEvery        100
""")
        
        # Create force_field.def
        ff_def = temp_workspace / "force_field.def"
        ff_def.write_text("# Force field\n")
        
        # Copy CIF file
        import shutil
        shutil.copy(sample_cif_file, temp_workspace / "structure.cif")
        
        result = runner.validate_setup(temp_workspace)
        
        assert result["valid"], f"Validation failed: {result['issues']}"
        assert len(result["cif_files"]) == 2  # structure.cif + test_structure.cif
        assert "force_field.def" in [f.name for f in result.get("ff_files", [])] or len(result["issues"]) == 0


@pytest.mark.unit
class TestRaspaRunnerUnit:
    """Pure unit tests without file I/O."""

    def test_check_success_with_success_message(self):
        """Should detect successful simulation."""
        runner = RaspaRunner(verbose=False)
        stdout = "Simulation finished\nNumber of finished Adsorbate-moves: 1000"
        stderr = ""
        returncode = 0
        
        assert runner._check_success(stdout, stderr, returncode)

    def test_check_success_with_error(self):
        """Should detect failed simulation."""
        runner = RaspaRunner(verbose=False)
        stdout = ""
        stderr = "ERROR: Invalid force field"
        returncode = 1
        
        assert not runner._check_success(stdout, stderr, returncode)

    def test_check_success_with_segfault(self):
        """Should detect segmentation fault."""
        runner = RaspaRunner(verbose=False)
        stdout = "Starting simulation"
        stderr = "Segmentation fault (core dumped)"
        returncode = 139  # Segfault return code
        
        assert not runner._check_success(stdout, stderr, returncode)

    def test_extract_error_from_stderr(self):
        """Should extract error message from stderr."""
        runner = RaspaRunner(verbose=False)
        stderr = "ERROR: Line 1\nERROR: Line 2\nERROR: Line 3"
        stdout = ""
        
        error = runner._extract_error(stdout, stderr)
        assert "ERROR: Line 1" in error
        assert len(error.split('\n')) <= 5  # Should limit to 5 lines
