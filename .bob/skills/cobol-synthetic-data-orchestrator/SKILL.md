---
name: cobol-synthetic-data-orchestrator
description: Master orchestrator that executes the end-to-end 6-stage COBOL SMT synthetic test data pipeline sequentially across isolated subagents with business rule traceability, Z3 constraint solving, dependency mock co-solving, and a mandatory user review checkpoint.
---

# COBOL SMT Synthetic Test Data Pipeline Orchestrator

This skill orchestrates the end-to-end 6-stage generation of mathematically verified, semantically realistic synthetic test data from COBOL programs and copybooks as defined in `pipeline_architecture.html`.

## Pipeline Architecture & Division of Responsibility

```
[COBOL Source / Copybook / Scanner DB]
                   │
                   ▼
┌───────────────────────────────────────────────┐
│ Stage 01: Rule Extraction & BRD Cataloging    │ (Skill: cobol-smt-stage1-rule-extraction)
│ Paradigm: HYBRID (AST + AI)                   │ Output: brd_catalog.json
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Stage 02: CFG Slicing & Symbolic Pathfinding  │ (Skill: cobol-smt-stage2-cfg-slicing)
│ Paradigm: 100% DETERMINISTIC (AST Graph / SQL)│ Output: path_slice.json + path_slice.sql
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Stage 03: Z3 SMT Constraint Solving           │ (Skill: cobol-smt-stage3-z3-solving)
│ Paradigm: 100% DETERMINISTIC (Z3 Solver)      │ Output: solver_solutions.json (Happy/Error/Boundary)
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Stage 04: Coordinated Dependency Mocking      │ (Skill: cobol-smt-stage4-mock-sync)
│ Paradigm: 100% DETERMINISTIC (SMT Binding)    │ Output: sql_mock_data.json, vsam_mock_data.json
└───────────────────────┬───────────────────────┘
                        │
                        ▼
             ╔═════════════════════╗
             ║  USER REVIEW GATE   ║ ◄── (Interactive approval via ask_followup_question)
             ╚══════════╦══════════╝
                        │ (Approved)
                        ▼
┌───────────────────────────────────────────────┐
│ Stage 05: LLM Semantic Enrichment             │ (Skill: cobol-smt-stage5-semantic-enrichment)
│ Paradigm: 100% AI + Invariant Verification    │ Output: enriched_record.json (DD.json context)
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│ Stage 06: Binary Memory Overlay & Codec       │ (Skill: cobol-smt-stage6-binary-codec)
│ Paradigm: 100% DETERMINISTIC (ctypes + struct)│ Output: memory_overlay.py + .bin EBCDIC buffer
└───────────────────────────────────────────────┘
```

---

## Output Directory Layout (MANDATORY)

All artifacts for a program MUST be stored under `test-data-gen/<PROGRAM_ID>/` (`$OUT` below), one folder per stage. Never write artifacts to the workspace root. Scripts must resolve paths relative to `__file__`, not absolute paths.

```text
test-data-gen/<PROGRAM_ID>/
├── 01_rule_extraction/       brd_catalog.json
├── 02_cfg_slicing/           path_slice.json, path_slice.sql
├── 03_z3_solving/            solver_engine.py, solver_solutions.json
├── 04_mock_sync/             sql_mock_data.json, vsam_mock_data.json, cics_mock_data.json, mq_mock_data.json
├── 05_semantic_enrichment/   stage5_enrich.py, enriched_record.json
└── 06_binary_codec/          memory_overlay.py, <entity>_records.bin, records.bin, *_ebcdic.txt, binary_payload_summary.json
```

Include the `$OUT` path in every subagent description.

---

## Execution Workflow

When invoked, execute the following stages strictly in sequence using isolated subagents:

