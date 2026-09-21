# Model retirements and withdrawals — InferenceCarbon owned benchmark
Compiled 7 August 2026 from the results corpus (mock files excluded) and the comparison-tracker workbooks' Run Log/Notes sheets. File names and dates only; no data values.

## Confirmed retirements

### gemini-3-pro-preview (Google API) — the Gemini anchor model
- Reported retired from the Google API on 1 June 2026 (operator's record; pre-campaign).
- Workbook evidence (comparison tracker run log): speed shows N/A from 2026-05-30 onward, logged daily as BLANK/NO_VALUE through 2026-08-07 without interruption.
- Benchmark evidence: every owned-benchmark request 404 "no longer available" — 118/118 failed, first attempt 2026-06-25 (campaign start) to 2026-08-07. The model never returned a successful sample in the owned campaign.

### deepseek-v4-flash-high (comparison tracker slug)
- Disappeared from the comparison tracker's model list on 2026-08-01; logged ERROR "slug not found in API list" daily 2026-08-01 through 2026-08-07 (ongoing at compile date). Source: InferenceCarbon_TokenSec_Daily_DeepSeek.xlsx Run Log. Same slug also showed N/A on 2026-06-01 (pre-API-cutover page era).

### GPT-5 (high), GPT-5.2 non-reasoning, GPT-5.2 xhigh (comparison tracker)
- Marked "(retiring)" in the OpenAI tracker's model labels; last Run Log entries 2026-06-07 (InferenceCarbon_TokenSec_Daily.xlsx). Dropped from tracking thereafter.

## Transient events (NOT retirements)

- gemini-2.5-flash and gemini-2.5-flash-lite: one 404 "no longer available" each from the Google API on 2026-07-09; both recovered and measured successfully through 2026-08-07 (264 and 109 requests, 1 failure each). Treated as a Google-side flap.
- Claude Sonnet 5 (Adaptive Reasoning, Max Effort), slug claude-sonnet-5: absent from the comparison tracker's list on 2026-07-02 only (single ERROR row in its run log); present before and after.

## Endpoint incompatibilities (NOT retirements; excluded from the retirement list)

- gpt-5-codex, gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5.2-codex, gpt-5.3-codex: 404 from 2026-06-25 (campaign start), all requests failed — "only supported in v1/responses / not a chat model". These were never reachable via the chat-completions compat layer the benchmark uses; they are live models, wrong endpoint.

## Notes
- variant_dates.csv in this directory covers every (provider, model_id, effort) in the results corpus, including all-failed rows.
- The 8 mock run files (mock: true, 2026-06-24 test era) are excluded from the CSV.
