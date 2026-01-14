# Changelog

All notable changes to GCMC-Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of GCMC-Agent
- GlobalSupervisor for workflow orchestration
- Research Team for literature parameter extraction
  - PaperSearchAgent for Semantic Scholar integration
  - ExtractionAgent for PDF/text parsing
  - ForceFieldWriterAgent for RASPA file generation
- Setup Team for simulation file generation
  - StructureExpert for CIF file handling
  - ForceFieldExpert for force field selection
  - SimulationInputExpert for RASPA input creation
  - CodingExpert for batch script generation
  - Evaluator for validation
- RaspaRunner for simulation execution
- ResultParser for output processing
- Complete documentation with MkDocs
- Unit test suite with pytest
- Example scripts and tutorials
- Evaluation scripts for paper reproduction (Table 1 & 2)

### Documentation
- Installation guide
- Quick start tutorial
- Architecture overview
- User guide for Research and Setup Teams
- RASPA integration guide
- API reference documentation
- Contributing guidelines
- Evaluation and reproduction guides

### Examples
- Quick start example
- Literature extraction workflow
- Custom force field setup
- Batch simulation execution
- Result parsing and visualization

## [0.1.1] - 2026-01-14

### Changed
- **BREAKING:** Replaced LangGraph architecture with pure ReAct implementation
  - Removed `supervisor.py`, `graph.py`, `state.py` (LangGraph-based)
  - All agents now use ReAct pattern for consistency
  - Simpler architecture, same functionality

### Added
- GlobalSupervisor with 4-phase workflow (Research → Setup → Simulator → Parser)
- True agent delegation in Setup Team Supervisor
- Fixed agent iteration limits (PaperSearchAgent: 10→20, PaperExtractionAgent: 15→30)
- Improved prompts to prevent infinite loops

### Removed
- LangGraph dependencies and related code
- Obsolete simple implementations (extraction.py, ff_writer.py, semantic_scholar_enhanced.py)

### Fixed
- Setup Team now executes real agents instead of placeholders
- PaperSearchAgent stops after checking 3-5 papers
- PaperExtractionAgent outputs JSON directly without file verification loop

---

## [0.1.0] - 2026-01-13

### Added
- Initial development version
- ReAct agent framework implementation
- RASPA integration
- Basic documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- RASPA installation check (file-based instead of --version)
- Test validation for simulation.input content
- Result parser for isotherm extraction

### Security
- API key management via environment variables
- Input sanitization for file operations

## Version Numbering

GCMC-Agent uses semantic versioning:

- **Major version** (X.0.0): Breaking changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
4. Push tag: `git push origin vX.Y.Z`
5. GitHub Actions creates release

## Future Roadmap

### Planned Features

**v0.2.0** (Q2 2026)
- Support for additional force fields (OPLS, AMBER)
- Molecular dynamics simulation support
- Enhanced literature search (arXiv, PubMed)
- Web interface for workflow management
- Docker container for easy deployment

**v0.3.0** (Q3 2026)
- Multi-framework workflows
- Automated parameter optimization
- Machine learning force field integration
- Cloud execution support (AWS, Azure)
- Advanced visualization and analysis tools

**v0.4.0** (Q4 2026)
- Real-time collaboration features
- Workflow templates and presets
- Integration with Materials Project
- High-throughput screening capabilities
- Publication-ready report generation

### Under Consideration

- Integration with other simulation engines (LAMMPS, GROMACS)
- Quantum chemistry integration (Gaussian, ORCA)
- Active learning for parameter refinement
- Web API for programmatic access
- Plugin system for custom agents

## Contributing

See [Contributing Guide](../development/contributing.md) for how to contribute to GCMC-Agent.

## Support

- **Bug reports**: [GitHub Issues](https://github.com/lichman0405/gcmc-agent/issues)
- **Feature requests**: [GitHub Discussions](https://github.com/lichman0405/gcmc-agent/discussions)
- **Questions**: [GitHub Discussions Q&A](https://github.com/lichman0405/gcmc-agent/discussions/categories/q-a)

## Links

- [Repository](https://github.com/lichman0405/gcmc-agent)

## Links

- [Repository](https://github.com/lichman0405/gcmc-agent)
- [Documentation](https://gcmc-agent.readthedocs.io)
- [PyPI Package](https://pypi.org/project/gcmc-agent)
- [License](license.md)
