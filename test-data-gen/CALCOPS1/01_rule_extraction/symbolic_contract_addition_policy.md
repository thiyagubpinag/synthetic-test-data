# SMT Symbolic Contract: 2.3.1 Business Rule: Addition Policy (CALCOPS1)

Source: `docs/business-rule/cobol/CALCOPS1-overview.md` (line 61), cross-checked against `cobol/CALCOPS1.cbl` `3000-ADDITION-PARA`.

Where InRange(X) = MIN <= X <= MAX, MAX = +5000000.00, MIN = -5000000.00.

| Rule Step | Logical Condition ($P_i$) | COBOL SMT Action / Status | Target Test Vector | Relevant Paragraphs | External Connections |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Operand Range Validation (Error/Validation)** | $A > \text{MAX} \lor A < \text{MIN} \lor B > \text{MAX} \lor B < \text{MIN}$ | `WS-STATUS-CODE = '40'` (STATUS-OUT-OF-RANGE); `WS-RESULT` unchanged | Invalidation / Out of Bounds | 3000-ADDITION-PARA, 0000-MAIN-PARA | None |
| **2. Zero Shortcut (Short-Circuit/Bypass)** | $\text{InRange}(A) \land \text{InRange}(B) \land A = 0 \land B = 0$ | `WS-RESULT = 0`, `WS-STATUS-CODE = '00'` | Trivial Zero Path / Shortcut | 3000-ADDITION-PARA | None |
| **3. Add (Happy / Nominal Sum)** | $\text{InRange}(A) \land \text{InRange}(B) \land \lnot(A = 0 \land B = 0)$ | `WS-RESULT = A + B`, `WS-STATUS-CODE = '00'` | Nominal & Boundary | 3000-ADDITION-PARA, 0000-MAIN-PARA | None |
| **4. Overflow Check (Exception / Size Error)** | $\text{InRange}(A) \land \text{InRange}(B) \land \lnot(A = 0 \land B = 0) \land \lvert A + B \rvert > 999999999.99$ | `WS-STATUS-CODE = '10'` (OVERFLOW) | Exception / Overflow (UNSAT, defensive only) | 3000-ADDITION-PARA | None |

**Note:** Step 4 is unreachable. The maximum in-range sum is +/-10,000,000.00, while `WS-RESULT` (`S9(9)V99`) holds up to +/-999,999,999.99. The source comment (lines 184-185) calls the size-error check "defensive only". Stage 3 should record it as UNSAT and should not force a vector.
