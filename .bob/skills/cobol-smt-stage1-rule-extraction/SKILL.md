---
name: cobol-smt-stage1-rule-extraction
description: Stage 1 of COBOL Synthetic Test Data Pipeline. Extracts business rules, AST paragraph nodes, decision points, Level-88 enums, and schema constraints from COBOL programs into brd_catalog.json.
---

# Stage 01: Business Rule Extraction & BRD Cataloging

**Approach:** Hybrid (Scanner SQLite AST + LLM Semantic Interpretation)  
**Input:** COBOL Source Program (`.cbl`, `.cob`), Copybooks (`.cpy`), and Scanner Database metadata  
**Output:** `brd_catalog.json` & `<entity>_extracted_rules.json`

## Purpose & Architecture Alignment
As defined in `pipeline_architecture.html` Stage 01:
- Scans program metadata and AST to extract all decision points (`IF`, `EVALUATE`, `WHEN`, `PERFORM UNTIL`, and Level-88 conditions).
- Uses the AST parser to extract paragraph lines and branch boundaries deterministically.
- Employs LLM to translate raw COBOL conditional logic, comments, and copybook structures into clear, human-readable business rules with canonical IDs (`BR-01`, `BR-02`, ...).
- Enables targeted sub-rule testing (e.g., targeting `BR-04 Tiered Risk Assessment`) to eliminate path explosion.

---

## Detailed Execution Steps

### 1. AST & Copybook Schema Parsing
1. Inspect Working-Storage, Local-Storage, and Linkage Sections:
   - Extract PIC clauses, byte lengths, numeric scale/precision, signed indicators, and usage formats (`COMP`, `COMP-3`, `DISPLAY`).
   - Extract Level-88 conditions and associate them with parent fields as discrete enums/allowed values.
   - Map field offsets and calculate total record lengths.

### 2. Procedural Logic & Decision Point Extraction
1. Traverse the Procedure Division paragraphs:
   - Identify branch gatekeepers: relational comparisons (`<`, `<=`, `=`, `>=`, `>`, `<>`), sign tests (`IS POSITIVE`, `IS NEGATIVE`), class tests (`IS NUMERIC`, `IS ALPHABETIC`).
   - Identify external dependency calls:
     - `EXEC SQL SELECT / INSERT / UPDATE / DELETE` (capturing SQL host variables and table predicates).
     - `READ / WRITE / REWRITE` against VSAM datasets (capturing record keys and status check logic).
     - `EXEC CICS` commands (COMMAREA, Channel/Container, `EIBRESP` handling).
     - `CALL` subprogram invocations (capturing `USING` parameter linkage).
     - IBM MQ operations (`MQGET`, `MQPUT`, `MQGMO`, `MQPMO`).

### 3. Canonical Rule ID Assignment & Cataloging
1. Group decision nodes into logical Business Rules:
   - Assign canonical IDs (`BR-01`, `BR-02`, `BR-03`, etc.).
   - Define rule trigger criteria, target paragraphs, dependencies, and expected outcomes.
   - Tag rule origin: `COPYBOOK_SCHEMA`, `PROCEDURAL_RULE`, or `INFERRED_ASSUMPTION`.

---

## Output Contract (`brd_catalog.json`)

```json
{
  "program_id": "LNVAL01",
  "generated_at": "2026-11-13T00:00:00Z",
  "data_structures": {
    "records": [
      {
        "record_name": "CUSTOMER-RECORD",
        "length": 80,
        "fields": [
          {"name": "IN-CUST-ID", "pic": "X(8)", "type": "ALPHANUMERIC", "length": 8, "offset": 0},
          {"name": "IN-LOAN-AMOUNT", "pic": "9(6)V99", "type": "DECIMAL", "precision": 8, "scale": 2, "length": 8, "offset": 8}
        ]
      }
    ]
  },
  "business_rules": [
    {
      "rule_id": "BR-01",
      "rule_name": "DB2 Customer Retrieval Verification",
      "target_paragraphs": ["1000-FETCH-DB2-DATA"],
      "trigger_criteria": "IN-CUST-ID IS NOT SPACES",
      "dependencies": [{"type": "DB2", "table": "CUSTOMER_TABLE", "keys": ["CUST_ID"], "status_check": "SQLCODE = 0"}],
      "error_sink": "9100-DB-ERR"
    },
    {
      "rule_id": "BR-04",
      "rule_name": "Tiered Risk Assessment & Loan Approval",
      "target_paragraphs": ["3000-EVALUATE-RISK"],
      "trigger_criteria": "IN-LOAN-AMOUNT <= 50000.00 AND DB-CREDIT-SCORE >= 700 AND VSAM-OVERDRAFT-CNT = 0 AND DB-TIER = 'GOLD'",
      "expected_outcome": "WS-RESULT = 'APPROVED-TIER-1'",
      "error_sink": "9200-VSAM-ERR"
    }
  ]
}
```
