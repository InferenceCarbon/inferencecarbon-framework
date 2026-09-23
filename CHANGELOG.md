# Changelog

All notable changes to the framework are recorded here. Version numbers
follow the scheme in [VERSIONING.md](VERSIONING.md); every release is
archived on Zenodo with its own version DOI.

## [Unreleased]

## [1.0.0] — 2026-09 (date and DOI filled on release)

First public release, accompanying the framework paper.

Paper identifiers: arXiv:TODO · version DOI 10.5281/zenodo.TODO · concept DOI 10.5281/zenodo.TODO.

### Deposit
- `data/InferenceCarbon_corpus_frozen_20260822.zip` — the frozen per-request measurement corpus
  (14,733 request records, 24 June – 22 August 2026), with its SHA-256 in `data/manifest.csv`.
- `data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` — the paper-authoritative calculation chain:
  Assumptions → Grid Intensity Data (Tables 3, 4, 5, 10) → Table 6 → Table 7 → C_Low / C_High → Table 8, with
  the corpus-derived input sheets (Corpus, Table B1, Bootstrap, Ratio Envelopes, Table 1), Table 8 - Log Widths,
  Pinching (Table 11) and Shape Correction (Appendix D.5.8).
- Final workbook deposited 23 September 2026 (SHA-256 `6692fd642a043fc5eda7ab9cd3714b663fae3e01e0e1d7b1c5bc4da4fe03e693`): sheet names match the paper's table
  numbers and note cells cite the final reference list; no value changed (VERIFICATION.md §3.1b).
- `data/workbooks/PUE_Calculation_Aug2026.xlsx` — the footprint-weighted PUE derivation (Table D1).
- `reproduce/corpus_summary.py` — regenerates the workbook's corpus-derived sheets from the frozen
  corpus with the filters stated in the paper; seeds 20260822 and 20260823.
- `reproduce/paper_tables.py` — exports every paper table from the workbook and checks a paper .docx
  against it cell by cell. Expected outputs committed under `reproduce/expected/`.
- `reproduce/formula_audit.py` — VERIFICATION.md step V6: no numeric cell on a calculation sheet is an
  undeclared constant (declared inputs listed in `reproduce/declared_inputs.json`).
- `parameters/` — routing shares and provider reference data (paper Appendix A), with per-row source
  and access date.
- `BASIS_OF_PREPARATION.md` — boundary, method, conventions and data-quality indicators in the form
  an inventory preparer or assurance provider expects.
- `VERIFICATION.md` — chain of evidence, verification steps, the verification record (author-side
  reproduction only, as of this release) and a reproduction-statement template.
- Collection engine (paper Appendix B), tracked-model manifests, tokenizer calibration, corpus checksum
  manifest and fetch script.
