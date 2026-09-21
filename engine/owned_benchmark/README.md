# InferenceCarbon — Owned Throughput Benchmark (OpenAI GPT)

A reproducible source of LLM throughput measurements, owned outright. It measures the
models ourselves against the provider APIs, using our own prompts and the open-source
`o200k_base` tokenizer, so **the resulting data is ours** — no redistribution or
competitive-use restriction, and reproducible by a reviewer.

It captures the throughput metrics public trackers publish **plus** the data the
InferenceCarbon energy model needs and they do not (native token counts, reasoning
tokens, a clean TTFT/decode split).

## What it does
- `discover` — reads OpenAI `/v1/models`, keeps GPT chat models, expands each reasoning
  family (gpt-5+) across the effort ladder `minimal/low/medium/high/xhigh`, maps the
  effort variants onto `reasoning_effort` parameters, and writes `manifest.json`.
  **New-model detection** is built in: it reports models added/removed since the last manifest.
- `run` — for each manifest entry, sends streamed requests and records the full per-request
  vector; summarizes as P50 across repeats; writes JSON + an Excel workbook.

## Alignment with standard throughput-benchmark methodology
| Common practice | Here |
|---|---|
| Workloads by input length (1k / **10k default** / 100k), min answer tokens | `--workload 1k\|10k\|100k` (same input/min-output targets) |
| `temperature 0, top_p 1` | Same (auto-dropped for reasoning models that reject them) |
| Streaming; TTFT = first token, TTFAT = first answer token | Same |
| Output speed measured after the first token | Same (`output_tps_*` over `t_end − TTFT`) |
| Token counts standardized in `o200k_base` | Same (`*_o200k`), **and** native counts kept |
| P50 representation | P50 across repeats (persist runs to span a rolling window) |
| Official OpenAI library | Same |

## Deliberate deviations (and why)
- **Native token counts kept alongside o200k_base.** Energy is consumed per *native* token
  the hardware emits; o200k normalization is a comparability choice, not an energy
  denominator. We record both.
- **Reasoning tokens captured** from `usage.completion_tokens_details` — needed for the
  `e_reasoning × hidden_tokens` term; public trackers do not expose per-call reasoning counts.
- **Our own prompts**, generated to the token budget, so the measurements are ours to publish.
- **Concurrency.** Default is single-stream (the usual headline figure). Note that single-stream is
  latency-optimized and *not* energy-representative; a higher-concurrency scenario is the
  recommended next addition.

## Mapping to the energy model
`E_request = E_fixed + e_prefill·input_tokens + e_decode·output_tokens + e_reasoning·hidden_tokens + E_tools + E_idle`

| Term | Field(s) captured | Note |
|---|---|---|
| e_prefill · input_tokens | `input_tokens_o200k`, `p50_ttft_s` | TTFT vs input-length slope isolates prefill |
| e_decode · output_tokens | `output_tokens_native`, `output_tps_native`, `itl_ms` | post-first-token rate isolates decode |
| e_reasoning · hidden_tokens | `reasoning_tokens` | from provider usage; 0 for non-reasoning |
| E_fixed / E_idle | `e2e_s`, fixed-latency intercept (via length sweep) | energy coefficients still need hardware data |
| E_tools | (not exercised) | add only for agentic/tool workloads |

The harness supplies the **token + timing structure**; the energy *coefficients*
(`e_*`, `E_fixed`, `E_idle`) still come from hardware data / your anchor calibration —
a hosted API cannot return joules.

