# InferenceCarbon engine bundle — for CarbonFirefly
Assembled by Cowork, 2026-08-07, from James's Mac. For commit to a CarbonFirefly branch by Claude Code.

## Contents
- owned_benchmark/ — the benchmark engine: inferencecarbon_bench.py (main, 68 KB), drivers and wrappers (_campaign_driver.py, campaign_wrapper.py, fire_wrapper.py, agent_runner.py, driver_20260802.py, shell drivers), configs (providers.json, prices.json, tracked_models*.json), README.md.
- InferenceCarbon_HeavyThinkers.command — local uncensored heavy-thinker run (150 s timeouts, double-click launcher).
- scheduled_prompts/ — the two published Cowork scheduled-task prompts (SKILL.md contents): owned multi-provider benchmark, reasoning rider. Other prompts in the operational stack are not published.

## Key audit (done in Cowork before export)
- No API keys, OAuth tokens, or credentials in any file — verified by pattern scan (sk-*, AIza*, ghp_*, Bearer, api_key/token/secret assignments, refresh/access_token, PEM blocks): zero matches.
- Keys live only in separate local key files, referenced by filename in providers.json (see engine/README.md). None are included here, and *APIKey*.txt and *Key.txt are gitignored.

## Deliberately excluded
- results/ corpus (~8,000 run_*.json), _runlogs/, bench_logs/, __pycache__, *.bak-*, err/tmp scratch files, spend-state files, and all Desktop workbooks (.xlsx). Say if any of these are wanted.

## Note for the repo
providers.json resolves key_file relative to the parent of the working directory (…/InferenceCarbonWorking/). Paths in the scheduled prompts assume the Mac Desktop layout; treat the prompts as documentation of the pipeline, not directly runnable in the repo container.
