import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.contract_loader import UniversalContractLoader
from src.solver_engine import GlobalSmtSolverEngine
from src.report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(
        description="Global COBOL SMT Symbolic Test Data Generator. Ingests any rule contract with complex logic and external connections."
    )
    parser.add_argument("--contract", "-c", type=str, required=True, help="Path to any symbolic contract JSON file")
    parser.add_argument("--out-json", "-j", type=str, default=None, help="Output path for generated JSON test dataset")
    parser.add_argument("--out-md", "-m", type=str, default=None, help="Output path for generated Markdown table report")

    args = parser.parse_args()

    contract_path = Path(args.contract).resolve()
    if not contract_path.exists():
        print(f"[-] Error: Contract file not found at: {contract_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Ingesting Universal Symbolic Contract: {contract_path.name}")
    contract = UniversalContractLoader.load_from_file(str(contract_path))
    print(f"[+] Rule ID: {contract.rule_id} | Name: {contract.rule_name} | Program: {contract.program}")
    print(f"[+] Loaded {len(contract.domain.variables)} Domain Variables and {len(contract.domain.constants)} Constants.")

    print(f"[*] Executing Global SMT Constraint Solving across {len(contract.contract_steps)} rule steps...")
    engine = GlobalSmtSolverEngine(contract)
    test_suite = engine.generate_global_test_suite()

    # Formatted Reports
    json_output = ReportGenerator.to_json(test_suite)
    md_output = ReportGenerator.to_markdown_table(contract.rule_id, test_suite)

    # Save outputs if specified
    if args.out_json:
        out_j_path = Path(args.out_json).resolve()
        out_j_path.parent.mkdir(parents=True, exist_ok=True)
        out_j_path.write_text(json_output, encoding="utf-8")
        print(f"[+] Saved Test Suite JSON to: {out_j_path}")

    if args.out_md:
        out_m_path = Path(args.out_md).resolve()
        out_m_path.parent.mkdir(parents=True, exist_ok=True)
        out_m_path.write_text(md_output, encoding="utf-8")
        print(f"[+] Saved Test Suite Markdown to: {out_m_path}")

    # Print summary to stdout
    print("\n" + "="*90)
    print(md_output)
    print("="*90 + "\n")

if __name__ == "__main__":
    main()