## Usage
```
# 1. put a funded key here:  ../OpenAIAPIKey.txt   (sibling of this folder)
# 2. build / refresh the model list (also detects new models):
python3 inferencecarbon_bench.py discover

# 3. cheap smoke test (one model, small workload):
python3 inferencecarbon_bench.py run --models gpt-4o-mini --workload 1k --repeats 2

# 4. a reasoning model, with a cost/time cap:
python3 inferencecarbon_bench.py run --models gpt-5-nano --workload 1k --repeats 2

# 5. full default run (10k input, 8 repeats) — COSTS REAL TOKENS:
python3 inferencecarbon_bench.py run --workload 10k --repeats 8

# pipeline check without spending anything:
python3 inferencecarbon_bench.py run --mock --workload 1k --limit 6 --repeats 3
```
Flags: `--models a,b` (filter), `--limit N`, `--max-output N` (cap completion tokens), `--mock`.

## Outputs
- `results/run_<ts>_<workload>.json` — every per-request record plus the P50 summary, one file per run. These accumulate into the measurement corpus; the frozen archive behind the paper is `data/InferenceCarbon_corpus_frozen_20260822.zip`.
- A daily summary workbook alongside the results directory — `Latest` sheet (P50 vector per model) and `Run Log`. Its path is set by the `workbook` field in `providers.json`.

## Cost & runtime
Each request spends real tokens. Cost scales with workload size × repeats × models, and
reasoning effort drives it hard (high/xhigh emit thousands of reasoning tokens). Start
small; cap with `--max-output`; consider running reasoning variants less often. A full
10k×8-repeat sweep over all 66 entries is the expensive end — budget before running it.

## Caveats
- **Region/TTFT.** TTFT includes network latency, so it is vantage-dependent. Run from
  a representative, consistent location and disclose it; steady-state throughput is the
  location-robust metric.
- **Reasoning TTFT.** If a provider does not stream reasoning tokens, TTFT collapses onto the
  first answer token and "thinking time" shows up as a long TTFT — give reasoning runs ample
  `--max-output` so they actually produce an answer.
- **Quantization** is provider-controlled and undisclosed; it confounds both speed and energy.
- **Not legal advice.** Methodology is grounded in standard practice; data and prompts are ours.

## Dependencies
`pip install openai tiktoken openpyxl`

## Recorder revision — 23 July 2026
Implements the data-collection changes from the comparison review.
- **Tier 1 (fixes):** reasoning-token capture hardened across all usage-field shapes
  (Gemini `thoughtsTokenCount` variants, flattened `reasoning_tokens`, total-minus-parts
  and native-minus-o200k derivations, with provenance in `reasoning_source`); raw usage
  payloads recorded (`usage_raw`) and missing payloads flagged (`usage_missing` — the
  opus-4-6/sonnet-4-6 gap); Magistral think-tags split out of the visible stream (TTFAT
  corrected, thinking counted as reasoning — pre-revision magistral-small visible tok/s
  is inflated); resolved model ids pinned behind '-latest' aliases; default-thinking
  models now get reasoning headroom above the visible cap (root cause of the truncated
  gemini-3.5/3.6-flash answers); `min_answer_met` QC flag.
- **Tier 2 (protocol):** 'short' (100/300) workload added — with '1k' this matches the
  framework paper's Table-1 short/medium query lengths; `--prompt-class reason` adds a
  thinking-eliciting puzzle class; `--reasoning-headroom` (default 4000) raises the cap
  for thinking variants; Anthropic effort ladder implemented via thinking budgets
  ('minimal' = off = R=1 baseline); deepseek-chat tracked as candidate true baseline;
  new `probe` subcommand verifies effort binding for pennies BEFORE a ladder is enabled.
- **Tier 3 (sampling):** per-model `repeats` (gemini-2.5-flash, the Gemini-paper anchor,
  now 5/fire); `--jitter` de-synchronizes fire times; daily sheets pool ONLY the 10k
  summarise series — riders stay in the JSON corpus.
- **Before the rider campaign:** run the probes in the tracked-file comments (Anthropic
  thinking, Gemini reasoning_effort, deepseek-chat baseline). Run reasoning riders
  locally with `--request-timeout 120` — the scheduled task's 40 s timeout censors
  exactly the heavy thinkers. Keep the scheduled comparison collection running in parallel as
  the independent cross-check.
