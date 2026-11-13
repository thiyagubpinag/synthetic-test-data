import ast
import re
from typing import Dict, Any, List, Optional
from z3 import (
    Solver, Real, Int, String, Bool, And, Or, Not, ToInt, ToReal, sat, unsat, ExprRef
)
from .models import SymbolicContract, ContractStep, PicSpec, ExternalConnection

class GlobalSmtSolverEngine:
    """Universal SMT execution engine capable of parsing complex boolean logic,

    evaluating multi-system dependencies (DB2, VSAM, CICS, MQ), and generating
    deterministic inputs/outputs for any COBOL business rule.
    """

    def __init__(self, contract: SymbolicContract):
        self.contract = contract
        self.z3_vars: Dict[str, ExprRef] = {}
        self._init_z3_variables()

    def _init_z3_variables(self):
        """Initializes typed Z3 symbolic variables for all domain variables,

        constants, and external system status codes.
        """
        # 1. Variables
        for var_name, pic in self.contract.domain.variables.items():
            clean = var_name.replace("-", "_")
            if pic.var_type == 'ALPHANUMERIC':
                self.z3_vars[var_name] = String(clean)
            elif pic.var_type == 'DECIMAL':
                self.z3_vars[var_name] = Real(clean)
            else:
                self.z3_vars[var_name] = Int(clean)

        # 2. External System Status Variables
        self.z3_vars['SQLCODE'] = Int('SQLCODE')
        self.z3_vars['WS-FILE-STATUS'] = String('WS_FILE_STATUS')
        self.z3_vars['EIBRESP'] = Int('EIBRESP')
        self.z3_vars['MQRC'] = Int('MQRC')

    def _get_domain_bounds(self) -> List[ExprRef]:
        """Collects physical PIC boundaries for all domain variables."""
        bounds = []
        for var_name, pic in self.contract.domain.variables.items():
            if pic.var_type in ('NUMERIC', 'DECIMAL') and pic.min_val is not None and pic.max_val is not None:
                z_var = self.z3_vars[var_name]
                bounds.append(z_var >= pic.min_val)
                bounds.append(z_var <= pic.max_val)
                if pic.var_type == 'DECIMAL' and pic.decimal_digits > 0:
                    # Restrict to the PIC's implied decimal scale (e.g. V99)
                    scaled = z_var * (10 ** pic.decimal_digits)
                    bounds.append(ToReal(ToInt(scaled)) == scaled)
        return bounds

    def _eval_condition(self, translated_expr: str) -> ExprRef:
        """Evaluates a translated expression, mapping Python and/or/not onto Z3 And/Or/Not."""
        class _BoolOpRewriter(ast.NodeTransformer):
            def visit_BoolOp(self, node):
                self.generic_visit(node)
                fn = 'And' if isinstance(node.op, ast.And) else 'Or'
                return ast.Call(func=ast.Name(id=fn, ctx=ast.Load()), args=node.values, keywords=[])

            def visit_UnaryOp(self, node):
                self.generic_visit(node)
                if isinstance(node.op, ast.Not):
                    return ast.Call(func=ast.Name(id='Not', ctx=ast.Load()), args=[node.operand], keywords=[])
                return node

        tree = ast.parse(translated_expr.strip(), mode='eval')
        tree = ast.fix_missing_locations(_BoolOpRewriter().visit(tree))
        return eval(compile(tree, '<contract>', 'eval'),
                    {'__builtins__': {}, 'And': And, 'Or': Or, 'Not': Not, 'self': self})

    def _translate_logical_expression(self, raw_expr: str) -> str:
        """Translates arbitrary COBOL/English logical expressions into valid Python/Z3 syntax."""
        expr = raw_expr.strip()

        # Strip annotation tags like (MAX=..., MIN=...) or [UNSAT: ...]
        expr = re.sub(r'\(MAX=[^)]+\)', '', expr)
        expr = re.sub(r'\(MIN=[^)]+\)', '', expr)
        expr = re.sub(r'\[UNSAT[^\]]*\]', '', expr)

        # Expand macros like InRange(VAR) -> (VAR >= MIN and VAR <= MAX)
        def replace_in_range(match):
            vname = match.group(1).strip()
            # Try to resolve variable name
            target_var = None
            for k in self.contract.domain.variables:
                if vname.upper() == k or k.endswith("-" + vname.upper()) or vname.upper() in k:
                    target_var = k
                    break
            if not target_var:
                target_var = vname

            min_c = self.contract.domain.constants.get(f"WS-MIN-OPERAND", self.contract.domain.constants.get("MIN", 0.0))
            max_c = self.contract.domain.constants.get(f"WS-MAX-OPERAND", self.contract.domain.constants.get("MAX", 999999.0))
            return f"(self.z3_vars['{target_var}'] >= {min_c} and self.z3_vars['{target_var}'] <= {max_c})"

        expr = re.sub(r'InRange\(([^)]+)\)', replace_in_range, expr, flags=re.I)

        # Handle operators
        expr = re.sub(r'\bAND\b', ' and ', expr, flags=re.I)
        expr = re.sub(r'\bOR\b', ' or ', expr, flags=re.I)
        expr = re.sub(r'\bNOT\b', ' not ', expr, flags=re.I)
        expr = re.sub(r'(?<![=<>!])=(?!=)', '==', expr)

        # Replace constants with their values
        for const_name, const_val in self.contract.domain.constants.items():
            if isinstance(const_val, (int, float)):
                expr = re.sub(rf'\b{re.escape(const_name)}\b', str(const_val), expr)

        # Replace variable references with self.z3_vars['VAR']
        for var_name in list(self.contract.domain.variables.keys()) + ['SQLCODE', 'WS-FILE-STATUS', 'EIBRESP', 'MQRC']:
            if var_name in expr:
                # Skip names already wrapped (e.g. by InRange expansion) to avoid nested substitution
                expr = re.sub(rf'(?<![\'"])\b{re.escape(var_name)}\b(?![\'"])', f"self.z3_vars['{var_name}']", expr)

        # Handle short names like A, B if they appear in expression
        for var_name in self.contract.domain.variables:
            short_name = var_name.split("-")[-1]
            if len(short_name) >= 1:
                pattern = rf'(?<![A-Za-z0-9_\'])\b{re.escape(short_name)}\b(?![A-Za-z0-9_\'])'
                expr = re.sub(pattern, f"self.z3_vars['{var_name}']", expr)

        # Handle single quotes to double quotes for strings
        expr = re.sub(r"'([^']*)'", r'"\1"', expr)
        return expr

    def _apply_external_connections(self, s: Solver, conns: List[ExternalConnection]):
        """Injects external mock dependencies (DB2, VSAM, CICS, MQ) into solver state."""
        for conn in conns:
            sys_name = conn.system.upper()
            if sys_name == "DB2":
                s.add(self.z3_vars['SQLCODE'] == int(conn.expected_value))
            elif sys_name == "VSAM":
                s.add(self.z3_vars['WS-FILE-STATUS'] == str(conn.expected_value))
            elif sys_name == "CICS":
                s.add(self.z3_vars['EIBRESP'] == int(conn.expected_value))
            elif sys_name == "MQ":
                s.add(self.z3_vars['MQRC'] == int(conn.expected_value))

    def _resolve_expected_action(self, smt_action: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Interprets the smt_action string to produce clean expected output values and status codes."""
        outputs = {}
        
        # 1. Status Code Extraction
        status_match = re.search(r"STATUS.*?=\s*['\"]?(\w+)['\"]?", smt_action, re.I)
        if status_match:
            outputs["STATUS_CODE"] = status_match.group(1)
        else:
            for code_name, code_val in self.contract.domain.status_codes.items():
                if code_name.upper() in smt_action.upper() or code_val in smt_action:
                    outputs["STATUS_CODE"] = code_val
                    break

        # 2. Result Assignment Expression
        res_match = re.search(r"(WS-[A-Z0-9\-]+|RESULT)\s*=\s*([^;]+)", smt_action, re.I)
        if res_match:
            target_var = res_match.group(1).strip()
            expr_str = res_match.group(2).strip()

            if "UNCHANGED" in expr_str.upper():
                outputs[target_var] = "UNCHANGED"
            elif expr_str.replace('.', '', 1).replace('-', '', 1).isdigit():
                outputs[target_var] = float(expr_str) if '.' in expr_str else int(expr_str)
            else:
                eval_env = dict(inputs)
                eval_env.update(self.contract.domain.constants)
                try:
                    clean_expr = expr_str
                    for k, v in eval_env.items():
                        clean_k = k.replace("-", "_")
                        clean_expr = re.sub(rf'\b{re.escape(k)}\b', clean_k, clean_expr)
                    
                    clean_dict = {k.replace("-", "_"): v for k, v in eval_env.items() if isinstance(v, (int, float))}
                    res_val = eval(clean_expr, {"__builtins__": None}, clean_dict)
                    outputs[target_var] = round(res_val, 2) if isinstance(res_val, float) else res_val
                except Exception:
                    outputs[target_var] = expr_str

        return outputs

    def generate_global_test_suite(self) -> List[Dict[str, Any]]:
        """Executes full constraint solving across all steps, generating test cases and mock contracts."""
        suite = []
        input_vars = [k for k in self.contract.domain.variables.keys() if "RESULT" not in k]

        for step in self.contract.contract_steps:
            step_record = {
                "step_id": step.step_id,
                "step_name": step.step_name,
                "category": step.category,
                "target_test_vector": step.target_test_vector,
                "relevant_paragraphs": step.relevant_paragraphs,
                "external_connections": [
                    {"system": e.system, "field": e.field, "expected_value": e.expected_value, "mock_payload": e.mock_payload}
                    for e in step.external_connections
                ],
                "test_cases": []
            }

            if not step.reachable or "[UNSAT" in step.logical_condition:
                step_record["reachable"] = False
                step_record["proof"] = "UNSAT: Path is mathematically unreachable under prerequisite range validations."
                suite.append(step_record)
                continue

            # Set up solver for this step
            s = Solver()
            for b in self._get_domain_bounds():
                s.add(b)

            self._apply_external_connections(s, step.external_connections)

            try:
                translated_expr = self._translate_logical_expression(step.logical_condition)
                s.add(self._eval_condition(translated_expr))
            except Exception as ex:
                raise RuntimeError(
                    f"{step.step_id}: cannot translate condition '{step.logical_condition}' "
                    f"-> '{translated_expr}': {ex}") from ex

            # Check Satisfiability and extract concrete inputs
            if s.check() == sat:
                model = s.model()
                concrete_inputs = {}
                for var_name in input_vars:
                    z_var = self.z3_vars[var_name]
                    val = model.eval(z_var, model_completion=True)
                    if val is not None:
                        val_str = str(val)
                        if "/" in val_str:
                            num, den = val_str.split("/")
                            val_float = float(num) / float(den)
                            concrete_inputs[var_name] = round(val_float, 2)
                        else:
                            try:
                                concrete_inputs[var_name] = float(val_str) if "." in val_str else int(val_str)
                            except ValueError:
                                concrete_inputs[var_name] = val_str

                expected_outputs = self._resolve_expected_action(step.smt_action, concrete_inputs)

                step_record["test_cases"].append({
                    "test_id": f"{step.step_id}-TC-01",
                    "description": f"Generated test case for {step.step_name}",
                    "inputs": concrete_inputs,
                    "expected_outputs": expected_outputs,
                    "external_mocks": {e.system: {"field": e.field, "value": e.expected_value} for e in step.external_connections if e.system != "NONE"}
                })
            else:
                step_record["reachable"] = False
                step_record["proof"] = "UNSAT: No input combination satisfies this step's constraint."

            suite.append(step_record)

        return suite
