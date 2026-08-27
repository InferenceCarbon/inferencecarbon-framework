#!/usr/bin/env python3
"""Build every final table value for v3_9x6_1 data-close revision (23 Aug 2026).
Inputs: analysis/refresh_R.json (frozen-corpus medians), analysis/supp_stats.json
(daily-median TPS mean/SD, short/long/heavy R cells with n).
Paper-authoritative constants (v3_9x6_1): anchor 0.577 Wh/400tok -> x2.5;
PUE mult 1.05 central (P 0.95/1.03); PQPC 2.99 for 5.x, 1.00 for 4o-mini
(PQPC rel 0.53/1.48); A 0.71/1.00; LB .353, MB .172 gCO2e/Wh.
R central = 1k hard-task (k=12) median. R_low = floor/central. R_high = short/central.
Heavy (k=36) reported as separate task-demand sensitivity, NOT in bands."""
import json
R=json.load(open('analysis/refresh_R.json'))
S=json.load(open('analysis/supp_stats.json'))
ANCHOR_WH=0.577*(1000/300)     # 1.9233 — corrected basis 24 Aug: per-1,000-OUTPUT tokens (100 in / 300 out anchor query)
PUE=1.05; PQPC5=2.99; LB=0.353; MB=0.172
FIXED={'5x':(0.36,1.52),'4o':(0.67,1.03)}   # per 4.11.8 (rounded as paper states)
ANCH_TPS=R['gpt-4o-mini']['tps_med']        # 78.3, campaign P50

ROSTER=[  # (row label in paper, corpus label, mode label, pqpc_class, note)
 ('gpt-4o-mini','gpt-4o-mini','None','4o',''),
 ('gpt-5 (high)','gpt-5 (high)','High','5x',''),
 ('gpt-5 (xhigh)','gpt-5 (xhigh)','xHigh','5x','NEW ROW - non-monotonic ladder'),
 ('gpt-5.2 (non-reasoning)','gpt-5.2 (minimal)','None','5x',''),
 ('gpt-5.2 (xhigh)','gpt-5.2 (xhigh)','xHigh','5x',''),
 ('gpt-5.4-nano (non-reasoning)','gpt-5.4-nano (minimal)','None','5x',''),
 ('gpt-5.4-nano (medium)','gpt-5.4-nano (medium)','Medium','5x',''),
 ('gpt-5.4-nano (xhigh)','gpt-5.4-nano (xhigh)','xHigh','5x',''),
 ('gpt-5.4-mini (non-reasoning)','gpt-5.4-mini (minimal)','None','5x',''),
 ('gpt-5.4-mini (medium)','gpt-5.4-mini (medium)','Medium','5x',''),
 ('gpt-5.4-mini (xhigh)','gpt-5.4-mini (xhigh)','xHigh','5x',''),
 ('gpt-5.4 (non-reasoning)','gpt-5.4 (minimal)','None','5x',''),
 ('gpt-5.4 (xhigh)','gpt-5.4 (xhigh)','xHigh','5x',''),
 ('gpt-5.5 (minimal)','gpt-5.5 (minimal)','Minimal (measured)','5x',''),
 ('gpt-5.5 (low)','gpt-5.5 (low)','Low','5x',''),
 ('gpt-5.5 (medium)','gpt-5.5 (medium)','Medium','5x',''),
 ('gpt-5.5 (high)','gpt-5.5 (high)','High','5x',''),
 ('gpt-5.5 (xhigh)','gpt-5.5 (xhigh)','xHigh','5x',''),
 ('gpt-5.6-luna (minimal)','gpt-5.6-luna (minimal)','Minimal (measured)','5x',''),
 ('gpt-5.6-luna (low)','gpt-5.6-luna (low)','Low','5x',''),
 ('gpt-5.6-luna (medium)','gpt-5.6-luna (medium)','Medium','5x',''),
 ('gpt-5.6-luna (high)','gpt-5.6-luna (high)','High','5x',''),
 ('gpt-5.6-luna (xhigh)','gpt-5.6-luna (xhigh)','xHigh','5x',''),
 ('gpt-5.6-sol (minimal)','gpt-5.6-sol (minimal)','Minimal (measured)','5x',''),
 ('gpt-5.6-sol (low)','gpt-5.6-sol (low)','Low','5x',''),
 ('gpt-5.6-sol (medium)','gpt-5.6-sol (medium)','Medium','5x',''),
 ('gpt-5.6-sol (high)','gpt-5.6-sol (high)','High','5x',''),
 ('gpt-5.6-sol (xhigh)','gpt-5.6-sol (xhigh)','xHigh','5x',''),
 ('gpt-5.6-sol (max)*','gpt-5.6-sol (xhigh)','Max (floor)','5x','xhigh floor'),
 ('gpt-5.6-terra (minimal)','gpt-5.6-terra (minimal)','Minimal (measured)','5x',''),
 ('gpt-5.6-terra (low)','gpt-5.6-terra (low)','Low','5x',''),
 ('gpt-5.6-terra (medium)','gpt-5.6-terra (medium)','Medium','5x',''),
 ('gpt-5.6-terra (high)','gpt-5.6-terra (high)','High','5x',''),
 ('gpt-5.6-terra (xhigh)','gpt-5.6-terra (xhigh)','xHigh','5x',''),
]
out={'meta':{'anchor_wh_1k':round(ANCHOR_WH,4),'anchor_tps':ANCH_TPS,'PUE':PUE,
 'PQPC_5x':PQPC5,'LB_gpWh':LB,'MB_gpWh':MB,'fixed':FIXED,
 'roster_changes':'gpt-5 (xhigh) added (non-monotonic ladder finding); luna/terra max rows dropped (tier not documented for those variants)'},
 't7':[], 't8':[], 't9':[], 'c_low':[], 'c_high':[], 't1':{}, 'logfactors':[]}

