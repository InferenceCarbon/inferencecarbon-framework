# Reproducing the paper's tables

`tables_7_to_10.py` regenerates Tables 7–10 from the committed parameter
tables (`../parameters/`) and workbooks (`../data/workbooks/`). It runs from
a clean clone, needs no API key and no corpus download, and its output is
committed under `expected/` so a replicator can diff what they get against
what we got:

```bash
python tables_7_to_10.py --out out/
diff -r out/ expected/
```

<!-- TODO(source needed): tables_7_to_10.py must be written against the real
workbooks and parameter values — it is the paper's calculation chain, not
scaffolding, and cannot be stubbed here without inventing the method. Commit
its verbatim output to expected/ in the same change, and record the measured
runtime in this README. -->
