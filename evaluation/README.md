# Paper Reproduction Evaluation

This directory contains scripts and data for reproducing results from the paper:

**"Towards Fully Automated Molecular Simulations"** (arXiv:2509.10210v1)

## Overview

Two main evaluations:

- **Table 1**: Setup team file generation (7 scenarios)
- **Table 2**: Literature data extraction (6 papers)

## Table 1: Setup Team Evaluation

**Script**: `run_table1_evaluation.py`

Tests RASPA simulation file generation for:

1. 1 structure × 1 adsorbate - Isotherm
2. 1 structure × 1 adsorbate - Widom insertion
3. 1 structure × 2 adsorbates - Binary mixture
4. 2 structures × 1 adsorbate - Screening
5. 1 structure × 1 adsorbate - Pressure range
6. Multi-temperature isotherm
7. Custom force field parameters

Run:
```bash
python evaluation/run_table1_evaluation.py
```

## Table 2: Literature Extraction

**Script**: `run_table2_evaluation.py`

Extracts data from 6 papers:

1. EPM2 (Harris et al. 1995)
2. Garcia-Sanchez et al. 2009
3. Martin-Calvo et al. 2015
4. Multi-gas TraPPE
5. TraPPE-zeo (Bai et al. 2013)
6. Vujic et al. 2016

Run:
```bash
python evaluation/run_table2_evaluation.py
```

### Ground Truth

`ground_truth/` contains manually extracted reference data (6 JSON files).

### Extracted Results

`extracted/` stores evaluation results (run scripts to generate).

## Metrics

**IoU Calculator**: `iou_calculator.py`

```python
from evaluation.iou_calculator import calculate_iou
iou = calculate_iou(extracted_data, ground_truth)
```

## Results

Paper reports:
- Table 1: ~95% success rate
- Table 2: ~95% accuracy

## Requirements

⚠️ **Note**: Evaluation requires:
- LLM API access (costs money)
- Research paper PDFs
- RASPA installation

For regular usage, see [../examples/](../examples/)
