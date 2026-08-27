import subprocess, json, re, sys, os, time
prov, cap = sys.argv[1], sys.argv[2]
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('results', exist_ok=True)
status_path = f'results/agent_status_{prov}.json'
pend_hist = []
last = {}
stop_reason = None
for call in range(1, 71):
    p = subprocess.run(['python3','inferencecarbon_bench.py','run','--provider',prov,
        '--workload','10k','--repeats','1','--max-output','2500','--budget',cap,
        '--time-budget','3','--request-timeout','40'], capture_output=True, text=True)
    out = p.stdout + p.stderr
    with open(f'results/agent_{prov}_run.log','a') as f:
        f.write(f'\n===== call {call} rc={p.returncode} =====\n'+out)
    m = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', out, re.S)
    d = {}
    if m:
        for cand in reversed(m):
            try:
                d = json.loads(cand); break
            except Exception: continue
    last = d
    json.dump({'call':call,'last':d,'ts':time.time()}, open(status_path,'w'))
    if d.get('ALL_DONE') is True:
        stop_reason='ALL_DONE'; break
    if d.get('stopped_on_budget') is True:
        stop_reason='BUDGET'; break
    pend = d.get('pending')
    if isinstance(pend, list): pend = len(pend)
    pend_hist.append(pend)
    if len(pend_hist) >= 3 and pend_hist[-1] == pend_hist[-2] == pend_hist[-3] and pend_hist[-1] is not None:
        stop_reason='STALL'; break
else:
    stop_reason='CALL_CEILING'
json.dump({'done':True,'stop_reason':stop_reason,'calls':call,'last':last}, open(status_path,'w'))
print(stop_reason)
