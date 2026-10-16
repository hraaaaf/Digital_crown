import test from 'node:test';
import assert from 'node:assert/strict';
import {runGate,attestationMarker,APPROVAL_LABEL} from './visual-approval-gate.mjs';

const repo='hraaaaf/Digital_crown',pr=878,old='a'.repeat(40),next='b'.repeat(40);
const signed=(sha=old,bot='github-actions[bot]')=>({
  user:{login:bot},body:attestationMarker(repo,pr,sha)+'\nVerified visual approval.',
});
function fixture(o={}){
  const d={head:o.head??old,labels:new Set(o.label===false?[]:[APPROVAL_LABEL]),
    comments:[...(o.comments??[])],frontend:o.frontend!==false,gets:0};
  let posts=0,deletes=0;
  const api={
    async get(route){
      if(o.failGet)throw Object.assign(new Error('GET unavailable'),{status:503});
      if(route===`/pulls/${pr}`){
        d.gets++;if(o.race&&d.gets>1)d.head=next;
        return {head:{sha:d.head}};
      }
      if(route.startsWith(`/pulls/${pr}/files?`)){
        if(o.overflow)return Array(100).fill({filename:'frontend/a.tsx'});
        return [{filename:d.frontend?'frontend/a.tsx':'backend/a.py'}];
      }
      if(route.startsWith(`/issues/${pr}/labels?`))
        return [...d.labels].map(name=>({name}));
      if(route.startsWith(`/issues/${pr}/comments?`))return [...d.comments];
      throw Error('Unexpected GET '+route);
    },
    async delete(route){
      assert.equal(route,`/issues/${pr}/labels/${APPROVAL_LABEL}`);
      deletes++;
      if(o.deleteError)throw Object.assign(new Error('DELETE forbidden'),{status:o.deleteError});
      if(o.deleteNoop)return;
      if(!d.labels.has(APPROVAL_LABEL))throw Object.assign(new Error('404'),{status:404});
      d.labels.delete(APPROVAL_LABEL);
    },
    async post(route,payload){
      assert.equal(route,`/issues/${pr}/comments`);
      posts++;
      if(o.postError)throw Error('POST forbidden');
      d.comments.push({user:{login:'github-actions[bot]'},body:payload.body});
    }
  };
  const run=(action,extra={})=>runGate({api,repo,number:pr,action,eventHead:old,...extra});
  return {d,run,get posts(){return posts},get deletes(){return deletes}};
}
test('positive approved exact HEAD creates trusted SHA attestation',async()=>{
  const f=fixture();
  assert.deepEqual(await f.run('labeled',{eventLabel:APPROVAL_LABEL}),{state:'approved',head:old});
  assert.equal(f.posts,1);assert.equal(f.d.comments[0].body.split('\n')[0],attestationMarker(repo,pr,old));
});
test('positive subsequent unrelated label uses existing matching bot attestation',async()=>{
  const f=fixture({comments:[signed()]});
  assert.equal((await f.run('labeled',{eventLabel:'unrelated'})).state,'approved');
  assert.equal(f.posts,0);
});
test('negative unrelated label cannot approve bare stale label',async()=>{
  const f=fixture();await assert.rejects(f.run('labeled',{eventLabel:'unrelated'}),/no trusted bot attestation/);
  assert.equal(f.posts,0);
});
test('negative old SHA attestation rejected for newer PR HEAD',async()=>{
  const f=fixture({head:next,comments:[signed(old)]});
  await assert.rejects(f.run('reopened',{eventHead:next}),/no trusted bot attestation/);
});
test('negative forged untrusted-user comment is not an approval',async()=>{
  const f=fixture({comments:[signed(old,'attacker')]});
  await assert.rejects(f.run('reopened'),/no trusted bot attestation/);
});
test('negative old webhook HEAD cannot approve newer server HEAD',async()=>{
  const f=fixture({head:next});
  await assert.rejects(f.run('labeled',{eventLabel:APPROVAL_LABEL}),/Stale webhook event/);
  assert.equal(f.posts,0);
});
test('negative mid-run PR HEAD drift rejects the approval',async()=>{
  const f=fixture({race:true});
  await assert.rejects(f.run('labeled',{eventLabel:APPROVAL_LABEL}),/HEAD changed during/);
});
test('negative missing visual approval label fails',async()=>{
  const f=fixture({label:false,comments:[signed()]});
  await assert.rejects(f.run('labeled',{eventLabel:APPROVAL_LABEL}),/require explicit visual approval label/);
});
test('synchronize revokes label, checks absence and deliberately fails',async()=>{
  const f=fixture();await assert.rejects(f.run('synchronize'),/approval revoked/);
  assert.equal(f.d.labels.size,0);assert.equal(f.deletes,1);
});
test('synchronize revokes even with non-frontend diff',async()=>{
  const f=fixture({frontend:false});await assert.rejects(f.run('synchronize'),/approval revoked/);
  assert.equal(f.d.labels.size,0);
});
test('non-UI synchronize without visual label stays green',async()=>{
  const f=fixture({frontend:false,label:false});
  assert.deepEqual(await f.run('synchronize'),{state:'skipped-non-ui',head:old});
  assert.equal(f.deletes,0);
});
test('stale synchronize webhook cannot revoke approval for a newer HEAD',async()=>{
  const f=fixture({head:next});
  await assert.rejects(f.run('synchronize'),/Stale synchronize event/);
  assert.equal(f.deletes,0);
  assert.equal(f.d.labels.has(APPROVAL_LABEL),true);
});
test('negative DELETE 403 must not silently pass',async()=>{
  const f=fixture({deleteError:403});
  await assert.rejects(f.run('synchronize'),/Failed to revoke stale visual approval/);
  assert.equal(f.d.labels.size,1);
});
test('negative DELETE success response but label still present fails',async()=>{
  const f=fixture({deleteNoop:true});
  await assert.rejects(f.run('synchronize'),/label still present/);
});
test('DELETE 404 and verified absent label safely rejects old approval',async()=>{
  const f=fixture({label:false});await assert.rejects(f.run('synchronize'),/approval revoked/);
});
test('negative GET 503 fails closed',async()=>{
  const f=fixture({failGet:true});await assert.rejects(f.run('synchronize'),/GET unavailable/);
});
test('negative posting attestation failure rejects approval',async()=>{
  const f=fixture({postError:true});
  await assert.rejects(f.run('labeled',{eventLabel:APPROVAL_LABEL}),/POST forbidden/);
});
test('negative pagination overflow is not interpreted as success',async()=>{
  const f=fixture({overflow:true});await assert.rejects(f.run('reopened'),/pagination exceeds/);
});
test('non-UI PR can skip human signoff without labels',async()=>{
  const f=fixture({frontend:false,label:false});
  assert.deepEqual(await f.run('opened'),{state:'skipped-non-ui',head:old});
});
test('static privilege boundary never checks out pull_request head',async()=>{
  const {readFile}=await import('node:fs/promises');
  const content=await readFile(new URL('../../.github/workflows/ui-human-visual-approval.yml',import.meta.url),'utf8');
  assert.match(content,/pull_request_target:/);
  assert.match(content,/ref: \$\{\{ github\.event\.repository\.default_branch \}\}/);
  assert.match(content,/persist-credentials: false/);
  assert.doesNotMatch(content,/ref:\s*\$\{\{\s*github\.event\.pull_request\.head/);
  assert.match(content,/node scripts\/ci\/visual-approval-gate\.mjs/);
});
