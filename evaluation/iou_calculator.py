#!/usr/bin/env python3
"""
IoU Calculator for Force Field Parameter Evaluation

Computes Intersection over Union (IoU) between extracted and ground truth force field parameters.
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_atom_param(atom_data: Dict[str, Any]) -> Tuple:
    """
    Normalize atom parameter to a comparable tuple.
    
    Returns: (atom_type, element, epsilon, sigma, charge)
    """
    atom_type = atom_data.get("atom_type", "").strip()
    element = atom_data.get("element", "").strip()
    
    # Normalize numerical values with tolerance
    epsilon = round(float(atom_data.get("epsilon", 0)), 2)
    sigma = round(float(atom_data.get("sigma", 0)), 3)
    charge = round(float(atom_data.get("charge", 0)), 4)
    
    return (atom_type, element, epsilon, sigma, charge)


def calculate_iou(extracted: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate IoU metrics between extracted and ground truth parameters.
    
    Returns:
        dict with: missed, wrong, correct, total_gt, total_extracted, iou, details
    """
    gt_atoms = ground_truth.get("atoms", [])
    ext_atoms = extracted.get("atoms", [])
    
    # Convert to normalized sets
    gt_set = set(normalize_atom_param(atom) for atom in gt_atoms)
    ext_set = set(normalize_atom_param(atom) for atom in ext_atoms)
    
    # Calculate metrics
    correct = gt_set & ext_set
    missed = gt_set - ext_set
    wrong = ext_set - gt_set
    
    # IoU = |intersection| / |union|
    union = gt_set | ext_set
    iou = len(correct) / len(union) if len(union) > 0 else 0.0
    
    # Count parameter-level errors
    missed_params = len(missed)
    wrong_params = len(wrong)
    
    # Extra atoms (in extracted but not in gt, by atom type only)
    gt_atom_types = {atom.get("atom_type") for atom in gt_atoms}
    ext_atom_types = {atom.get("atom_type") for atom in ext_atoms}
    extra_atom_types = ext_atom_types - gt_atom_types
    
    return {
        "missed": missed_params,
        "wrong": wrong_params,
        "correct": len(correct),
        "total_gt": len(gt_set),
        "total_extracted": len(ext_set),
        "iou": round(iou, 2),
        "extra_atoms": list(extra_atom_types),
        "missed_details": [
            {
                "atom_type": m[0],
                "element": m[1],
                "epsilon": m[2],
                "sigma": m[3],
                "charge": m[4]
            } for m in missed
        ],
        "wrong_details": [
            {
                "atom_type": w[0],
                "element": w[1],
                "epsilon": w[2],
                "sigma": w[3],
                "charge": w[4]
            } for w in wrong
        ]
    }


def compare_all_runs(
    extracted_dir: Path,
    ground_truth_dir: Path,
    paper_id: str,
    num_runs: int = 5
) -> Dict[str, Any]:
    """
    Compare multiple runs of extraction against ground truth.
    
    Returns aggregated statistics.
    """
    gt_file = ground_truth_dir / f"{paper_id}.json"
    if not gt_file.exists():
        raise FileNotFoundError(f"Ground truth file not found: {gt_file}")
    
    gt_data = load_json(gt_file)
    
    results = []
    for run_num in range(1, num_runs + 1):
        ext_file = extracted_dir / f"{paper_id}_run{run_num}.json"
        if not ext_file.exists():
            print(f"⚠️  Warning: {ext_file} not found, skipping")
            continue
        
        ext_data = load_json(ext_file)
        iou_result = calculate_iou(ext_data, gt_data)
        results.append(iou_result)
    
    if not results:
        return {
            "paper_id": paper_id,
            "num_runs": 0,
            "error": "No extraction results found"
        }
    
    # Aggregate statistics
    import statistics
    
    ious = [r["iou"] for r in results]
    missed_counts = [r["missed"] for r in results]
    wrong_counts = [r["wrong"] for r in results]
    
    return {
        "paper_id": paper_id,
        "num_runs": len(results),
        "missed_avg": round(statistics.mean(missed_counts), 1),
        "wrong_avg": round(statistics.mean(wrong_counts), 1),
        "iou_avg": round(statistics.mean(ious), 2),
        "iou_std": round(statistics.stdev(ious), 2) if len(ious) > 1 else 0.0,
        "all_runs": results
    }


if __name__ == "__main__":
    # Example usage
    eval_dir = Path(__file__).parent
    
    paper_id = "garcia_sanchez_2009"
    result = compare_all_runs(
        extracted_dir=eval_dir / "extracted",
        ground_truth_dir=eval_dir / "ground_truth",
        paper_id=paper_id,
        num_runs=5
    )
    
    print(json.dumps(result, indent=2))
