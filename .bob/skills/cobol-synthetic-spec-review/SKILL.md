---
name: cobol-synthetic-spec-review
description: Use when converting extracted COBOL rules into a unified test specification and generating visual review artifacts with bidirectional rule-to-test-case traceability for stakeholder approval.
---

# Unified Specification & Visual Review Dashboard (Step 2)

This skill structures extracted COBOL rules into a unified schema JSON and creates interactive visual review artifacts (HTML/Markdown) including a bidirectional Rule Traceability Matrix and Coverage KPI Dashboard for stakeholder validation.

## Process
1. **Contract JSON Generation**:
   - Construct schema dictionary mapping fields, types, constraints, nullability, unique keys, and allowed value sets.
   - Include metadata: target program name, entity name, authoring date, rule origins.
   - Embed `business_rules` with canonical IDs (`BR-01`, `BR-02`), descriptions, conditions, and placeholders for linked test cases (`covered_by_test_cases: []`).

2. **Visual Dashboard / Review Artifact**:
   - Create a clean, interactive HTML artifact `<entity>_rules_visualization.html` featuring:
     - Field Definition & Physical Layout
     - Validation Constraints & Edge Limits
     - Rule Origins & Traceability Status
     - **Rule-to-Test Case Traceability Matrix** with interactive test case badges
     - **Rule Coverage Progress Bar & Metric** (tracking covered vs. uncovered rules)

3. **Approval Tracking**:
   - Provide clear acceptance criteria and status flags (Draft, In-Review, Approved).
