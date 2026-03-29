# Sample fixtures (synthetic / non-sensitive)

Use these to exercise each Streamlit tab without real client data. Paths are relative to the `actuarial_agents_suite` folder.

| File | Agent tab | How to use |
|------|-----------|------------|
| [`sample_loss_triangle.csv`](sample_loss_triangle.csv) | **P&C Reserving** | Upload as CSV. Triangle-style loss development. |
| [`sample_pricing_rating.csv`](sample_pricing_rating.csv) | **Pricing & rate** | Upload; premium, loss, exposure by state/LOB/year. |
| [`sample_experience_study.csv`](sample_experience_study.csv) | **Experience study** | Upload; segment-level frequency/severity-style aggregates. |
| [`sample_pension_plan.csv`](sample_pension_plan.csv) | **Pension / benefits** | Upload (optional); synthetic member-level roll-up fields. |
| [`sample_model_validation_context.md`](sample_model_validation_context.md) | **Model validation** | Open file, copy into **Context to review** (no upload in UI). |
| [`sample_ifrs_questions.md`](sample_ifrs_questions.md) | **IFRS & risk narrative** | Copy a prompt into **Question** (no data upload). |
| [`sample_research_questions.txt`](sample_research_questions.txt) | **Regulatory research** | Copy a line into **Research question**; verify web citations. |

**P&C Reserving** also supports arbitrary CSV/XLSX triangles or policy extracts—the samples above are minimal demos only.
