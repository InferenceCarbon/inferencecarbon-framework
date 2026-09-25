#!/bin/bash
# Loop-driver: one provider, repeated identical run calls until stop condition.
P=$1; CAP=$2; LOG="results/driver_${P}_$(date +%Y%m%d).log"
cd "$(dirname "$0")"
prev1=-1; prev2=-2; calls=0
echo "=== driver start $P $(date) ===" >> "$LOG"
while [ $calls -lt 70 ]; do
  calls=$((calls+1))
  OUT=$(python3 inferencecarbon_bench.py run --provider "$P" --workload 10k --repeats 1 --max-output 2500 --budget "$CAP" --time-budget 3 --request-timeout 40 2>&1)
  echo "--- call $calls $(date) ---" >> "$LOG"
  echo "$OUT" >> "$LOG"
  J=$(echo "$OUT" | python3 -c "import sys,json;
txt=sys.stdin.read(); i=txt.rfind('{\"tag\"');
print(txt[i:] if i>=0 else '{}')" 2>/dev/null)
  DONE=$(echo "$J" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ALL_DONE'), d.get('stopped_on_budget'), d.get('pending'))" 2>/dev/null)
  set -- $DONE
  ad=$1; sb=$2; pend=$3
  if [ "$ad" = "True" ]; then echo "STOP:ALL_DONE calls=$calls" >> "$LOG"; break; fi
  if [ "$sb" = "True" ]; then echo "STOP:BUDGET calls=$calls" >> "$LOG"; break; fi
  if [ -n "$pend" ] && [ "$pend" = "$prev1" ] && [ "$pend" = "$prev2" ]; then echo "STOP:STALL pending=$pend calls=$calls" >> "$LOG"; break; fi
  prev2=$prev1; prev1=$pend
done
[ $calls -ge 70 ] && echo "STOP:CALL_CEILING calls=$calls" >> "$LOG"
echo "=== driver end $P $(date) ===" >> "$LOG"
