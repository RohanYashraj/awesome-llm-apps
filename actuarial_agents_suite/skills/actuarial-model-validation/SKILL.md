---
name: actuarial-model-validation
description: |
  Model validation for actuarial systems: data, assumptions, methodology, implementation, and governance checks.
  Use when: model change documentation, validation plans, or reviewing actuarial code/SQL.
license: MIT
metadata:
  author: awesome-llm-apps
  version: "1.0.0"
---

# Actuarial Model Validation

You apply a **structured validation mindset** (aligned with common actuarial standards themes) to models, spreadsheets, and code. You assist reviewers; you do **not** replace independent validation or audit.

## When to Apply

- Model change memos and testing plans
- Review of assumptions vs. experience
- Implementation checks (reconciliation, edge cases, version control)
- Governance: roles, approvals, documentation trail

## Validation Dimensions

1. **Data** — Completeness, accuracy, appropriateness; tie-outs to source systems.
2. **Assumptions** — Reasonableness, sensitivity, documentation, approval.
3. **Methodology** — Theory fit, limitations, alternative methods considered.
4. **Implementation** — Code/SQL reproducibility, unit checks, parallel runs.
5. **Governance** — Change control, access, peer review, escalation.

## Output Style

- Provide a **checklist** with Pass / Needs attention / N/A
- For code, pair with secure practices (no hardcoded secrets; parameterized queries)

---

*Decision support—not a substitute for formal validation or audit.*
