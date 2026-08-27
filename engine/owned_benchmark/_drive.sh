#!/bin/bash
# usage: _drive.sh PROVIDER CAP
P="$1"; CAP="$2"
DIR="/sessions/zen-funny-bell/mnt/Desktop/InferenceCarbonWorking/owned_benchmark"
cd "$DIR"
rm -f _runlogs/flag_$P
timeout 43 bash -c '
P="'"$P"'"; CAP="'"$CAP"'"
while true; do
  timeout 40 python3 inferencecarbon_bench.py run --provider "$P" --workload 10k --repeats 1 --max-output 2500 --budget "$CAP" --time-budget 3 --request-timeout 40 > _runlogs/last_$P.json 2>&1
  if grep -q "\"ALL_DONE\": true" _runlogs/last_$P.json; then echo ALL_DONE > _runlogs/flag_$P; break; fi
  if grep -q "\"stopped_on_budget\": true" _runlogs/last_$P.json; then echo BUDGET > _runlogs/flag_$P; break; fi
done
'
echo "outer_exit=$? flag=$(cat _runlogs/flag_$P 2>/dev/null || echo none)"
