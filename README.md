# InferenceCarbon framework

## What this is

The repository accompanying *"So, What's the Carbon Cost of Using AI?" A
Bounded Estimation Framework for Calculating the Per-Token Carbon Intensity of
Large Language Model Inference Under Limited Disclosure, Using the Worked
Example of OpenAI's GPT-5 Model Family* (Manktelow, 2026): the collection engine, the parameter tables, and the
scripts that reproduce the paper's tables.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22962475.svg)](https://doi.org/10.5281/zenodo.22962475)

- Paper: submitted to arXiv on 25 September 2026; identifier to follow (see CHANGELOG.md)
- Archive: concept DOI [10.5281/zenodo.22962475](https://doi.org/10.5281/zenodo.22962475) (always resolves to the
  latest version); this release, v1.0.0: version DOI [10.5281/zenodo.22962476](https://doi.org/10.5281/zenodo.22962476)

## Current version

**v1.0.0** — version DOI 10.5281/zenodo.TODO — see [CHANGELOG.md](CHANGELOG.md).
Cite the version DOI to fix a specific calculation.

## Repository map

```
engine/         Collection engine (paper Appendix B): benchmark, drivers, scheduled-task prompts
manifests/      Tracked-model manifests, one per provider, with entry/retirement dates
calibration/    Tokenizer calibration (o200k_base vs native); the canonical basis statement
parameters/     Everything Appendix A tabulates, with per-row source and access date
data/           Frozen corpus and checksum manifest, Zenodo fetch script, derived workbooks
reproduce/      corpus_summary.py (corpus → workbook inputs) and paper_tables.py (workbook → tables, paper check); expected outputs committed
briefs/         Per-brief data folders and reproduce scripts
BASIS_OF_PREPARATION.md   Boundary, method, conventions, data-quality indicators — for inventory preparers and assurance providers
VERIFICATION.md           Chain of evidence, verification steps and record, known discrepancies, reproduction-statement template
```

## Reproducing the paper's tables

The tables regenerate from committed parameters and workbooks — **no corpus
download and no API key required**:

```bash
git clone https://github.com/InferenceCarbon/inferencecarbon-framework.git && cd inferencecarbon-framework
pip install -r reproduce/requirements.txt
python reproduce/paper_tables.py --workbook data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --out out/tables
diff -r out/tables reproduce/expected/tables
```

Runtime: about five seconds. To go one step further back — from the frozen corpus to the workbook's
measured inputs — run `reproduce/corpus_summary.py` (about ten seconds), which can also regenerate the
workbook's input sheets outright (`--write-workbook`); `reproduce/formula_audit.py` checks that no
numeric cell on a calculation sheet is an undeclared constant. See `reproduce/README.md`.
The full verification procedure, and what has and has not been independently verified, is in
[VERIFICATION.md](VERIFICATION.md).

## Running the collection engine

Not required to reproduce the tables. The engine reads each provider's API
key from local key files that are never committed (names and per-provider
budget caps in [engine/owned_benchmark/providers.json](engine/owned_benchmark/providers.json));
a full campaign run makes real API calls against every tracked provider up
to those caps. See [engine/README.md](engine/README.md).

## Data provenance, and what is deliberately absent

The raw per-request corpus ships in this repository as
`data/InferenceCarbon_corpus_frozen_20260822.zip` (8.5 MB, 14,733 request
records, 24 Jun – 22 Aug 2026) and is mirrored in the Zenodo data deposit.
Both copies verify against the same SHA-256 in `data/manifest.csv`:

```bash
(cd data && shasum -a 256 -c InferenceCarbon_corpus_frozen_20260822.sha256)
```

To fetch and verify the Zenodo mirror instead:

```bash
python data/fetch_corpus.py
```

Third-party benchmark series used for the cross-checks in section 5.3 of
the paper are not reproduced here. The paper states what was compared and
over which window; a replicator needs their own access to those series.

## Licensing

This repository is the frozen, per-release snapshot from which the
release's published tables regenerate; it exists to be recomputed,
subsetted and built upon.

- **Code** — [Apache 2.0](LICENSE): the same openness as MIT with an
  explicit patent grant and no implied trademark rights.
- **Summary workbooks and parameter tables** — [CC BY-NC 4.0](LICENSE-DATA),
  with express permissions: non-commercial use (recomputation, subsetting,
  teaching, research, publication) needs no permission; use by regulators,
  standards bodies and public authorities, and verification or assurance of
  figures derived from the tables, including by commercial auditors, is
  expressly permitted. Commercial use requires a licence
  (info@inferencecarbon.ai).
- **Frozen raw measurement corpus** — [CC BY-NC 4.0](LICENSE-DATA), with the
  same express permissions: regulators, standards bodies and public
  authorities, and verification or assurance of figures derived from it,
  including by commercial auditors. What the non-commercial term withholds is
  the assembly of deposited corpora into a commercial data product; commercial
  use requires a licence.
- No trademark rights are granted. The paper text is licensed separately
  (CC BY-NC-ND 4.0 in its preprint versions). Paper Section 8.2 and
  Appendix H.1 are canonical.

The live operational stack (multi-vantage scheduling, model manifests and
quality-assurance layers) and the live measurement database served through
the InferenceCarbon.ai API are not published here; the API's terms of
service are the operative license for that service
(methodology@inferencecarbon.ai).

## Where the live figures are

The current, continuously updated figures (every tracked model and reasoning
setting, with bounds and confidence) are served by the InferenceCarbon.ai API:
free for academic research, regulators and public bodies, personal use and a
30-day evaluation, with a key from https://www.inferencecarbon.ai/api. The
same figures are shown at https://www.inferencecarbon.ai/models, and the
calculator at https://www.inferencecarbon.ai/calculator applies them to a
query. To challenge a figure or the method: https://www.inferencecarbon.ai/review-this-paper.

## How to cite

See [CITATION.cff](CITATION.cff) (GitHub renders it as "Cite this
repository"). Version DOI to fix a calculation; concept DOI for the
framework as a whole; the arXiv identifier for the text. **A headline figure
travels with its plausibility band and its confidence label** — quoting the
central value alone misrepresents the finding.

## Corrections

methodology@inferencecarbon.ai. If you are a provider: an audited per-model
disclosure of energy per token would retire these estimates, and we would
welcome that outcome.

## What this repository is not

Not a measurement system. The figures are bounded estimates, at Low
confidence on the headline, and the Low/Central/High envelopes are part of
the finding, not decoration around it.
