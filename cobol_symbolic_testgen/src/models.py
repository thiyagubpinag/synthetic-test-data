from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union

@dataclass
class PicSpec:
    """Represents a parsed COBOL PIC definition and its mathematical domain."""
    raw_pic: str
    var_type: str  # 'NUMERIC', 'DECIMAL', 'ALPHANUMERIC'
    is_signed: bool
    integer_digits: int
    decimal_digits: int
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    string_length: Optional[int] = None

@dataclass
class ExternalConnection:
    """Represents an external system connection (DB2, VSAM, CICS, MQ)."""
    system: str  # 'DB2', 'VSAM', 'CICS', 'MQ', 'NONE'
    field: str   # e.g., 'SQLCODE', 'WS-FILE-STATUS', 'EIBRESP', 'MQRC'
    expected_value: Any
    mock_payload: Optional[Dict[str, Any]] = None

@dataclass
class ContractDomain:
    """Global data dictionary and domain definitions for a program/rule."""
    variables: Dict[str, PicSpec]
    constants: Dict[str, Any]
    status_codes: Dict[str, str]

@dataclass
class ContractStep:
    """A discrete logical condition step within a business rule."""
    step_id: str
    step_name: str
    category: str  # 'ERROR_VALIDATION', 'HAPPY_SHORTCUT', 'HAPPY_NOMINAL', 'BOUNDARY', 'EXCEPTION', 'FAULT_INJECTION'
    logical_condition: str
    smt_action: str
    target_test_vector: str
    relevant_paragraphs: List[str] = field(default_factory=list)
    reachable: bool = True
    external_connections: List[ExternalConnection] = field(default_factory=list)

@dataclass
class SymbolicContract:
    """Top-level contract specification for any COBOL business rule."""
    rule_heading: str
    rule_id: str
    rule_name: str
    program: str
    source_brd: Optional[str] = None
    domain: ContractDomain = field(default_factory=lambda: ContractDomain({}, {}, {}))
    contract_steps: List[ContractStep] = field(default_factory=list)