for row,lab,mode,pc,note in ROSTER:
    d=R[lab]; s=S['tps'].get(lab,{}); rc=S['R'].get(lab,{})
    tps=d['tps_med']; adj=ANCH_TPS/tps
    e1=ANCHOR_WH*adj; e2=e1*PUE
    pq=PQPC5 if pc=='5x' else 1.00
    e3=e2*pq
    Rc=d['R_abs']; whF=e3*Rc
    t7=dict(row=row,tps=tps,adj=round(adj,3),tps_wh=round(e1,2),pue=PUE,
            pue_wh=round(e2,2),pqpc=pq,pqpc_wh=round(e3,2),mode=mode,
            R=Rc,wh=round(whF,2),n_tps=d['n'],
            n_R=rc.get('1k_reason',{}).get('n'))
    out['t7'].append(t7)
    lb=whF*LB; mb=whF*MB
    out['t8'].append(dict(row=row,wh=round(whF,2),lb=round(lb,2),mb=round(mb,2)))
    # bands
    m,sd=s.get('tps_daily_mean'),s.get('tps_daily_sd')
    Tl=m/(m+sd); Th=m/(m-sd)
    if Rc==1.0 and mode=='None': Rl=Rh=1.0
    else:
        fl=d.get('R_floor') or 1.0
        sh=rc.get('short_reason',{}).get('med')
        Rl=fl/Rc; Rh=(sh/Rc) if sh else 1.0
    fl_,fh_=FIXED[pc]
    lo=fl_*Tl*Rl; hi=fh_*Th*Rh
    out['t9'].append(dict(row=row,lb_low=round(lb*lo,2),lb_c=round(lb,2),lb_high=round(lb*hi,2),
                          mb_low=round(mb*lo,2),mb_c=round(mb,2),mb_high=round(mb*hi,2)))
    out['c_low'].append(dict(row=row,wh=round(whF,2),tps_m=m,tps_sd=sd,mode=mode,
        fixed=fl_,T=round(Tl,2),R=round(Rl,2),comp=round(lo,2),
        wh_low=round(whF*lo,2),lb=round(lb*lo,2),mb=round(mb*lo,2)))
    out['c_high'].append(dict(row=row,wh=round(whF,2),tps_m=m,tps_sd=sd,mode=mode,
        fixed=fh_,T=round(Th,2),R=round(Rh,2),comp=round(hi,2),
        wh_high=round(whF*hi,2),lb=round(lb*hi,2),mb=round(mb*hi,2)))
    import math
    out['logfactors'].append(dict(row=row,
        A=round(math.log(1.00/0.71),2) if pc=='5x' else round(math.log(1.0/0.71),2),
        PQPC=round(math.log(1.48/0.53),2) if pc=='5x' else 0.0,
        P=round(math.log(1.03/0.95),2),
        T=round(math.log(Th/Tl),2), Rf=round(math.log(Rh/Rl),2) if Rl>0 else None,
        heavy=d.get('R_heavy')))

# Table 1: GPT-5.5 grid (short / 1k / 10k-long / floor) with n
for e in ['minimal','low','medium','high','xhigh']:
    lab=f'gpt-5.5 ({e})'; d=R[lab]; rc=S['R'].get(lab,{})
    out['t1'][e]=dict(short=rc.get('short_reason',{}).get('med'), n_s=rc.get('short_reason',{}).get('n'),
        k1=d['R_abs'], n_1=rc.get('1k_reason',{}).get('n'),
        long=d.get('R_long'), n_l=rc.get('10k_reason',{}).get('n'),
        floor=d.get('R_floor'), heavy=d.get('R_heavy'), n_h=rc.get('1k_reason-heavy',{}).get('n'))
json.dump(out,open('analysis/final_tables.json','w'),indent=1)
# quick display of headline values
print("anchor TPS (4o-mini P50):",ANCH_TPS)
for t in out['t7'][:6]: print(t['row'],t['tps'],'R',t['R'],'->',t['wh'],'Wh')
print('...')
mx=max(out['t8'],key=lambda x:x['lb']); mn=min([x for x in out['t8'] if x['row']!='gpt-4o-mini'],key=lambda x:x['lb'])
print('max LB:',mx['row'],mx['lb'],' min LB(5.x):',mn['row'],mn['lb'],' span',round(mx['lb']/mn['lb'],1),'x')
print('T1 5.5:',json.dumps(out['t1'],indent=0)[:400])
