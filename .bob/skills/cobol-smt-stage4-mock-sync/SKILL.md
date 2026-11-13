---
name: cobol-smt-stage4-mock-sync
description: Stage 4 of COBOL Synthetic Test Data Pipeline. Performs deterministic SMT key binding and synchronized mock dataset generation for DB2 SQLCODE, VSAM File Status, CICS COMMAREA, and MQ payloads.
---

# Stage 04: Coordinated Dependency Mocking & SMT Binding

**Approach:** 100% Deterministic (SMT Key Binding & Return Code Multi-System Solver)  
**Input:** `solver_solutions.json`, `path_slice.json`, COBOL SQL/VSAM/CICS definitions  
**Output:** Synchronized mock datasets: `sql_mock_data.json`, `vsam_mock_data.json`, `cics_mock_data.json`, `mq_mock_data.json`

## Purpose & Architecture Alignment
As defined in `pipeline_architecture.html` Stage 04:
- Downstream COBOL branches rely on external database queries (`EXEC SQL`), VSAM file reads (`READ ACCT-FILE`), and CICS linkages.
- In traditional test generation, mock data is synthesized independently of program inputs, causing runtime test failures when query WHERE clauses fail to match mock table keys.
- Stage 04 treats dependency outputs and return codes as free symbolic variables bound via equality constraints ($MOCK\_DB\_KEY = IN\_CUSTOMER\_ID$) during the SMT solve.
- This produces unified, co-solved payloads where input keys and mock table responses match with 100% mathematical precision.

---

## Detailed Execution Steps

### 1. Key Binding Formulation
1. Identify all WHERE clauses, VSAM record keys, and subprogram linkage parameters from `path_slice.json`.
2. Establish deterministic binding rules:
   - For DB2: Bind host variable parameter `:IN-CUST-ID` to mock row column `CUST_ID`.
   - For VSAM: Bind `MOVE IN-CUST-ID TO VSAM-ACCT-NO` to mock dataset key `VSAM_ACCT_NO`.
   - For CICS: Bind commarea request fields to response container payloads.

### 2. Multi-Scenario Mock Extraction
For each solved solution in `solver_solutions.json` (Happy, Error, Boundary):
1. **DB2 SQL Mocking**:
   - Extract `SQLCODE` (0 = Success, +100 = Not Found, -911 = Deadlock, -803 = Duplicate Key).
   - Generate mock table result sets matching exact query predicates and column data types.
2. **VSAM Record Mocking**:
   - Extract `FILE_STATUS` ('00' = Success, '23' = Key Not Found, '10' = End of File).
   - Generate mock VSAM record buffer matching key structure and field lengths.
3. **CICS & Subprogram Mocking**:
   - Extract `EIBRESP` / `EIBRESP2` normal vs. error codes (`PGMIDERR`, `NOTFND`, `LOCKED`).
   - Package mock COMMAREA response buffers.
4. **IBM MQ Mocking**:
   - Extract `CompCode` / `ReasonCode` (`MQRC_NO_MSG_AVAILABLE`, `MQRC_TRUNCATED_MSG_FAILED`).
   - Format mock message payloads.

---

## Output Contract (`sql_mock_data.json` & `vsam_mock_data.json`)

### DB2 Mocks (`sql_mock_data.json`)
```json
[
  {
    "scenario_id": "SOL-HP-01",
    "query": "SELECT CREDIT_SCORE, CUST_TIER FROM CUSTOMER_TABLE WHERE CUST_ID = :IN-CUST-ID",
    "bind_values": {
      "IN-CUST-ID": "CUST1001"
    },
    "mock_response": {
      "SQLCODE": 0,
      "rows": [
        {
          "CUST_ID": "CUST1001",
          "CREDIT_SCORE": 750,
          "CUST_TIER": "GOLD"
        }
      ]
    }
  },
  {
    "scenario_id": "SOL-ERR-DB-NOTFND",
    "query": "SELECT CREDIT_SCORE, CUST_TIER FROM CUSTOMER_TABLE WHERE CUST_ID = :IN-CUST-ID",
    "bind_values": {
      "IN-CUST-ID": "CUST9999"
    },
    "mock_response": {
      "SQLCODE": 100,
      "rows": []
    }
  }
]
```

### VSAM Mocks (`vsam_mock_data.json`)
```json
[
  {
    "scenario_id": "SOL-HP-01",
    "dataset_name": "ACCT.FILE.KSDS",
    "key_field": "VSAM_ACCT_NO",
    "lookup_key": "CUST1001",
    "mock_response": {
      "FILE_STATUS": "00",
      "record": {
        "VSAM_ACCT_NO": "CUST1001",
        "OVERDRAFT_CNT": 0,
        "CURRENT_BALANCE": 12500.50
      }
    }
  }
]
```
