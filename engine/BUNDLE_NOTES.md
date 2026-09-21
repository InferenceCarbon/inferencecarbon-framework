# InferenceCarbon engine bundle — export notes

The release snapshot of the collection engine described in paper Appendix B.

## Contents
- owned_benchmark/ — the benchmark engine: inferencecarbon_bench.py (main), drivers and wrappers (_campaign_driver.py, campaign_wrapper.py, fire_wrapper.py, agent_runner.py, driver_20260802.py, shell drivers), configs (providers.json, prices.json, tracked_models*.json), README.md.
- InferenceCarbon_HeavyThinkers.command — local uncensored heavy-thinker run (150 s timeouts, double-click launcher).
- scheduled_prompts/ — the two published scheduled-task prompts: owned multi-provider benchmark, reasoning rider. Other prompts in the operational stack are not published.

## Key audit (before export)
- No API keys, OAuth tokens, or credentials in any file — verified by pattern scan (sk-*, AIza*, ghp_*, Bearer, api_key/token/secret assignments, refresh/access_token, PEM blocks): zero matches.
- Keys live only in separate local key files, referenced by filename in providers.json (see engine/README.md). None are included here, and *APIKey*.txt and *Key.txt are gitignored.

## Deliberately excluded from engine/
- Run logs, bench logs, __pycache__, backup and scratch files, spend-state files, and the operational tracker workbooks. The results corpus is deposited separately as data/InferenceCarbon_corpus_frozen_20260822.zip.

## Note on paths
providers.json resolves key_file relative to the parent of the working directory. Paths in the scheduled prompts assume the original desktop layout; treat the prompts as documentation of the pipeline, not as directly runnable from a clone.
