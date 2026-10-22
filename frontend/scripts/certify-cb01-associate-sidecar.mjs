/**
 * CB-01 Associate Sidecar — isolated synthetic responsive visual acceptance.
 * This is a preview-only desktop shell, never the real cabinet baseline.
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium, request } from 'playwright';

if (process.env.DIGITALCROWN_ISOLATED_RUNTIME !== '1') {
  throw new Error('REFUSED: isolated T2 required');
}
const apiOrigin = process.env.CB01_T2_API_URL || 'http://127.0.0.1:8005';
const appOrigin = process.env.CB01_T2_APP_URL || 'http://127.0.0.1:5173';
for (const u of [apiOrigin, appOrigin]) {
  const parsed = new URL(u);
  if (parsed.protocol !== 'http:' || !['localhost', '127.0.0.1'].includes(parsed.hostname)
      || parsed.username || parsed.password || parsed.search || parsed.hash
      || (parsed.pathname !== '' && parsed.pathname !== '/')) {
    throw new Error('REFUSED: loopback origins only');
  }
}
const user = process.env.T2_USER, password = process.env.T2_PASSWORD;
const patientId = process.env.T2_PATIENT_ID || '';
if (!user?.startsWith('t2-') || !password || !/^[1-9][0-9]{0,9}$/.test(patientId)) {
  throw new Error('REFUSED: synthetic identity and patient ID needed');
}
const output = path.resolve('../artifacts/cb01-associate-sidecar');
fs.mkdirSync(output, { recursive: true });
const api = await request.newContext({ baseURL: apiOrigin });
const login = await api.post('/api/auth/login', { form: { username:user, password } });
if (!login.ok()) throw new Error('Synthetic auth rejected');
const tokens = await login.json();

// S05/S06 are independent receptionist identities. An owner-browser PASS is
// insufficient evidence of reception RBAC; verify role-specific HTTP after
// seeding the synthetic dossier, before entering the UI scenarios.
const futureDossierProposal=[
  '/rdv','dossier:CB01-N-101','2099-01-01','10:00','30','consultation','CONFIRMER',
];
const roleChecks={s05ReceptionDossier:'NOT_RUN',s06NoAgenda:'NOT_RUN'};
// Synthetic bearer credentials stay in memory, never in reports.
const roleTokens=Object.create(null);
const roleStorageStates=Object.create(null);
// The OWNER enrolled this physical lab workstation in the outer harness.
// Its opaque device cookie is tenant-scoped and may be used by distinct staff
// sessions on that same station. Enrollment itself is OWNER-ONLY, never staff.
const ownerState=await api.storageState();
const workstationCookies=ownerState.cookies.filter(c=>c.name==='dc_workstation');
if(workstationCookies.length!==1 || workstationCookies[0].httpOnly!==true)
  throw new Error('REFUSED: no unique owner-enrolled secure workstation fixture');
for (const [kind,envPrefix] of [['s05','T2_S05'],['s06','T2_S06']]) {
  const account=process.env[envPrefix+'_USER'];
  const secret=process.env[envPrefix+'_PASSWORD'];
  if (!account?.startsWith('t2-') || !secret) {
    throw new Error('REFUSED: synthetic role credentials missing: '+kind);
  }
  // The generic wrapper's request context includes the owner's auth cookie;
  // do NOT reuse that principal. Fresh context + staff login -> staff JWT.
  // Add ONLY the cabinet's pre-enrolled, owner-authorized workstation cookie.
  // The production middleware still checks the station against tenant scope.
  // APIRequestContext has no addCookies(); compose a fresh cookie jar from
  // the staff login (staff access JWT) plus *only* the existing device cookie.
  const loginApi=await request.newContext({
    baseURL:apiOrigin, storageState:{cookies:[],origins:[]},
  });
  let roleToken, staffState;
  try {
    const signedIn=await loginApi.post('/api/auth/login',{
      form:{username:account,password:secret},
    });
    if (!signedIn.ok()) throw new Error('FAIL: receptionist login '+kind+' HTTP '+signedIn.status());
    roleToken=(await signedIn.json()).access_token;
    staffState=await loginApi.storageState();
  } finally {
    await loginApi.dispose();
  }
  if(staffState.cookies.filter(c=>c.name==='access_token' && c.value===roleToken).length!==1
      || staffState.cookies.some(c=>c.name==='dc_workstation' || c.name==='dc_station_escape')) {
    throw new Error('REFUSED: receptionist login jar is not an isolated principal '+kind);
  }
  const roleApi=await request.newContext({
    baseURL:apiOrigin,
    storageState:{cookies:[...staffState.cookies,...workstationCookies],origins:[]},
  });
  try {
    roleTokens[kind]=roleToken;
    const check=await roleApi.get('/api/workstation/bootstrap',{
      headers:{Authorization:'Bearer '+roleToken},
    });
    if (check.status()!==200) {
      throw new Error('FAIL: authenticated receptionist workstation bootstrap '+kind+' HTTP '+check.status());
    }
    const boot=await check.json();
    if (boot.authenticated!==true || boot.enrollmentRequired!==false || !boot.workstationId) {
      throw new Error('REFUSED: synthetic role cannot use already enrolled cabinet workstation '+kind);
    }
    const state=await roleApi.storageState();
    if (state.cookies.find(c=>c.name==='access_token')?.value!==roleToken
        || state.cookies.filter(c=>c.name==='dc_workstation').length!==1
        || state.cookies.some(c=>c.name==='dc_station_escape')) {
      throw new Error('REFUSED: ambiguous role JWT or workstation/escape cookies '+kind);
    }
    roleStorageStates[kind]=state;
    const sendRolePreview=async messages => {
      const response=await roleApi.post('/api/bot/workflows/preview',{
        data:{messages},
        headers:{Authorization:'Bearer '+roleToken},
      });
      return {status:response.status(),payload:await response.json()};
    };
  if(kind==='s05') {
    const r=await sendRolePreview(futureDossierProposal);
    if(r.status!==200 || r.payload?.status!=='proposal_only'
      || r.payload?.proposal?.type!=='CREATE_APPOINTMENT'
      || !Number.isInteger(r.payload?.proposal?.params?.patient_id)
      || /"pending_action_id"|"pendingActionId"|"action_id"|"actionId"/.test(
        JSON.stringify(r.payload))) {
      throw new Error('FAIL: S05 receptionist dossier proposal not safe');
    }
    roleChecks.s05ReceptionDossier='PASS_PROPOSAL_ONLY';
  } else {
    const a=await sendRolePreview(['/rdv']);
    const b=await sendRolePreview(futureDossierProposal);
    if(a.status!==403 || b.status!==403
      || JSON.stringify(a.payload)!==JSON.stringify(b.payload)
      || JSON.stringify(b.payload).includes('CB01-N-101')) {
      throw new Error('FAIL: S06 secretary no-agenda access did not fail closed');
    }
    roleChecks.s06NoAgenda='PASS_403';
    }
  } finally {
    await roleApi.dispose();
  }
}
const browser = await chromium.launch({ headless:true });
const evidence = [];
const wallClockEvidence=[];
try {
  // Real Chromium/Vite module under two distinct browser timezones.
  // The clinical API contract stores LOCAL wall clock, not ISO UTC instants.
  for (const timezoneId of ['Africa/Casablanca','America/New_York']) {
    const tzContext=await browser.newContext({timezoneId});
    try {
      const tzPage=await tzContext.newPage();
      await tzPage.goto(appOrigin+'/login',{waitUntil:'domcontentloaded',timeout:90000});
      const rows=await tzPage.evaluate(async () => {
        const { formatAgendaWallClock }=await import('/src/utils/agendaWallClock.ts');
        return [ [0,30], [10,0], [23,30] ].map(([h,m]) => {
          const value=new Date(2026,9,18,h,m);
          return {wall:formatAgendaWallClock(value),utc:value.toISOString()};
        });
      });
      const expected=['2026-10-18T00:30:00','2026-10-18T10:00:00','2026-10-18T23:30:00'];
      if(rows.some((row,i)=>row.wall!==expected[i])
          || !rows.some(row=>!row.utc.startsWith(row.wall))) {
        throw new Error('FAIL: Agenda wall clock differs from cabinet local time '+timezoneId+' '+JSON.stringify(rows));
      }
      wallClockEvidence.push({timezoneId,rows,status:'PASS_REAL_CHROMIUM_LOCAL_WALL_CLOCK'});
    } finally {
      await tzContext.close();
    }
  }
  // The launcher belongs to MainLayout and may be visible while Dashboard
  // still shows its loading spinner. Require the REAL dashboard to finish
  // hydrating and its animation/sidebar reflow to stabilize BEFORE proof.
  const dashboardVisualProof=[];
  const assertDashboardReady=async(page,width,phase)=>{
    await page.locator('main h1').filter({hasText:/^Bonjour,/}).first()
      .waitFor({state:'visible',timeout:45000});
    await page.waitForFunction(()=>{
      const main=document.querySelector('main');
      const heading=main?.querySelector('h1');
      const text=main?.innerText||'';
      const motionRoot=heading?.closest('div[class*="max-w-"]');
      return Boolean(location.pathname==='/dashboard'
        && heading?.textContent?.trim().startsWith('Bonjour,')
        && text.includes('Nouveau Patient')
        && text.includes('Dossiers Patients')
        && !text.includes('Initialisation de votre cabinet')
        && motionRoot && Number(getComputedStyle(motionRoot).opacity)>=0.99);
    },null,{timeout:45000,polling:'raf'});
    await page.mouse.move(width-12,Math.round(page.viewportSize().height/2));
    if(width>=1280)
      await page.waitForFunction(()=>{
        const sidebar=document.querySelector('aside.sidebar-shell');
        return sidebar?.getAttribute('data-expanded')==='false'
          && Math.abs(sidebar.getBoundingClientRect().width-68)<1;
      },null,{timeout:15000,polling:'raf'});
    const proof=await page.evaluate(()=>{
      const main=document.querySelector('main');
      const heading=main?.querySelector('h1');
      const motionRoot=heading?.closest('div[class*="max-w-"]');
      return {
        path:location.pathname,
        hasGreeting:Boolean(heading?.textContent?.trim().startsWith('Bonjour,')),
        hasActions:Boolean(main?.innerText?.includes('Nouveau Patient')
          && main?.innerText?.includes('Dossiers Patients')),
        initialLoaderAbsent:!Boolean(main?.innerText?.includes('Initialisation de votre cabinet')),
        motionOpacity:motionRoot?Number(getComputedStyle(motionRoot).opacity):null,
        sidebarCollapsed:document.querySelector('aside.sidebar-shell')?.getAttribute('data-expanded')==='false',
        viewportWidth:document.documentElement.clientWidth,
      };
    });
    if(proof.path!=='/dashboard'||!proof.hasGreeting||!proof.hasActions
      ||!proof.initialLoaderAbsent||proof.motionOpacity<0.99
      ||(width>=1280&&!proof.sidebarCollapsed)||proof.viewportWidth!==width)
      throw Error('NOT_CERTIFIED: '+phase+' Dashboard not stable at '+width+' '+JSON.stringify(proof));
    dashboardVisualProof.push({width,phase,status:'PASS_REAL_LOADED_DASHBOARD',...proof});
  };
  for (const width of [390, 430, 1280, 1440, 1600, 1920]) {
    const desktop = width >= 1600;
    const docked = width >= 768 && width < 1600;
    const height = desktop ? 900 : 844;
    const context = await browser.newContext({ viewport:{width,height} });
    await context.addInitScript(({access,refresh}) => {
      localStorage.setItem('token',access);
      localStorage.setItem('refresh_token',refresh||'');
      localStorage.setItem('appMode','prod');
    }, {access:tokens.access_token,refresh:tokens.refresh_token});
    const page = await context.newPage();
    if (desktop) {
      // Synthetic history fixture: browser must render only safe text,
      // even when server records contain legacy pending-action payloads.
      await page.route('**/api/bot/sessions',route=>route.fulfill({
        status:200, contentType:'application/json',
        body:JSON.stringify([{
          id:'cb01-history',title:'CB01 Synthétique',updated_at:'2026-10-18',
        }]),
      }));
      await page.route('**/api/bot/sessions/cb01-history/messages',route=>route.fulfill({
        status:200, contentType:'application/json',
        body:JSON.stringify([{
          id:'msg-1',sender:'bot',text:'Historique synthétique consultable',
          pendingActionId:'never-execute',pendingAction:{type:'CREATE_APPOINTMENT'},
        }]),
      }));
    }
    const errors=[],writes=[];
    page.on('pageerror',error => errors.push(String(error)));
    page.on('request',req => {
      if (/\/api\/(bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(req.url())
          && req.method() !== 'GET') writes.push(req.method());
    });
    await page.goto(appOrigin+'/dashboard',{waitUntil:'domcontentloaded',timeout:90000});
    const opener=page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
    await opener.waitFor({state:'visible',timeout:30000});
    await assertDashboardReady(page,width,'BEFORE');
    await page.screenshot({path:path.join(output,'before-'+width+'.png')});
    await opener.click();
    const sidecar=page.locator('[data-cb01-associate-sidecar]');
    const overlay=page.locator('[data-ux1-c-crownbot-overlay]');
    if (desktop || docked) {
      await sidecar.waitFor({state:'visible',timeout:15000});
      if(await overlay.count()) throw new Error('FAIL: hidden duplicate chatbot mounted');
      const initialClose=page.getByRole('button',{name:'Réduire le panneau Crown Bot'});
      await initialClose.waitFor({state:'visible'});
      if (!await initialClose.evaluate(el=>el===document.activeElement)) {
        throw new Error('FAIL: focus not moved into opened sidecar on initial launch');
      }
      // Browser keyboard traversal, not a jsdom approximation: the next
      // Tab must enter the chat and Shift+Tab must return to Reduce.
      await page.keyboard.press('Tab');
      // B01: a translated-offscreen History drawer can still contain buttons.
      // Merely being a descendant of sidecar is NOT proof of visible focus.
      const tabbableInSidecar=await page.evaluate(() => {
        const el=document.activeElement;
        const panel=document.querySelector('[data-cb01-associate-sidecar]');
        const hiddenHistory=document.querySelector('[data-cb01-history-drawer]');
        if (!el || !panel || !hiddenHistory || !hiddenHistory.hasAttribute('inert')
            || hiddenHistory.getAttribute('aria-hidden')!=='true') return false;
        const rect=el.getBoundingClientRect();
        const frame=panel.getBoundingClientRect();
        const style=getComputedStyle(el);
        return Boolean(el.matches('button, input, a, select, textarea')
          && el.closest('[data-cb01-associate-sidecar]')
          && !el.closest('[inert], [aria-hidden="true"]')
          && rect.width>0 && rect.height>0
          && rect.left>=frame.left-2 && rect.right<=frame.right+2
          && rect.top>=frame.top-2 && rect.bottom<=frame.bottom+2
          && style.visibility!=='hidden' && style.display!=='none');
      });
      if (!tabbableInSidecar) {
        throw new Error('FAIL: Tab focus not visibly reachable or closed History drawer still tabbable');
      }
      await page.keyboard.press('Shift+Tab');
      if (!await initialClose.evaluate(el=>el===document.activeElement)) {
        throw new Error('FAIL: Shift+Tab did not return to Reduce');
      }
      if (desktop) {
      // B-NEW-01: real Chromium keyboard navigation of the History drawer.
      // The operator must enter History, dismiss it with Escape and return
      // to the original trigger without closing the entire sidecar.
      const historyToggle=sidecar.getByRole('button',{name:"Ouvrir l'historique Crown Bot"});
      await historyToggle.focus();
      await page.keyboard.press('Enter');
      const historyClose=sidecar.getByRole('button',{name:"Fermer l'historique Crown Bot"});
      await historyClose.waitFor({state:'visible'});
      if(!await historyClose.evaluate(el=>el===document.activeElement)) {
        throw new Error('FAIL: History open did not move focus to its close control');
      }
      const historyDrawer=sidecar.locator('[data-cb01-history-drawer]');
      if(await historyDrawer.getAttribute('aria-hidden')!=='false'
          || await historyDrawer.getAttribute('inert')!==null
          || await historyDrawer.getAttribute('role')!=='dialog'
          || await historyDrawer.getAttribute('aria-modal')!=='true') {
        throw new Error('FAIL: open History drawer remained hidden or inert');
      }
      // Real keyboard modal containment: Shift+Tab from first wraps to last,
      // Tab from last returns to first.
      const historyLast=historyDrawer.locator('button').last();
      await page.keyboard.press('Shift+Tab');
      if(!await historyLast.evaluate(el=>el===document.activeElement))
        throw new Error('FAIL: history Shift+Tab did not wrap to last control');
      await page.keyboard.press('Tab');
      if(!await historyClose.evaluate(el=>el===document.activeElement))
        throw new Error('FAIL: history Tab did not wrap to first control');
      await page.keyboard.press('Escape');
      if(await historyDrawer.getAttribute('aria-hidden')!=='true'
          || await historyDrawer.getAttribute('inert')===null
          || !await historyToggle.evaluate(el=>el===document.activeElement)
          || !await sidecar.isVisible()) {
        throw new Error('FAIL: History Escape did not restore focus without closing sidecar');
      }
      await historyToggle.click();
      await historyDrawer.getByRole('button',{name:'Ouvrir la conversation CB01 Synthétique'}).click();
      const historyView=sidecar.getByRole('region',{
        name:'Conversation archivée — lecture seule',
      });
      await historyView.getByText('Historique synthétique consultable').waitFor({state:'visible'});
      if(await sidecar.getByRole('button',{name:/Confirmer|Exécuter/i}).count()
          || await sidecar.getByText('never-execute').count()) {
        throw new Error('FAIL: history revived a historical clinical action');
      }
      await historyView.getByRole('button',{name:'Retour aux actions'}).click();
      await sidecar.getByRole('button',{name:'Mon programme'}).waitFor({state:'visible'});
      }
      if (docked) {
        await sidecar.getByRole('region',{name:'Assistant Crown Bot — consultation'}).waitFor({state:'visible'});
        if ((await sidecar.getAttribute('data-cb01-workspace-dock'))===null)
          throw Error('FAIL: medium desktop must reserve a bottom dock');
      }
    } else {
      await overlay.waitFor({state:'visible',timeout:15000});
      if(await sidecar.count()) throw new Error('FAIL: sidecar wrongly mounted on fallback');
      // CB-01 narrow web fallback exists at 390/430; 1280/1440 use a bottom dock.
      // Accessibility must not be tested only in the 1600/1920 sidecar.
      const tabs=overlay.getByRole('tablist',{name:'Vues de Crown Bot'});
      const chatTab=tabs.getByRole('tab',{name:'Chat'});
      const brainTab=tabs.getByRole('tab',{name:/Mémoire contextuelle/});
      await tabs.waitFor({state:'visible'});
      if(await chatTab.getAttribute('aria-selected')!=='true'
          || await overlay.getByRole('tabpanel').getAttribute('aria-labelledby')!=='cb01-tab-chat') {
        throw new Error('FAIL: accessible fallback first-value tab invalid at '+width);
      }
      const preview=overlay.getByRole('region',{name:'Assistant Crown Bot — consultation'});
      await preview.waitFor({state:'visible'});
      for(const label of ['Mon programme','Trouver un patient','Préparer un RDV'])
        await preview.getByRole('button',{name:label}).waitFor({state:'visible'});
      await chatTab.focus();
      await page.keyboard.press('Home');
      if(!await brainTab.evaluate(el=>el===document.activeElement)
          || await brainTab.getAttribute('aria-selected')!=='true') {
        throw new Error('FAIL: fallback Home keyboard tab navigation at '+width);
      }
      await page.keyboard.press('End');
      if(!await chatTab.evaluate(el=>el===document.activeElement)
          || await chatTab.getAttribute('aria-selected')!=='true') {
        throw new Error('FAIL: fallback End keyboard tab navigation at '+width);
      }
    }
    const result=await page.evaluate(() => {
      const root=document.documentElement;
      const sidecar=document.querySelector('[data-cb01-associate-sidecar]');
      const overlay=document.querySelector('[data-ux1-c-crownbot-overlay]');
      const main=document.querySelector('main');
      const rect=el => {
        if(!el) return null;
        const r=el.getBoundingClientRect();
        return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};
      };
      return {
        viewport:root.clientWidth,
        overflow:root.scrollWidth>root.clientWidth+2,
        main:rect(main),sidecar:rect(sidecar),overlay:rect(overlay),
        chatCount:document.querySelectorAll('[data-cb01-associate-sidecar] [aria-label="Assistant Crown Bot — consultation"], [data-ux1-c-crownbot-overlay] [aria-label="Assistant Crown Bot — consultation"]').length,
      };
    });
    if (errors.length || writes.length || result.overflow) {
      throw new Error('FAIL: browser errors, writes or page overflow at '+width);
    }
    if (desktop && (!result.sidecar || !result.main
      || result.sidecar.width < 350 || result.sidecar.width > 485
      || result.main.width < 400 || result.main.right>result.sidecar.x+3
      || result.sidecar.right > width+3)) {
      throw new Error('FAIL: sidecar does not preserve clinical workspace at '+width+
        ' '+JSON.stringify(result));
    }
    if (docked && (!result.sidecar || !result.main || result.overlay
      || result.sidecar.width < 700 || result.main.width < 700
      || result.main.bottom > result.sidecar.y+3
      || result.sidecar.bottom > height+3)) {
      throw Error('FAIL: medium desktop panel overlaps the clinical workspace at '+
        width+' '+JSON.stringify(result));
    }
    let staffSearchChecks = 'NOT_RUN_WEB_FALLBACK';
    if (desktop) {
      // S02/S04 browser-backed synthetic staff scenario, not full human UX.
      const panel=page.locator('[data-cb01-associate-sidecar]');
      // FIRST_VALUE_UI : no extra Chat-tab click after the launcher.
      const preview=panel.getByRole('region',{name:'Assistant Crown Bot — consultation'});
      await preview.waitFor({state:'visible'});
      // Real Chromium accessibility semantics and roving keyboard navigation.
      const tabs=panel.getByRole('tablist',{name:'Vues de Crown Bot'});
      await tabs.waitFor({state:'visible'});
      const chatTab=tabs.getByRole('tab',{name:'Chat'});
      const brainTab=tabs.getByRole('tab',{name:/Mémoire contextuelle/});
      if(await chatTab.getAttribute('aria-selected')!=='true'
          || await chatTab.getAttribute('tabindex')!=='0'
          || await brainTab.getAttribute('tabindex')!=='-1') {
        throw new Error('FAIL: first-value accessible Chat tab is not selected');
      }
      await chatTab.focus();
      await page.keyboard.press('ArrowLeft');
      if(!await brainTab.evaluate(el=>el===document.activeElement)
          || await brainTab.getAttribute('aria-selected')!=='true'
          || await panel.getByRole('tabpanel').getAttribute('aria-labelledby')!=='cb01-tab-brain') {
        throw new Error('FAIL: ArrowLeft must focus/select memory with its tabpanel');
      }
      await page.keyboard.press('End');
      if(!await chatTab.evaluate(el=>el===document.activeElement)
          || await chatTab.getAttribute('aria-selected')!=='true'
          || await panel.getByRole('tabpanel').getAttribute('aria-labelledby')!=='cb01-tab-chat') {
        throw new Error('FAIL: End must focus/select accessible Chat tab');
      }
      await preview.waitFor({state:'visible'});
      for (const label of ['Mon programme','Trouver un patient','Préparer un RDV']) {
        await preview.getByRole('button',{name:label}).waitFor({state:'visible'});
      }
      // WCAG 1.4.3 — measure real computed foreground/background pixels for
      // essential first-value instruction text (normal-size: at least 4.5:1).
      const firstValueContrast=await preview.locator('.bg-white').first().locator('p').first().evaluate(element => {
        // Tailwind 4 computed colors are often OKLCH, not legacy rgb().
        // Ask Chromium itself for an explicit sRGB conversion via CSS Color 4.
        const parse = value => {
          const probe=document.createElement('span');
          probe.style.color='color-mix(in srgb, '+value+' 100%, transparent)';
          document.body.appendChild(probe);
          const normalized=getComputedStyle(probe).color;
          probe.remove();
          const m=normalized.match(/^color\(srgb\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)/);
          if(!m) throw new Error('FAIL: unsupported computed color '+value+' -> '+normalized);
          return m.slice(1,4).map(Number);
        };
        const luminance=rgb=>rgb.map(v=>
          v<=0.04045 ? v/12.92 : ((v+0.055)/1.055)**2.4,
        ).reduce((a,v,i)=>a+v*[0.2126,0.7152,0.0722][i],0);
        const foreground=luminance(parse(getComputedStyle(element).color));
        const background=luminance(parse(getComputedStyle(element.parentElement).backgroundColor));
        return (Math.max(foreground,background)+0.05)/(Math.min(foreground,background)+0.05);
      });
      if(firstValueContrast < 4.5) {
        throw new Error('FAIL: first-value text contrast under WCAG 4.5:1: '+firstValueContrast);
      }
      // CB-01 FIRST_VALUE_UI: the one-click "Mon programme" is a real
      // tenant-scoped GET from the canonical agenda, not a bot mock or write.
      const cabinetDayRead=page.waitForResponse(resp=>
        new URL(resp.url()).pathname==='/api/bot/workflows/cabinet-day'
        && resp.request().method()==='GET',{timeout:15000});
      const programmeRead=page.waitForResponse(resp=>
        new URL(resp.url()).pathname==='/api/appointments/'
        && resp.request().method()==='GET',{timeout:15000});
      await preview.getByRole('button',{name:'Mon programme'}).click();
      const [cabinetDayResult,programmeResult]=await Promise.all([cabinetDayRead,programmeRead]);
      if(cabinetDayResult.status()!==200) throw new Error('FAIL: canonical day not authorized');
      const cabinetDay=await cabinetDayResult.json();
      const readUrl=new URL(programmeResult.url());
      if(cabinetDay.timezone!=='Africa/Casablanca'
         || readUrl.searchParams.get('start_date')!==cabinetDay.start_date
         || readUrl.searchParams.get('end_date')!==cabinetDay.end_date
         || !cabinetDay.start_date.startsWith(cabinetDay.day)) {
        throw new Error('FAIL: Agenda GET not scoped to server canonical business day');
      }
      if(programmeResult.status()!==200) {
        throw new Error('FAIL: Mon programme returned '+programmeResult.status());
      }
      const programme=preview.getByRole('status',{name:'Programme du jour'});
      await programme.waitFor({state:'visible'});
      if(!await programme.getByText(/Source : Agenda du cabinet.*Lecture serveur à/).count()) {
        throw new Error('FAIL: successful programme has no truthful server source');
      }
      const findPatient=async selector => {
        await preview.getByRole('button',{name:'Réinitialiser la simulation'}).click();
        await preview.getByRole('button',{name:'Trouver un patient'}).click();
        await preview.getByText('Patient : saisissez un identifiant',{exact:false}).waitFor();
        await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(selector);
        await preview.getByRole('button',{name:'Envoyer'}).click();
      };
      await findPatient('dossier:CB01-N-101');
      await preview.getByText('Patient identifié dans votre cabinet.').waitFor();
      await preview.getByText('Patient identifié : AMINA BENALI — Dossier CB01-N-101').waitFor();

      await findPatient('BENALI');
      await preview.getByText('Plusieurs patients correspondent.',{exact:false}).waitFor();
      const matches=preview.locator('[aria-label="Choisir le dossier patient"] button');
      if(await matches.count()!==2) throw new Error('FAIL: homonyms must show both choices');
      await preview.getByRole('button',{name:/AMINA BENALI.*CB01-N-101/}).click();
      await preview.getByText('Patient identifié : AMINA BENALI — Dossier CB01-N-101').waitFor();

      await findPatient(patientId);
      await preview.getByText('Plusieurs patients correspondent.',{exact:false}).waitFor();
      await preview.getByRole('button',{name:/T2 CERTIFICATION.*T2-0001/}).click();
      await preview.getByText('Patient identifié : T2 CERTIFICATION — Dossier T2-0001').waitFor();
      staffSearchChecks='PASS_DOSSIER_HOMONYMS_NUMERIC_COLLISION';

      // Owner browser: dossier lookup -> non-executable future appointment.
      // /rdv is NEVER a booking; capture actual HTTP payload and forbid action IDs.
      await preview.getByRole('button',{name:'Réinitialiser la simulation'}).click();
      await preview.getByRole('button',{name:'Préparer un RDV'}).click();
      const nextStep=async (value,expectedPrompt) => {
        await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(value);
        await preview.getByRole('button',{name:'Envoyer'}).click();
        await preview.getByText(expectedPrompt,{exact:false}).waitFor({state:'visible'});
      };
      await nextStep('BENALI','Plusieurs patients correspondent.');
      await preview.getByRole('button',{name:/AMINA BENALI.*CB01-N-101/}).click();
      await preview.getByText('Date du rendez-vous au format',{exact:false}).waitFor();
      await preview.getByText('Patient sélectionné (vérifié par le serveur) : AMINA BENALI — Dossier CB01-N-101').waitFor();
      await nextStep('2099-01-01','Heure du rendez-vous au format');
      await preview.getByText('Patient sélectionné (vérifié par le serveur) : AMINA BENALI — Dossier CB01-N-101').waitFor();
      await nextStep('10:00','Durée : 15, 30, 45 ou 60');
      await nextStep('30','Motif : consultation, détartrage ou couronne');
      await nextStep('consultation','Tapez CONFIRMER');
      await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill('CONFIRMER');
      const finalResponse=page.waitForResponse(r=>
        r.url().includes('/api/bot/workflows/preview')
        && r.request().method()==='POST',{timeout:15000});
      await preview.getByRole('button',{name:'Envoyer'}).click();
      const finalResult=await finalResponse;
      if(finalResult.status()!==200) {
        throw new Error('FAIL: synthetic dossier appointment proposal HTTP '+finalResult.status());
      }
      const finalPayload=await finalResult.json();
      if(finalPayload?.status!=='proposal_only'
        || finalPayload?.proposal?.type!=='CREATE_APPOINTMENT'
        || finalPayload?.proposal?.params?.datetime_start!=='2099-01-01T10:00:00'
        || finalPayload?.proposal?.params?.duration_minutes!==30
        || finalPayload?.proposal?.params?.motif!=='CONSULTATION'
        || !Number.isInteger(finalPayload?.proposal?.params?.patient_id)
        || finalPayload?.proposal?.params?.patient_id<=0
        || /"pending_action_id"|"pendingActionId"|"action_id"|"actionId"/.test(
          JSON.stringify(finalPayload))) {
        throw new Error('FAIL: S05 dossier appointment preview not fail-closed non-executable');
      }
      await preview.getByText('Rendez-vous proposé : aperçu uniquement, non enregistré et non exécutable.').waitFor();
      await preview.getByText('Patient sélectionné (vérifié par le serveur) : AMINA BENALI — Dossier CB01-N-101').waitFor();
      staffSearchChecks+='|PASS_OWNER_HOMONYM_RDV_IDENTITY_STABLE_PROPOSAL_ONLY|PASS_SERVER_CABINET_DAY|PASS_ARIA_TABS_KEYBOARD|PASS_FIRST_VALUE_TEXT_CONTRAST';
    }
    await assertDashboardReady(page,width,'AFTER');
    await page.screenshot({path:path.join(output,'after-'+width+'.png')});
    evidence.push({width,mode:desktop?'sidecar-reflow':docked?'workspace-bottom-dock':'web-floating-fallback',
      staffSearchChecks,
      result,errors:errors.length,writes:writes.length});
    if(desktop) {
      const closeButton=page.getByRole('button',{name:'Réduire le panneau Crown Bot'});
      await closeButton.waitFor({state:'visible'});
      // The staff scenario ended with focus on its patient-selection control.
      // Put focus back on the reducer before verifying a keyboard Escape.
      await closeButton.focus();
      // Press Escape, confirm that a keyboard-only user can close and reopen.
      await page.keyboard.press('Escape');
      await sidecar.waitFor({state:'detached'});
      const launcher=page.getByRole('button',{name:'Ouvrir CrownBot'});
      await launcher.waitFor({state:'visible'});
      if(!await launcher.evaluate(el=>el===document.activeElement)) {
        throw new Error('FAIL: Escape did not restore focus to the launcher');
      }
      await page.keyboard.press('Enter');
      await sidecar.waitFor({state:'visible'});
      // The reopened assistant must also show FIRST_VALUE without tab clicks.
      // Keep an unfinished clinical search draft while the browser equivalent
      // of 200% zoom makes the sidebar switch into narrow floating mode.
      const sidecarPreview=sidecar.getByRole('region',{name:'Assistant Crown Bot — consultation'});
      await sidecarPreview.waitFor({state:'visible',timeout:15000});
      await sidecarPreview.getByRole('button',{name:'Réinitialiser la simulation'}).click();
      await sidecarPreview.getByRole('button',{name:'Trouver un patient'}).click();
      const inProgressDraft='dossier:BROUILLON-NON-SOUMIS';
      await sidecarPreview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(inProgressDraft);
      const proxyWidth=Math.floor(width/2);
      // Reflow PROXY: half the CSS viewport width; NOT native Chrome zoom.
      await page.setViewportSize({width:proxyWidth,height});
      // The already-mounted Sidecar can remain visible before matchMedia's
      // responsive update. Require the actual dock transition; stay fail-closed.
      try {
        await page.waitForFunction(() => {
          const panel=document.querySelector('[data-cb01-associate-sidecar]');
          return panel?.hasAttribute('data-cb01-workspace-dock')
            && !document.querySelector('[data-ux1-c-crownbot-overlay]');
        },null,{timeout:15000});
      } catch {
        const diagnostic=await page.evaluate(() => ({
          width:window.innerWidth,
          wideQuery:matchMedia('(min-width: 1600px)').matches,
          dockQuery:matchMedia('(min-width: 768px)').matches,
          isDock:!!document.querySelector('[data-cb01-workspace-dock]'),
          hasOverlay:!!document.querySelector('[data-ux1-c-crownbot-overlay]'),
        }));
        throw Error('FAIL: desktop sidecar did not reflow to medium desktop dock '+
          JSON.stringify(diagnostic));
      }
      await sidecar.waitFor({state:'visible'});
      const floatingPreview=sidecar.getByRole('region',{name:'Assistant Crown Bot — consultation'});
      const floatingDraft=await floatingPreview.getByRole('textbox',{
        name:'Votre réponse de simulation',
      }).inputValue();
      if(floatingDraft!==inProgressDraft) {
        throw new Error('FAIL: 200% CSS reflow discarded unfinished patient-search draft');
      }
      const reflow=await page.evaluate(() => {
        const root=document.documentElement;
        const overlay=document.querySelector('[data-cb01-workspace-dock]');
        const box=overlay?.getBoundingClientRect();
        return {
          viewport:root.clientWidth,
          overflow:root.scrollWidth>root.clientWidth+2,
          overlay:box?{x:box.x,width:box.width,right:box.right}:null,
        };
      });
      if (reflow.overflow || !reflow.overlay ||
        reflow.overlay.x < -1 || reflow.overlay.right>proxyWidth+1) {
        throw new Error('FAIL: 200% CSS reflow proxy clipped the dock at '+width+
          ' '+JSON.stringify(reflow));
      }
      await page.screenshot({
        path:path.join(output,'reflow-proxy-200-'+width+'.png'),
      });
      // Reverse the viewport change. The same draft and conversation must
      // remain on screen; do not silently restart the patient lookup.
      await page.setViewportSize({width,height});
      await sidecar.waitFor({state:'visible'});
      if(await sidecar.getByRole('textbox',{name:'Votre réponse de simulation'}).inputValue()
          !==inProgressDraft) {
        throw new Error('FAIL: restoring desktop viewport lost patient-search draft');
      }
      await page.getByRole('button',{name:'Réduire le panneau Crown Bot'}).click();
      await sidecar.waitFor({state:'detached'});
      if(!await launcher.evaluate(el=>el===document.activeElement)) {
        throw new Error('FAIL: reducer did not restore focus after CSS reflow');
      }
      evidence[evidence.length-1].keyboard='PASS_ESCAPE_ENTER_RESTORE_FOCUS_TAB_SHIFT_TAB';
      evidence[evidence.length-1].draftSurvivesReflow='PASS_BOTH_DIRECTIONS';
      evidence[evidence.length-1].zoom200ReflowProxy=reflow;
    }
    await context.close();
  }
  // CB-01 synthetic layout-only clinical views: these are the REAL routed
  // React Agenda and PatientDetails screens, not a dashboard mockup. The tests
  // reserve a non-overlapping dock at 1280/1440 and reflow >=1600.
  // They do NOT prove that staff completed a clinical workflow or that
  // records/appointments were written, confirmed, or usable at native 200%.
  const clinicalRouteEvidence=[];
  for (const width of [1280,1440,1600,1920]) {
    for (const spec of [
      {slug:'agenda',pathname:'/agenda'},
      {slug:'patient',pathname:'/patients/'+patientId},
    ]) {
      const context=await browser.newContext({viewport:{width,height:900}});
      try {
        await context.addInitScript(({access,refresh}) => {
          localStorage.setItem('token',access);
          localStorage.setItem('refresh_token',refresh||'');
          localStorage.setItem('appMode','prod');
        },{access:tokens.access_token,refresh:tokens.refresh_token});
        const page=await context.newPage();
        const errors=[],writes=[];
        page.on('pageerror',error=>errors.push(String(error)));
        page.on('request',req=>{
          if (/\/api\/(bot\/execute|appointments\/?|patients\/?|devis\/?)/.test(req.url())
              && req.method()!=='GET') writes.push(req.method());
        });
        await page.goto(appOrigin+spec.pathname,{
          waitUntil:'domcontentloaded',timeout:90000,
        });
        await page.locator('main').first().waitFor({state:'visible',timeout:30000});
        if (new URL(page.url()).pathname!==spec.pathname) {
          throw new Error('FAIL: clinical route redirected unexpectedly: '+spec.slug);
        }
        await page.waitForFunction(()=>{
          const main=document.querySelector('main');
          return Boolean(main && (main.innerText||'').trim().length>10);
        },null,{timeout:30000});
        // The app's left navigation auto-expands on hover with a 340ms
        // width transition (68 -> 288px). Chromium initially places its
        // mouse at 0,0 over this nav. Move it into the clinical canvas and
        // wait for the actual collapsed geometry BEFORE measuring either
        // screenshot; a mid-transition baseline is not a layout regression.
        // Do not loosen the strict <=3px before/after workspace assertion.
        await page.mouse.move(width-12,450);
        await page.waitForFunction(()=>{
          const sidebar=document.querySelector('aside.sidebar-shell');
          return sidebar?.getAttribute('data-expanded')==='false'
            && Math.abs(sidebar.getBoundingClientRect().width-68)<1;
        },null,{timeout:15000});
        const baseline=await page.evaluate(()=>{
          const main=document.querySelector('main')?.getBoundingClientRect();
          return main?{left:main.left,right:main.right,width:main.width}:null;
        });
        if(!baseline || baseline.width<720) {
          throw new Error('FAIL: clinical BASELINE screen unexpectedly constrained '+
            spec.slug+' '+width+' '+JSON.stringify(baseline));
        }
        await page.screenshot({path:path.join(output,
          'clinical-'+spec.slug+'-before-'+width+'.png')});
        const opener=page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
        await opener.waitFor({state:'visible',timeout:20000});
        await opener.click();
        const expectedSidecar=width>=1600;
        const sidecar=page.locator('[data-cb01-associate-sidecar]');
        const overlay=page.locator('[data-ux1-c-crownbot-overlay]');
        const dock=page.locator('[data-cb01-workspace-dock]');
        await sidecar.waitFor({state:'visible',timeout:15000});
        if(await overlay.count() || (expectedSidecar ? (await dock.count())>0 : (await dock.count())!==1)) {
          throw new Error('FAIL: wrong assistant mode at clinical width '+width);
        }
        const geometry=await page.evaluate(()=>{
          const rect=el=>{
            const r=el?.getBoundingClientRect();
            return r?{left:r.left,right:r.right,width:r.width,top:r.top,bottom:r.bottom,height:r.height}:null;
          };
          const root=document.documentElement;
          return {
            overflow:root.scrollWidth>root.clientWidth+2,
            main:rect(document.querySelector('main')),
            sidecar:rect(document.querySelector('[data-cb01-associate-sidecar]')),
            dock:rect(document.querySelector('[data-cb01-workspace-dock]')),
            overlay:rect(document.querySelector('[data-ux1-c-crownbot-overlay]')),
            visibleClinicalText:(document.querySelector('main')?.innerText||'').trim().length>10,
          };
        });
        const commonFailure=!geometry.main || !geometry.visibleClinicalText
          || geometry.overflow || writes.length>0 || errors.length>0;
        const layoutFailure=expectedSidecar
          ? (!geometry.sidecar || geometry.overlay
            || geometry.main.width<780
            || geometry.main.right>geometry.sidecar.left+3
            || geometry.sidecar.right>width+3)
          : (!geometry.dock || geometry.overlay || !geometry.sidecar
            || Math.abs(geometry.main.width-baseline.width)>3
            || geometry.main.bottom>geometry.dock.top+3
            || geometry.dock.right>width+3
            || geometry.main.height<200);
        if(commonFailure || layoutFailure) {
          throw new Error('FAIL: clinical width safety '+
            spec.slug+' '+width+' '+JSON.stringify({
              baseline,geometry,errors:errors.length,writes:writes.length,
            }));
        }
        await page.screenshot({path:path.join(output,
          'clinical-'+spec.slug+'-after-'+width+'.png')});
        // On intermediate widths the dock restores full clinical height
        // on close without masking underlying commands.
        if(!expectedSidecar) {
          await sidecar.getByRole('button',{name:'Réduire le panneau Crown Bot'}).click();
          await sidecar.waitFor({state:'detached'});
          // PatientDetails nests its own <main> inside MainLayout's clinical
          // <main>. Compare the same OUTER workspace used by querySelector
          // in baseline/AFTER, rather than a strict locator matching both.
          const restored=await page.locator('main').first().boundingBox();
          if(!restored || Math.abs(restored.width-baseline.width)>3
              || errors.length || writes.length) {
            throw new Error('FAIL: dock close did not restore clinic page '+
              spec.slug+' '+width);
          }
        }
        clinicalRouteEvidence.push({
          route:spec.slug,width,
          status:expectedSidecar
            ? 'PASS_SYNTHETIC_SIDECAR_LAYOUT_ONLY'
            : 'PASS_SYNTHETIC_DOCK_NO_OVERLAP_AND_CLOSE',
          baseline,geometry,errors:0,writes:0,
        });
      } finally {
        await context.close();
      }
    }
  }
  // Integrated CB-01 S05/S06: authentic MainLayout/Chat/Preview, actual
  // localhost FastAPI with disposable staff. No API mocks or clinical writes.
  const realRoleBrowserEvidence=[];
  // FUE-C: first meaningful server-confirmed result, NOT just 3 CTA visible.
  const fueC={type:'FUE-C',persona:'S05_SYNTHETIC_RECEPTION',
    start:'DASHBOARD_READY_BEFORE_CROWNBOT_LAUNCH',firstValue:'NOT_RUN',
    humanE2E:'NOT_RUN',appBackend:'REAL_VITE_MAINLAYOUT_FASTAPI_SYNTHETIC_DB'};
  for (const kind of ['s06','s05']) {
    const context=await browser.newContext({
      viewport:{width:1600,height:900},storageState:roleStorageStates[kind],
    });
    try {
      await context.addInitScript(token=>{
        localStorage.setItem('token',token);
        localStorage.setItem('appMode','prod');
      },roleTokens[kind]);
      const page=await context.newPage();
      const errors=[],writes=[],statuses=[];
      page.on('pageerror',err=>errors.push(err.name));
      page.on('request',req=>{
        const p=new URL(req.url()).pathname;
        if(req.method()!=='GET' && ['/api/bot/execute','/api/appointments','/api/patients','/api/devis'].some(prefix=>p===prefix||p.startsWith(prefix+'/')))
          writes.push(req.method());
      });
      page.on('response',response=>{
        const u=new URL(response.url());
        if(u.origin===apiOrigin && u.pathname==='/api/bot/workflows/preview'
            && response.request().method()==='POST')statuses.push(response.status());
      });
      await page.goto(appOrigin+'/dashboard',{waitUntil:'domcontentloaded',timeout:90000});
      if(new URL(page.url()).pathname!=='/dashboard')
        throw Error('FAIL: CB-01 S05/S06 real application admission denied');
      const launcher=page.locator('button[aria-label="Ouvrir CrownBot"]:visible').first();
      await launcher.waitFor({state:'visible',timeout:30000});
      // Start click-to-First-Value only from a genuinely usable dashboard,
      // not MainLayout with the still-visible cabinet initialization spinner.
      await assertDashboardReady(page,1600,kind.toUpperCase()+'_FUE_BEFORE');
      const fueStartedAt=performance.now();
      const fueActions={clicks:0,typedAnswers:0};
      await launcher.click(); fueActions.clicks++;
      const panel=page.locator('[data-cb01-associate-sidecar]');
      await panel.waitFor({state:'visible',timeout:15000});
      const preview=panel.getByRole('region',{name:'Assistant Crown Bot — consultation'});
      await preview.waitFor({state:'visible'});
      const rdv=preview.getByRole('button',{name:'Préparer un RDV'});
      const nextPreviewResponse=()=>page.waitForResponse(resp=>
        new URL(resp.url()).pathname==='/api/bot/workflows/preview'
        && resp.request().method()==='POST', {timeout:20000});
      if(kind==='s06') {
        const p=nextPreviewResponse();
        await rdv.click(); fueActions.clicks++;
        const r=await p;
        if(r.status()!==403 || (await r.json())?.detail!=='Accès refusé.')
          throw Error('FAIL: S06 browser expected canonical 403; got HTTP '+r.status());
        await preview.getByText('Accès refusé pour ce parcours.').waitFor({state:'visible'});
        if((await preview.locator('[aria-label="Choisir le dossier patient"]').count())!==0
            || (await preview.getByText('AMINA BENALI',{exact:false}).count())!==0)
          throw Error('FAIL: S06 browser leaked synthetic patient identity');
      } else {
        await rdv.click(); fueActions.clicks++;
        await preview.getByText('Patient : saisissez un identifiant',{exact:false}).waitFor();
        const next=async(value,prompt)=>{
          await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill(value); fueActions.typedAnswers++;
          await preview.getByRole('button',{name:'Envoyer'}).click(); fueActions.clicks++;
          await preview.getByText(prompt,{exact:false}).waitFor({state:'visible'});
        };
        await next('dossier:CB01-N-101','Date du rendez-vous au format');
        await next('2099-01-01','Heure du rendez-vous au format');
        await next('10:00','Durée : 15, 30, 45 ou 60');
        await next('30','Motif : consultation, détartrage ou couronne');
        await next('consultation','Tapez CONFIRMER');
        await preview.getByRole('textbox',{name:'Votre réponse de simulation'}).fill('CONFIRMER'); fueActions.typedAnswers++;
        const p=nextPreviewResponse();
        await preview.getByRole('button',{name:'Envoyer'}).click(); fueActions.clicks++;
        const r=await p, data=await r.json();
        const serialized=JSON.stringify(data);
        if(r.status()!==200 || data?.status!=='proposal_only'
            || data?.proposal?.type!=='CREATE_APPOINTMENT'
            || data?.proposal?.params?.datetime_start!=='2099-01-01T10:00:00'
            || data?.proposal?.params?.duration_minutes!==30
            || !Number.isInteger(data?.proposal?.params?.patient_id)
            || ['pending_action_id','pendingActionId','action_id','actionId'].some(k=>serialized.includes('"'+k+'"')))
          throw Error('FAIL: S05 browser received actionable or invalid real backend proposal');
        await preview.getByText('Rendez-vous proposé : aperçu uniquement, non enregistré et non exécutable.').waitFor();
        // Timer stops ONLY after real HTTP proposal_only and visible non-executable UI.
        const elapsedMs=Math.round(performance.now()-fueStartedAt);
        if(!Number.isSafeInteger(elapsedMs) || elapsedMs<=0 || fueActions.clicks!==8 || fueActions.typedAnswers!==6)
          throw Error('FAIL: FUE-C observed first-value metric/actions invalid');
        Object.assign(fueC,{firstValue:'PASS_SERVER_PROPOSAL_ONLY_VISIBLE_NOT_BOOKED',
          elapsedMs,clicks:fueActions.clicks,typedAnswers:fueActions.typedAnswers,
          decisionSteps:7,httpStatus:200,clinicalWrites:0,requiredPractitionerValidation:'NOT_EXECUTABLE'});
      }
      if(errors.length || writes.length || !statuses.length
          || statuses.some(code=>code!==(kind==='s06'?403:200)))
        throw Error('FAIL: CB-01 integrated role HTTP/JS or write evidence mismatch');
      await assertDashboardReady(page,1600,kind.toUpperCase()+'_FUE_AFTER');
      const screenshot='cb01-live-api-rbac-'+kind+'-1600.png';
      await page.screenshot({path:path.join(output,screenshot)});
      realRoleBrowserEvidence.push({scenario:kind.toUpperCase(),
        source:'MAINLAYOUT_CROWNBOTCHAT_REAL_FASTAPI_SYNTHETIC_DB',
        status:kind==='s06'?'PASS_HTTP_403_VISIBLE_DENIAL':'PASS_HTTP_200_NON_EXECUTABLE_PROPOSAL',
        httpStatuses:statuses,clinicalWrites:0,pageErrors:0,screenshot,
        humanCabinetE2E:'NOT_RUN'});
    } finally { await context.close(); }
  }
  const summary={kind:'CB01_SYNTHETIC_PREVIEW_ONLY',flagDependent:true,
    firstValueOneClickChromium:'PASS_3_BUSINESS_CTA_VISIBLE_DIRECTLY_AFTER_LAUNCH',
    historyReadOnlyChromium:'PASS_SYNTHETIC_HISTORY_TEXT_NO_EXECUTE_AND_MODAL_KEYBOARD',
    bSidecarShell:true,clinicalStaffE2E:'NOT_RUN',realCabinetBefore:'NOT_CAPTURED',
    browserZoom200Percent:'CSS_WIDTH_HALVED_REFLOW_PROXY_ONLY_NOT_NATIVE_ZOOM', sourceHead:process.env.CB01_SOURCE_HEAD||'UNVERIFIED',
    roleChecks,realRoleBrowserEvidence,fueC,evidence,clinicalRouteEvidence,wallClockEvidence,
    dashboardVisualProof};
  fs.writeFileSync(path.join(output,'summary.json'),JSON.stringify(summary,null,2));
  console.log('CB01_ASSOCIATE_SIDECAR_VISUAL: PASS',JSON.stringify(evidence));
} finally {
  await browser.close();
  await api.dispose();
}
