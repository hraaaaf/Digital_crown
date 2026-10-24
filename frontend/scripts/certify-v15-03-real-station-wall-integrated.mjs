/**
 * V1.5-03.21 real browser -> localhost FastAPI -> disposable SQLite -> wall.
 * No page.route, HAR playback, intercepted HTTP, fake API responses, or cabinet data.
 * Workstations have separate HttpOnly identity cookies; receptionist has own login.
 */
import { chromium, request } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

if (process.env.T2_STATION_FUE !== '1' || process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('FAIL CLOSED: T2_STATION_FUE=1 and isolated runtime required');
}
const baseURL = 'http://127.0.0.1:8005';
const uiURL = 'http://127.0.0.1:5173';
const out = path.resolve('artifacts/v15-03-real-integration');
const user = process.env.T2_USER;
const password = process.env.T2_PASSWORD;
if (!user || !password) throw new Error('Synthetic T2 credentials required');
const pin = '2468'; // Disposable test-only PIN.
const fixture = JSON.parse(await fs.readFile(path.join(out, 'seed.json'), 'utf8')).patients;
const evidence = {
  scope: 'Single isolated GitHub runner, real Chromium HTTP, real FastAPI and disposable SQLite; NOT physical LAN/NFC',
  head: process.env.EVALUATED_SHA || null,
  actors: {},
  http: [],
  screenshots: [],
  scenarios: {},
};
const assert = (ok, text) => { if (!ok) throw new Error(text); };
const apiOK = async (response, label, expected) => {
  const actual = response.status();
  assert(expected.includes(actual), label + ': HTTP ' + actual + ' body=' + (await response.text()).slice(0, 400));
  return response;
};
async function buildWorkstation(mode, label) {
  const api = await request.newContext({ baseURL, timeout: 25000 });
  const login = await apiOK(await api.post('/api/auth/login', {
    form: { username: user, password },
  }), label + ' login', [200]);
  const tokens = await login.json();
  const headers = { Authorization: 'Bearer ' + tokens.access_token };
  const enroll = await apiOK(await api.post('/api/workstation/enroll', {
    data: { accountPassword: password }, headers,
  }), label + ' enroll', [200]);
  const enrollment = await enroll.json();
  if (label === 'kiosk') {
    await apiOK(await api.post('/api/workstation/owner-pin', {
      data: { accountPassword: password, newPin: pin }, headers,
    }), 'owner pin', [200]);
  }
  await apiOK(await api.post('/api/workstation/mode', {
    data: { mode, ownerPin: pin }, headers,
  }), label + ' mode', [200]);
  evidence.actors[label] = { workstationId: enrollment.workstationId, mode };
  return { api, tokens, headers, storageState: await api.storageState() };
}
async function newActorPage(browser, actor, viewport) {
  const ctx = await browser.newContext({
    storageState: actor.storageState,
    viewport,
    colorScheme: 'light',
  });
  const page = await ctx.newPage();
  await page.addInitScript(v => {
    localStorage.setItem('token', v.access);
    localStorage.setItem('refresh_token', v.refresh || '');
    localStorage.setItem('appMode', 'prod');
  }, { access: actor.tokens.access_token, refresh: actor.tokens.refresh_token });
  page.on('response', response => {
    if (response.url().startsWith(baseURL + '/api/workstation/')) {
      evidence.http.push({ actor: actor.label, method: response.request().method(),
        path: new URL(response.url()).pathname, status: response.status() });
    }
  });
  page.on('pageerror', err => {
    evidence.http.push({ actor: actor.label, pageerror: err.message });
  });
  return { page, ctx };
}
async function snap(page, filename) {
  const file = path.join(out, filename);
  await page.screenshot({ path: file, fullPage: true, animations: 'disabled' });
  evidence.screenshots.push(filename);
}
async function flow(browser, station, key, expectedNumber, label) {
  const actor = { ...station, label: 'kiosk-' + key };
  const {page,ctx} = await newActorPage(browser, actor, {width:430,height:932});
  try {
    await page.goto(uiURL + '/station', { waitUntil:'domcontentloaded', timeout:90000 });
    await page.locator('[data-station-action="appointment"]').waitFor({ state:'visible',timeout:45000 });
    await page.locator('[data-station-action="appointment"]').click();
    await page.locator('[data-station-fallback-toggle]').waitFor({state:'visible',timeout:18000});
    await snap(page, 'kiosk-' + key + '-qr-before.png');
    await page.locator('[data-station-fallback-toggle]').click();
    const form = page.locator('[data-station-fallback-form]');
    await form.waitFor({state:'visible', timeout:10000});
    await form.getByLabel('Téléphone').fill(fixture[key].phone);
    await form.getByLabel('Date de naissance').fill(fixture[key].birthDate);
    await form.getByRole('button', {name:'Confirmer mon identité'}).click();
    await page.locator('[data-station-arrival-bridge]').waitFor({state:'visible',timeout:15000});
    if (expectedNumber === 0) {
      await page.locator('[data-station-no-appointment]').waitFor({state:'visible',timeout:15000});
      await page.locator('[data-station-staff-notified]').waitFor({state:'visible',timeout:15000});
      evidence.scenarios[key] = {status:'no_appointment',staffNotified:true};
      await snap(page, 'kiosk-zero-staff-notified-after.png');
    } else {
      const options = page.locator('[data-station-appointment-id]');
      await options.first().waitFor({state:'visible',timeout:15000});
      assert(await options.count() === expectedNumber, key + ': wrong appointment count');
      const selectedId = fixture[key].appointmentIds[0];
      await page.locator('[data-station-appointment-id="' + selectedId + '"]').click();
      await snap(page, 'kiosk-' + key + '-selection-before.png');
      await page.getByRole('button', {name:'Confirmer mon arrivée'}).click();
      await page.locator('[data-station-arrival-confirmed]').waitFor({state:'visible',timeout:15000});
      evidence.scenarios[key] = {status:'arrived', appointmentId:selectedId,shownCount:expectedNumber};
      await snap(page, 'kiosk-' + key + '-arrival-after.png');
    }
    return evidence.scenarios[key];
  } finally {
    await ctx.close();
  }
}

