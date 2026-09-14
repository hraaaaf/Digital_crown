#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / 'audit' / 'out'
front = json.loads((OUTDIR / 'frontend.json').read_text())
back = json.loads((OUTDIR / 'backend.json').read_text())

pairs = [
 ('sna','sna','Steiner SNA'), ('snb','snb','Steiner SNB'), ('anb','anb','Steiner ANB'),
 ('i_na_angle','i_na_angle','Steiner U1/NA angle'), ('i_nb_angle','i_nb_angle','Steiner L1/NB angle'),
 ('fma','fma','Tweed FMA'), ('impa','impa','Tweed IMPA'), ('fmia','fmia','Tweed FMIA'),
 ('u1_frankfort','u1_frankfort','CRANIOM U1/Frankfort'),
 ('impa','l1_downs_craniom','CRANIOM L1/Downs'),
 ('interincisal','interincisal','CRANIOM interincisal'),
 ('eline_ls','eline_ls','Ricketts E-line Ls'), ('eline_li','eline_li','Ricketts E-line Li')
]
rows=[]
for case_id, fvals in front.items():
    bvals=back[case_id]
    for fk,bk,label in pairs:
        fv,bv=fvals.get(fk),bvals.get(bk)
        if fv is None and bv is None:
            status,delta='PASS_UNAVAILABLE',None
        elif fv is None or bv is None:
            status,delta='DIVERGENCE_AVAILABILITY',None
        else:
            delta=round(float(fv)-float(bv),4)
            status='PASS' if abs(delta)<=0.1 else 'DIVERGENCE_VALUE'
        rows.append({'case':case_id,'measure':label,'frontend':fv,'backend':bv,'delta':delta,'status':status})

divergences=[r for r in rows if r['status'].startswith('DIVERGENCE')]
contract_findings=[{
 'measure':'Steiner U1-NA / L1-NB linear mm',
 'status':'FRONTEND_ONLY_NOT_BACKEND_CERTIFIED',
 'evidence':'Frontend uses incisal-edge-to-line distance while backend Steiner V1 intentionally omits the linear metric because the required crown landmark is unavailable.'
}]
report={
 'audit_execution':'PASS',
 'concordance_certified':len(divergences)==0 and not contract_findings,
 'tolerance_after_ui_rounding':0.1,
 'rows':rows,
 'divergences':divergences,
 'contract_findings':contract_findings
}
(OUTDIR/'concordance-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
lines=['# R18 Cephalometric Concordance Audit','',f"- Audit execution: **{report['audit_execution']}**",f"- Concordance certified: **{report['concordance_certified']}**",f"- Divergences: **{len(divergences)}**",'','| Case | Measure | Frontend | Backend | Delta | Status |','|---|---|---:|---:|---:|---|']
for r in divergences:
    lines.append(f"| {r['case']} | {r['measure']} | {r['frontend']} | {r['backend']} | {r['delta']} | {r['status']} |")
lines += ['','## Contract finding','','- Steiner U1-NA / L1-NB linear mm: frontend-only; no certified backend V1 counterpart.','']
(OUTDIR/'concordance-report.md').write_text('\n'.join(lines))
print('\n'.join(lines))
