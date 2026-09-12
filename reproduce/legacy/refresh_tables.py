#!/usr/bin/env python3
"""InferenceCarbon — 18 August table refresh (single frozen-corpus pass).

DUFF-DATA POLICY: the corpus is immutable; nothing is deleted. Records that would
distort results are EXCLUDED BY THE FILTERS BELOW, so every exclusion is auditable
and reversible. Run from owned_benchmark/: python3 analysis/refresh_tables.py

KNOWN CELL VERDICTS (2026-08-16): claude-fable-5 at 1k reason/reason-heavy is REFUSED by
the model's safety layer (finish_reason content_filter, 0 content tokens — verified by raw
non-streaming request; the bench records these as 'no tokens' errors). Report the cell as
"unmeasurable: safety-layer refusal", NOT as missing or censored-by-thinking. Its short
cell succeeds intermittently (same filter, marginal) — use the successes, note the rate.

Filters (the 'cleared-down' set):
  F1  mock records: excluded everywhere.
  F2  reasoning (R) cells: prompt_class=='reason' AND prompt_version==2 ONLY.
      v1 hard-task records (23 Jul) confounded task size with prompt length — quarantined.
  F3  R cells require ok, reasoning_tokens present, visible>50; timed-out streams lose
      usage so censoring self-excludes; 'no tokens' cap-exhaustion errors are ok=False.
  F4  TPS series: 10k summarise, o200k basis, ok records only.
  F5  R floors: 10k summarise hidden-token ratios (any version — basis unchanged).
  F6  gpt-4o (retired, n=2) and any variant with <8 TPS records: excluded from tables,
      listed in the report.

BASE POLICY (decided 2026-07-23, James): MEASURED BASIS THROUGHOUT — no variant takes
R=1.0 by definition. Every row, minimal included, carries its own measured multiplier
for the stated task regime; the label 'non-reasoning' is applied only where measurement
supports it (gpt-4o-mini and the gpt-5/5.2/5.4 minimal settings, which measure 1.0).
Rationale: auditability (table never contradicts corpus telemetry) and per-prompt
usefulness (minimal-on-hard-task is priced truthfully; effort-dial savings quoted as
ratios of published rows). R_rel stays a DERIVED ratio for 4.12, never a chain input.

Outputs: analysis/newtables.json (consumed by edit_tables.py), plus an audit report:
  - remaining short-fallback rows (dagger set) — regenerate Table 7 daggers from this;
  - effort-monotonicity warnings per family (1k basis);
  - R_abs (vs 1.0) AND R_rel (vs same-family minimal cell, same basis) per variant —
    the minimal-thinks-on-hard-tasks finding (5.5+ families) makes the base definition
    a paper decision; both are computed so the choice is explicit.
"""
import json, glob, statistics as st, sys
from collections import defaultdict
tps=defaultdict(list); R2=defaultdict(list); FLOOR=defaultdict(list); excluded=defaultdict(int)
for fp in glob.glob('results/run_2*.json'):
    try: d=json.load(open(fp))
    except Exception: continue
    if d.get('mock') or d.get('provider','openai')!='openai': continue           # F1
    wl=d.get('workload')
    for r in d.get('records',[]):
        lab=r.get('label'); pc=r.get('prompt_class','summarise')
        if wl=='10k' and pc=='summarise' and r.get('ok') and r.get('output_tps_o200k'):
            tps[lab].append(r['output_tps_o200k'])                               # F4
            v,h=r.get('output_tokens_o200k'),r.get('reasoning_tokens')
            if v and h is not None and v>50: FLOOR[lab].append((v+h)/v)          # F5
        if pc in ('reason','reason-heavy'):
            # drop truncation artefacts: a record clamped to a tiny max_tokens
            # (the 2026-08-18 HTTP-status-400 clamp bug) hit its cap without
            # finishing — not a real reasoning measurement. Exclude clamp<2000.
            _cl=r.get('max_tokens_clamped')
            if _cl is not None and _cl<2000:
                excluded['truncation_clamp']=excluded.get('truncation_clamp',0)+1; continue
            if r.get('prompt_version')!=2: excluded['v1_reason']+=1; continue    # F2
            v,h=r.get('output_tokens_o200k'),r.get('reasoning_tokens')
            if r.get('ok') and v and h is not None and v>50:
                R2[(lab,wl,pc)].append((v+h)/v)                                     # F3
            else: excluded['censored_or_failed']+=1
med=lambda xs: round(st.median(xs),2) if xs else None
print('exclusions:',dict(excluded))
report={'daggers':[],'monotonicity':[],'thin':[]}
EFF=['minimal','low','medium','high','xhigh']
fams=sorted({l.split(' (')[0] for l in tps if l.startswith('gpt-5')})
out={}
for f in fams+['gpt-4o-mini']:
    prev=0
    for e in (EFF if f!='gpt-4o-mini' else [None]):
        lab=f'{f} ({e})' if e else f
        r1,rs=med(R2.get((lab,'1k','reason'),[])),med(R2.get((lab,'short','reason'),[]))
        rl=med(R2.get((lab,'10k','reason'),[]))
        rh=med(R2.get((lab,'1k','reason-heavy'),[]))
        fl=med(FLOOR.get(lab,[]))
        n=len(tps.get(lab,[]))
        if n<8 and lab!='gpt-4o-mini': report['thin'].append((lab,n))            # F6
        Rc,src=(r1,'1k') if r1 else ((rs,'short*') if rs else (1.0,'MISSING'))
        if src=='short*': report['daggers'].append(lab)
        if e not in (None,'minimal') and r1:
            if r1<prev-0.3: report['monotonicity'].append(f'{f}: falls {prev}->{r1} at {e}')
            prev=r1
        rmin=med(R2.get((f'{f} (minimal)','1k','reason'),[])) or 1.0
        out[lab]=dict(tps_med=med(tps.get(lab,[])), n=n, R_abs=Rc, R_src=src,
                      R_long=rl, R_heavy=rh, R_floor=fl, R_rel=round(Rc/rmin,2) if Rc else None)
json.dump(out, open('analysis/refresh_R.json','w'), indent=1)
print(json.dumps(report, indent=1))
print('wrote analysis/refresh_R.json — feed into newtables build + regenerate daggers from report["daggers"]')
