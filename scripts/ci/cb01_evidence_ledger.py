"""CB-01 cross-gate evidence ledger; never upgrades human E2E from technical checks."""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('DIGITALCROWN_ISOLATED_RUNTIME') != '1':
    raise SystemExit('REFUSED: isolated GitHub Actions only')
head = os.environ.get('CB01_SOURCE_HEAD','')
if len(head)!=40 or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=head:
    raise SystemExit('REFUSED: evidence not on exact checked-out HEAD')
root = Path('artifacts/cb01-associate-sidecar')

def load(name):
    p=root/name
    if not p.is_file():
        raise SystemExit(f'FAIL: missing required proof {name}')
    j=json.loads(p.read_text(encoding='utf-8'))
    if j.get('sourceHead',j.get('exactHead'))!=head:
        raise SystemExit(f'FAIL: foreign source SHA {name}')
    return j

http=load('http-pg-s07-s09-evidence.json')
cipher=load('sqlcipher-s07-s09-evidence.json')
matrix=load('s01-s12-synthetic-matrix.json')
sidecar=load('summary.json')
# Real browser -> real FastAPI, separate synthetic staff role/tenant identities.
# No mocked HTTP result is admissible for S05/S06 here.
role_evidence=sidecar.get('realRoleBrowserEvidence')
if not isinstance(role_evidence,list) or len(role_evidence)!=2:
    raise SystemExit('FAIL: S05/S06 integrated browser evidence missing')
by_role={item.get('scenario'):item for item in role_evidence}
expected_roles={
    'S05':('PASS_HTTP_200_NON_EXECUTABLE_PROPOSAL',200),
    'S06':('PASS_HTTP_403_VISIBLE_DENIAL',403),
}
if set(by_role)!=set(expected_roles):
    raise SystemExit('FAIL: S05/S06 browser role matrix incomplete or duplicated')
for role,(status,expected_http_status) in expected_roles.items():
    entry=by_role[role]
    if (entry.get('source')!='MAINLAYOUT_CROWNBOTCHAT_REAL_FASTAPI_SYNTHETIC_DB'
        or entry.get('status')!=status
        or not isinstance(entry.get('httpStatuses'),list)
        or not entry['httpStatuses']
        or any(code!=expected_http_status for code in entry['httpStatuses'])
        or entry.get('clinicalWrites')!=0 or entry.get('pageErrors')!=0
        or entry.get('humanCabinetE2E')!='NOT_RUN'
        or not (root/entry.get('screenshot','')).is_file()):
        raise SystemExit('FAIL: S05/S06 integrated browser role proof invalid '+role)

if (http['S07']['status']!='PASS_HTTP_ROUTER_PG_INTEGRATION'
    or http['S09']['status']!='PASS_HTTP_BOT_EXECUTE_ABA_INTEGRATION'
    or http['S10']['status']!='PASS_REAL_409_RESPONSE_CONTRACT'
    or http['S12']['status']!='PASS_HTTP_READ_ACK_PERSISTENCE'
    or cipher['S07']['status']!='PASS_SQLCIPHER_PRIMITIVES_ONLY'
    or cipher['S09']['status']!='PASS_SQLCIPHER_REVISION_PRIMITIVE_ONLY'
    or http['S12']['missingHttpStatus']!=404
    or http['S12']['otherTenantHttpStatus']!=404
    or http['S12']['authorizedAckStatus']!=200):
    raise SystemExit('FAIL: expected technical S07/S09/S10/S12 proof absent')
cases=matrix.get('scenarios')
if isinstance(cases,dict):
    by_id=cases
elif isinstance(cases,list):
    by_id={c.get('id'):c for c in cases}
else:
    raise SystemExit('FAIL: unsupported matrix cases schema')
for scenario in ('S07','S09','S10','S12'):
    if by_id.get(scenario,{}).get('humanE2E')!='NOT_RUN':
        raise SystemExit(f'FAIL: {scenario} human E2E unexpectedly promoted')
if matrix.get('counts',{}).get('humanE2EValidated')!=0:
    raise SystemExit('FAIL: artificial human certification')

scenarios={
 'S05':{'browser':'PASS_REAL_FASTAPI_RECEPTION_PROPOSAL_ONLY',
        'ui':'REAL_MAINLAYOUT_SYNTHETIC_STAFF_NOT_HUMAN'},
 'S06':{'browser':'PASS_REAL_FASTAPI_RECEPTION_403_VISIBLE_DENIAL',
        'ui':'REAL_MAINLAYOUT_SYNTHETIC_STAFF_NOT_HUMAN'},
 'S07':{'http':'PASS_PG_REAL_ROUTER_CONCURRENT','sqlcipher':'PASS_ENCRYPTED_DB_PRIMITIVES',
        'ui':'NOT_RUN_FULL_STAFF_JOURNEY'},
 'S09':{'http':'PASS_PG_BOT_EXECUTE_STALE_AND_FRESH','sqlcipher':'PASS_ENCRYPTED_DB_ABA_PRIMITIVE',
        'ui':'NOT_RUN_FULL_STAFF_JOURNEY'},
 'S10':{'http':'PASS_REAL_409_STRUCTURED_DETAIL','ui':'PASS_VITEST_REAL_SHAPE_MOCKED_TRANSPORT',
        'limitation':'UI Vitest exercises real-shape object, not a live secretary browser connected to the PostgreSQL race'},
 'S12':{'http':'PASS_PG_REAL_ROUTER_404_200_PERSISTED_ACK','ui':'PASS_VITEST_WS_SIMULATED_ACK_AND_REFUSAL',
        'limitation':'Backend ACK and frontend simulated WebSocket tests, not live WebSocket to real clinic'},
}
out={'schema':'CB01_CROSS_GATE_PROOF_V1','sourceHead':head,'scenarios':scenarios,
     'humanE2EValidated':0,'clinicalCabinetUsed':False,
     'independentReviews':0,'converged':False,
     'originalS01S12MatrixUnmodified':True,
     'integrity':'Each technical proof separated from staff E2E; no synthetic-to-human status promotion'}
(root/'cross-gate-evidence.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('CB01_CROSS_GATE_LEDGER: PASS_SYNTHETIC_PG_UI_S05_S06_BROWSER_REAL_API; HUMAN_E2E_0; CONVERGED_NO')
