# Workbooks

Summary workbooks reproducing the paper's per-model energy and carbon
tables (Tables 7 – 9) and the PUE derivation.

| File | Contents |
|---|---|
| `OpenAIModelCalculations_Aug2026.xlsx` | The full calculation chain: anchor, throughput scaling, PUE, Per-Query Power Correction and measured reasoning multipliers, through to per-1,000-token location- and market-based intensities, with the uncertainty bounds of Table 9 |
| `PUE_Calculation_Aug2026.xlsx` | The footprint-weighted PUE derivation (paper Appendix A.1) |

## Provenance rule

Every value in these workbooks is either campaign-measured (owned data,
paper Appendix B) or derived from the committed parameter tables. The
workbooks are a derived view: they regenerate from the frozen corpus in
`../` and the scripts in `../../reproduce/`.
