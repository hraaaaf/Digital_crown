/**
 * Visual approval is valid only for the exact HEAD attested by the trusted bot.
 * This module runs on pull_request_target from a TRUSTED BASE checkout only.
 */
import { readFile } from 'node:fs/promises';

export const APPROVAL_LABEL='visual-approved-by-achraf';
export const ATTESTATION_PREFIX='dc-human-visual-approval:v1';
const SHA=/^[0-9a-f]{40}$/;
const REPO=/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const BOT='github-actions[bot]';

function valid(v,test,which){ if(!test) throw new Error('Invalid '+which); return v; }
export function attestationMarker(repo,number,head){
  valid(repo,REPO.test(repo),'repository');
  valid(number,Number.isSafeInteger(number)&&number>0,'PR number');
  valid(head,SHA.test(head),'head SHA');
  return `<!-- ${ATTESTATION_PREFIX} repo=${repo} pr=${number} sha=${head} -->`;
}
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
const hasAttestation=async(api,repo,pr,sha)=>{
  const marker=attestationMarker(repo,pr,sha);
  return (await pages(api,`/issues/${pr}/comments`)).some(x=>
    x?.user?.login===BOT && typeof x.body==='string' &&
    x.body.split('\n')[0]===marker);
};

/** An unrelated label action can NEVER bless a stale approval label. */
export async function runGate({api,repo,number,action,eventHead,eventLabel}){
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
    const touchesUI=files.some(x=>typeof x?.filename==='string'&&x.filename.startsWith('frontend/'));
    const priorLabel=await hasLabel(api,number);
    // Do not block back-end/docs PRs that have never needed visual approval.
    // An existing label, even on a non-UI PR, must still be revoked.
    if(!touchesUI&&!priorLabel)return {state:'skipped-non-ui',head:actual};
    try{ await api.delete(`/issues/${number}/labels/${APPROVAL_LABEL}`); }
    catch(error){
      if(error?.status!==404)throw new Error('Failed to revoke stale visual approval',{cause:error});
    }
    if(await hasLabel(api,number))
      throw new Error('Stale visual approval label still present after DELETE');
    if((await head(api,number))!==actual)
      throw new Error('PR HEAD changed during approval revocation');
    throw new Error('PR HEAD changed: approval revoked; new screenshots and explicit approval required');
  }

  const files=await pages(api,`/pulls/${number}/files`);
  if(!files.some(x=>typeof x?.filename==='string'&&x.filename.startsWith('frontend/')))
    return {state:'skipped-non-ui',head:await head(api,number)};

  const actual=await head(api,number);
  if(actual!==eventHead)throw new Error('Stale webhook event: PR HEAD differs from event HEAD');
  if(!(await hasLabel(api,number)))throw new Error('UI changes require explicit visual approval label');

  if(action==='labeled'&&eventLabel===APPROVAL_LABEL){
    const marker=attestationMarker(repo,number,actual);
    await api.post(`/issues/${number}/comments`,{
      body:`${marker}\nVisual approval label accepted for exact PR HEAD \`${actual}\`. New commits invalidate it.`,
    });
  }
  if(!(await hasAttestation(api,repo,number,actual)))
    throw new Error('Approval label has no trusted bot attestation for current HEAD');
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
    post:(r,b)=>request('POST',r,b),
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
      eventLabel:payload?.label?.name,
    });
    console.log(`PASS visual gate: ${result.state}, PR HEAD ${result.head}`);
  }catch(error){
    console.error(`::error::Visual gate fails closed: ${error.message}`);
    process.exitCode=1;
  }
}
if(process.argv[1]&&import.meta.url===`file://${process.argv[1]}`)
  await main();
