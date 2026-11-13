## Global SMT Test Suite for Rule: `BR-ADD-2.3.1`

| Test ID | Step Name | Category / Vector | Concrete Inputs | Expected Outputs & Status | External System Mocks |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `STEP-01-TC-01` | Operand Range Validation | Invalidation / Out of Bounds | `WS-OPERAND-A=0, WS-OPERAND-B=-5000000.01` | `STATUS_CODE=40, WS-STATUS-CODE='40' (STATUS-OUT-OF-RANGE)` | `None` |
| `STEP-02-TC-01` | Zero Shortcut | Trivial Zero Path / Shortcut | `WS-OPERAND-A=0, WS-OPERAND-B=0` | `STATUS_CODE=00, WS-RESULT=0` | `None` |
| `STEP-03-TC-01` | Add Operands | Nominal & Boundary (A=B=+5000000.00 -> 10000000.00; A=B=-5000000.00 -> -10000000.00; A=0,B!=0; negatives; A=-B) | `WS-OPERAND-A=-0.01, WS-OPERAND-B=-0.01` | `STATUS_CODE=00, WS-RESULT=-0.02` | `None` |
| `STEP-04-N/A` | Overflow / Size Error Check | **EXCEPTION** (UNSAT) | *Mathematically Unreachable* | `UNSAT: Path is mathematically unreachable under prerequisite range validations.` | `None` |