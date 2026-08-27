#!/bin/bash
# Run ONE single-model bench invocation per shell call (locked params).
# Preflight self-heals any xlsx corrupted by a prior mid-save timeout.
# timeout 44 keeps us under the 45s shell cap; the bench persists run/progress/spend
# BEFORE the workbook save, so a cut never loses a measurement.
# Args: <provider> <cap>
set +e
prov="$1"; cap="$2"
DIR="/sessions/blissful-admiring-wozniak/mnt/Desktop/InferenceCarbonWorking/owned_benchmark"
cd "$DIR" || exit 9

# --- preflight: quarantine any corrupt owned workbooks so this run starts clean ---
python3 - <<'PY'
import glob, os, openpyxl, time
desk="/sessions/blissful-admiring-wozniak/mnt/Desktop"
q=os.path.join(desk,"_corrupt_quarantine"); os.makedirs(q,exist_ok=True)
for f in glob.glob(os.path.join(desk,"InferenceCarbon_*Owned.xlsx")):
    try:
        openpyxl.load_workbook(f)
    except Exception:
        b=os.path.join(q, os.path.basename(f)+"."+time.strftime("%H%M%S")+".corrupt")
        os.replace(f,b); print("preflight quarantined", os.path.basename(f))
PY

timeout 44 python3 inferencecarbon_bench.py run --provider "$prov" --workload 10k \
    --repeats 1 --max-output 2500 --budget "$cap" --time-budget 3 --request-timeout 40 \
    > results/_iter_${prov}.json 2> results/_iter_${prov}.err
rc=$?
flag=$(python3 - "$prov" <<'PY'
import sys,json
p=sys.argv[1]
try:
    j=json.load(open(f"results/_iter_{p}.json"))
    print("STOP" if (j.get("ALL_DONE") or j.get("stopped_on_budget")) else "GO",
          "pending="+str(j.get("pending")), "cum="+str(j.get("est_cumulative_usd")),
          "budget" if j.get("stopped_on_budget") else ("alldone" if j.get("ALL_DONE") else "more"))
except Exception:
    print("UNK pending=? cum=? parsefail(rc-based)")
PY
)
echo "rc=$rc $flag"
echo "BATCH_END provider=$prov"
