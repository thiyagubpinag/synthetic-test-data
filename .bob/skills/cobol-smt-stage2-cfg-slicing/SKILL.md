---
name: cobol-smt-stage2-cfg-slicing
description: Stage 2 of COBOL Synthetic Test Data Pipeline. Performs 100% deterministic backward symbolic path slicing from target business rule paragraphs to program entry nodes.
---

# Stage 02: CFG Pathfinding & Symbolic Slicing

**Approach:** 100% Deterministic (Graph Theory + SQL Recursive CTEs / AST Traversal)  
**Input:** `brd_catalog.json`, Target Rule ID (e.g. `BR-04`), COBOL Source / Scanner SQLite DB  
**Output:** `path_slice.json` & `path_slice.sql`

## Purpose & Architecture Alignment
As defined in `pipeline_architecture.html` Stage 02:
- Traverses all feasible execution paths from program `ENTRY` to the target rule paragraph (e.g. `3000-EVALUATE-RISK`).
- Queries the SQLite Scanner database or builds control flow graph to extract branch conditions and back-substitute intermediate calculated variables into root inputs.
- Eliminates whole-program path explosion by pruning dead code and focusing symbolic equations exclusively on the slice reaching the selected business rule.
- Operates 100% deterministically without AI hallucination.

---

## Detailed Execution Steps

### 1. Identify Target Sinks & Entry Points
1. Ingest `brd_catalog.json` and select the target rule (e.g., `BR-04`).
2. Identify target paragraph AST nodes (`3000-EVALUATE-RISK`).
3. Set the root entry node (`PROCEDURE DIVISION` / `0000-MAIN` entry).

### 2. Control Flow Graph (CFG) Backward Traversal
1. Trace backwards from the target paragraph to root entry:
   - Collect all upstream `PERFORM`, `GO TO`, and sequential statement blocks.
   - Enumerate all branch decision points (`IF`, `EVALUATE`, `WHEN`, `ON SIZE ERROR`) encountered along the traversal.
   - Record execution order and statement IDs.

### 3. Symbolic Back-Substitution
1. Track variable assignments (`MOVE`, `COMPUTE`, `ADD`, `STRING`) along the path:
   - For every variable $V$ used in a path predicate, trace $V$ backwards to its definition.
   - Substitute expressions until $V$ is expressed solely in terms of primary program inputs, external database column values, or constant literals.
   - Example:
     - Rule uses `WS-QUALIFIED-FLAG = 'Y'`
     - Back-substitution traces: `MOVE 'Y' TO WS-QUALIFIED-FLAG` when `IN-SCORE >= 650`
     - Sliced constraint resolves to: `IN-SCORE >= 650`.

### 4. Path Predicate Collection
1. Group the collected conditions into path predicates:
   - **Path Gatekeepers**: All conditional expressions that must evaluate to TRUE for execution to reach the rule paragraph.
   - **Target Predicates**: Conditions inside the rule paragraph determining success vs. alternate branches.

---

## Output Contract (`path_slice.json`)

```json
{
  "program_id": "LNVAL01",
  "target_rule_id": "BR-04",
  "target_paragraph": "3000-EVALUATE-RISK",
  "execution_path": [
    {"step": 1, "paragraph": "0000-MAIN", "action": "ENTRY"},
    {"step": 2, "paragraph": "1000-FETCH-DB2-DATA", "action": "EXEC_SQL_SELECT", "status_check": "SQLCODE == 0"},
    {"step": 3, "paragraph": "2000-READ-VSAM-DATA", "action": "READ_VSAM", "status_check": "WS-FILE-STATUS == '00'"},
    {"step": 4, "paragraph": "3000-EVALUATE-RISK", "action": "EVALUATE_CONDITIONS"}
  ],
  "symbolic_constraints": [
    {"source_stmt": "1000-FETCH-DB2-DATA", "expr": "SQLCODE == 0", "type": "DEPENDENCY_STATUS"},
    {"source_stmt": "2000-READ-VSAM-DATA", "expr": "WS-FILE-STATUS == '00'", "type": "DEPENDENCY_STATUS"},
    {"source_stmt": "3000-EVALUATE-RISK", "expr": "IN_LOAN_AMOUNT <= 50000.00", "type": "INPUT_RANGE"},
    {"source_stmt": "3000-EVALUATE-RISK", "expr": "DB_CREDIT_SCORE >= 700", "type": "DEPENDENCY_VALUE"},
    {"source_stmt": "3000-EVALUATE-RISK", "expr": "VSAM_OVERDRAFT_CNT == 0", "type": "DEPENDENCY_VALUE"},
    {"source_stmt": "3000-EVALUATE-RISK", "expr": "DB_TIER == 'GOLD'", "type": "DEPENDENCY_VALUE"}
  ],
  "input_dependencies": ["IN-CUST-ID", "IN-LOAN-AMOUNT"],
  "external_dependencies": [
    {"system": "DB2", "columns": ["CREDIT_SCORE", "CUST_TIER"], "key": "CUST_ID"},
    {"system": "VSAM", "fields": ["OVERDRAFT_CNT"], "key": "VSAM_ACCT_NO"}
  ]
}
```
