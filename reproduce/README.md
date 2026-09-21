# Reproducing the paper's tables

Three scripts, one chain. None needs an API key.

| Script | From | To | Runtime |
|---|---|---|---|
| `corpus_summary.py` | frozen corpus zip (checksum verified on load) | the workbook's Corpus, Table B1, Bootstrap, RatioEnvelopes and Table 1 input cells: as CSV (`--out`), as a read-only agreement report against a workbook (`--workbook`), or written directly into a copy of the workbook (`--write-workbook IN OUT`) | ~10 s |
| `paper_tables.py` | the deposited workbook | every paper table as CSV; optional cell-by-cell check of a paper .docx (`--paper`) | ~5 s |
| `formula_audit.py` | the deposited workbook | VERIFICATION.md step V6: reports any numeric cell on a calculation sheet that is neither a formula nor a declared input; exit status 1 if any | ~2 s |

```bash
pip install -r requirements.txt
python corpus_summary.py --corpus ../data/InferenceCarbon_corpus_frozen_20260822.zip --out out/cs \
       --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx      # agreement report: 644/644
diff -r out/cs expected/corpus_summary
python paper_tables.py --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --out out/tables
diff -r out/tables expected/tables                                             # should be silent
python formula_audit.py --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx
python paper_tables.py --workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx --paper <paper.docx>
```

## Regenerating the workbook (release procedure)

The corpus -> workbook step is mechanical:

```bash
python corpus_summary.py --corpus ../data/InferenceCarbon_corpus_frozen_20260822.zip --out out/cs \
       --write-workbook ../data/workbooks/OpenAIModelCalculations_v1.0.0.xlsx out/regen.xlsx
soffice --headless --convert-to xlsx --outdir out/recalc out/regen.xlsx     # or open and save in Excel
python paper_tables.py --workbook out/recalc/regen.xlsx --out out/tables && diff -r out/tables expected/tables
```

`--write-workbook` writes only value cells and leaves every formula untouched; the recalculation step restores
the cached values the export scripts read. The deposited workbook is the recalculated output of exactly this
procedure. A different LibreOffice or Excel build may differ in the last floating-point digit; the CSV export
rounds to six decimals, so the diff should still be silent.

Filters, seeds and exclusions are stated in each script's docstring and in the paper (Appendix B.4, D.5.5, D.6).
`expected/corpus_summary/provenance.json` records the exclusion counts of the deposited run.
