#!/usr/bin/env python3
"""CB-00 LOCAL T2 ONLY: read-only /patient HTTP latency, cold + warm p50/p95.

Requires explicitly launched ISOLATED synthetic T2 backend and BOTH preview
flags in that disposable process. Will NEVER enable flags or change data.
Only targets http://127.0.0.1 or http://localhost, never a public host.
Usage:
  DIGITALCROWN_ISOLATED_RUNTIME=1 T2_USER=t2-browser@cabinet.ma \
  T2_PASSWORD='<synthetic test credential>' \
  python scripts/ci/crownbot_cb00_latency_probe.py --out /tmp/cb00.json
"""
import argparse
import json
import os
import statistics
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def quantile(values, f):
    values = sorted(values)
    x = (len(values)-1)*f
    low = int(x)
    high = min(low+1,len(values)-1)
    return values[low]+(values[high]-values[low])*(x-low)


def post(url, obj, headers=None):
    req = Request(url, data=json.dumps(obj).encode(), headers={
        'Content-Type':'application/json', **(headers or {})}, method='POST')
    t0 = time.perf_counter_ns()
    with urlopen(req, timeout=15) as response:
        code = response.status
        result = json.loads(response.read().decode())
    duration_ms = (time.perf_counter_ns()-t0)/1e6
    return code,result,duration_ms


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--api',default='http://127.0.0.1:8005')
    ap.add_argument('--n',type=int,default=30)
    ap.add_argument('--out',default='/tmp/crown-bot-cb00-metrics.json')
    args = ap.parse_args()
    parsed = urlparse(args.api)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost'):
        raise SystemExit('REFUSED: only synthetic localhost T2')
    if os.getenv('DIGITALCROWN_ISOLATED_RUNTIME')!='1':
        raise SystemExit('REFUSED: DIGITALCROWN_ISOLATED_RUNTIME=1 required')
    user,password=os.getenv('T2_USER',''),os.getenv('T2_PASSWORD','')
    if not user.startswith('t2-') or not password:
        raise SystemExit('REFUSED: synthetic T2-only credentials required')
    if not 20<=args.n<=200:
        raise SystemExit('REFUSED: 20–200 successful warm samples required')
    # FastAPI login expects form-urlencoded; secrets are never logged/stored.
    from urllib.parse import urlencode
    auth_req=Request(
        args.api+'/api/auth/login',
        data=urlencode({'username':user,'password':password}).encode(),
        headers={'Content-Type':'application/x-www-form-urlencoded'},
        method='POST')
    with urlopen(auth_req,timeout=15) as response:
        if response.status!=200: raise RuntimeError('T2 login failed')
        token=json.loads(response.read().decode())['access_token']
    headers={'Authorization':'Bearer '+token}
    def call():
        status,result,elapsed=post(args.api+'/api/bot/workflows/preview',
                                   {'messages':['/patient']},headers)
        if status!=200 or result.get('status')!='clarification' or result.get('proposal'):
            raise RuntimeError('Unexpected T2 response: no timing accepted')
        return elapsed
    cold=call()
    warm=[call() for _ in range(args.n)]
    data={'scope':'ISOLATED_SYNTHETIC_LOCAL_T2',
          'metric':'HTTP full response only, NOT end-to-end browser UX',
          'sample_n':len(warm),'cold_first_ms':round(cold,2),
          'warm_p50_ms':round(quantile(warm,0.5),2),
          'warm_p95_ms':round(quantile(warm,0.95),2),
          'warm_max_ms':round(max(warm),2),
          'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    # No tokens, response bodies, patient names, or credentials persisted.
    with open(args.out,'w',encoding='utf-8') as f:
        json.dump(data,f,indent=2)
    print(json.dumps(data,indent=2))


if __name__=='__main__':
    main()
