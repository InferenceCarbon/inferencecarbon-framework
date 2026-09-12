# Workbooks

| File | Contents |
|---|---|
| `OpenAIModelCalculations_v1.0.0.xlsx` | The paper-authoritative calculation chain: Assumptions -> GridIntensity (Tables 3, 4, 5, 11) -> Table7 -> Table8 -> C_Low / C_High -> Table9; Corpus, TableB1, Bootstrap, RatioEnvelopes and T1_GPT55_Grid (corpus-derived inputs, **written by** `reproduce/corpus_summary.py --write-workbook`); Levers and Pinching (Table 11a, summary rows as live formulas); ShapeCorrection (Appendix D.5.8); `Changes_v1.0.0` (every cell changed in the 12 September round, with old and new values; the cells themselves carry a cyan fill). Recalculated and saved by LibreOffice headless. SHA-256 1b061ec4d5a2766fb3d41179277be8819c82d169e76ed9967db2890837527bd3 |
| `PUE_Calculation_Aug2026.xlsx` | The footprint-weighted PUE derivation (paper Appendix A.1, Table 6) |

## Provenance rule

Every numeric cell on a calculation sheet is either a formula, a BLUE-font typed parameter with a source row in
`../../parameters/`, or a corpus-derived input written by `corpus_summary.py`. `reproduce/formula_audit.py`
enforces this (VERIFICATION.md step V6) and passes with zero undeclared constants.
