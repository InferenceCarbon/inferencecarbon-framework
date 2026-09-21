# Collection engine (paper Appendix B)

The scripts that ran the owned benchmark campaign described in Appendix B of
the paper: the benchmark engine itself, its drivers and wrappers, and the
Claude Cowork scheduled-task prompts that fired it daily.

**You do not need to run the engine to reproduce the paper's tables.** The
tables regenerate from committed parameters and workbooks — see
`../reproduce/`. A full campaign run makes real API calls against every
tracked provider under the per-provider budget caps in
`owned_benchmark/providers.json`.

## Layout

| Path | What it is |
|---|---|
| `owned_benchmark/inferencecarbon_bench.py` | The benchmark engine (Appendix B.2–B.5): streamed requests per model variant, TTFT/decode split, native + o200k_base token counts, hidden reasoning-token capture, per-request JSON corpus records |
| `owned_benchmark/providers.json` | Per-provider config: OpenAI-compatible endpoints, tracked-model files, effort styles, thinking budgets, budget caps |
| `owned_benchmark/tracked_models*.json` | Curated tracked-model lists per provider (OpenAI auto-discovers new major families; other providers are hand-curated — Appendix B.5) |
| `owned_benchmark/prices.json` | Per-model pricing used for spend estimation |
| `owned_benchmark/*_driver*`, `*wrapper*`, `round.sh` | Campaign drivers and wrappers for scheduled and batch fires |
| `scheduled_prompts/` | The two scheduled-task prompts that operated the collection pipeline (documentation of the procedure — they assume the original desktop layout and are not directly runnable from a clone) |
| `InferenceCarbon_HeavyThinkers.command` | Local launcher for the uncensored heavy-thinker passes (150–240 s timeouts) that the 45 s scheduled sandbox would otherwise censor. Run manually, at the operator's discretion |

## Credentials

No credential appears in any committed file. The engine reads each
provider's API key from a plain-text key file named in `providers.json`
(`OpenAIAPIKey.txt`, `AnthropicAPIKey.txt`, `GeminiAPIKey.txt`,
`MistralDesktopKey.txt`, `DeepSeekAPIKey.txt`), resolved relative to the
parent of the working directory. Key files are gitignored
(`*APIKey*.txt`, `*Key.txt`); create them locally to run the engine.

## Provenance notes

- `BUNDLE_NOTES.md` records the export audit and what was deliberately
  excluded from `engine/` (run logs and spend state; the raw corpus is
  deposited under `../data/`).
- The contact address in the scheduled prompts was normalised to
  methodology@inferencecarbon.ai for publication.
- Comparison pollers for third-party benchmark series are part of the
  operational stack and are not published here; no third-party series
  values appear in this repository.
