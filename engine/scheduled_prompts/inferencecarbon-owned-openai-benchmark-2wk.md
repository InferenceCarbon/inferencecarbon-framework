---
name: inferencecarbon-owned-openai-benchmark-2wk
description: Owned throughput benchmark, multi-provider: OpenAI, Anthropic, Google/Gemini, Mistral, DeepSeek. Loops over providers with a key present, 2x/day, per-provider budget caps, one daily workbook per provider. Runs until James says stop.
---

Check that Gemini 3.6 Flash and 3.5 Flash Lite are included in figures.

Owned throughput-benchmark campaign (InferenceCarbon), MULTI-PROVIDER. Run silently and autonomously; no clarifying questions. The campaign has NO end date — keep running until James explicitly says to stop. (The original 4-week end-date guard was removed on 2026-07-23 at James's request.)

STEP 1 — LOCATE + DETECT PROVIDERS (one bash call).
   BASE=$(ls -d /sessions /*/mnt/Desktop 2>/dev/null | head -1)
   DIR="$BASE/InferenceCarbonWorking/owned_benchmark"
Confirm "$DIR/inferencecarbon_bench.py" and "$DIR/providers.json" exist. Install deps quietly:
   pip install --break-system-packages -q openai tiktoken openpyxl
List providers whose key file is present (these run this fire):
   cd "$DIR" && python3 -c "import json,os; w=os.path.dirname(os.getcwd()); p=json.load(open('providers.json'))['providers']; print([s for s,c in p.items() if os.path.exists(os.path.join(w,c['key_file']))])"
Recompute/cd into $DIR for every later bash call (bash calls are independent).

STEP 2 — FOR EACH PROVIDER with a key. PROVIDER ORDER AND SEQUENCING (changed 2026-07-23 after the fragmented 23 July run):
   - Run providers STRICTLY ONE AT A TIME, in this order: anthropic, deepseek, mistral, google, openai. OpenAI goes LAST because it has by far the most variants (~46) and can absorb ~2 hours; the four smaller labs together need only ~15 minutes, so if the session is ever cut short they are complete and only OpenAI is partial.
   - NEVER interleave providers. Finish the current provider COMPLETELY (see stop conditions below) before touching the next.
   - NEVER write the final report while any provider still has pending models and none of its stop conditions has been met. An interrupted, slow, or errored bash call is NOT a stop condition — re-issue the identical call and continue.
  2a. DISCOVER (one call): `cd "$DIR" && python3 inferencecarbon_bench.py discover --provider <P>`. OpenAI auto-adds new major families; the others use locked, hand-curated lists and only REPORT new ids as "new_candidates" (note them; they are not auto-added).
  2b. RUN, ONE MODEL PER CALL until done. Per-provider hard budget cap (USD, cumulative over the campaign): openai=300, anthropic=130, google=200, mistral=130, deepseek=90. (Caps set 2026-07-27 at James's request: current spend + ~30 days at observed burn, one consistent cap per provider in both this task and providers.json. OpenAI history: 85 → 150 on 2026-07-20, → 300 on 2026-07-27. Revisit ~2026-08-27. The caps no longer guarantee a margin below account credit, so requests may fail if account credit runs out — report failures, do not retry indefinitely.) Repeatedly call (each its own bash call):
     cd "$DIR" && python3 inferencecarbon_bench.py run --provider <P> --workload 10k --repeats 1 --max-output 2500 --budget <CAP> --time-budget 3 --request-timeout 40
  Keep calling (identical params) until one of exactly THREE stop conditions: (i) the printed JSON shows "ALL_DONE": true; (ii) "stopped_on_budget": true (stop, note prominently); (iii) STALL — "pending" does not fall across THREE consecutive calls (stop, report the stall). Safety ceiling: at most 70 calls per provider. No other reason justifies stopping a provider early.
  2c. VALIDITY — a throughput of 0 tok/s is an invalid sample, never a real value. If any model's latest measurement this fire is 0 (or today's row in the daily workbook shows 0), re-measure that model once more before declaring the provider done; if it is still 0, leave the cell for the engine to handle and flag the model in the report. Never treat 0 as satisfying "measured".
  2d. COMPLETION CHECK — after a provider's stop condition is reached, open its daily summary workbook (~/Desktop/InferenceCarbon_TokenSec_Daily_Owned.xlsx for OpenAI; ..._Anthropic_/_Gemini_/_Mistral_/_DeepSeek_Owned.xlsx) with openpyxl and verify today's date row has a numeric, non-zero value in every model column. List any blank or zero columns in the final report with the reason (budget / stall / API error). Do not skip this check.

STEP 3 — BUDGET ALERT (James wants to know if any budget is running low). For each provider, take est_cumulative_usd from its final printed JSON and compute pct = est_cumulative / CAP. Build an ALERTS list of any provider where pct >= 0.80 OR stopped_on_budget is true. If ALERTS is non-empty:
   - Create a Gmail draft (tool create_draft) to methodology@inferencecarbon.ai, subject "[InferenceCarbon] Budget alert — <date>", body listing each flagged provider, its est. spend vs cap, and whether it stopped. (Draft only — do not send.)
   - Begin the chat report with a bold line: "BUDGET ALERT: <providers> at/over 80% of cap."
If no provider is flagged, skip the draft.

STEP 4 — REPORT (post to chat, one short block PER PROVIDER, plus the alert line from STEP 3 if any). "variants measured" means measurements taken THIS FIRE, not cumulative campaign counts:
   InferenceCarbon owned benchmark — <provider> <tag>:
     variants measured this fire: <count>
     today's daily row: <complete / N of M filled — list the gaps and reasons from STEP 2d>
     est. cumulative spend: $<est_cumulative_usd> of $<CAP> cap (<pct>%)
     budget stopped: yes/no
     new candidate models: <new_candidates list or none>

NOTES ON DESIGN (do not change without being asked):
   - Providers, OpenAI-compatible base URLs, key filenames, model filters and output workbooks live in providers.json. A provider runs ONLY if its key file is in the InferenceCarbonWorking folder. Keys present: OpenAI, Anthropic (AnthropicAPIKey.txt), Google/Gemini (GeminiAPIKey.txt), Mistral (MistralDesktopKey.txt), DeepSeek (DeepSeekAPIKey.txt).
   - Budgets are PER-PROVIDER HARD caps, saved after every request in results/spend_state_<provider>.json; a provider stops collecting at its cap and CANNOT overspend it. Since 2026-07-27 the same cap applies in providers.json (heavy-thinkers script) and here — keep the two aligned if either changes.
   - Calibrated 2026-06-25: all five stream + report usage via the compat layer. OpenAI = curated, reasoning across minimal/low/medium/high/xhigh. DeepSeek V4 honours reasoning_effort (broken out: non-reasoning + high). Anthropic/Google/Mistral collect ONE default variant per model (efforts:[], locked); reasoning breakouts for Anthropic/Google are a known TODO.
   - high/xhigh (OpenAI) requests usually hit the 40s cap and still yield a valid partial throughput sample (o200k-based). max-output 2500 bounds every request's cost.
   - OUTPUTS per provider: results/run_*.json (canonical per-measurement record, provider-tagged), an engine workbook (Latest + Run Log), and the standalone daily summary in daily-tracker format — ~/Desktop/InferenceCarbon_TokenSec_Daily_Owned.xlsx (OpenAI) and ..._Anthropic_/_Gemini_/_Mistral_/_DeepSeek_Owned.xlsx.
   - HISTORY: the 23 July morning fire fragmented because the agent interleaved providers, stalled ~2 h mid-run, then reported instead of resuming. The sequencing rules in STEP 2 exist to prevent a recurrence.
