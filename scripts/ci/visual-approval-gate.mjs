/**
 * The trusted pull_request_target:labeled workflow run itself attests the approved
 * PR HEAD, without requiring a separate GitHub API issue-comment write.
 * The runner MUST execute this script from the trusted default branch only.
 */
import { readFile } from 'node:fs/promises';

export const APPROVAL_LABEL='visual-approved-by-achraf';
export const APPROVER_LOGIN='hraaaaf';
const SHA=/^[0-9a-f]{40}$/;
const REPO=/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

function valid(v,test,which){ if(!test) throw new Error('Invalid '+which); return v; }
async function pages(api,url) {
  const all=[];
  for(let page=1;page<=100;page++){
    const rows=await api.get(`${url}${url.includes('?')?'&':'?'}per_page=100&page=${page}`);
    if(!Array.isArray(rows)) throw new Error('GitHub pagination is not an array');
    all.push(...rows);
    if(rows.length<100)return all;
  }
  throw new Error('GitHub pagination exceeds 100 pages: fail closed');
}
const head=async(api,pr)=>{
  const result=await api.get(`/pulls/${pr}`);
  return valid(result?.head?.sha,SHA.test(result?.head?.sha??''),'current PR HEAD');
};
const hasLabel=async(api,pr)=>
  (await pages(api,`/issues/${pr}/labels`)).some(x=>x?.name===APPROVAL_LABEL);
/** Owner's 25 Oct 2026 waiver: exact, independently evidenced token-only waves.
 * This is deliberately SHA-bound: an altered diff never inherits the waiver.
 * Future waves require their own exact-diff + build/contrast proof and a
 * trusted manifest update, NOT a fake owner visual approval label.
 */
export const TOKEN_ONLY_CERTIFIED_WAVES=Object.freeze({
  1097:{sha:'722d34edbbfd7235b7bb768b6b8012fb0740126b',proof:40241662730,scope:40241662872,path:'.github/workflows/app-theme-neutral-bulk-wave02.yml'},
  1098:{sha:'310354cf7600799b076aa4ffb84d6d3f52c8eb16',proof:40242074409,scope:40242074395,path:'.github/workflows/app-theme-neutral-bulk-wave03.yml'},
  1100:{sha:'23bd6acaf0f652e00383fa96f2dfc87c7e8fe6df',proof:40243194930,scope:40243195164,path:'.github/workflows/app-theme-neutral-bulk-wave04.yml'},
  1101:{sha:'e841fa786405d975a40e7b6ea2c31fb2ba31a246',proof:40245197477,scope:40245197605,path:'.github/workflows/app-theme-status-wave05.yml'},
  1102:{sha:'db5eeca6991c8560d4984a5f83b5afcf2d0c76bf',proof:40246248646,scope:40246248714,path:'.github/workflows/app-theme-neutral-wave06.yml'},
  1103:{sha:'ede172d1c25891e0c2e40f21eb73e2f02eca7532',proof:40247331818,scope:40247331868,path:'.github/workflows/app-theme-neutral-wave07.yml'},
  1104:{sha:'7a209b5d78de51e0ccf9a8d7fb599e63d3caf40d',proof:40249242088,scope:40249242098,path:'.github/workflows/app-theme-neutral-wave08.yml'},
  1112:{sha:'713015966650f5c8b22eccce77c5fd884c9baefd',proof:40359767052,scope:40359767295,path:'.github/workflows/theme-wave09-cosmetic.yml',oracle:'scripts/ci/theme_wave09_cosmetic.py',sources:['frontend/src/features/admin/SetupWizard/steps/Step1Identity.tsx','frontend/src/features/admin/SetupWizard/steps/Step2Specialties.tsx','frontend/src/features/admin/SetupWizard/steps/Step7Confirmation.tsx']},
  1113:{sha:'ad73a1064315bc4d00f75bd617ee96a1bb9b2eb3',proof:40359133018,scope:40359132940,path:'.github/workflows/theme-wave10-cosmetic.yml',oracle:'scripts/ci/theme_wave10_cosmetic.py',sources:['frontend/src/features/admin/SetupWizard/steps/Step5Design.tsx']},
  1114:{sha:'052f28e8896e096bd17e4ee35cb9f8a49be07d74',proof:40359802932,scope:40359803238,path:'.github/workflows/theme-wave11-cosmetic.yml',oracle:'scripts/ci/theme_wave11_cosmetic.py',sources:['frontend/src/components/PWAInstallPrompt.tsx','frontend/src/pages/ForgotPasswordPage.tsx']},
});
async function verifiedTokenOnlyWaiver(api,number,actual,files) {
  const entry=TOKEN_ONLY_CERTIFIED_WAVES[number];
  if(!entry||entry.sha!==actual)return false;
  // Exact head plus a bounded file inventory: no API, auth, RBAC or backend.
  const paths=files.map(x=>x?.filename);
  if(!paths.length||!paths.some(p=>typeof p==='string'&&p.startsWith('frontend/src/')&&p.endsWith('.tsx')))
    throw new Error('Pinned token-only wave has no TSX source change');
  // New waves require an exact trusted file inventory; old waves retain their proven contract.
  const allowlist=entry.sources ? new Set([...entry.sources,entry.path,entry.oracle]) : null;
  if(allowlist && (paths.length!==allowlist.size || new Set(paths).size!==paths.length))
    throw new Error('Pinned token-only wave file inventory mismatch');
  for(const p of paths) {
    if(typeof p!=='string'||(allowlist ? !allowlist.has(p) : !(p.startsWith('frontend/src/')&&p.endsWith('.tsx')||p===entry.path||p==='scripts/ci/theme_neutral_batch02.py')))
      throw new Error('Pinned token-only wave includes an unapproved path');
  }
  if(!paths.includes(entry.path))throw new Error('Pinned token-only proof workflow is absent');
  for(const [runId,expectedPath] of [[entry.proof,entry.path],[entry.scope,null]]) {
    const run=await api.get(`/actions/runs/${runId}`);
    if(run?.head_sha!==actual||run?.status!=='completed'||run?.conclusion!=='success'||run?.event!=='pull_request')
      throw new Error('Pinned token-only CI proof is absent or not GREEN on exact SHA');
    if(expectedPath && run?.path!==expectedPath)
      throw new Error('Pinned token-only CI workflow path mismatch');
    if(!expectedPath && run?.name!=='CI Scope Gate')
      throw new Error('Pinned token-only CI scope workflow mismatch');
  }
  return true;
}

