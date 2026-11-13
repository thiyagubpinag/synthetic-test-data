---
name: cobol-smt-stage5-semantic-enrichment
description: Stage 5 of COBOL Synthetic Test Data Pipeline. Uses LLM and Data Dictionary (DD.json) to enrich raw SMT numeric/dummy values into realistic domain entities while strictly validating mathematical boundaries.
---

# Stage 05: LLM Semantic Enrichment & Data Dictionary Integration

**Approach:** 100% AI / LLM (Prompt + Data Dictionary context) with Deterministic Invariant Validation  
**Input:** `solver_solutions.json`, `sql_mock_data.json`, `vsam_mock_data.json`, and `bobz/DD.json`  
**Output:** `enriched_record.json` and `<entity>_enriched_test_suite.json`

## Purpose & Architecture Alignment
As defined in `pipeline_architecture.html` Stage 05:
- SMT solvers output abstract numbers, dummy strings (`"AAAAA"`, `99999`), or minimal integer assignments that satisfy equations but lack domain realism.
- Stage 05 utilizes an LLM guided by the project Data Dictionary (`DD.json`) to enrich raw mathematical vectors into realistic names, street addresses, postal codes, and Luhn-valid credit card numbers.
- **Safety Guarantee:** Performs a post-enrichment deterministic verification pass to guarantee that the LLM has NOT mutated or violated any mathematical boundary conditions or SMT invariants ($Score \ge 700$, $LoanAmount \le 50000.00$).

---

## Detailed Execution Steps

### 1. Ingest Data Dictionary Context
1. Read `bobz/DD.json` to extract semantic business meaning for each variable:
   - Identify domain types (e.g. `CUST-ID` -> Customer Identifier, `ADDR-LINE-1` -> Street Address, `CARD-NUM` -> Payment Card).
   - Read business descriptions and allowed formats.

### 2. LLM Semantic Synthesis
1. Prompt LLM to enrich abstract values:
   - Replace dummy IDs (`"CUST1001"`) with domain-formatted realistic IDs (`"CUST89210"`).
   - Generate realistic names (`"ELEANOR VANCE"`), dates (`"2026-11-13"`), and narrative descriptions.
   - For credit cards: generate valid Luhn check-digit numbers.
   - Maintain exact consistency across bound mock keys (e.g., if `IN_CUST_ID` becomes `"CUST89210"`, update `sql_mock_data` and `vsam_mock_data` to match `"CUST89210"`).

### 3. Program Outputs After Path Execution
1. After enrichment, derive `program_outputs` by executing the target path (from `path_slice.json`) with the enriched `program_inputs` and `external_mocks`:
   - Walk the sliced paragraphs in order, applying each MOVE/COMPUTE/IF/EVALUATE outcome to the working-storage and linkage fields.
   - Record the final values of every field the path writes: output/COMMAREA fields, return codes, status/flag fields (e.g. `WS_RESULT`), and fields written to files, DB2 (INSERT/UPDATE/DELETE) or CICS (RETURN/SEND).
   - Include the final `SQLCODE`/`FILE STATUS`/`EIBRESP` observed on the path and the CICS `RETURN-CODE`, where applicable.
2. Outputs must be computed from the enriched inputs, not copied from the abstract SMT values. If enrichment changed a value that flows into an output (e.g. `IN_CUST_ID` echoed to `OUT_CUST_ID`), the output must reflect the enriched value.
3. Respect PIC clauses: numeric outputs are truncated/rounded per PIC/COMP rules; strings are padded or truncated to field length.
4. `program_outputs` is the post-execution state; `expected_outcome` remains the short business-result summary and must be consistent with it.

### 4. Deterministic Invariant Validation Gate
1. Run automated Python verification assertions:
   - Assert all numeric bounds from Stage 03 are strictly preserved ($LoanAmount_{enriched} == LoanAmount_{SMT}$ or within the same equivalence class).
   - Assert string lengths do not exceed PIC clause capacities.
   - Assert all foreign key bindings between inputs and mock rows remain identical.
   - Assert `program_outputs` is consistent with the path execution of the enriched inputs, and that `expected_outcome` values match the corresponding `program_outputs` fields.
   - If any invariant is violated, reject LLM output and fall back to mathematically verified values.

---

## Output Contract (`enriched_record.json`)

```json
{
  "scenario_id": "HAPPY_PATH_TIER1_APPROVAL",
  "target_business_rule": "BR-04",
  "program_inputs": {
    "IN_CUST_ID": "CUST89210",
    "IN_CUSTOMER_NAME": "ELEANOR VANCE",
    "IN_APPLICATION_DATE": "2026-11-13",
    "IN_LOAN_AMOUNT": 25000.00,
    "IN_LOAN_TERM_MONTHS": 36
  },
  "external_mocks": {
    "db2_queries": [
      {
        "query": "SELECT CREDIT_SCORE, CUST_TIER FROM CUSTOMER_TABLE WHERE CUST_ID = :IN-CUST-ID",
        "bind_values": {"IN-CUST-ID": "CUST89210"},
        "mock_response": {
          "SQLCODE": 0,
          "CREDIT_SCORE": 780,
          "CUST_TIER": "GOLD"
        }
      }
    ],
    "vsam_reads": [
      {
        "dataset": "ACCT.FILE.KSDS",
        "key": "CUST89210",
        "mock_response": {
          "FILE_STATUS": "00",
          "OVERDRAFT_CNT": 0,
          "ACCOUNT_HOLDER": "ELEANOR VANCE"
        }
      }
    ]
  },
  "program_outputs": {
    "fields": {
      "WS_RESULT": "APPROVED-TIER-1",
      "OUT_CUST_ID": "CUST89210",
      "OUT_APPROVED_AMOUNT": 25000.00,
      "OUT_RETURN_CODE": 0
    },
    "final_status": {
      "SQLCODE": 0,
      "FILE_STATUS": "00",
      "EIBRESP": 0,
      "RETURN_CODE": 0
    },
    "side_effects": [
      {
        "type": "DB2_INSERT",
        "target": "LOAN_TABLE",
        "values": {"CUST_ID": "CUST89210", "LOAN_AMOUNT": 25000.00, "STATUS": "APPROVED-TIER-1"}
      }
    ],
    "executed_path": ["0000-MAINLINE", "1000-VALIDATE", "2000-CHECK-CREDIT", "3000-APPROVE-TIER-1"]
  },
  "expected_outcome": {
    "WS_RESULT": "APPROVED-TIER-1"
  },
  "invariant_verification": {
    "status": "PASSED",
    "checked_invariants": [
      "IN_LOAN_AMOUNT <= 50000.00 (Actual: 25000.00)",
      "DB_CREDIT_SCORE >= 700 (Actual: 780)",
      "VSAM_OVERDRAFT_CNT == 0 (Actual: 0)",
      "Key Binding IN_CUST_ID == DB2 CUST_ID == VSAM ACCT_NO"
    ]
  }
}
```
