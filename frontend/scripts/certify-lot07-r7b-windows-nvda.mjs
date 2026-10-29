/**
 * LOT07 R7B — real NVDA screen reader on hosted Windows, genuine authenticated
 * React + FastAPI synthetic Cabinet. This is not DOM/ARIA-only certification.
 * Never retain spoken medical/credentials text; persist ONLY bounded booleans.
 */
import { nvda } from '@guidepup/guidepup';

const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const indicators={
  command:s=>/ouvrir sur un autre [ée]cran/i.test(s)&&/button|bouton/i.test(s),
  comparison:s=>/\bT\s*0\b.{0,90}\bT\s*2\b/i.test(s)&&/button|bouton/i.test(s),
  popupHeading:s=>/suivi orthodontique/i.test(s)&&/heading|titre|en-t[eê]te/i.test(s),
  popupTimepoint:s=>/\bT0\b/i.test(s)&&/heading|titre|en-t[eê]te/i.test(s),
};
export async function certifyR7RealWindowsNvda({page,check,report,capture}) {
  if(process.platform!=='win32'||process.env.GITHUB_ACTIONS!=='true'||
     process.env.DIGITALCROWN_ISOLATED_RUNTIME!=='1'||
     process.env.LOT07_R7_NVDA_CERT!=='1'){
    throw Error('REFUSED: real NVDA only in isolated Windows GitHub Actions');
  }
  const evidence={
    tool:'guidepup actual Windows NVDA speech',
    realNvdaStarted:false,spokenRoles:{
      command:false,comparison:false,popupHeading:false,popupTimepoint:false,
    },
    popupActual:false,pass:false,physicalSecondDisplay:false,
    osDisplayDpi200:false,humanClinicalApproved:false,errors:[],
    speechDiagnostics:[],
  };
  report.r7Nvda=evidence;
  let active=false,popup=null;
  const record=async(stage='unspecified')=>{
    const raw=await nvda.spokenPhraseLog();
    const phrases=(Array.isArray(raw)?raw:[raw]).map(String);
    for(const [k,test] of Object.entries(indicators)){
      if(phrases.some(test))evidence.spokenRoles[k]=true;
    }
    // Only Boolean metadata, never capture speech strings (may include PHI).
    const meta={stage,count:phrases.length,
      buttonRole:phrases.some(v=>/button|bouton/i.test(v)),
      headingRole:phrases.some(v=>/heading|titre|en-t[eê]te/i.test(v)),
      openName:phrases.some(v=>/ouvrir sur un autre [ée]cran/i.test(v)),
      comparisonName:phrases.some(v=>/\bT\s*0\b.{0,90}\bT\s*2\b/i.test(v)),
      roles:{...evidence.spokenRoles}};
    evidence.speechDiagnostics.push(meta);
    console.log('LOT07_R7B_NVDA_SPEECH_META',JSON.stringify(meta));
  };
  const navigate=async(keys,count)=>{
    for(let i=0;i<count;i++){
      try{
        if(keys==='next')await nvda.next();
        else await nvda.perform(nvda.keyboardCommands.moveToNextFormField);
      }catch(e){
        evidence.errors.push(keys+' navigation '+String(e).slice(0,130));
        break;
      }
      await sleep(140);
      await record(keys+'-'+i);
      if(keys==='forms'&&evidence.spokenRoles.command&&evidence.spokenRoles.comparison)break;
    }
  };
  try{
    const trigger=page.getByRole('button',{name:'Ouvrir sur un autre écran'});
    await trigger.waitFor({state:'visible',timeout:25000});
    await page.waitForFunction(()=>{
      const button=Array.from(document.querySelectorAll('button'))
        .find(el=>(el.textContent||'').includes('Ouvrir sur un autre écran'));
      return Boolean(button&&!button.disabled);
    },null,{timeout:30000});
    check('r7b-nvda-real-react-button-before-screenreader',await trigger.isEnabled());
    await page.bringToFront();
    await nvda.start({capture:true});
    active=true;evidence.realNvdaStarted=true;
    await sleep(850);
    await nvda.clearSpokenPhraseLog();
    try{await nvda.perform(nvda.keyboardCommands.exitFocusMode);}catch{}
    try{await nvda.press('Control+Home');}catch{}
    await record('document-home');
    // Explicitly visit real browser controls before relying on NVDA's browse
    // cursor. No DOM-derived "spoken" success and no mocked screen reader.
    const pair=page.getByRole('button',{name:/T0\s*→\s*T2/});
    await pair.waitFor({state:'visible',timeout:20000});
    await pair.focus();
    await sleep(550);
    await record('focused-real-pair');
    await nvda.press('Tab');
    await sleep(550);
    await record('NVDA-real-tab-after-pair');
    await trigger.focus();
    await sleep(550);
    await record('focused-real-presenter');
    await nvda.press('Shift+Tab');
    await sleep(550);
    await record('NVDA-real-shift-tab');
    await navigate('forms',18);
    if(!evidence.spokenRoles.command||!evidence.spokenRoles.comparison){
      try{await nvda.press('Control+Home');}catch{}
      await navigate('next',75);
    }
    check('r7b-nvda-reads-canonical-compare-and-open-buttons',
      evidence.spokenRoles.command&&evidence.spokenRoles.comparison,
      {roles:evidence.spokenRoles,
        recentDiagnostics:evidence.speechDiagnostics.slice(-8)});
    // The actual popup is opened by the authenticated parent browser; no
    // intercepted routes or second bearer token. NVDA visits the popup OS UI.
    const [child]=await Promise.all([
      page.waitForEvent('popup',{timeout:20000}),trigger.click(),
    ]);
    popup=child;
    await child.locator('[data-testid="r6d-readonly-presenter"]')
      .waitFor({state:'visible',timeout:20000});
    evidence.popupActual=true;
    await child.bringToFront();
    await child.locator('h1').focus().catch(()=>{});
    await sleep(500);
    await nvda.clearSpokenPhraseLog();
    try{await nvda.perform(nvda.keyboardCommands.exitFocusMode);}catch{}
    try{await nvda.press('Control+Home');}catch{}
    await navigate('next',42);
    check('r7b-nvda-reads-popup-headings-and-T0',
      evidence.spokenRoles.popupHeading&&evidence.spokenRoles.popupTimepoint,
      {roles:evidence.spokenRoles});
    check('r7b-nvda-popup-has-no-editable-controls',
      await child.locator('input,textarea,select,button,form,[contenteditable="true"]').count()===0);
    await capture(child,'r7b-windows-NVDA-popup-TARGET');
    evidence.pass=true;
    return evidence;
  }finally{
    try{if(active)await nvda.stop();}catch(e){evidence.errors.push('stop '+String(e).slice(0,130));}
    try{if(popup&&!popup.isClosed())await popup.close();}catch{}
  }
}
