---
name: cobol-smt-stage3-z3-solving
description: Stage 3 of COBOL Synthetic Test Data Pipeline. Uses Z3 SMT solver to deterministically solve mathematical constraints across Happy Path, Error Paths, and Boundary Limits.
---

# Stage 03: Z3 SMT Constraint Solving

**Approach:** 100% Deterministic (Z3 SMT Solver — First-Order Logic & Presburger Arithmetic)  
**Input:** `path_slice.json` and PIC schema bounds  
**Output:** `solver_solutions.json` & `solver_engine.py`

## Purpose & Architecture Alignment
As defined in `pipeline_architecture.html` Stage 03:
- Converts COBOL PIC ranges, decimal arithmetic, and relational conditions into First-Order Logic constraints.
- Formulates equations in Z3 to deterministically solve for concrete values across three distinct test suites:
  1. **Happy Path ($\Phi_{Happy}$):** Conjunction of all path gatekeepers, normal exit nodes, and interior nominal values.
  2. **Error Paths ($\Phi_{Error}$):** Systematic branch negation (Weakest Precondition Inversion: negating branch $k$ while keeping $1..k-1$ valid) and fault injection.
  3. **Boundary Paths ($Points$):** Discrete 4-point limit testing: $\{Limit, Limit - \epsilon, Limit + \epsilon, Min(PIC), Max(PIC)\}$.
- Delivers mathematically guaranteed constraint satisfaction with zero LLM hallucination.

---

## Mathematical Formulation

### 1. Happy Path Formulation ($\Phi_{Happy}$)
$$\Phi_{Happy} = \bigwedge_{i=1}^{n} P_i(X) \land (SQLCODE = 0) \land (FILE\_STATUS = \text{"00"}) \land Bounds(PIC)$$
- Enforces all positive gatekeeper predicates simultaneously.
- Sets target outcome to positive sink (e.g., `WS-RESULT = 'APPROVED-TIER-1'`).
- Solves for nominal central values within valid ranges.

### 2. Error Path Formulation ($\Phi_{Error_k}$)
$$\Phi_{Error_k} = \left(\bigwedge_{i < k} P_i(X)\right) \land \neg P_k(X) \land Bounds(PIC)$$
- Systematically produces one test case per branch negation point $k$.
- Generates inputs that steer execution into error handlers, rollbacks, and abend branches.

### 3. Boundary Condition Formulation ($Points_L$)
For any relational comparison $X \le L$ or $X \ge L$:
- $X = L$ (Exact limit threshold)
- $X = L - 1$ (Off-by-one under limit, adjusted for scale e.g. $-0.01$ for 2-decimal currencies)
- $X = L + 1$ (Off-by-one over limit, adjusted for scale)
- $X = MinValue(PIC)$ (Physical COBOL lower bound, e.g. `000000.00` or negative if signed)
- $X = MaxValue(PIC)$ (Physical COBOL upper bound, e.g. `999999.99` for `PIC 9(6)V99`)

---

## Python / Z3 Solver Script Structure

```python
from z3 import Solver, Int, Real, String, And, Or, Not, sat

def solve_constraints():
    s = Solver()
    
    # Declare primary input symbolic variables
    in_cust_id = String('IN_CUST_ID')
    in_loan_amount = Real('IN_LOAN_AMOUNT')
    
    # Declare dependency output symbolic variables
    db_credit_score = Int('DB_CREDIT_SCORE')
    db_tier = String('DB_TIER')
    sqlcode = Int('SQLCODE')
    vsam_overdraft_cnt = Int('VSAM_OVERDRAFT_CNT')
    ws_file_status = String('WS_FILE_STATUS')
    
    # 1. PIC & Physical Domain Constraints
    s.add(in_loan_amount >= 0.0, in_loan_amount <= 999999.99)
    s.add(db_credit_score >= 300, db_credit_score <= 850)
    s.add(vsam_overdraft_cnt >= 0, vsam_overdraft_cnt <= 99)
    
    # 2. Happy Path Configuration
    s.push()
    s.add(sqlcode == 0)
    s.add(ws_file_status == "00")
    s.add(in_loan_amount <= 50000.00)
    s.add(db_credit_score >= 700)
    s.add(vsam_overdraft_cnt == 0)
    s.add(db_tier == "GOLD")
    
    if s.check() == sat:
        happy_model = s.model()
        print("Happy Path Solution:", happy_model)
    s.pop()
    
    # 3. Systematic Error Path: Negative Credit Score (< 700)
    s.push()
    s.add(sqlcode == 0)
    s.add(ws_file_status == "00")
    s.add(in_loan_amount <= 50000.00)
    s.add(db_credit_score < 700)  # Inverted predicate
    s.add(vsam_overdraft_cnt == 0)
    s.add(db_tier == "GOLD")
    if s.check() == sat:
        error_model = s.model()
        print("Error Path (Low Score):", error_model)
    s.pop()
```

---

## Output Contract (`solver_solutions.json`)

```json
{
  "target_rule_id": "BR-04",
  "solutions": {
    "happy_path": [
      {
        "id": "SOL-HP-01",
        "description": "Tier 1 Approval nominal case",
        "variables": {
          "IN_CUST_ID": "CUST1001",
          "IN_LOAN_AMOUNT": 25000.00,
          "DB_CREDIT_SCORE": 750,
          "DB_TIER": "GOLD",
          "SQLCODE": 0,
          "VSAM_OVERDRAFT_CNT": 0,
          "WS_FILE_STATUS": "00"
        },
        "expected_outcome": "APPROVED-TIER-1"
      }
    ],
    "error_paths": [
      {
        "id": "SOL-ERR-01",
        "description": "Credit score below threshold (699)",
        "negated_predicate": "DB-CREDIT-SCORE >= 700",
        "variables": {
          "IN_CUST_ID": "CUST1001",
          "IN_LOAN_AMOUNT": 25000.00,
          "DB_CREDIT_SCORE": 699,
          "DB_TIER": "GOLD",
          "SQLCODE": 0,
          "VSAM_OVERDRAFT_CNT": 0,
          "WS_FILE_STATUS": "00"
        },
        "expected_outcome": "REJECTED"
      }
    ],
    "boundary_paths": [
      {
        "id": "SOL-BND-01",
        "description": "Exact upper loan amount threshold (50000.00)",
        "variables": {
          "IN_CUST_ID": "CUST1001",
          "IN_LOAN_AMOUNT": 50000.00,
          "DB_CREDIT_SCORE": 700,
          "DB_TIER": "GOLD",
          "SQLCODE": 0,
          "VSAM_OVERDRAFT_CNT": 0,
          "WS_FILE_STATUS": "00"
        },
        "expected_outcome": "APPROVED-TIER-1"
      },
      {
        "id": "SOL-BND-02",
        "description": "Loan amount off-by-one cent over threshold (50000.01)",
        "variables": {
          "IN_CUST_ID": "CUST1001",
          "IN_LOAN_AMOUNT": 50000.01,
          "DB_CREDIT_SCORE": 700,
          "DB_TIER": "GOLD",
          "SQLCODE": 0,
          "VSAM_OVERDRAFT_CNT": 0,
          "WS_FILE_STATUS": "00"
        },
        "expected_outcome": "REJECTED"
      }
    ]
  }
}
```
