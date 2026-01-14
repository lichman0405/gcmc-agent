#!/usr/bin/env python3
"""
Table 2 Evaluation Script

Runs the 6 force field extraction tests (5 times each) and calculates metrics.
Supports:
- Local PDF files (via pypdf)
- Semantic Scholar API downloads
- Hardcoded example texts (fallback)
"""

import json
import sys
import argparse
from pathlib import Path
from statistics import mean, stdev
from typing import Optional, Dict

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from gcmc_agent.client import DeepSeekConfig, OpenAIChatClient
from gcmc_agent.research.extraction_agent import PaperExtractionAgent
from gcmc_agent.research.semantic_scholar import SemanticScholarClient

from iou_calculator import calculate_iou, load_json

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("⚠️  pypdf not installed. PDF loading disabled. Install with: pip install pypdf")


# Paper metadata: DOI, title, search query for Semantic Scholar
PAPER_METADATA = {
    "garcia_sanchez_2009": {
        "doi": "10.1021/jp810871f",
        "title": "Transferable Force Field for Carbon Dioxide Adsorption in Zeolites",
        "search_query": "Garcia-Sanchez transferable force field carbon dioxide zeolites",
        "pdf_filename": "garcia_sanchez_2009.pdf"
    },
    "trappe_zeo_bai_2013": {
        "doi": "10.1021/jp4074224",
        "title": "TraPPE-zeo: Transferable Potentials for Phase Equilibria Force Field for All-Silica Zeolites",
        "search_query": "Bai TraPPE-zeo transferable potentials all-silica zeolites",
        "pdf_filename": "trappe_zeo_bai_2013.pdf"
    },
    "vujic_2016": {
        "doi": "10.1088/0965-0393/24/4/045002",
        "title": "Transferable Force-Field for Modelling of CO2, N2, O2 and Ar in All-Silica and Na+ Exchanged Zeolites",
        "search_query": "Vujic transferable force-field CO2 N2 O2 Ar zeolites",
        "pdf_filename": "vujic_2016.pdf"
    },
    "epm2_harris_1995": {
        "doi": "10.1021/j100031a034",
        "title": "Carbon Dioxide's Liquid-Vapor Coexistence Curve And Critical Properties",
        "search_query": "Harris EPM2 carbon dioxide liquid-vapor coexistence",
        "pdf_filename": "epm2_harris_1995.pdf"
    },
    "martin_calvo_2015": {
        "doi": "10.1039/C5CP03749B",
        "title": "Transferable Force Fields for Adsorption of Small Gases in Zeolites",
        "search_query": "Martin-Calvo transferable force fields small gases zeolites",
        "pdf_filename": "martin_calvo_2015.pdf"
    },
    "multigas_trappe": {
        "doi": "10.1016/S0378-3812(98)00306-6",
        "title": "TraPPE: A Transferable Potential for Phase Equilibria",
        "search_query": "Martin Siepmann TraPPE transferable potential phase equilibria",
        "pdf_filename": "multigas_trappe.pdf"
    },
}

# Paper texts (abbreviated versions with force field tables - fallback when PDF not available)
PAPERS = {
    "garcia_sanchez_2009": """
Transferable Force Field for Carbon Dioxide Adsorption in Zeolites
J. Phys. Chem. C 2009, 113, 8814-8820

Force Field Parameters
The CO2 molecule is modeled using the TraPPE force field.

Table 1: Lennard-Jones Parameters for CO2
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
C_co2        27.0        2.80      +0.70
O_co2        79.0        3.05      -0.35

Mixing rules: Lorentz-Berthelot
""",
    
    "trappe_zeo_bai_2013": """
TraPPE-zeo: Transferable Potentials for Phase Equilibria Force Field for All-Silica Zeolites
J. Phys. Chem. C 2013, 117, 24375-24387

Table 1: Force Field Parameters for Zeolite Framework
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
Si           22.0        2.30      0.0
O_z          53.0        3.30      0.0

Additional note: The framework atoms have a small offset:
O_b          85.7        2.96      0.0

Mixing rules: Lorentz-Berthelot
""",
}


