/**
 * CPV2-01C ONLY — Disposable synthetic Pocket phone FUE server.
 * Runs exclusively in GitHub Actions on an isolated runner.
 * Serves the real built frontend but NEVER connects to cabinet, DB or PHI.
 * Synthetic auth/ECDH endpoints support manual 6-digit pairing / unlink.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {
  randomBytes, randomInt, randomUUID, createECDH, hkdfSync,
  createCipheriv, createHmac, timingSafeEqual,
} from 'node:crypto';

const PORT = 5173;
const started = Date.now();
const maxAgeMs = 27 * 60 * 1000;
const secret = randomBytes(32);
const publicId = randomBytes(8).toString('hex');
const masterKey = randomBytes(32).toString('hex');
const devices = new Map();
const dist = path.resolve('frontend/dist');
let ticket = null;

function issueTicket() {
  ticket = { code: String(randomInt(100000, 1000000)), expires: Date.now() + 5 * 60_000, used: false };
  fs.writeFileSync('/tmp/cpv2-fue-code.txt', ticket.code, { mode: 0o600 });
}
issueTicket();

function send(res, status, object, headers = {}) {
  const body = JSON.stringify(object);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    ...headers,
  });
  res.end(body);
}
function cookiePage(res, html) {
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'",
  });
  res.end(html);
}
function jwt(body) {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(JSON.stringify(body)).toString('base64url');
  const data = header + '.' + payload;
  const signature = createHmac('sha256', secret).update(data).digest('base64url');
  return data + '.' + signature;
}
function getSession(req) {
  const value = String(req.headers.authorization ?? '');
  if (!value.startsWith('Bearer ')) return null;
  const t = value.slice(7);
  const parts = t.split('.');
  if (parts.length !== 3) return null;
  const signature = createHmac('sha256', secret).update(parts[0] + '.' + parts[1]).digest('base64url');
  const a = Buffer.from(signature), b = Buffer.from(parts[2]);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
    if (payload.exp <= Date.now()/1000 || !devices.has(payload.device_id)) return null;
    const device = devices.get(payload.device_id);
    if (device.revoked || payload.epoch !== device.epoch) return null;
    return { payload, device };
  } catch { return null; }
}
function newTokens(id, epoch) {
  const exp = Math.floor(Date.now() / 1000) + 60 * 60;
  return {
    access_token: jwt({ sub: '1', role:'DENTISTE', tenant_id: 1, device_id: id, epoch, exp }),
    refresh_token: jwt({ sub: '1', role:'DENTISTE', tenant_id: 1, device_id: id, epoch, exp, type:'refresh' }),
    device_id: id,
  };
}
async function readJson(req) {
  let s = '';
  for await (const chunk of req) {
    s += chunk;
    if (s.length > 4096) throw Error('Payload too large');
  }
  return JSON.parse(s || '{}');
}
function encryptPairing(clientPubHex) {
  if (!/^(04)[0-9a-f]{128}$/i.test(String(clientPubHex))) throw Error('Invalid ECDH public key');
  const ecdh = createECDH('prime256v1');
  ecdh.generateKeys();
  const shared = ecdh.computeSecret(Buffer.from(clientPubHex,'hex'));
  const key = Buffer.from(hkdfSync('sha256',shared,Buffer.alloc(32),Buffer.from('zka_mobile_bridge'),32));
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm',key,iv);
  const enc = Buffer.concat([cipher.update(masterKey,'utf8'),cipher.final(),cipher.getAuthTag()]);
  return {
    server_public_key_hex: ecdh.getPublicKey(undefined,'uncompressed').toString('hex'),
    encrypted_master_key_hex: Buffer.concat([iv,enc]).toString('hex'),
  };
}
function snapshot(url) {
  const day = url.searchParams.get('target_date') || new Date().toISOString().slice(0,10);
  return {
    generated_at: new Date().toISOString(),
    role:'DENTISTE', is_superadmin: false,
    appointments: [
      { id:101, patient_id:11, time:'09:00', date:day, patient_name:'Patient TEST 01', phone:null, motif:'Essai de connexion', status:'PLANIFIE', duration_minutes:30 },
      { id:102, patient_id:12, time:'10:15', date:day, patient_name:'Patient TEST 02', phone:null, motif:'Essai hors ligne', status:'EN_ATTENTE', duration_minutes:45 },
    ],
    finance: { today_revenue:0, month_revenue:0, month_variation:null, appointments_count:2, weekly_revenue:[], total_patients:2,total_debt:0 },
    debtors:[],
  };
}
function serveStatic(req,res,url) {
  let filename;
  try {
    const decoded=decodeURIComponent(url.pathname);
    if (decoded.includes('\0')||decoded.split('/').includes('..')) return send(res,400,{detail:'Bad path'});
    filename=path.resolve(dist,'.'+decoded);
    if (!filename.startsWith(dist+path.sep) && filename!==dist) return send(res,403,{detail:'Forbidden'});
    if (!fs.existsSync(filename)||!fs.statSync(filename).isFile()) filename=path.join(dist,'index.html');
    if (!fs.existsSync(filename)) return send(res,503,{detail:'Compiling Pocket'});
    const ext=path.extname(filename);
    const mime={
      '.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8',
      '.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.json':'application/json',
      '.woff2':'font/woff2','.webp':'image/webp','.ico':'image/x-icon','.webmanifest':'application/manifest+json',
    }[ext]||'application/octet-stream';
    res.writeHead(200,{'Content-Type':mime,'Cache-Control':ext==='.html'?'no-store':'public, max-age=60',
      'X-Content-Type-Options':'nosniff','X-Robots-Tag':'noindex, nofollow'});
    fs.createReadStream(filename).pipe(res);
  } catch (e) { send(res,500,{detail:'Static unavailable'}); }
}
const s=http.createServer(async(req,res)=>{
  if(Date.now()-started>maxAgeMs) return send(res,410,{detail:'Lab expired'});
  const url=new URL(req.url||'/', 'http://127.0.0.1:'+PORT);
  if(req.method==='GET' && url.pathname==='/health') return send(res,200,{ok:true,lab:true,source:'SYNTHETIC_ONLY',started});
  if(req.method==='GET' && url.pathname==='/lab/pair') {
    if(!ticket||Date.now()>ticket.expires||ticket.used) issueTicket();
    const escape=String(ticket.code).replace(/[&<>]/g,'');
    return cookiePage(res,'<!doctype html><html lang="fr"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pocket FUE synthétique</title><body style="font-family:system-ui;max-width:450px;margin:35px auto;padding:15px"><h2>Digital Crown Pocket — LAB</h2><p><strong>Données fictives uniquement.</strong> Pas de connexion à votre cabinet.</p><p>Code à 6 chiffres (usage unique, 5 minutes) :</p><div style="font-size:42px;letter-spacing:6px;font-weight:bold">'+escape+'</div><p><a href="/mobile/onboarding">Ouvrir Pocket</a></p><p>En cas d’expiration, actualiser cette page pour un nouveau code.</p><p>Serveur éphémère, arrêt automatique.</p></body></html>');
  }
  if(url.pathname.startsWith('/api/')) {
    const mobile = url.pathname.startsWith('/api/mobile/');
    if(req.method==='POST'&&url.pathname==='/api/mobile/claim-token') {
      try {
        const body=await readJson(req);
        if(!ticket||ticket.used||Date.now()>ticket.expires||String(body.token)!==ticket.code)
          return send(res,404,{detail:'Code invalide, expiré ou déjà utilisé. Ouvrez /lab/pair pour renouveler.'});
        const crypt=encryptPairing(body.client_public_key_hex);
        ticket.used=true;
        const id=randomUUID();
        devices.set(id,{revoked:false,epoch:1});
        const token=newTokens(id,1);
        return send(res,200,{publicId,...crypt,...token,user_id:1,tenant_id:1,role:'DENTISTE',is_lab:true});
      } catch { return send(res,400,{detail:'Appairage non valide'}); }
    }
    if(req.method==='POST'&&url.pathname==='/api/mobile/refresh-token') {
      try {
        const b=await readJson(req);
        const fakeReq={ headers: { authorization:'Bearer '+String(b.refresh_token||'') } };
        const current=getSession(fakeReq);
        if(!current||current.payload.type!=='refresh') return send(res,401,{detail:'Session invalide'});
        current.device.epoch++;
        return send(res,200,newTokens(current.payload.device_id,current.device.epoch));
      } catch { return send(res,401,{detail:'Token invalide'}); }
    }
    if(mobile||url.pathname==='/api/clinics/mobile-theme') {
      const current=getSession(req);
      if(!current) return send(res,401,{detail:'Session révoquée ou absente'});
      if(url.pathname==='/api/mobile/revoke-device'&&req.method==='POST'){
        current.device.revoked=true;
        return send(res,200,{revoked:true});
      }
      if(url.pathname==='/api/mobile/snapshot')return send(res,200,snapshot(url));
      if(url.pathname==='/api/mobile/patients')return send(res,200,{data:[
        {id:11,name:'Patient TEST 01',phone:null},{id:12,name:'Patient TEST 02',phone:null}]});
      if(url.pathname==='/api/mobile/passkey/status')return send(res,200,{
        state:'disabled',credential_id:null,rp_id:'lab.invalid',expected_origin:'',origin_ready:false,user_verification:'required',server_gate:false});
      if(url.pathname==='/api/mobile/capabilities')return send(res,200,{
        version:1,principal_kind:'staff',capabilities:{
          'agenda.read':{allowed:true,scope:'cabinet',reason:null},
          'cabinet.patients.read':{allowed:true,scope:'cabinet',reason:null},
          'cabinet.clinical.read':{allowed:true,scope:'cabinet',reason:null},
          'cabinet.finance.read':{allowed:true,scope:'cabinet',reason:null}}});
      if(url.pathname==='/api/mobile/quick-actions/capabilities')return send(res,200,{
        can_create_appointment:false,can_create_patient:false,can_open_clinical_context:false,can_pay:false});
      if(url.pathname==='/api/clinics/mobile-theme')return send(res,200,{
        selected_theme:'elite',primary_color:'#003380',secondary_color:'#1e40af',accent_color:'#60a5fa',
        app_accent_color:null,font_fr:'inter'});
      if(url.pathname==='/api/mobile/dentists')return send(res,200,{dentists:[]});
      if(url.pathname==='/api/mobile/lab-jobs')return send(res,200,[]);
      if(url.pathname.startsWith('/api/mobile/appointments/'))return send(res,403,{detail:'Modifications désactivées en laboratoire'});
      return send(res,200,[]);
    }
    return send(res,404,{detail:'Ce laboratoire n’a pas d’autres APIs.'});
  }
  if(req.method!=='GET'&&req.method!=='HEAD')return send(res,405,{detail:'Method not allowed'});
  serveStatic(req,res,url);
});
s.listen(PORT,'127.0.0.1',()=>console.log('CPV2_FUE_LAB_READY localhost:'+PORT+' synthetic only'));
setTimeout(()=>{console.log('CPV2_FUE_LAB_EXPIRED');s.close();},maxAgeMs).unref();
