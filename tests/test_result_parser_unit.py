"""
Unit tests for ResultParser.

Tests the isotherm data parsing and validation functionality.
"""

import pytest
from pathlib import Path
from gcmc_agent.tools.result_parser import ResultParser, IsothermData


class TestIsothermData:
    """Tests for IsothermData dataclass."""

    def test_empty_isotherm_invalid(self):
        """Empty isotherm should be invalid."""
        isotherm = IsothermData()
        assert not isotherm.is_valid()

    def test_valid_isotherm(self):
        """Valid isotherm with data should pass validation."""
        isotherm = IsothermData(
            molecule="CO2",
            structure="MFI",
            temperature=298.0,
            pressures=[0.1, 1.0, 10.0],
            loadings=[0.5, 2.3, 4.1]
        )
        assert isotherm.is_valid()
        assert len(isotherm) == 3

    def test_mismatched_data_invalid(self):
        """Isotherm with mismatched pressure/loading should be invalid."""
        isotherm = IsothermData(
            pressures=[0.1, 1.0],
            loadings=[0.5, 2.3, 4.1]  # One extra loading
        )
        assert not isotherm.is_valid()

    def test_negative_pressure_invalid(self):
        """Negative pressure should make isotherm invalid."""
        isotherm = IsothermData(
            pressures=[-0.1, 1.0, 10.0],
            loadings=[0.5, 2.3, 4.1]
        )
        assert not isotherm.is_valid()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        isotherm = IsothermData(
            molecule="CO2",
            structure="MFI",
            temperature=298.0,
            pressures=[0.1, 1.0],
            loadings=[0.5, 2.3]
        )
        data = isotherm.to_dict()
        
        assert data["molecule"] == "CO2"
        assert data["structure"] == "MFI"
        assert data["temperature"] == 298.0
        assert len(data["pressures"]) == 2

    def test_save_and_load_json(self, temp_workspace):
        """Test saving and loading JSON."""
        isotherm = IsothermData(
            molecule="CO2",
            structure="MFI",
            temperature=298.0,
            pressures=[0.1, 1.0],
            loadings=[0.5, 2.3]
        )
        
        json_file = temp_workspace / "test_isotherm.json"
        isotherm.save_json(json_file)
        
        assert json_file.exists()
        assert json_file.stat().st_size > 0


class TestResultParser:
    """Tests for ResultParser class."""

    def test_parser_initialization(self):
        """Parser should initialize without errors."""
        parser = ResultParser(verbose=False)
        assert parser is not None

    def test_validate_output_missing_dir(self, temp_workspace):
        """Validation should fail for missing directory."""
        parser = ResultParser()
        result = parser.validate_output(temp_workspace / "nonexistent")
        
        assert not result["valid"]
        assert not result["output_dir_exists"]

    def test_validate_output_no_data_files(self, temp_workspace):
        """Validation should fail if no data files present."""
        output_dir = temp_workspace / "Output" / "System_0"
        output_dir.mkdir(parents=True)
        
        parser = ResultParser()
        result = parser.validate_output(output_dir)
        
        assert not result["valid"]
        assert len(result["data_files"]) == 0

    def test_validate_output_with_data_files(self, temp_workspace):
        """Validation should pass with data files present."""
        output_dir = temp_workspace / "Output" / "System_0"
        output_dir.mkdir(parents=True)
        
        # Create a dummy data file
        data_file = output_dir / "output_CO2_298K.data"
        data_file.write_text("dummy data")
        
        parser = ResultParser()
        result = parser.validate_output(output_dir)
        
        assert result["valid"]
        assert len(result["data_files"]) == 1


@pytest.mark.unit
class TestIsothermDataUnit:
    """Unit tests that don't require external resources."""

    def test_length_operator(self):
        """Test __len__ operator."""
        isotherm = IsothermData(
            pressures=[0.1, 1.0, 10.0, 50.0],
            loadings=[0.5, 2.3, 4.1, 5.8]
        )
        assert len(isotherm) == 4

    def test_empty_uncertainties(self):
        """Isotherm should work without uncertainties."""
        isotherm = IsothermData(
            pressures=[0.1, 1.0],
            loadings=[0.5, 2.3],
            uncertainties=[]
        )
        assert isotherm.is_valid()
