# Versioning

This file mirrors the policy in sections 8.4 (Data Availability) and 8.5
(Correction Policy and Versioning) of the framework paper. The paper is
canonical; if the two ever disagree, the paper wins and this file has a bug.

## The mutable/frozen split

This repository is the **mutable** working copy of the framework:
methodology, parameter tables and scripts are maintained here as a living
document. The **citable record** for each release is an immutable archive on
Zenodo, which mints a persistent DOI per tagged release. The raw per-request
measurement corpus for the paper's window ships in this repository as
`data/InferenceCarbon_corpus_frozen_20260822.zip` and is mirrored, with the
release snapshot of the collection engine, in the frozen Zenodo deposit.
`data/manifest.csv` holds the SHA-256 of every deposited corpus file so a
replicator can verify what they fetched. The benchmark campaign continues
beyond the paper's window; the ongoing series is operated through the
InferenceCarbon.ai API rather than deposited. The full corpus and summary
workbooks are deposited at major versions only; minor releases deposit only
the workbooks their changed tables consume. Deposited artifacts carry the
class licenses of paper Section 8.2 and Appendix H.1 whatever the release
class: Apache 2.0 for software, CC BY 4.0 for the summary workbooks and
parameter tables, and CC BY-NC 4.0 (with an express permission for
verification and assurance use) for the raw corpus.

## Version numbers

Semantic versioning, per paper section 8.5:

- **Major** (e.g. v1.0 → v2.0) — methodology changes that break
  comparability between releases.
- **Minor** (e.g. v1.0 → v1.1) — parameter updates that preserve
  comparability (including substantive updates to the Appendix A provider
  reference data).

Each release carries three identifiers — the semantic version, its Zenodo
DOI, and, where the paper text itself changed, an arXiv revision number —
and [CHANGELOG.md](CHANGELOG.md) maps the three, so a reader holding any one
of them can establish the other two.

## Corrections and restatement

Substantive corrections are incorporated into subsequent versions with
change logs published here. When the revised GHG Protocol Scope 2 standard
is published, market-based figures will be re-stated under the revised
method in the next release, with the change logged. Downstream briefs in the
InferenceCarbon series cite the specific framework version they used;
figures published by the InferenceCarbon.ai products stamp the methodology
version they were computed under.

Corrections, additional empirical data and per-model disclosures are
welcome: methodology@inferencecarbon.ai.

## Paper-authoritative artifacts

Within a release the workbook `data/workbooks/OpenAIModelCalculations_<version>.xlsx` is the
authoritative calculation chain: paper tables are regenerated from it, never edited by hand, and
`reproduce/paper_tables.py --paper` is the check. The frozen corpus is authoritative for the
measured inputs; `reproduce/corpus_summary.py` is the check on the workbook's Corpus, Bootstrap and
RatioEnvelopes sheets. Where the paper, the workbook and the corpus disagree, the corpus wins, then
the workbook, and the discrepancy is logged in VERIFICATION.md §4 until the next release fixes it.

## Deposit contents and licenses per release class

| Release class | Deposited on Zenodo | Licenses |
|---|---|---|
| Major (vX.0) | Repository snapshot, summary workbooks, parameter tables, full raw corpus for the release window | Software: Apache 2.0; summary workbooks and parameter tables: CC BY 4.0; raw corpus: CC BY-NC 4.0 with the verification and assurance permission (see LICENSE, LICENSE-DATA) |
| Minor (vX.Y) | Repository snapshot and the summary workbooks the release's changed tables consume | Software: Apache 2.0; summary workbooks and parameter tables: CC BY 4.0 (see LICENSE, LICENSE-DATA) |
