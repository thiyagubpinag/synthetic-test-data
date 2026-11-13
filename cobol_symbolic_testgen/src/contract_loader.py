import re
import json
from typing import Dict, Any, Union
from .models import PicSpec, ContractDomain, ContractStep, ExternalConnection, SymbolicContract

class UniversalContractLoader:
    """Universal loader that parses any COBOL data definitions, constants, and complex SMT contracts."""

    @staticmethod
    def parse_pic(pic_str: str) -> PicSpec:
        """Globally parses any COBOL PIC specification (numeric, decimal, signed, alphanumeric)."""
        clean = pic_str.strip().upper()
        
        # Alphanumeric strings: PIC X(n) or PIC X..X
        if 'X' in clean or 'A' in clean:
            len_match = re.search(r'[XA]\((\d+)\)', clean)
            if len_match:
                length = int(len_match.group(1))
            else:
                x_match = re.search(r'([XA]+)', clean)
                length = len(x_match.group(1)) if x_match else 1
            return PicSpec(
                raw_pic=pic_str,
                var_type='ALPHANUMERIC',
                is_signed=False,
                integer_digits=0,
                decimal_digits=0,
                string_length=length
            )

        # Numeric / Decimal PICs: S9(n)V9(m), 9(n)V99, S9(n), 9(n), etc.
        is_signed = 'S' in clean
        int_digits = 0
        dec_digits = 0

        v_parts = clean.split('V')
        
        # Left of implied decimal point
        int_match = re.search(r'9\((\d+)\)|(9+)', v_parts[0])
        if int_match:
            int_digits = int(int_match.group(1)) if int_match.group(1) else len(int_match.group(2))

        # Right of implied decimal point
        if len(v_parts) > 1:
            dec_match = re.search(r'9\((\d+)\)|(9+)', v_parts[1])
            if dec_match:
                dec_digits = int(dec_match.group(1)) if dec_match.group(1) else len(dec_match.group(2))

        scale = 10 ** dec_digits if dec_digits > 0 else 1
        max_int = (10 ** int_digits) - 1
        max_dec = (1.0 - (1.0 / scale)) if dec_digits > 0 else 0.0
        max_val = float(max_int) + max_dec
        min_val = -max_val if is_signed else 0.0

        var_type = 'DECIMAL' if dec_digits > 0 else 'NUMERIC'

        return PicSpec(
            raw_pic=pic_str,
            var_type=var_type,
            is_signed=is_signed,
            integer_digits=int_digits,
            decimal_digits=dec_digits,
            min_val=round(min_val, dec_digits),
            max_val=round(max_val, dec_digits)
        )

    @classmethod
    def load_from_file(cls, filepath: str) -> SymbolicContract:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.load_from_dict(data)

    @classmethod
    def load_from_dict(cls, data: Dict[str, Any]) -> SymbolicContract:
        domain_raw = data.get("domain", {})
        variables: Dict[str, PicSpec] = {}
        constants: Dict[str, Any] = {}
        status_codes = domain_raw.get("status_codes", {})

        for k, v in domain_raw.items():
            if k == "status_codes":
                continue
            if isinstance(v, str) and ("PIC" in v.upper()):
                variables[k] = cls.parse_pic(v)
            else:
                # Handle numeric, boolean, or string constants
                val_str = str(v).strip()
                if val_str.startswith("+"):
                    val_str = val_str[1:]
                try:
                    constants[k] = float(val_str) if "." in val_str else int(val_str)
                except ValueError:
                    constants[k] = v

        domain = ContractDomain(
            variables=variables,
            constants=constants,
            status_codes=status_codes
        )

        steps = []
        for s in data.get("contract_steps", []):
            ext_conns = []
            for e in s.get("external_connections", []):
                ext_conns.append(ExternalConnection(
                    system=e.get("system", "NONE").upper(),
                    field=e.get("field", "N/A"),
                    expected_value=e.get("expected_value", "N/A"),
                    mock_payload=e.get("mock_payload", None)
                ))

            steps.append(ContractStep(
                step_id=s.get("step_id", ""),
                step_name=s.get("step_name", ""),
                category=s.get("category", "HAPPY_NOMINAL"),
                logical_condition=s.get("logical_condition", ""),
                smt_action=s.get("smt_action", ""),
                target_test_vector=s.get("target_test_vector", ""),
                relevant_paragraphs=s.get("relevant_paragraphs", []),
                reachable=s.get("reachable", True),
                external_connections=ext_conns
            ))

        return SymbolicContract(
            rule_heading=data.get("rule_heading", ""),
            rule_id=data.get("rule_id", ""),
            rule_name=data.get("rule_name", ""),
            program=data.get("program", ""),
            source_brd=data.get("source_brd", None),
            domain=domain,
            contract_steps=steps
        )
