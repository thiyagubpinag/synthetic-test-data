---
name: cobol-synthetic-data-generation
description: Use when generating deterministic, validated synthetic dataset records across generated test scenarios for COBOL programs with rule traceability metadata embedded.
---

# Synthetic Test Record Generation (Step 4)

This skill produces reproducible, validated synthetic test data records from approved scenarios and specifications using a deterministic generator engine (Python script), preserving end-to-end rule traceability.

## Process
1. **Deterministic Python Generator Engine**:
   - Utilize seeded PRNGs (`random.seed` / Faker with fixed seed) for reproducibility.
   - Strictly honor byte-length and padding conventions:
     - Alpha/Alphanumeric: Left-justified, space-padded up to field size.
     - Numeric: Leading zero-padded or fixed length digits.
     - Decimal: Fixed decimal precision without raw float imprecision.

2. **Scenario & Rule Mapping to Record Synthesis**:
   - Map each Scenario Test Case (TCxx) into one or more concrete data records.
   - Embed `target_business_rules` metadata in generated record payloads for auditability.
   - Inject exact boundary and test values while generating valid realistic data for non-targeted attributes.

3. **Data Verification & Buffer Export**:
   - Verify every generated record against the unified specification contract.
   - Format output into desired formats:
     - Structured JSON `<entity>_synthetic_records.json`
     - Fixed-length EBCDIC/ASCII raw copybook / commarea buffer streams.