/** A pinned cosmetic-wave PR must never escape attestation by removing its last TSX. */
function requirePinnedSource(number,files){
  const entry=TOKEN_ONLY_CERTIFIED_WAVES[number];
  if(entry?.sources && !files.some(x=>typeof x?.filename==='string'&&entry.sources.includes(x.filename)))
    throw new Error('Pinned token-only wave file inventory mismatch');
}
/** Only the trusted, owner-created approval label event may approve a UI HEAD. */
export async function runGate({api,repo,number,action,eventHead,eventLabel,eventSender}){
  valid(repo,REPO.test(repo),'repository');
  valid(number,Number.isSafeInteger(number)&&number>0,'PR number');
  valid(eventHead,SHA.test(eventHead),'event HEAD');
  valid(action,['opened','reopened','synchronize','labeled','unlabeled'].includes(action),'event action');

  // Even if the changed-file list no longer contains frontend/, a new HEAD
  // must revoke any existing visual label and CONFIRM it disappeared.
  if(action==='synchronize'){
    const actual=await head(api,number);
    if(actual!==eventHead)throw new Error('Stale synchronize event: HEAD differs from PR HEAD');
    const files=await pages(api,`/pulls/${number}/files`);
    requirePinnedSource(number,files);
    const touchesUI=files.some(x=>typeof x?.filename==='string'&&x.filename.startsWith('frontend/'));
    const priorLabel=await hasLabel(api,number);
    // Do not block back-end/docs PRs that have never needed visual approval.
    // An existing label, even on a non-UI PR, must still be revoked.
    if(!touchesUI&&!priorLabel)return {state:'skipped-non-ui',head:actual};
    if(priorLabel){
      try{ await api.delete(`/issues/${number}/labels/${APPROVAL_LABEL}`); }
      catch(error){
        if(error?.status!==404)throw new Error(`Failed to revoke stale visual approval (HTTP ${error?.status??'unknown'})`,{cause:error});
      }
    }
    if(await hasLabel(api,number))
      throw new Error('Stale visual approval label still present after DELETE');
    if((await head(api,number))!==actual)
      throw new Error('PR HEAD changed during approval revocation');
    if(await verifiedTokenOnlyWaiver(api,number,actual,files)) {
      if((await head(api,number))!==actual)throw new Error('PR HEAD changed during auto token-only synchronize checks');
      return {state:'auto-token-only-verified',head:actual};
    }
    throw new Error('PR HEAD changed: approval revoked; new screenshots and explicit approval required');
  }

  const files=await pages(api,`/pulls/${number}/files`);
  requirePinnedSource(number,files);
  if(!files.some(x=>typeof x?.filename==='string'&&x.filename.startsWith('frontend/')))
    return {state:'skipped-non-ui',head:await head(api,number)};

  const actual=await head(api,number);
  if(actual!==eventHead)throw new Error('Stale webhook event: PR HEAD differs from event HEAD');
  if(await verifiedTokenOnlyWaiver(api,number,actual,files)) {
    if((await head(api,number))!==actual)throw new Error('PR HEAD changed during auto token-only validation');
    return {state:'auto-token-only-verified',head:actual};
  }
  if(!(await hasLabel(api,number)))throw new Error('UI changes require explicit visual approval label');

  // The trusted GitHub Actions check is the durable SHA-bound attestation.
  // No PR comment writes; event identity + SHA come from GitHub's webhook,
  // never from untrusted PR code.
  if(action!=='labeled'||eventLabel!==APPROVAL_LABEL)
    throw new Error('Fresh explicit visual approval label event required');
  if(eventSender!==APPROVER_LOGIN)
    throw new Error('Visual approval label must be added by the authorized owner');
  if((await head(api,number))!==actual)
    throw new Error('PR HEAD changed during visual approval checks');
  if(!(await hasLabel(api,number)))
    throw new Error('Visual approval label disappeared during verification');

  return {state:'approved',head:actual};
}

