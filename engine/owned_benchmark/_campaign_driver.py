#!/usr/bin/env python3
"""Autonomous campaign driver for the scheduled owned-benchmark task.
Invokes inferencecarbon_bench.py once per model (locked params) because the
calling shell caps at 45s; the per-model invocation params are unchanged.
Writes incremental status to results/_driver_master.json so progress can be polled.
"""
import subprocess, json, sys, os, datetime as dt

# Caps read from providers.json budget_cap (single source of truth, 2026-07-23);
# stale hardcoded values (openai 85 etc.) removed — they had drifted from the live caps.
def _caps():
    try:
        p = json.load(open("providers.json"))["providers"]
        return {s: c.get("budget_cap") for s, c in p.items()}
    except Exception:
        return {"openai": 400, "anthropic": 120, "google": 160, "mistral": 120, "deepseek": 80}
CAPS = _caps()
ORDER = ["openai", "anthropic", "google", "mistral", "deepseek"]
STATUS = "results/_driver_master.json"
# IC_WORKLOAD / IC_PROMPT_CLASS let the scheduled task fire rider workloads (short / 1k /
# reason-class) without editing this file; defaults preserve the 10k summarise campaign.
# Thinking variants automatically get +4000 completion-cap headroom above --max-output
# (2026-07-23 recorder revision), so the 2500 here is the VISIBLE-answer cap.
WORKLOAD = os.environ.get("IC_WORKLOAD", "10k")
PROMPT_CLASS = os.environ.get("IC_PROMPT_CLASS", "summarise")
RUN_PARAMS = ["--workload",WORKLOAD,"--repeats","1","--max-output","2500",
              "--prompt-class",PROMPT_CLASS,
              "--time-budget","3","--request-timeout","40"]

master = {"started": dt.datetime.now().isoformat(timespec="seconds"),
          "providers": {}, "current": None, "done": False}

def flush():
    json.dump(master, open(STATUS, "w"), indent=2)

def run_json(args):
    p = subprocess.run(["python3","inferencecarbon_bench.py"]+args,
                       capture_output=True, text=True)
    out = p.stdout.strip()
    try:
        return json.loads(out), p
    except Exception:
        # try to salvage last json object
        i = out.rfind("{")
        if i >= 0:
            try:
                return json.loads(out[i:]), p
            except Exception:
                pass
        return None, p

flush()
for prov in ORDER:
    cap = CAPS[prov]
    pinfo = {"cap": cap, "models_this_fire": 0, "calls": 0,
             "est_cumulative_usd": None, "stopped_on_budget": False,
             "all_done": False, "stall": False, "new_candidates": [],
             "discover": None, "error": None}
    master["providers"][prov] = pinfo
    master["current"] = prov
    flush()

    # 2a discover
    dj, dp = run_json(["discover","--provider",prov])
    if dj is not None:
        pinfo["discover"] = dj
        pinfo["new_candidates"] = dj.get("new_candidates") or dj.get("new") or []
    else:
        pinfo["discover_err"] = (dp.stderr or "")[-300:]
    flush()

    # 2b run loop, one model per invocation
    prev_pending = None
    stall = 0
    for call in range(70):
        j, p = run_json(["run","--provider",prov,"--budget",str(cap)]+RUN_PARAMS)
        if j is None:
            pinfo["error"] = "unparseable run output"
            pinfo["raw_stdout"] = (p.stdout or "")[-400:]
            pinfo["raw_stderr"] = (p.stderr or "")[-400:]
            flush()
            break
        pinfo["calls"] += 1
        pinfo["models_this_fire"] += j.get("models_this_call", 0)
        pinfo["est_cumulative_usd"] = j.get("est_cumulative_usd")
        pinfo["stopped_on_budget"] = bool(j.get("stopped_on_budget"))
        pending = j.get("pending")
        flush()
        if j.get("ALL_DONE"):
            pinfo["all_done"] = True
            break
        if pinfo["stopped_on_budget"]:
            break
        if prev_pending is not None and pending is not None and pending >= prev_pending:
            stall += 1
        else:
            stall = 0
        prev_pending = pending
        if stall >= 3:
            pinfo["stall"] = True
            break
    flush()

master["current"] = None
master["done"] = True
master["finished"] = dt.datetime.now().isoformat(timespec="seconds")
flush()
print("DRIVER_DONE")
