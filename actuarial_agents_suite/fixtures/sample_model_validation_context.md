# Synthetic model summary (for validation copilot demo only)

## Model purpose
**GLM frequency model v3.2** predicts annual claim counts by segment using log link and Poisson error. Intended for internal pricing support; **not** for external filing without independent review.

## Key inputs
- Policy attributes: territory, vehicle class, credit tier (binned), annual mileage band.
- Exposure: car-years; capped at 3.0 per policy for commercial fleet.
- Training window: accident years 2018–2022; valuation as of 2023-12-31.

## Outputs
- Expected claim count per policy-year at granular cell level.
- Relativities vs base level; base is **Territory 05 / Class A / Tier 3**.

## Known limitations (documented)
1. Sparse cells merged using credibility weight **Z = n / (n + K)** with K fixed by line (see appendix — not reproduced here).
2. **No** explicit weather or inflation covariates; calendar trend applied as single index post-fit.
3. Large fleet accounts handled with off-model adjustment in underwriting; model score is **indicative only** for those risks.

## Validation test plan (excerpt)
| Test ID | Description | Pass criteria |
|--------|-------------|----------------|
| T-01 | Hold-out lift chart (2022 AY) | Top decile lift > 1.8 vs bottom |
| T-02 | Dual lift by territory | No territory with inverted ranking |
| T-03 | Residual deviance vs prior version | Improve or document degradation |
| T-04 | Data QC | Missing rate < 2% on core variables |

## Code snippet (illustrative — not executed in app)
```python
# Pseudocode: link check
eta = X @ beta
mu = np.exp(eta) * exposure
```

---

*All figures and IDs are fictional. Paste this block into **Context to review** and ask the agent to critique gaps, tests, or documentation quality.*
