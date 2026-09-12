# Changelog

All notable changes to the framework are recorded here. Version numbers
follow the scheme in [VERSIONING.md](VERSIONING.md); every release is
archived on Zenodo with its own version DOI.

## [Unreleased]

## [1.0.0] — 2026-09 (release candidate; date and DOI filled on release)

First public release, accompanying the framework paper. Version numbering starts at 1.0.0
with this release; the paper's internal draft numbering does not appear here.

Paper identifiers: arXiv:TODO · version DOI 10.5281/zenodo.TODO · concept DOI 10.5281/zenodo.TODO.

### Methodology and figures (relative to the 26 August review draft)
- Google Cloud credited at its reported CY2025 GHG Protocol market-based Scope 2 realised intensity
  (64.6 gCO₂e/kWh, Google 2026 Environmental Report) instead of its 66% hourly carbon-free-energy share,
  so the Section 3.7 realised-intensity rule applies to Microsoft, Oracle and Google alike and every
  market-based figure rests on a 2015-Guidance quantity. Market-based headline 64 → 52 gCO₂e/kWh;
  procurement-lag scenario 172 → 159. Location-based figures unchanged.
- Shape correction for queries far from the anchor's 1:3 input:output shape (paper Appendix D.5.8;
  pre-fill ratio 0.012 from the anchor's own two-point fit, 0.058 as sensitivity); Table 9 gains a
  50,000-token-input row; limitation 29 restated. The two-term prefill/decode model is deferred to v2.0.
- Reasoning-cell filter: answers that stop short of the prompt's word minimum are excluded from the
  fixed-task reasoning cells (10 September 2026); the k = 36 heavy rung is exempt (see VERIFICATION.md §4).
- Routing shares restated from the contract-value proxy with the AWS $100B investment included:
  Azure 23.4 / Oracle-Stargate 39.3 / AWS 11.7 / GCP 25.5.

### Deposit
- `data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` — the paper-authoritative calculation chain,
  now carrying the GridIntensity (Tables 3, 4, 5, 10) and ShapeCorrection (Appendix D.5.8) sheets.
  Replaces `OpenAIModelCalculations_Aug2026.xlsx`. 12 September: corpus-derived input sheets written by
  `corpus_summary.py --write-workbook` (no hand-pasted values remain); Table 10a summary rows converted
  from typed constants to live formulas, correcting one typed value (7.19× → 7.79×); every changed cell
  cyan-filled and listed on the `Changes_v1.0.0` sheet. The paper's bound tables (then numbered 9, 10, 11a, C1 – C3; now 8, 9, 10a, C1 – C3)
  were regenerated from it — 236 cells moved at the last displayed decimal (≤ 0.5%), centrals unchanged.
- `reproduce/formula_audit.py` — VERIFICATION.md step V6; passes with zero undeclared constants.
- 12 September, second round: paper tables resequenced in order of appearance (main text 1 – 11 with
  10a; the PUE table becomes Appendix Table D1) and references renumbered in order of first citation
  (six uncited entries removed; 1 – 97). Workbook sheets Table7/Table8/Table9 renamed Table6/Table7/Table8
  with every formula reference and note remapped (logged on `Changes_v1.0.0`); `tables_7_to_10.py`
  renamed `paper_tables.py` with outputs named for the new table numbers; docs and `parameters/*.csv`
  citation numbers rebuilt against the renumbered list.
- `reproduce/corpus_summary.py` — regenerates the workbook's corpus-derived sheets (Corpus, Table B1,
  Bootstrap, RatioEnvelopes) from the frozen corpus with the filters stated in the paper; seeds 20260822
  and 20260823. Replaces the legacy `refresh_tables.py` / `build_final_tables.py` pair, moved to
  `reproduce/legacy/`.
- `reproduce/tables_7_to_10.py` (renamed `reproduce/paper_tables.py` on resequencing, see above) — exports every paper table from the workbook and checks a paper .docx
  against it cell by cell. Expected outputs committed under `reproduce/expected/`.
- `BASIS_OF_PREPARATION.md` — boundary, method, conventions and data-quality indicators in the form
  an inventory preparer or assurance provider expects.
- `VERIFICATION.md` — chain of evidence, verification steps, the verification record (author-side
  reproduction only, as of this release), known workbook discrepancies, and a reproduction-statement template.
- `parameters/` — routing shares and provider reference restated to the v1.0.0 values (Google CY2025
  realised intensity; Microsoft and Oracle realised intensities; pre-fill ratio).
- Collection engine (paper Appendix B), tracked-model manifests, tokenizer calibration, corpus checksum
  manifest and fetch script, as in the 26 August draft deposit.
