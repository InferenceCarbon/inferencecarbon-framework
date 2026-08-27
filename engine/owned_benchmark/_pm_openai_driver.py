#!/usr/bin/env python3
"""One-off driver for the 2026-07-23 PM fire, openai only.
Exists because the calling shell caps at 45s and high/xhigh requests run ~40s;
invokes inferencecarbon_bench.py once per model in-process (identical locked
params, bench applies budget_cap from providers.json automatically) and writes
poll-able status to results/_pm_openai_status.json.
Stop conditions per SKILL: ALL_DONE / stopped_on_budget / stall (pending flat
across 3 consecutive calls) / 70-call safety ceiling.
"""
import subprocess, json, datetime as dt

STATUS = "results/_pm_openai_status.json"
PARAMS = ["run", "--provider", "openai", "--workload", "10k", "--repeats", "1",
          "--max-output", "2500", "--time-budget", "3", "--request-timeout", "40"]

st = {"started": dt.datetime.now().isoformat(timespec="seconds"),
      "calls": 0, "models_this_fire": 0, "pending": None,
      "est_cumulative_usd": None, "all_done": False,
      "stopped_on_budget": False, "stall": False, "done": False, "error": None}

def flush():
    json.dump(st, open(STATUS, "w"), indent=2)

flush()
prev_pending, stall = None, 0
for _ in range(70):
    p = subprocess.run(["python3", "inferencecarbon_bench.py"] + PARAMS,
                       capture_output=True, text=True)
    out = p.stdout.strip()
    i = out.rfind("{")
    try:
        j = json.loads(out[i:])
    except Exception:
        st["error"] = "unparseable output"
        st["raw_tail"] = (out or p.stderr or "")[-400:]
        break
    st["calls"] += 1
    st["models_this_fire"] += j.get("models_this_call", 0)
    st["pending"] = j.get("pending")
    st["est_cumulative_usd"] = j.get("est_cumulative_usd")
    st["stopped_on_budget"] = bool(j.get("stopped_on_budget"))
    st["all_done"] = bool(j.get("ALL_DONE"))
    flush()
    if st["all_done"] or st["stopped_on_budget"]:
        break
    pending = j.get("pending")
    if prev_pending is not None and pending is not None and pending >= prev_pending:
        stall += 1
    else:
        stall = 0
    prev_pending = pending
    if stall >= 3:
        st["stall"] = True
        break

st["done"] = True
st["finished"] = dt.datetime.now().isoformat(timespec="seconds")
flush()
print("PM_OPENAI_DRIVER_DONE")