let browser;
let station, wall, reception;
try {
  station = await buildWorkstation('station', 'kiosk');
  wall = await buildWorkstation('station', 'wall');
  reception = await buildWorkstation('cabinet', 'reception-workstation');
  const receptionLogin = await apiOK(await reception.api.post('/api/auth/login', {
    form: {username: 't2-reception@cabinet.ma', password},
  }), 'reception staff login', [200]);
  const receptionTokens = await receptionLogin.json();
  reception.headers = {Authorization:'Bearer ' + receptionTokens.access_token};
  assert(new Set([station.storageState.cookies.find(c=>c.name==='dc_workstation')?.value,
    wall.storageState.cookies.find(c=>c.name==='dc_workstation')?.value,
    reception.storageState.cookies.find(c=>c.name==='dc_workstation')?.value]).size===3,
    'workstation identity cookies must be distinct');
  await apiOK(await station.api.patch('/api/workstation/patient-session/config', {
    data: {fallbackMode:'phone_dob', ownerPin:pin},headers:station.headers,
  }), 'configure fallback by owner', [200]);

  browser = await chromium.launch({headless:true});
  const wallBrowser = await newActorPage(browser,{...wall,label:'wall'}, {width:1280,height:900});
  const wallPage = wallBrowser.page;
  await wallPage.goto(uiURL + '/station/wall',{waitUntil:'domcontentloaded',timeout:90000});
  await wallPage.locator('[data-workstation-experience="station-wall"]').waitFor({state:'visible',timeout:45000});
  await snap(wallPage, 'wall-initial-before.png');
  const unauthenticated = await request.newContext({baseURL});
  const denied = await unauthenticated.get('/api/workstation/wall-display');
  assert([401,403].includes(denied.status()),'anonymous wall data is not denied');
  await unauthenticated.dispose();

  await flow(browser, station, 'zero', 0);
  const alerts = await apiOK(await reception.api.get('/api/workstation/staff-assistance',{
    headers: reception.headers,
  }), 'real receptionist staff alert read',[200]);
  const alertRows = (await alerts.json()).alerts;
  assert(alertRows.length===1, 'zero-case must create ONE receptionist-visible alert');
  await apiOK(await reception.api.post('/api/workstation/staff-assistance/'+alertRows[0].alertId+'/acknowledge',{
    headers:reception.headers,
  }), 'real staff acknowledgement',[200]);

  await flow(browser,station,'single',1);
  const arrivedOne = await apiOK(await station.api.get('/api/workstation/wall-display', {
    headers:station.headers,
  }), 'post-arrival wall snapshot',[200]);
  assert((await arrivedOne.json()).waitingCount===1, 'wall must read one arrived appointment from backend');
  await wallPage.locator('[data-wall-state="waiting"]').waitFor({state:'visible',timeout:12000});
  await snap(wallPage,'wall-one-waiting-after.png');
  const oneId = fixture.single.appointmentIds[0];
  await apiOK(await reception.api.post('/api/workstation/wall-display/appointments/'+oneId+'/call',{
    headers:reception.headers,data: {ticketNumber:307},
  }), 'receptionist calls patient 1',[200]);
  await wallPage.locator('[data-wall-state="calling"]').waitFor({state:'visible',timeout:15000});
  await wallPage.getByText('N° 307').waitFor({state:'visible',timeout:12000});
  await snap(wallPage,'wall-one-called-after.png');

  await flow(browser,station,'multiple',2);
  const multiId = fixture.multiple.appointmentIds[0];
  await apiOK(await reception.api.post('/api/workstation/wall-display/appointments/'+multiId+'/call',{
    headers:reception.headers,data:{ticketNumber:308},
  }), 'receptionist calls patient 2',[200]);
  await wallPage.getByText('N° 308').waitFor({state:'visible',timeout:15000});
  await snap(wallPage,'wall-two-called-after.png');
  const last = await apiOK(await wall.api.get('/api/workstation/wall-display',{
    headers:wall.headers,
  }), 'independent wall workstation reads same DB',[200]);
  const state = await last.json();
  assert(state.waitingCount===2, 'wall must show exactly 2 arrived appointments');
  assert(state.currentCall?.ticketNumber===308,'wall API must show second call');
  assert(state.identityMode==='initials','privacy fallback must not expose full names');
  const fullText=await wallPage.locator('[data-workstation-experience="station-wall"]').innerText();
  assert(!fullText.includes('STATION-FICTIF'),'wall leaks synthetic family name');
  assert(!evidence.http.some(x=>x.pageerror), 'browser JavaScript exception');
  assert(evidence.http.some(x=>x.actor==='kiosk-single'&&x.path.endsWith('/fallback')&&x.status===200),'missing real fallback HTTP proof');
  assert(evidence.http.some(x=>x.actor==='kiosk-single'&&x.path.endsWith('/arrive')&&x.status===200),'missing real arrival HTTP proof');
  assert(evidence.http.some(x=>x.actor==='wall'&&x.path.endsWith('/wall-display')&&x.status===200),'missing independent wall HTTP proof');
  evidence.scenarios.wall = {waitingCount:state.waitingCount, identityMode:state.identityMode,
    latestCall:state.currentCall?.ticketNumber, separateWorkstations:true};
  await wallBrowser.ctx.close();
  console.log('V15_G03_21_REAL_BROWSER_API_WALL_PASS ' + JSON.stringify(evidence.scenarios));
} finally {
  if (browser) await browser.close();
  await Promise.allSettled([station?.api?.dispose(),wall?.api?.dispose(),reception?.api?.dispose()]);
  await fs.mkdir(out,{recursive:true});
  await fs.writeFile(path.join(out,'evidence-after.json'), JSON.stringify(evidence,null,2));
}