def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract text from PDF file."""
    if not PYPDF_AVAILABLE:
        print(f"❌ pypdf not available. Cannot extract from {pdf_path}")
        return None
    
    try:
        reader = PdfReader(pdf_path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = "\n".join(text_parts)
        print(f"✅ Extracted {len(full_text)} characters from {pdf_path.name}")
        return full_text
    except Exception as e:
        print(f"❌ Error extracting PDF {pdf_path}: {e}")
        return None


def download_paper_from_semantic_scholar(paper_id: str, metadata: Dict, output_dir: Path) -> Optional[str]:
    """Try to download paper from Semantic Scholar."""
    try:
        client = SemanticScholarClient()
        
        # Search for paper
        print(f"🔍 Searching Semantic Scholar for: {metadata['search_query']}")
        results = client.search(
            query=metadata['search_query'],
            limit=3,
            fields=['title', 'abstract', 'openAccessPdf', 'externalIds']
        )
        
        if not results:
            print(f"❌ No results found on Semantic Scholar")
            return None
        
        # Find matching paper (check DOI or title)
        target_paper = None
        for paper in results:
            external_ids = paper.get('externalIds', {})
            if external_ids.get('DOI') == metadata['doi']:
                target_paper = paper
                print(f"✅ Found paper by DOI: {metadata['doi']}")
                break
            elif metadata['title'].lower() in paper.get('title', '').lower():
                target_paper = paper
                print(f"✅ Found paper by title match")
                break
        
        if not target_paper:
            print(f"❌ Could not match paper in results")
            return None
        
        # Check for open access PDF
        pdf_info = target_paper.get('openAccessPdf')
        if pdf_info and pdf_info.get('url'):
            pdf_url = pdf_info['url']
            print(f"📥 Found open access PDF: {pdf_url}")
            
            # Download PDF
            import requests
            response = requests.get(pdf_url, timeout=30)
            if response.status_code == 200:
                pdf_path = output_dir / metadata['pdf_filename']
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded PDF to {pdf_path}")
                
                # Extract text
                return extract_text_from_pdf(pdf_path)
            else:
                print(f"❌ Failed to download PDF: HTTP {response.status_code}")
        else:
            print(f"❌ No open access PDF available")
        
        return None
        
    except Exception as e:
        print(f"❌ Error downloading from Semantic Scholar: {e}")
        return None


def load_paper_text(paper_id: str, pdf_dir: Optional[Path] = None, use_api: bool = False) -> str:
    """Load paper text from PDF, API, or fallback to hardcoded examples."""
    metadata = PAPER_METADATA[paper_id]
    
    # Try 1: Local PDF file
    if pdf_dir:
        pdf_path = pdf_dir / metadata['pdf_filename']
        if pdf_path.exists():
            print(f"📄 Loading from local PDF: {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
            if text:
                return text
    
    # Try 2: Semantic Scholar API
    if use_api:
        pdf_cache_dir = Path(__file__).parent / "pdfs"
        pdf_cache_dir.mkdir(exist_ok=True)
        
        text = download_paper_from_semantic_scholar(paper_id, metadata, pdf_cache_dir)
        if text:
            return text
    
    # Fallback: Hardcoded example
    print(f"⚠️  Using hardcoded example text for {paper_id}")
    return PAPERS[paper_id]


# Fallback paper texts (abbreviated versions with force field tables)
PAPERS = {
    "garcia_sanchez_2009": """
Transferable Force Field for Carbon Dioxide Adsorption in Zeolites
J. Phys. Chem. C 2009, 113, 8814-8820

Force Field Parameters
The CO2 molecule is modeled using the TraPPE force field.

Table 1: Lennard-Jones Parameters for CO2
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
C_co2        27.0        2.80      +0.70
O_co2        79.0        3.05      -0.35

Mixing rules: Lorentz-Berthelot
""",
    
    "trappe_zeo_bai_2013": """
TraPPE-zeo: Transferable Potentials for Phase Equilibria Force Field for All-Silica Zeolites
J. Phys. Chem. C 2013, 117, 24375-24387

Table 1: Force Field Parameters for Zeolite Framework
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
Si           22.0        2.30      0.0
O_z          53.0        3.30      0.0

Additional note: The framework atoms have a small offset:
O_b          85.7        2.96      0.0

Mixing rules: Lorentz-Berthelot
""",
    
    "vujic_2016": """
Transferable Force-Field for Modelling of CO2, N2, O2 and Ar in All-Silica and Na+ Exchanged Zeolites
Modelling Simul. Mater. Sci. Eng. 2016, 24, 045002

Table 2: Lennard-Jones Parameters
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
C_co2        28.129      2.757     +0.6512
O_co2        80.507      3.033     -0.3256
N_n2         38.298      3.310     -0.4050
O_o2         49.0        3.020     -0.1130
Ar           124.07      3.358     0.0

Mixing rules: Lorentz-Berthelot
""",
    
    "epm2_harris_1995": """
Carbon Dioxide's Liquid-Vapor Coexistence Curve And Critical Properties
J. Phys. Chem. 1995, 99, 12021-12024

EPM2 Model Parameters
Table I: Molecular Parameters for CO2
Atom    ε/kB (K)    σ (Å)     q (|e|)
C       28.129      2.757     +0.6512
O       80.507      3.033     -0.3256

Bond length: C-O = 1.149 Å
Combining rules: Lorentz-Berthelot
""",
    
    "martin_calvo_2015": """
Transferable Force Fields for Adsorption of Small Gases in Zeolites
Phys. Chem. Chem. Phys. 2015, 17, 24048-24055

Force Field: TraPPE model for CO2
Table 1: CO2 Parameters
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
C_co2        27.0        2.80      +0.70
O_co2        79.0        3.05      -0.35

Lorentz-Berthelot mixing rules
""",
    
    "multigas_trappe": """
TraPPE: A Transferable Potential for Phase Equilibria
Fluid Phase Equilibria 1998

Table 3: United-Atom Parameters for Small Molecules
Atom Type    ε/kB (K)    σ (Å)     q (|e|)
CH4          148.0       3.73      0.0
C_co2        27.0        2.80      +0.70
O_co2        79.0        3.05      -0.35
N_n2         36.0        3.31      -0.482
O_o2         49.0        3.02      0.0

