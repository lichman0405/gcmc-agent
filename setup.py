"""Setup configuration for gcmc-agent."""
from setuptools import setup, find_packages

setup(
    name="gcmc-agent",
    version="0.1.1",
    description="Multi-agent LLM framework for RASPA molecular simulations",
    author="Shibo Li",
    author_email="shadow.li981@gmail.com",
    url="https://github.com/lichman0405/gcmc-agent",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "openai>=1.52.0",
        "langchain>=0.3.0",
        "langchain-openai>=0.2.0",
        # "langgraph>=0.2.30",  # Optional - not used in ReAct implementation
        "python-dotenv>=1.0.1",
        "pymatgen>=2024.9.16",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pypdf>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "mypy>=1.5.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "pylint>=2.17.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.1.0",
            "mkdocstrings[python]>=0.22.0",
        ],
    },
)
