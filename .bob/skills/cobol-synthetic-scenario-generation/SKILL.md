---
name: cobol-synthetic-scenario-generation
description: Use when generating comprehensive test scenarios (valid, invalid, boundary, business edge cases) from a unified COBOL rule specification with full rule-to-test-case coverage tracking.
---

# Test Scenario Generation & Rule Coverage Matrix (Step 3)

This skill designs structured test scenarios covering boundary values, domain rules, equivalence partitions, and combinatorial cases, enforcing 100% business rule traceability.

## Process
1. **Rule Inventory Ingestion**:
   - Read the list of business rules (`BR-xx`) and field constraints from `<entity>_rule_spec.json`.
   - Initialize the rule coverage tracker.

2. **Scenario Design & Rule Tagging**:
   - For every business rule, generate at least one positive test case and one boundary/negative test case where applicable:
     - **Positive / Baseline**: Verifies normal execution path (`SQLCODE = 0`, expected return code).
     - **Boundaries**: Min/Max length limits, value limits, date boundaries.
     - **Negative & Error Paths**: Error simulation (missing fields, duplicate keys, abend branches).
   - Tag each scenario explicitly with its target rules: `"target_business_rules": ["BR-01", "BR-03"]`.

3. **Coverage Verification & Gap Analysis**:
   - Calculate coverage: `covered_rules / total_rules * 100%`.
   - If any business rule is left uncovered (`covered_by_test_cases` is empty), generate dedicated targeted scenarios to cover the gap.

4. **Output Contract**:
   - Output `<entity>_scenarios.json` containing:
     - `coverage_summary`: Total rules, covered rules, coverage percentage, uncovered list.
     - `scenarios`: Array of test cases with `target_business_rules`, category, parameters, and expected outcomes.
