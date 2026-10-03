# Changelog

All notable changes to the framework are recorded here. Version numbers
follow the scheme in [VERSIONING.md](VERSIONING.md); every release is
archived on Zenodo with its own version DOI.

## [Unreleased]

Corrections from the audit of 1 October 2026. Documentation and tooling only: no workbook, corpus,
parameter value or table changes, and nothing is re-deposited.

### Fixed
- `reproduce/requirements.txt` pins the library versions the expected outputs were last reproduced with
  (numpy 1.26.4, openpyxl 3.1.2, lxml 5.2.1; re-run 3 October 2026: `corpus_summary`, `paper_tables` and
  `formula_audit` all identical to `expected/`).
- `LICENSE-DATA` section 2 carries the same wording on reproduction in guidance and standards as the paper
  (Appendix H.1) and section 1.
- `data/fetch_corpus.py` pointed at a placeholder Zenodo record and could not run. It now downloads the
  v1.0.0 deposit (10.5281/zenodo.22962476), takes the corpus out of the release archive and checks its
  SHA-256 against `data/manifest.csv`.
- `parameters/`: bracketed reference numbers now match the reference list of the published paper (text
  v1.0.1); they carried an earlier draft's numbering. One dead source link replaced (NREL life-cycle
  update), and the upstream gas figure in a note corrected from ~100 to ~93 gCO2e/kWh to match the paper.
  No parameter value changed.
- Corpus count: the 14,733 request records include 52 synthetic pipeline-test (mock) records from
  24 June 2026. README, `manifests/README.md` and `manifests/RETIREMENTS.md` now say so; RETIREMENTS.md
  wrongly said they were excluded from `variant_dates.csv`. The reproduction scripts exclude them
  (filter F1), so no table is affected. Paper Appendix B.1 quotes the same total; its wording is to be
  clarified in the next text revision.
- `manifests/openai.json`: campaign start corrected to 24 June 2026 (was 25 June, the first day of the
  other providers' series).
- VERSIONING.md: Patch row added to the deposit table. VERIFICATION.md: stale cross-reference fixed, and
  the independent-reproduction item now says V4 needs the paper's .docx, which is not deposited.
- CITATION.cff: message updated; data licence listed beside the code licence.
- Wording that described companion briefs as already published (calibration/, manifests/, briefs/).

### Notes on the frozen v1.0.0 deposit
The deposit cannot be changed. It carries, and will keep, the following residue, all corrected on main:
placeholder identifiers in its own CHANGELOG.md and README.md ("zenodo.TODO", "arXiv:TODO"); the earlier
reference numbering in `parameters/` and one reference number in BASIS_OF_PREPARATION.md; and the
non-working `data/fetch_corpus.py`. None affects the corpus, the workbooks or the reproduction scripts.

## [1.0.1] — 2026-10-01 — paper text only

Patch release (VERSIONING.md): the paper's wording is revised for clarity. No method, parameter, table
value or deposited file changes, so there is no new tag and no new data and code deposit. v1.0.0
([10.5281/zenodo.22962476](https://doi.org/10.5281/zenodo.22962476)) remains the release behind the paper's tables.

The paper is now archived on Zenodo as a record of its own (type Preprint), separate from the data and code
deposit: version DOI [10.5281/zenodo.23084616](https://doi.org/10.5281/zenodo.23084616), all versions
[10.5281/zenodo.23084615](https://doi.org/10.5281/zenodo.23084615).

| Release | Data and code deposit | Paper text | arXiv |
| --- | --- | --- | --- |
| v1.0.0, 25 Sep 2026 | 10.5281/zenodo.22962476 | not deposited separately | submitted 25 Sep 2026; not yet announced |
| v1.0.1, 1 Oct 2026 | unchanged (v1.0.0) | 10.5281/zenodo.23084616 | to be posted as a replacement once the submission is announced |

Checks: V4 re-run on the v1.0.1 text, 1,971 of 1,971 cells agree; all 19 tables identical to v1.0.0
(VERIFICATION.md §3.1c).

### Changed
- VERSIONING.md: patch class defined, mirroring paper Section 8.5 as revised in v1.0.1.
- README.md, CITATION.cff: link and cite the paper by its own DOI.

## [1.0.0] — 2026-09-25

First public release, accompanying the framework paper.

Identifiers: version DOI [10.5281/zenodo.22962476](https://doi.org/10.5281/zenodo.22962476) (this deposit) · concept DOI
[10.5281/zenodo.22962475](https://doi.org/10.5281/zenodo.22962475) (all versions) · arXiv: submitted 25 September 2026,
identifier recorded here when announced.

Note on the tagged snapshot: the v1.0.0 tag and the Zenodo deposit were created
before these identifiers existed, so CITATION.cff and README.md inside the tagged
tree carry none; the identifiers were added on main in the commit following the
release. The deposited files are otherwise identical to the tag.

### Deposit
- `data/InferenceCarbon_corpus_frozen_20260822.zip` — the frozen per-request measurement corpus
  (14,733 request records, 24 June – 22 August 2026), with its SHA-256 in `data/manifest.csv`.
- `data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx` — the paper-authoritative calculation chain:
  Assumptions → Grid Intensity Data (Tables 3, 4, 5, 10) → Table 6 → Table 7 → C_Low / C_High → Table 8, with
  the corpus-derived input sheets (Corpus, Table B1, Bootstrap, Ratio Envelopes, Table 1), Table 8 - Log Widths,
  Pinching (Table 11) and Shape Correction (Appendix D.5.8).
- Final workbook deposited 23 September 2026 (SHA-256 `6692fd642a043fc5eda7ab9cd3714b663fae3e01e0e1d7b1c5bc4da4fe03e693`): sheet names match the paper's table
  numbers and note cells cite the final reference list; no value changed (VERIFICATION.md §3.1b).
- `data/workbooks/PUE_Calculation_Sep_2026.xlsx` — the footprint-weighted PUE derivation (Table D1).
  Renamed from `PUE_Calculation_Aug2026.xlsx` on 23 September 2026; note cells updated to the final
  paper's reference numbers (Jegham [16]; Azure [69], Crusoe [66], AWS [70], Google [37]). Values unchanged.
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
