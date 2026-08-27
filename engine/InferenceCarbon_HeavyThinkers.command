#!/bin/bash
# InferenceCarbon — uncensored heavy-thinker measurement (double-click to run).
#
# WHY THIS EXISTS: the scheduled benchmark task runs inside a shell capped at 45 s per
# call, so its 40 s request timeout censors exactly the variants that think longest
# (their E2E pins at ~40.0 s in the engine workbooks). This script runs OUTSIDE that
# constraint, on this Mac, with a 150 s per-request timeout, and ONLY for the variants
# whose corpus history shows >=50% timed-out requests (--timeout-capped-only).
#
# WHAT IT RUNS: for each provider — (a) the 10k summarise workload (uncensored TPS and
# long-query reasoning), then (b) the short reason-class workload (uncensored short-query
# reasoning multipliers). 2 repeats per variant per pass; run it on several different
# days to accumulate samples (results append to the same corpus; budget caps from
# providers.json apply automatically). Expect roughly 45-60 minutes per full run.
#
# Safe to interrupt: every completed request is already saved before the next starts.

set -u
DIR="$HOME/Desktop/InferenceCarbonWorking/owned_benchmark"
cd "$DIR" || { echo "Cannot find $DIR"; exit 1; }

echo "== Checking python packages (first run may install to --user) =="
python3 -c "import openai, tiktoken, openpyxl" 2>/dev/null || \
  pip3 install --user -q openai tiktoken openpyxl || \
  { echo "Package install failed — run: pip3 install --user openai tiktoken openpyxl"; exit 1; }

TS=$(date +%Y%m%d-%H%M)
for P in openai anthropic google mistral deepseek; do
  echo ""
  echo "==== $P — 10k summarise, uncensored (timeout 150s) ===="
  caffeinate -i python3 inferencecarbon_bench.py run --provider "$P" --workload 10k \
      --timeout-capped-only --repeats 2 --max-output 2500 \
      --request-timeout 150 --run-tag "heavy-$TS"
  echo ""
  echo "==== $P — short reason-class, uncensored (timeout 150s) ===="
  caffeinate -i python3 inferencecarbon_bench.py run --provider "$P" --workload short --prompt-class reason \
      --timeout-capped-only --repeats 2 --max-output 2500 \
      --request-timeout 150 --run-tag "heavy-$TS"
done

# Reason-class passes for the variants the RIDER has deferred (censored in the 45s
# sandbox: a timed-out stream loses its usage payload = no reasoning-token count).
# The rider writes results/deferred_openai_<workload>_reason.json automatically; this
# reads those lists so new deferrals are picked up without editing this script. These
# cells carry the papers' largest multipliers and ONLY accumulate samples here:
# 2 repeats per variant per run — please run on at least FOUR separate days.
for W in short 1k; do
  DEF=$(python3 -c "
import json,glob
ls=set()
for f in glob.glob('results/deferred_openai_${W}_reason.json'):
    try: ls|=set(json.load(open(f)))
    except Exception: pass
print(','.join(sorted(ls)))")
  if [ -n "$DEF" ]; then
    echo ""
    echo "==== openai — $W reason-class, rider-deferred variants, uncensored ===="
    echo "     [$DEF]"
    # headroom 16000: the 23 Jul run showed gpt-5 medium+ at 1k exhausts the default
    # 6,500-token cap on thinking alone and returns "no tokens" — not a timeout.
    caffeinate -i python3 inferencecarbon_bench.py run --provider openai --workload "$W" --prompt-class reason \
        --models "$DEF" --repeats 2 --max-output 2500 --reasoning-headroom 16000 \
        --request-timeout 240 --run-tag "heavy-$TS"
  else
    echo ""
    echo "==== openai — $W reason-class: no rider-deferred variants recorded yet — skipping ===="
  fi
done

# RIDER CATCH-UP (added 30 Jul): the scheduled rider only fires while the Claude app is
# open — 29 July collected nothing. This pass makes every click also count as one full
# rider fire (short + 1k, all providers, uncensored), so missed scheduled days are
# recoverable locally. ~20-30 min extra.
TS2=$(date +%Y%m%d-%H%M)
for W in short 1k; do
  for P in openai anthropic google mistral deepseek; do
    echo ""
    echo "==== catch-up: $P — $W reason-class ===="
    caffeinate -i python3 inferencecarbon_bench.py run --provider "$P" --workload "$W" --prompt-class reason \
        --repeats 1 --max-output 2500 --request-timeout 240 --run-tag "catchup-$TS2"
  done
done

echo ""
echo "==== Done. Corpus updated; workbooks rebuilt. This window can be closed. ===="
read -p "Press return to close."
