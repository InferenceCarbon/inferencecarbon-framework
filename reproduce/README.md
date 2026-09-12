# Reproducing the paper's tables

Two scripts, one chain. Neither needs an API key.

| Script | From | To | Runtime |
|---|---|---|---|
| `corpus_summary.py` | frozen corpus zip (checksum verified on load) | the workbook's Corpus, Table B1, Bootstrap and RatioEnvelopes sheets, as CSV | ~10 s |
| `tables_7_to_10.py` | the deposited workbook | every paper table as CSV; optional cell-by-cell check of a paper .docx | ~5 s |

```bash
pip install -r requirements.txt
python corpus_summary.py --corpus ../data/InferenceCarbon_corpus_frozen_20260822.zip --out out/cs \
       --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx      # prints the agreement report
diff -r out/cs expected/corpus_summary                                        # should be silent
python tables_7_to_10.py --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --out out/tables
diff -r out/tables expected/tables                                             # should be silent
python tables_7_to_10.py --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --paper <paper.docx>
```

The step between the two scripts — pasting `corpus_summary.py`'s output into the workbook's Corpus and
Bootstrap sheets — is manual in v1.0.0; the `--workbook` comparison is the check that it was done correctly.
Making it mechanical is on the verification to-do list (VERIFICATION.md §5).

Filters, seeds and exclusions are stated in each script's docstring and in the paper (Appendix B.4, D.6).
`expected/corpus_summary/provenance.json` records the exclusion counts of the deposited run.

`legacy/` holds the 23 August 2026 refresh scripts that produced the review draft's tables; they are
superseded and kept for the audit trail only.
