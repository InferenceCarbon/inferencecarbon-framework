# Workbooks

| File | Contents |
|---|---|
| `OpenAIModelCalculations_v1.0.0.xlsx` | The paper-authoritative calculation chain: Assumptions -> GridIntensity (Tables 3, 4, 5, 10) -> Table6 -> Table7 -> C_Low / C_High -> Table8; Corpus, TableB1, Bootstrap, RatioEnvelopes and T1_GPT55_Grid (corpus-derived inputs, **written by** `reproduce/corpus_summary.py --write-workbook`); Levers and Pinching (Table 10a, summary rows as live formulas); ShapeCorrection (Appendix D.5.8); `Changes_v1.0.0` (every cell changed in the 12 September rounds, including the sheet renames Table7/8/9 → Table6/7/8, with old and new values; the cells themselves carry a cyan fill). Recalculated and saved by LibreOffice headless. SHA-256 396dc5c7a0c57909130274ea19d9f85709ca34fd5a4a35e24ba5d4e80d696a59 |
| `PUE_Calculation_Aug2026.xlsx` | The footprint-weighted PUE derivation (paper Appendix A.1, Table D1) |

## Provenance rule

Every numeric cell on a calculation sheet is either a formula, a BLUE-font typed parameter with a source row in
`../../parameters/`, or a corpus-derived input written by `corpus_summary.py`. `reproduce/formula_audit.py`
enforces this (VERIFICATION.md step V6) and passes with zero undeclared constants.
