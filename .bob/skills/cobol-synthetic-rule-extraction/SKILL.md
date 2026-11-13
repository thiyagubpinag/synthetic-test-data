---
name: cobol-synthetic-rule-extraction
description: Use when extracting data schemas and business rules from COBOL copybooks and program logic for test data generation with canonical Rule ID assignments.
---

# COBOL Synthetic Rule Extraction (Step 1)

This skill guides the extraction of deterministic data schemas and business constraints from COBOL source code and copybooks, assigning canonical identifiers (`BR-01`, `BR-02`, etc.) to each rule.

## Process
1. **Deterministic Schema Parsing**:
   - Inspect Working-Storage / Linkage section data items.
   - Extract PIC clauses, numeric lengths, decimal positions, signed indicators, and display/binary/comp-3 usage.
   - Map COBOL representations:
     - `PIC 9(n)` -> NUMERIC (length n)
     - `PIC X(n)` -> ALPHANUMERIC (length n)
     - `PIC 9(n)V9(m)` -> DECIMAL (precision n+m, scale m)
     - Level-88 items -> ENUM / ALLOWED_VALUES

2. **Procedural Logic & Constraint Extraction**:
   - Trace conditional evaluation statements (`IF`, `EVALUATE`, `WHEN`, `PERFORM UNTIL`).
   - Identify value ranges (e.g. `AGE > 0 AND AGE <= 120`), mandatory checks, cross-field validations, and error branches.
   - Assign a canonical ID to every business rule (`BR-01`, `BR-02`, etc.).

3. **Origin Classification**:
   - Tag each field and rule with origin:
     - `COPYBOOK_SCHEMA`: Pure field layout representation
     - `PROCEDURAL_RULE`: Verified logic inside PROCEDURE DIVISION
     - `INFERRED_ASSUMPTION`: Inferred context requiring confirmation

4. **Output Contract**:
   - Produce a standardized JSON schema specification `<entity>_extracted_rules.json` with indexed business rules ready for downstream traceability and test case mapping.