export function githubApiClient({token,repo}){
  valid(token,typeof token==='string'&&token.length>0,'token');
  valid(repo,REPO.test(repo),'repository');
  const request=async(method,route,body)=>{
    const response=await fetch(`https://api.github.com/repos/${repo}${route}`,{
      method,
      headers:{
        Authorization:`Bearer ${token}`,
        Accept:'application/vnd.github+json',
        'X-GitHub-Api-Version':'2022-11-28',
        'User-Agent':'DigitalCrown-VisualApprovalGate',
        ...(body===undefined?{}:{'Content-Type':'application/json'}),
      },
      ...(body===undefined?{}:{body:JSON.stringify(body)}),
    });
    if(!response.ok){
      // Never log untrusted response bodies or credentials in privileged CI.
      const error=new Error(`GitHub API ${method} failed (${response.status})`);
      error.status=response.status;
      throw error;
    }
    return response.status===204?null:response.json();
  };
  return {
    get:r=>request('GET',r),
    delete:r=>request('DELETE',r),
  };
}
async function main(){
  const payload=JSON.parse(await readFile(process.env.GITHUB_EVENT_PATH,'utf8'));
  const repo=process.env.GITHUB_REPOSITORY;
  try{
    const result=await runGate({
      api:githubApiClient({token:process.env.GH_TOKEN,repo}),
      repo,number:payload?.pull_request?.number,
      action:payload?.action,eventHead:payload?.pull_request?.head?.sha,
      eventLabel:payload?.label?.name,eventSender:payload?.sender?.login,
    });
    console.log(`PASS trusted GitHub Action attestation: ${result.state}, PR HEAD ${result.head}`);
  }catch(error){
    console.error(`::error::Visual gate fails closed: ${error.message}`);
    process.exitCode=1;
  }
}
if(process.argv[1]&&import.meta.url===`file://${process.argv[1]}`)
  await main();