### Stage 1: Spawn Rule & Schema Extraction Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage1-rule-extraction` skill using `use_skill`.
   Target file: <path_to_cobol_program_or_copybook>
   Extract all Working-Storage / Linkage section data items (PIC, lengths, types) and procedural validation logic (IF/EVALUATE/conditions).
   Assign canonical IDs (BR-01, BR-02, etc.) to all business rules.
   Output schema and catalog into `$OUT/01_rule_extraction/brd_catalog.json` and return a summary.
   ```
2. Verify `$OUT/01_rule_extraction/brd_catalog.json` is generated.

---

### Stage 2: Spawn CFG Slicing Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage2-cfg-slicing` skill using `use_skill`.
   Inputs: `$OUT/01_rule_extraction/brd_catalog.json` and target rule ID (default: primary business rule, e.g. BR-04).
   Perform backward symbolic slicing from target rule paragraph back to program entry.
   Back-substitute calculated variables into primary inputs and external dependencies.
   Output `$OUT/02_cfg_slicing/path_slice.json` and `$OUT/02_cfg_slicing/path_slice.sql` and return a path summary.
   ```
2. Verify `$OUT/02_cfg_slicing/path_slice.json` is generated.

---

### Stage 3: Spawn Z3 SMT Constraint Solver Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage3-z3-solving` skill using `use_skill`.
   Input: `$OUT/02_cfg_slicing/path_slice.json`
   Formulate First-Order Logic constraints in Z3:
   1. Solve Happy Path equations (Phi_Happy).
   2. Solve Error Paths via systematic branch negation (Phi_Error_k).
   3. Solve 4-point boundary limits (limit, limit-1, limit+1, PIC min/max).
   Output `$OUT/03_z3_solving/solver_solutions.json` and `$OUT/03_z3_solving/solver_engine.py` and return a solutions table.
   ```
2. Verify `$OUT/03_z3_solving/solver_solutions.json` is generated.

---

### Stage 4: Spawn Dependency Mock Sync Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage4-mock-sync` skill using `use_skill`.
   Inputs: `$OUT/03_z3_solving/solver_solutions.json` and `$OUT/02_cfg_slicing/path_slice.json`
   Generate synchronized mock datasets with exact matching primary keys and return codes:
   - DB2 SQL query mocks (`$OUT/04_mock_sync/sql_mock_data.json`) with SQLCODE 0/100/-911.
   - VSAM dataset mocks (`$OUT/04_mock_sync/vsam_mock_data.json`) with FILE STATUS '00'/'23'.
   - CICS COMMAREA / MQ message mocks.
   Return a summary of co-solved mocks.
   ```
2. Verify mock data JSON files are created.

---

### Mandatory User Review & Approval Checkpoint (GATE)
**CRITICAL**: Do NOT proceed to semantic enrichment or binary packing until the user has reviewed and approved the SMT solution specification.

1. Present the generated SMT solutions, mathematical boundaries, and synchronized mocks to the user.
2. Prompt the user using `ask_followup_question`:
   - **Question**: "The mathematical path constraints and synchronized external mocks have been solved deterministically across Happy, Error, and Boundary suites in `$OUT/03_z3_solving/solver_solutions.json` and `$OUT/04_mock_sync/sql_mock_data.json`. Would you like to approve this test specification to proceed with AI semantic enrichment and binary EBCDIC packing?"
   - **suggestion_a**: "Yes, approve specification and generate enriched test records"
   - **suggestion_b**: "Adjust business rule parameters or constraints before continuing"
   - **suggestion_c**: "Cancel pipeline"

3. **Handling User Decisions**:
   - If user chooses **Adjust**: Modify `$OUT/02_cfg_slicing/path_slice.json` / constraints and re-solve via Stage 3.
   - If user chooses **Cancel**: Stop the pipeline cleanly.
   - If user chooses **Approve**: Proceed to Stage 5.

---

### Stage 5: Spawn Semantic Enrichment Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage5-semantic-enrichment` skill using `use_skill`.
   Inputs: `$OUT/03_z3_solving/solver_solutions.json`, `$OUT/04_mock_sync/sql_mock_data.json`, `$OUT/04_mock_sync/vsam_mock_data.json`, and `bobz/DD.json`.
   Enrich abstract numbers/dummy strings with realistic names, dates, addresses, and Luhn-valid cards.
   Run invariant verification to guarantee mathematical boundaries are strictly preserved.
   Output `$OUT/05_semantic_enrichment/enriched_record.json` and return verification metrics.
   ```
2. Verify `$OUT/05_semantic_enrichment/enriched_record.json` is generated and invariant checks pass.

---

### Stage 6: Spawn Binary Memory Overlay & Codec Subagent
1. Spawn an isolated subagent using `spawn_subagent`:
   ```
   Description:
   First, activate the `cobol-smt-stage6-binary-codec` skill using `use_skill`.
   Inputs: `$OUT/05_semantic_enrichment/enriched_record.json` and `$OUT/01_rule_extraction/brd_catalog.json`.
   Compile COBOL copybook structure into Python `ctypes.BigEndianStructure`.
   Pack enriched JSON records into byte-accurate EBCDIC (cp1047), COMP-3, and COMP binary streams.
   Output `$OUT/06_binary_codec/memory_overlay.py` and `$OUT/06_binary_codec/<entity>_records.bin` and return hex dump summary.
   ```
2. Verify binary artifacts are generated.

---

### Final Consolidated Delivery
Deliver the complete pipeline execution summary to the user with clickable links to all generated artifacts:
- Stage 01 Catalog: `[brd_catalog.json](test-data-gen/<PROGRAM>/01_rule_extraction/brd_catalog.json)`
- Stage 02 Path Slice: `[path_slice.json](test-data-gen/<PROGRAM>/02_cfg_slicing/path_slice.json)`
- Stage 03 SMT Solutions: `[solver_solutions.json](test-data-gen/<PROGRAM>/03_z3_solving/solver_solutions.json)`
- Stage 04 Synchronized Mocks: `[sql_mock_data.json](test-data-gen/<PROGRAM>/04_mock_sync/sql_mock_data.json)` & `[vsam_mock_data.json](test-data-gen/<PROGRAM>/04_mock_sync/vsam_mock_data.json)`
- Stage 05 Enriched Payload: `[enriched_record.json](test-data-gen/<PROGRAM>/05_semantic_enrichment/enriched_record.json)`
- Stage 06 Binary Buffer: `[memory_overlay.py](test-data-gen/<PROGRAM>/06_binary_codec/memory_overlay.py)` & `[records.bin](test-data-gen/<PROGRAM>/06_binary_codec/records.bin)`
