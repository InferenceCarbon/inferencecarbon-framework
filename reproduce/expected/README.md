# Expected outputs (v1.0.0)

- `corpus_summary/` — verbatim output of `corpus_summary.py` on the frozen corpus (11 September 2026).
- `tables/` — verbatim output of `tables_7_to_10.py` on `OpenAIModelCalculations_v1.0.0.xlsx`.

A replicator diffs their own output against these. Differences in the bootstrap columns beyond the third
decimal indicate a different random-number stream, not a different method; differences anywhere else
indicate a real discrepancy and should be reported to methodology@inferencecarbon.ai.