Mixing rules: Lorentz-Berthelot
""",
}


def run_extraction(paper_id: str, paper_text: str, run_num: int, output_dir: Path):
    """Run a single extraction and save results."""
    print(f"\n{'='*60}")
    print(f"Run {run_num}: {paper_id}")
    print(f"{'='*60}")
    
    load_dotenv()
    cfg = DeepSeekConfig.from_env()
    llm_client = OpenAIChatClient(cfg)
    workspace_root = Path.cwd()
    
    agent = PaperExtractionAgent(
        llm_client=llm_client,
        workspace_root=workspace_root,
        model="deepseek-chat",
        verbose=True
    )
    
    result = agent.run(
        paper_text=paper_text,
        paper_title=paper_id
    )
    
    # Parse the result
    if result.success:
        # Extract JSON from answer
        answer = result.answer
        try:
            # Try to parse as JSON
            if answer.strip().startswith('{'):
                extracted_data = json.loads(answer)
            else:
                # Look for JSON in the answer
                import re
                json_match = re.search(r'\{.*\}', answer, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = {"error": "Could not parse JSON", "raw": answer}
        except json.JSONDecodeError as e:
            extracted_data = {"error": f"JSON parse error: {e}", "raw": answer}
    else:
        extracted_data = {"error": result.error}
    
    # Save result
    output_file = output_dir / f"{paper_id}_run{run_num}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2)
    
    print(f"✅ Saved to {output_file}")
    print(f"   Success: {result.success}")
    print(f"   Iterations: {len(result.thought_action_history)}")


def main():
    """Run Table 2 evaluation."""
    parser = argparse.ArgumentParser(description='Run Table 2 Force Field Extraction Evaluation')
    parser.add_argument('--pdf-dir', type=Path, help='Directory containing PDF files')
    parser.add_argument('--use-api', action='store_true', help='Download papers from Semantic Scholar')
    parser.add_argument('--paper', type=str, help='Run specific paper only (e.g., garcia_sanchez_2009)')
    parser.add_argument('--runs', type=int, default=5, help='Number of runs per paper (default: 5)')
    args = parser.parse_args()
    
    eval_dir = Path(__file__).parent
    extracted_dir = eval_dir / "extracted"
    gt_dir = eval_dir / "ground_truth"
    extracted_dir.mkdir(exist_ok=True)
    
    num_runs = args.runs
    
    print("="*80)
    print("TABLE 2 EVALUATION: Force Field Extraction")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Runs per paper: {num_runs}")
    print(f"  PDF directory: {args.pdf_dir or 'Not specified'}")
    print(f"  Use Semantic Scholar API: {args.use_api}")
    print(f"  Specific paper: {args.paper or 'All papers'}")
    print()
    
    # Select papers to run
    papers_to_run = [args.paper] if args.paper else list(PAPERS.keys())
    
    # Run extractions
    for paper_id in papers_to_run:
        if paper_id not in PAPERS:
            print(f"❌ Unknown paper: {paper_id}")
            continue
            
        print(f"\n{'#'*80}")
        print(f"# {paper_id.upper()}")
        print(f"{'#'*80}")
        
        # Load paper text (with PDF/API support)
        paper_text = load_paper_text(paper_id, pdf_dir=args.pdf_dir, use_api=args.use_api)
        
        for run_num in range(1, num_runs + 1):
            run_extraction(paper_id, paper_text, run_num, extracted_dir)
    
    # Evaluate results
    print(f"\n\n{'='*80}")
    print("EVALUATION RESULTS")
    print(f"{'='*80}\n")
    
    summary = []
    for paper_id in papers_to_run:
        from iou_calculator import compare_all_runs
        
        try:
            result = compare_all_runs(
                extracted_dir=extracted_dir,
                ground_truth_dir=gt_dir,
                paper_id=paper_id,
                num_runs=num_runs
            )
            summary.append(result)
            
            print(f"\n{paper_id}:")
            print(f"  Runs: {result['num_runs']}")
            print(f"  Missed: {result['missed_avg']:.1f}")
            print(f"  Wrong: {result['wrong_avg']:.1f}")
            print(f"  IoU: {result['iou_avg']:.2f} ± {result['iou_std']:.2f}")
            
        except Exception as e:
            print(f"\n{paper_id}: ERROR - {e}")
    
    # Save summary
    summary_file = eval_dir / "table2_results.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n\n✅ Summary saved to {summary_file}")
    
    # Print table
    print(f"\n{'='*80}")
    print("TABLE 2 SUMMARY (Paper Format)")
    print(f"{'='*80}")
    print(f"{'Force Field':<40} {'Missed':<10} {'Wrong':<10} {'IoU':<10}")
    print("-" * 80)
    
    for result in summary:
        paper_name = result['paper_id'].replace('_', ' ').title()
        print(f"{paper_name:<40} {result['missed_avg']:<10.1f} {result['wrong_avg']:<10.1f} {result['iou_avg']:<10.2f}")


if __name__ == "__main__":
    main()
