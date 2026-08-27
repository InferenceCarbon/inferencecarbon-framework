#!/bin/bash
cd "$(dirname "$0")"
for PC in "anthropic 130" "deepseek 90" "mistral 130" "google 200" "openai 300"; do
  set -- $PC
  P=$1; C=$2
  python3 inferencecarbon_bench.py discover --provider $P > results/discover_$P.json 2>&1
  python3 campaign_wrapper.py $P $C >> results/driver_log.txt 2>&1
done
echo "DRIVER_ALL_DONE" >> results/driver_log.txt
