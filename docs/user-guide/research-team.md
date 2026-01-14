# Research Team

The Research Team extracts simulation parameters from scientific literature.

## Overview

The Research Team consists of specialized agents that work together to:

1. Search for relevant scientific papers
2. Extract force field parameters
3. Convert data to RASPA format
4. Verify completeness and accuracy

## Components

### PaperSearchAgent

Searches academic databases for relevant papers.

**Tools**:
- `search_semantic_scholar(query)` - Search by keywords
- `get_paper_metadata(paper_id)` - Retrieve paper details
- `filter_by_relevance(results)` - Rank papers

**Example**:
```python
from gcmc_agent.research import PaperSearchAgent

agent = PaperSearchAgent(llm_client)
papers = agent.search("TraPPE force field zeolites")

for paper in papers:
    print(f"{paper['title']} ({paper['year']})")
```

### ExtractionAgent

Extracts structured data from papers.

**Capabilities**:
- Parse PDF and text formats
- Identify force field parameters (σ, ε, q)
- Extract simulation conditions (T, P, cycles)
- Recognize structure names and types

**Tools**:
- `extract_from_pdf(file_path)` - PDF text extraction
- `parse_parameters(text)` - Parameter identification
- `extract_tables(pdf)` - Table data extraction

**Output Format**:
```json
{
  "molecule": "CO2",
  "framework": "ZIF-8",
  "force_field": {
    "type": "TraPPE",
    "parameters": {
      "C_co2": {"sigma": 2.80, "epsilon": 27.0, "charge": 0.70},
      "O_co2": {"sigma": 3.05, "epsilon": 79.0, "charge": -0.35}
    }
  },
  "simulation": {
    "temperature": 298,
    "pressures": [1e4, 5e4, 1e5],
    "cycles": 10000
  }
}
```

### ForceFieldWriterAgent

Converts extracted data to RASPA files.

**Generates**:
- `force_field.def` - LJ parameters and charges
- `pseudo_atoms.def` - Atom type definitions
- `force_field_mixing_rules.def` - Mixing rules

**Example Output** (`force_field.def`):
```
# Force field for CO2 (TraPPE)
# Extracted from Harris et al. 1995

C_co2  lennard-jones  27.0   2.80
O_co2  lennard-jones  79.0   3.05

C_co2  charge  0.70
O_co2  charge -0.35
```

## Workflow Example

### Complete Research Pipeline

```python
from gcmc_agent.research import ResearchSupervisor

supervisor = ResearchSupervisor(llm_client)

# User request
request = "Extract CO2 parameters from Dubbeldam 2007 paper"

# Execute research workflow
result = supervisor.run(request)

# Result contains:
result = {
    "paper": {
        "title": "...",
        "authors": "Dubbeldam et al.",
        "year": 2007
    },
    "extracted_data": {
        "molecule": "CO2",
        "force_field": {...}
    },
    "files": {
        "force_field": "path/to/force_field.def",
        "pseudo_atoms": "path/to/pseudo_atoms.def"
    }
}
```

## Advanced Features

### Multi-Paper Extraction

Extract and compare parameters from multiple papers:

```python
papers = ["Harris 1995", "Potoff 2001", "Dubbeldam 2007"]
results = []

for paper in papers:
    data = extraction_agent.extract(paper)
    results.append(data)

# Compare parameters
comparison = compare_force_fields(results)
```

### Automatic Validation

The team validates extracted data:

- Parameter ranges (physically reasonable?)
- Unit consistency (K vs kJ/mol)
- Charge neutrality (sum of charges = 0)
- Completeness (all required atoms defined)

### Error Recovery

Handles common extraction issues:

- **Missing data**: Request user input or use defaults
- **Ambiguous text**: Ask for clarification
- **Format variations**: Try multiple parsing strategies
- **OCR errors**: Apply text correction

## Integration with Setup Team

Research Team output feeds directly into Setup Team:

```python
# Research Team generates parameters
research_result = research_team.run(paper_query)

# Setup Team uses them
setup_result = setup_team.run(
    structure="ZIF-8",
    force_field=research_result["files"]["force_field"],
    conditions=research_result["extracted_data"]["simulation"]
)
```

## Best Practices

1. **Be specific**: "Extract CO2 TraPPE from Harris 1995" > "get CO2 params"
2. **Verify sources**: Check paper citations and credibility
3. **Compare multiple sources**: Cross-validate parameters
4. **Manual review**: Always review extracted parameters

## Limitations

- **PDF quality**: Poor scans may have OCR errors
- **Paywalls**: Some papers not accessible
- **Table complexity**: Complex multi-column tables may fail
- **Implicit data**: Parameters described in text not tables

## See Also

- [Setup Team](setup-team.md) - Using extracted parameters
- [API Reference](../api/agents.md) - Detailed API docs
