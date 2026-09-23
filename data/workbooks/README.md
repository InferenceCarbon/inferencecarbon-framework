# Workbooks

| File | Contents |
|---|---|
| `OpenAIModelCalculations_v1.0.0.xlsx` | The paper-authoritative calculation chain: Assumptions -> Grid Intensity Data (Tables 3, 4, 5, 10) -> Table 6 -> Table 7 -> C_Low / C_High -> Table 8; Corpus, Table B1, Bootstrap, Ratio Envelopes and Table 1 (corpus-derived inputs, **written by** `reproduce/corpus_summary.py --write-workbook`); Table 8 - Log Widths and Pinching (Table 11, summary rows as live formulas); Shape Correction (Appendix D.5.8). Recalculated and saved by LibreOffice headless. |
| `PUE_Calculation_Aug2026.xlsx` | The footprint-weighted PUE derivation (paper Appendix D.4, Table D1; provider PUE values from Appendix A) |

SHA-256 of the deposited `OpenAIModelCalculations_v1.0.0.xlsx`: `6692fd642a043fc5eda7ab9cd3714b663fae3e01e0e1d7b1c5bc4da4fe03e693` (final v1.0.0 workbook, 23 September 2026).

## Provenance rule

Every numeric cell on a calculation sheet is either a formula, a typed parameter listed in
`../../reproduce/declared_inputs.json` (with its source beside it in the workbook and in `../../parameters/`), or a corpus-derived input written by `corpus_summary.py`. `reproduce/formula_audit.py`
enforces this (VERIFICATION.md step V6) and passes with zero undeclared constants.
