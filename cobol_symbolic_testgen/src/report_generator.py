import json
from typing import List, Dict, Any

class ReportGenerator:
    """Formats global solver test suites into Markdown tables and JSON test data files."""

    @staticmethod
    def to_json(suite: List[Dict[str, Any]], indent: int = 2) -> str:
        return json.dumps(suite, indent=indent)

    @staticmethod
    def to_markdown_table(contract_id: str, suite: List[Dict[str, Any]]) -> str:
        lines = []
        lines.append(f"## Global SMT Test Suite for Rule: `{contract_id}`\n")
        lines.append("| Test ID | Step Name | Category / Vector | Concrete Inputs | Expected Outputs & Status | External System Mocks |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

        for step in suite:
            if not step.get("reachable", True):
                lines.append(f"| `{step['step_id']}-N/A` | {step['step_name']} | **{step['category']}** (UNSAT) | *Mathematically Unreachable* | `{step.get('proof', 'UNSAT')}` | `None` |")
                continue

            for tc in step.get("test_cases", []):
                t_id = tc["test_id"]
                s_name = step["step_name"]
                desc = tc["description"]
                inps = tc["inputs"]
                outs = tc["expected_outputs"]
                mocks = tc.get("external_mocks", {})

                inp_str = ", ".join([f"{k}={v}" for k, v in inps.items()])
                out_str = ", ".join([f"{k}={v}" for k, v in outs.items()])
                mock_str = ", ".join([f"{sys}: {m['field']}={m['value']}" for sys, m in mocks.items()]) if mocks else "None"

                lines.append(f"| `{t_id}` | {s_name} | {step['target_test_vector']} | `{inp_str}` | `{out_str}` | `{mock_str}` |")

        return "\n".join(lines)
