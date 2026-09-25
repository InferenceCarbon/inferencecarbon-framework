#!/bin/bash
DIR="$1"; cd "$DIR"
declare -A CAP=( [openai]=400 [anthropic]=120 [google]=160 [mistral]=120 [deepseek]=80 )  # 2026-07-23: aligned with providers.json budget_cap
SD=/tmp/icstate; mkdir -p "$SD"
run_one(){
  local P="$1"
  [ -f "$SD/done_$P" ] && return
  local OUT
  OUT=$(timeout 38 python3 inferencecarbon_bench.py run --provider "$P" --workload 10k --repeats 1 --max-output 2500 --budget "${CAP[$P]}" --time-budget 3 --request-timeout 30 2>&1)
  local ST=$(echo "$OUT" | grep -E '"(pending|ALL_DONE|stopped_on_budget|est_cumulative)"' | tr '\n' ' ')
  echo "$P: $ST"
  echo "$ST" | grep -q '"ALL_DONE": true' && { echo "$ST" > "$SD/done_$P"; echo "  -> $P DONE_ALL"; }
  echo "$ST" | grep -q '"stopped_on_budget": true' && { echo "$ST" > "$SD/done_$P"; echo "  -> $P DONE_BUDGET"; }
}
for P in openai anthropic google mistral deepseek; do run_one "$P" & done
wait
