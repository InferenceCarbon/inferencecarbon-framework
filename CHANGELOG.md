# Changelog

All notable changes to the framework are recorded here. Version numbers
follow the scheme in [VERSIONING.md](VERSIONING.md); every release is
archived on Zenodo with its own version DOI.

## [Unreleased]

## [1.0.0] — 2026-08-26 (planned)

First public release, accompanying the framework paper submitted to arXiv on
26 August 2026. Version numbering starts at 1.0.0 with this release; the
paper's own draft numbering is internal and does not appear here.

- Collection engine (paper Appendix B): campaign scripts, pollers, and
  environment-variable-only configuration.
- Tracked-model manifests, one per provider, with entry/retirement dates.
- Tokenizer calibration runs (o200k_base vs native), with the calibrated-
  tokenizer basis stated once in `calibration/README.md`.
- Parameter tables (paper Appendix A) with per-row source and access date.
- Frozen corpus committed to `data/` and mirrored in the Zenodo data deposit
  (22 Aug 2026 data close; 14,733 request records, 24 Jun – 22 Aug 2026;
  SHA-256 in `data/manifest.csv`), with checksum manifest and fetch script.
- Data-close refresh outputs (`reproduce/expected/`): final per-variant
  tables, measured reasoning multipliers, and supplementary statistics,
  regenerated once from the frozen corpus on 23 Aug 2026.
- Summary workbooks reproducing paper Tables 7–9 (`data/workbooks/`).
- Manifests and variant dates refreshed to the actual 22 Aug close
  (54 models, 106 variants).
- Version DOI: 10.5281/zenodo.TODO (filled in after the release is minted).
