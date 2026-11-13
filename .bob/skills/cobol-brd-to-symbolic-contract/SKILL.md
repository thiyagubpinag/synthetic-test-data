---
name: cobol-brd-to-symbolic-contract
description: Extracts formal SMT symbolic contracts by locating a specific Business Rule Heading within a BRD document file, generating logical conditions (Pi), expected actions, target test vectors, paragraph anchors, and external middleware connections (DB2/VSAM/CICS/MQ).
---

# Global BRD Rule to Symbolic Contract Extractor

## Purpose
Given a **BRD document file** (e.g. `docs/business-rule/...` or any markdown/text BRD) and a **Rule Heading / Rule ID** provided by the user, locate the exact rule section, parse its decomposed steps, and produce a formal **SMT Symbolic Contract Table** and JSON specification.

---

## Inputs
1. **Target Rule Heading / Rule Name:** (e.g. `2.3.1 Business Rule: Addition Policy` or `Addition Policy` or `BR-01`)
2. **BRD Document:** Active file, specified file path, or search across `docs/business-rule/**/*.md`

---

## Extraction Steps

1. **Locate & Read Rule Section:** Search the BRD file for the matching Rule Heading and read all sub-sections:
   - Purpose & Scope
   - Rule Steps (Conditions, Actions, Outcomes, Relevant Paragraphs)
   - Business Significance
2. **Decompose Rule Steps:** Break into individual logical sub-steps:
   - Input Range / Schema Validation
   - Short-circuit / Trivial Bypass
   - Core Nominal Calculation
   - Boundary Limit Thresholds
   - Exception / Overflow / Fault Handling
3. **Formulate First-Order Logic ($P_i$):** Express conditions as precise boolean/relational equations using variable names and operators (`<`, `<=`, `>`, `>=`, `==`, `!=`, `AND`, `OR`, `NOT`).
4. **Map Actions, Status & Vectors:** Define expected outputs, status codes, target test vectors, paragraph anchors, and external middleware connections (DB2 `SQLCODE`, VSAM `FILE STATUS`, CICS `EIBRESP`, MQ Reason Codes).
5. **Output Results:** Emit both the Markdown Contract Table and JSON specification.

---

## Output Contract (Markdown Table Format)

| Rule Step | Logical Condition ($P_i$) | COBOL SMT Action / Status | Target Test Vector | Relevant Paragraphs | External Connections |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. [Step Name] (Error/Validation)** | [Exact relational condition, e.g. $A < \text{MIN} \lor A > \text{MAX}$] | `Status != '00'` / Error Code | Invalidation / Out of Bounds | [Paragraph Names or N/A] | [DB2/VSAM/CICS/MQ or None] |
| **2. [Step Name] (Short-Circuit/Bypass)** | [Bypass condition, e.g. $A = 0 \land B = 0$] | `Result = 0`, `Status = '00'` | Trivial Zero Path / Shortcut | [Paragraph Names or N/A] | [DB2/VSAM/CICS/MQ or None] |
| **3. [Step Name] (Happy / Nominal Sum)** | [Nominal conditions, e.g. $\text{Valid}(A, B) \land \dots$] | `Result = Expression`, `Status = '00'` | Nominal & Boundary | [Paragraph Names or N/A] | [DB2/VSAM/CICS/MQ or None] |
| **4. [Step Name] (Exception / Size Error)** | [Overflow/failure condition, e.g. $A + B > \text{MAX}$] | `Status = '10'` (OVERFLOW) | Exception / Overflow | [Paragraph Names or N/A] | [DB2/VSAM/CICS/MQ or None] |

---

## Output Contract (JSON Format)

```json
{
  "rule_heading": "<MATCHED_RULE_HEADING>",
  "rule_id": "<RULE_ID>",
  "rule_name": "<RULE_NAME>",
  "contract_steps": [
    {
      "step_id": "STEP-01",
      "step_name": "<STEP_NAME>",
      "category": "ERROR_VALIDATION | HAPPY_SHORTCUT | HAPPY_NOMINAL | BOUNDARY | EXCEPTION",
      "logical_condition": "<PRECISE_BOOLEAN_EXPRESSION>",
      "smt_action": "<EXPECTED_ACTION_AND_STATUS>",
      "target_test_vector": "<TEST_VECTOR_TYPE>",
      "relevant_paragraphs": ["<PARAGRAPH_NAMES>"],
      "external_connections": [
        {
          "system": "DB2 | VSAM | CICS | MQ | NONE",
          "field": "<STATUS_OR_CODE_FIELD>",
          "expected_value": "<VALUE>"
        }
      ]
    }
  ]
}
```
