"""LOT07 B10 — empty top-level patient display with real HTTP CSP sandbox.

No patient, source, token, session or case data appears in this HTTP response.
Patient projection arrives after loading through a dedicated MessageChannel only.
The CSP header (NOT a meta tag) makes this top-level document opaque-origin.
"""
import base64
import hashlib
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_STYLE = """html{font-family:system-ui,Arial,sans-serif;background:#0d1b2a;color:#f5f8fc}
body{margin:0;padding:clamp(20px,5vw,70px)}header{border-bottom:1px solid #526175;padding-bottom:26px}
h1{font-size:clamp(24px,3vw,42px);margin:8px 0}
small,p{color:#cfdae9}small{letter-spacing:.13em;text-transform:uppercase}
main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:32px}
article{border:1px solid #566983;border-radius:18px;background:#1b3045;padding:22px;min-height:158px}
h2{font-size:30px;margin:0 0 12px}li{margin:8px 0;word-wrap:break-word}
footer{padding-top:32px;font-size:15px;color:#c5d2e2}
@media(max-width:650px){main{grid-template-columns:1fr}}"""
_SCRIPT = r"""(() => {
'use strict';
const params=new URLSearchParams(location.search);
const origin=params.get('origin');
const channel=params.get('channel');
if(!origin || !/^https?:\/\/[^/]+$/.test(origin) ||
   !channel || !/^[0-9a-f-]{36}$/.test(channel)) return;
let attached=false;
let expiry;
const make=(tag,value,attr)=>{
  const el=document.createElement(tag);
  el.textContent=value;
  if(attr)el.setAttribute('data-testid',attr);
  return el;
};
const valid=(snapshot)=>{
  if(!snapshot || !Array.isArray(snapshot.pair) ||
      snapshot.pair.length!==2 || ![0,1].includes(snapshot.pair[0]) ||
      ![1,2].includes(snapshot.pair[1]) ||
      snapshot.pair[0]>=snapshot.pair[1] ||
      !Array.isArray(snapshot.points) || snapshot.points.length!==3)return false;
  return snapshot.points.every((p,i)=>
    p && p.ordinal===i && typeof p.occurred_at==='string' &&
    Number.isFinite(Date.parse(p.occurred_at)) &&
    Array.isArray(p.sources) && p.sources.length<=32 &&
    p.sources.every(s=>s && ['CLINICAL_ASSET','CEPHALO','PANORAMIC'].includes(s.kind) &&
      Number.isSafeInteger(s.refId) && s.refId>0));
};
const close=()=>{
  document.body.replaceChildren();
  window.close();
};
const render=(snapshot)=>{
  if(!valid(snapshot)){close();return;}
  const header=document.createElement('header');
  header.append(
    make('small','Digital Crown · Présentation en lecture seule'),
    make('h1','Suivi orthodontique · T0 → T1 → T2'),
    make('p','Comparaison sélectionnée : T'+snapshot.pair[0]+' → T'+snapshot.pair[1],'r6d-pair'),
  );
  const main=document.createElement('main');
  main.setAttribute('data-testid','r6d-readonly-presenter');
  for(const point of snapshot.points){
    const card=document.createElement('article');
    card.setAttribute('data-r6d-ordinal',String(point.ordinal));
    const date=new Date(point.occurred_at);
    card.append(make('h2','T'+point.ordinal),
      make('p',date.toLocaleDateString('fr-FR',{year:'numeric',month:'long',day:'numeric'})));
    const sources=document.createElement('ul');
    for(const source of point.sources){
      const label=source.kind==='CEPHALO'?'Céphalo':
        source.kind==='PANORAMIC'?'Panoramique':'Média';
      sources.append(make('li',label+' · source #'+source.refId));
    }
    card.append(sources);
    main.append(card);
  }
  document.body.replaceChildren(header,main,
    make('footer','Sources canoniques vérifiées. Lecture seule. Aucune interprétation clinique automatique.'));
  clearTimeout(expiry);
  expiry=setTimeout(close,28000);
};
window.addEventListener('message',(event)=>{
  if(attached || event.origin!==origin || event.data?.type!=='DC_PRESENTER_INIT' ||
     event.data.channel!==channel || event.ports?.length!==1)return;
  const port=event.ports[0];
  attached=true;
  port.onmessage=(message)=>{
    const data=message.data;
    if(!data || data.channel!==channel)return;
    if(data.type==='DC_PRESENTER_CLOSE'){close();return;}
    if(data.type!=='DC_PRESENTER_UPDATE')return;
    render(data.snapshot);
    port.postMessage({type:'DC_PRESENTER_ACK',channel,seq:data.seq});
  };
  port.start();
  port.postMessage({type:'DC_PRESENTER_READY',channel});
});
const parent=window.opener;
if(parent){
  parent.postMessage({type:'DC_PRESENTER_HELLO',channel},origin);
  window.opener=null;
}
setTimeout(()=>{if(!attached)close();},10000);
})();"""

def _hash(source: str) -> str:
    return base64.b64encode(hashlib.sha256(source.encode("utf-8")).digest()).decode("ascii")

_HTML = (
    "<!doctype html><html lang='fr'><head><meta charset='utf-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
    "<title>Digital Crown · Présentation du suivi</title>"
    "<style>" + _STYLE + "</style></head><body>"
    "<main role='status'>Initialisation de la présentation sécurisée…</main>"
    "<script>" + _SCRIPT + "</script></body></html>"
)
_CSP = (
    "sandbox allow-scripts; default-src 'none'; "
    "script-src 'sha256-" + _hash(_SCRIPT) + "'; "
    "style-src 'sha256-" + _hash(_STYLE) + "'; "
    "connect-src 'none'; img-src 'none'; object-src 'none'; "
    "form-action 'none'; base-uri 'none'; frame-ancestors 'none'"
)

@router.get("/presenter-window", include_in_schema=False)
def empty_opaque_patient_presentation() -> HTMLResponse:
    """Public empty shell only; a validated authenticated parent supplies data."""
    return HTMLResponse(
        content=_HTML,
        headers={
            "Content-Security-Policy": _CSP,
            "Cache-Control": "no-store, max-age=0",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )
