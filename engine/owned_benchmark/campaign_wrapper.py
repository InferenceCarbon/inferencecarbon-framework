import json, subprocess, sys, os, re, time
prov, cap = sys.argv[1], sys.argv[2]
d = os.path.dirname(os.path.abspath(__file__))
log = os.path.join(d, f"results/campaign_log_{prov}.jsonl")
cmd = ["python3", os.path.join(d,"inferencecarbon_bench.py"), "run", "--provider", prov,
       "--workload","10k","--repeats","1","--max-output","2500","--budget",cap,
       "--time-budget","3","--request-timeout","40"]
pending_hist=[]
final={}
for i in range(70):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=d)
        out = r.stdout
    except subprocess.TimeoutExpired:
        with open(log,"a") as f: f.write(json.dumps({"call":i,"error":"call_timeout"})+"\n")
        continue
    m = re.search(r'\{.*\}', out, re.S)
    j = {}
    if m:
        try: j = json.loads(m.group(0))
        except Exception: j={"raw": out[-2000:]}
    j["_call"]=i
    with open(log,"a") as f: f.write(json.dumps(j)+"\n")
    final=j
    if j.get("ALL_DONE") is True:
        j["_stop"]="ALL_DONE"; break
    if j.get("stopped_on_budget") is True:
        j["_stop"]="BUDGET"; break
    p=j.get("pending")
    pending_hist.append(p)
    if len(pending_hist)>=3 and pending_hist[-1]==pending_hist[-2]==pending_hist[-3] and p is not None:
        j["_stop"]="STALL"; break
else:
    final["_stop"]="CALL_CEILING"
final["_provider"]=prov
with open(os.path.join(d,f"results/campaign_final_{prov}.json"),"w") as f:
    json.dump(final,f,indent=1)
print("WRAPPER_DONE", prov, final.get("_stop"))
