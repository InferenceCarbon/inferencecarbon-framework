# Legacy refresh scripts (superseded)

`refresh_tables.py` and `build_final_tables.py`, with their outputs `refresh_R.json`, `supp_stats.json`,
`final_tables.json` and `refresh_provenance.txt`, produced the 23 August 2026 data-close refresh for the
review draft. They are superseded by `../corpus_summary.py` and `../tables_7_to_10.py` and are kept
unmodified for the audit trail. Note that `build_final_tables.py` carries the review draft's constants
(market-based 0.172 gCO₂e/Wh, 34-row roster), not the v1.0.0 values.
