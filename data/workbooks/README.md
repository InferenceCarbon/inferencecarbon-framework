# Workbooks

| File | Contents |
|---|---|
| `OpenAIModelCalculations_v1.0.0.xlsx` | The paper-authoritative calculation chain: Assumptions -> GridIntensity (Tables 3, 4, 5, 10) -> Table6 -> Table7 -> C_Low / C_High -> Table8; Corpus, TableB1, Bootstrap, RatioEnvelopes and T1_GPT55_Grid (corpus-derived inputs, **written by** `reproduce/corpus_summary.py --write-workbook`); Levers and Pinching (Table 11, summary rows as live formulas); ShapeCorrection (Appendix D.5.8). Recalculated and saved by LibreOffice headless. |
| `PUE_Calculation_Aug2026.xlsx` | The footprint-weighted PUE derivation (paper Appendix D.4, Table D1; provider PUE values from Appendix A) |

## Provenance rule

Every numeric cell on a calculation sheet is either a formula, a typed parameter listed in
`../../reproduce/declared_inputs.json` (with its source beside it in the workbook and in `../../parameters/`), or a corpus-derived input written by `corpus_summary.py`. `reproduce/formula_audit.py`
enforces this (VERIFICATION.md step V6) and passes with zero undeclared constants.
