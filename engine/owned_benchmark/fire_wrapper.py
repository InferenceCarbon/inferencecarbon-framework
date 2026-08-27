#!/usr/bin/env python3
"""Scheduled-fire wrapper: repeatedly runs the bench for one provider until a
stop condition (ALL_DONE / stopped_on_budget / stall / 70-call ceiling).
Writes progress to results/fire_<provider>_<date>.log and a final status JSON
to results/fire_<provider>_<date>_status.json. Re-issuable safely."""
import json, subprocess, sys, os, datetime

provider = sys.argv[1]
date = datetime.date.today().isoformat()
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
logp = f"results/fire_{provider}_{date}.log"
statusp = f"results/fire_{provider}_{date}_status.json"

def log(msg):
    with open(logp, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")

cmd = [sys.executable, "inferencecarbon_bench.py", "run", "--provider", provider,
       "--workload", "10k", "--repeats", "1", "--max-output", "2500",
       "--time-budget", "3", "--request-timeout", "40"]

pending_history = []
last_json = None
stop_reason = None
calls = 0
while calls < 70:
    calls += 1
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=600).stdout
    except subprocess.TimeoutExpired:
        log(f"call {calls}: subprocess timeout 600s; re-issuing")
        continue
    # last JSON object in output
    j = None
    try:
        start = out.rindex("{")
        # find the outermost JSON: scan back for balanced braces from the last '{' won't work;
        # instead try progressively from each '{' from the end
        for i in range(len(out) - 1, -1, -1):
            if out[i] == "{":
                try:
                    j = json.loads(out[i:])
                    # keep expanding to find outermost
                except Exception:
                    continue
        # better: find first '{' whose parse succeeds scanning from the front of the tail
    except ValueError:
        pass
    # robust approach: try parsing from each '{' from the beginning, keep the last full-line JSON
    j = None
    lines = out.strip().splitlines()
    # try to parse trailing block as JSON
    for k in range(len(lines)):
        blob = "\n".join(lines[k:])
        try:
            j = json.loads(blob)
            break
        except Exception:
            continue
    if j is None:
        log(f"call {calls}: no JSON parsed; tail: {out.strip()[-300:]}")
        continue
    last_json = j
    pend = j.get("pending")
    log(f"call {calls}: pending={pend} ALL_DONE={j.get('ALL_DONE')} budget={j.get('stopped_on_budget')} spend={j.get('est_cumulative_usd')}")
    if j.get("ALL_DONE") is True:
        stop_reason = "ALL_DONE"; break
    if j.get("stopped_on_budget") is True:
        stop_reason = "BUDGET"; break
    pending_history.append(pend)
    if len(pending_history) >= 3 and pending_history[-1] == pending_history[-2] == pending_history[-3] and pending_history[-1] is not None:
        stop_reason = "STALL"; break
if stop_reason is None:
    stop_reason = "CALL_CEILING"
with open(statusp, "w") as f:
    json.dump({"provider": provider, "stop_reason": stop_reason, "calls": calls,
               "final": last_json}, f, indent=2)
log(f"DONE reason={stop_reason} calls={calls}")
