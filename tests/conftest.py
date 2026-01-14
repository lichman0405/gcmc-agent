"""
Pytest configuration and fixtures for GCMC-Agent tests.
"""

import pytest
from pathlib import Path
from typing import Generator
import tempfile
import shutil

# Test markers
pytest_plugins = ["pytest_mock"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "llm: Tests requiring LLM API calls")
    config.addinivalue_line("markers", "raspa: Tests requiring RASPA installation")
    config.addinivalue_line("markers", "slow: Slow tests")


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="gcmc_agent_test_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def templates_dir(project_root: Path) -> Path:
    """Get the templates directory."""
    return project_root / "templates" / "raspa"


@pytest.fixture
def sample_cif_file(temp_workspace: Path) -> Path:
    """Create a minimal sample CIF file for testing."""
    cif_content = """data_MFI
_cell_length_a    20.022
_cell_length_b    19.899
_cell_length_c    13.383
_cell_angle_alpha 90.000
_cell_angle_beta  90.000
_cell_angle_gamma 90.000
_symmetry_space_group_name_H-M 'P n m a'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Si1 Si 0.42230 0.05590 0.86880
O1  O  0.37190 0.05560 0.77790
"""
    cif_file = temp_workspace / "test_structure.cif"
    cif_file.write_text(cif_content)
    return cif_file


@pytest.fixture(scope="session")
def skip_llm_tests(request):
    """Skip tests marked with 'llm' if no API key is configured."""
    import os
    if not os.getenv("DEEPSEEK_API_KEY"):
        pytest.skip("LLM tests skipped: DEEPSEEK_API_KEY not set")


@pytest.fixture(scope="session")
def skip_raspa_tests(request):
    """Skip tests marked with 'raspa' if RASPA is not installed."""
    from gcmc_agent.tools.raspa_runner import RaspaRunner
    runner = RaspaRunner(verbose=False)
    if not runner.raspa_exe:
        pytest.skip("RASPA tests skipped: RASPA not installed")


@pytest.fixture
def mock_llm_response():
    """Provide a mock LLM response for testing."""
    return {
        "thought": "Test thought",
        "action": "Test action",
        "observation": "Test observation",
        "answer": "Test answer"
    }


@pytest.fixture
def sample_force_field_params():
    """Provide sample force field parameters for testing."""
    return {
        "molecule": "CO2",
        "atoms": [
            {"type": "C_co2", "epsilon": 27.0, "sigma": 2.80, "charge": 0.70},
            {"type": "O_co2", "epsilon": 79.0, "sigma": 3.05, "charge": -0.35},
        ],
        "bonds": [
            {"atoms": ["C", "O"], "length": 1.149}
        ]
    }


@pytest.fixture
def sample_simulation_request():
    """Provide a sample simulation request for testing."""
    return {
        "molecule": "CO2",
        "structure": "MFI",
        "temperature": 298.0,
        "pressures": [0.1, 1.0, 10.0],
        "simulation_type": "isotherm"
    }
