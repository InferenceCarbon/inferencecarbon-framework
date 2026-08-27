---
name: inferencecarbon-reasoning-rider-14d
description: 25-day rider campaign (extended 2026-07-23 to cover James's 8-15 Aug holiday): reasoning-token measurement at short and 1k workloads with the reason prompt class, 3 fires/day across all five providers. Delivers ±10% reasoning-token medians. Ends 17 Aug 2026.
---

You are running one fire of the InferenceCarbon REASONING RIDER campaign (owned benchmark).

END DATE CHECK FIRST: if today's date is after 2026-08-17, do NOT run anything. Instead report that the rider is complete and recommend James disables this task.

Setup: the benchmark lives in the Desktop folder at InferenceCarbonWorking/owned_benchmark (under the session's Desktop mount). All commands run from that directory. If python packages are missing: pip install openai tiktoken openpyxl --break-system-packages

Purpose: measure hidden reasoning tokens per model variant on a difficulty × length grid. Two FIXED reference tasks: prompt-class "reason" (12-element puzzle) and "reason-heavy" (36-element puzzle, 1k workload only). The 10k summarise series is a SEPARATE task — never run the default prompt class here.

RUN TAG — copy the command lines below EXACTLY as written; the $(...) parts are shell substitutions that compute the slot tag at runtime. Do NOT replace them with literal text or invent your own tag. (A hand-written tag caused a silent queue collision that wasted the midday fires of 24-29 July.)

PASS LIST (run every pass, all five providers each, in this order; never skip or substitute a pass even if its queue completes instantly):
  Pass 1: WORKLOAD=short  CLASS=reason
  Pass 2: WORKLOAD=1k     CLASS=reason
  Pass 3: WORKLOAD=1k     CLASS=reason-heavy
  Pass 4 (ONLY if local hour < 10): WORKLOAD=10k  CLASS=reason

For each pass, for each PROVIDER in openai anthropic google mistral deepseek, repeat this command (substituting WORKLOAD, CLASS, PROVIDER) until its JSON shows "ALL_DONE": true OR "stopped_on_budget": true (~60 iteration cap):

timeout 44 python3 inferencecarbon_bench.py run --provider PROVIDER --workload WORKLOAD --prompt-class CLASS --repeats 1 --max-output 2500 --time-budget 3 --request-timeout 34 --run-tag "rider-$(date +%Y%m%d)-$(H=$(date +%H); if [ "$H" -lt 10 ]; then echo am; elif [ "$H" -lt 17 ]; then echo noon; else echo eve; fi)"

Notes:
- Deferral is automatic (censored-skip; applies to both reason classes). Do not probe, reorder, or use --skip-efforts/--models. A shell timeout is routine — re-issue the identical command.
- Budget caps come from providers.json; on stopped_on_budget, note it and move on. Never raise caps or pass --budget.
- Do not modify code, configs, or workbooks by hand.

Report (concise): per pass and provider — completed, pending, censored-skip list, est_cumulative_usd; flag any provider within 15% of its budget_cap in providers.json. Also run: ls results/run_*$(date -d yesterday +%Y%m%d)*_1k.json — if it matches nothing, open the report with "MISSED DAY yesterday — app was likely closed; James should double-click InferenceCarbon_HeavyThinkers.command (its catch-up pass recovers the day)." During 8-15 Aug James is on holiday: keep reports short, no questions.
