# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Workspace Type
Application platform: IBM Z
**Type:** IBM Enterprise COBOL for z/OS (CICS + embedded DB2 SQL)
**Purpose:** Source programs in `cobol/` are inputs to a 6-stage synthetic test data pipeline (COBOL → business rules → CFG slice → Z3 solve → dependency mocks → LLM enrichment → EBCDIC binary).

## Build / Lint / Test
- No build, lint, or test tooling is configured (no Makefile, package.json, JCL, or DBB config). Do not invent commands.
- Validate COBOL edits with `get_diagnostics` (Z Open Editor language server).
- `.venv/` has `z3` and `pytest` installed, but no test files exist yet. When tests are added, run a single one with `.venv/bin/pytest path/to/test_x.py::test_name`.
- `zapp.yaml` sets `cobol/` as both the copybook syslib and the analysis scope, with `containsCics: true`. Copybooks must live under `cobol/` to resolve.
- All pipeline outputs live in `test-data-gen/<PROGRAM_ID>/01_rule_extraction … 06_binary_codec/` (never the workspace root); scripts resolve paths from `__file__`.
- Pipeline outputs are JSON/Python artifacts (`brd_catalog.json`, `path_slice.json`, `solver_solutions.json`, `sql_mock_data.json`, `vsam_mock_data.json`, `enriched_record.json`, `memory_overlay.py`, `*.bin`). Use `.venv/bin/python` (Python 3.14), not system Python, so `z3` imports.

## Pipeline (non-obvious)
- Entry point is the `cobol-synthetic-data-orchestrator` skill in `.bob/skills/`. Each stage is its own skill (`cobol-smt-stage1..6-*`) and MUST run in an isolated `spawn_subagent` that first calls `use_skill` for that stage.
- Stages 2–4 are deterministic (AST/SQL, Z3, SMT key binding). Never let the LLM invent values there; only Stage 5 is LLM-driven, and it must preserve Z3 boundary values (invariant check).
- Mandatory user approval gate (via `ask_followup_question`) after Stage 4 and before Stage 5/6. Do not skip it.
- Stages 1–2 query the scanner DB through `execute_sql_query`; the DB path is `databaseLocation` in `.bobz/local-settings.json` (call `get_sql_schema` first). Run `scan_program` if it is missing.
- Business rules use canonical IDs `BR-01`, `BR-02`, …; every scenario/mock must carry its rule ID for traceability.
- Per-rule output layout: `manifest.json`, `01_happy_path.json`, `02_error_paths.json`, `03_boundary_conditions.json`, `mocks/` (see `brainstorm.md` §3).
- Error-path mocks use real mainframe codes: `SQLCODE` 0/+100/-911, `FILE STATUS` '00'/'23', CICS `EIBRESP`.
- Binary stage: EBCDIC `cp1047`, COMP-3/COMP packing, `ctypes.BigEndianStructure`, honor `REDEFINES`.

## COBOL Source Conventions (observed)
- Fixed-format COBOL: sequence area cols 1–6, indicator col 7; commented-out `COPY`/`EXEC SQL` lines use `*` in col 7 (e.g. `COPY LGCMAREA` is commented out in the program and fields are inlined).
- Subprogram calls via `EXEC CICS LINK PROGRAM('...')`; SQL via `EXEC SQL ... END-EXEC`; error paths do `EXEC CICS RETURN`.
- Always edit with fixed-format column rules in mind; run `get_diagnostics` after every COBOL change.

## Data Dictionary
Not present. The canonical location would be `bobz/DD.json`; Stage 5 expects it. Create it via the `data-dictionary-management` skill before running Stage 5 (read COBOL files only after invoking that skill).

## Coding Standards
No coding-standards skill exists in the workspace yet. If one is added, apply it for COBOL generation/modification.

## Technical Documentation Location
**Key files:** `brainstorm.md`, `pipeline_architecture.html`, `_bmad-output/brainstorming/` (brainstorm session output).

| Program / Area | Documentation File(s) | Description/Purpose |
|----------------|----------------------|---------------------|
| `cobol/*.cbl` (all programs) | `brainstorm.md`, `pipeline_architecture.html` | Synthetic test-data pipeline design, stage contracts, artifact schemas |
| Pipeline skills (`.bob/skills/cobol-smt-*`, `cobol-synthetic-*`) | `pipeline_architecture.html` | Stage-by-stage skill definitions |

**Auto-Update Rules:**
1. When code is modified, check the mapped documentation for drift.
2. If docs are out of sync, prompt the user to update them.
3. When analyzing a COBOL program, consult its mapped documentation first.
4. Update this table when new programs or docs are added.
