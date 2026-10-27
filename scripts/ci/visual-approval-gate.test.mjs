import test from 'node:test';
import assert from 'node:assert/strict';
import { runGate, requiresHumanVisualReview, APPROVAL_LABEL, APPROVER_LOGIN, TOKEN_ONLY_CERTIFIED_WAVES, CERTIFIED_ISOLATED_UI_PROTOTYPES } from './visual-approval-gate.mjs';

const repo = 'hraaaaf/Digital_crown';
const pr = 910;
const old = 'a'.repeat(40);
const next = 'b'.repeat(40);

function fixture(options = {}) {
  const state = {
    sha: options.sha ?? old,
    labels: new Set(options.label === false ? [] : [APPROVAL_LABEL]),
    frontend: options.frontend !== false,
    gets: 0,
  };
  let deletes = 0;
  let posts = 0;
  const api = {
    async get(route) {
      if (options.failGet) throw Object.assign(new Error('GET unavailable'), { status: 503 });
      if (route === `/pulls/${pr}`) {
        state.gets++;
        if (options.race && state.gets > 1) state.sha = next;
        return { head: { sha: state.sha } };
      }
      if (route.startsWith(`/pulls/${pr}/files?`)) {
        if (options.overflow) return Array(100).fill({ filename: 'frontend/a.tsx' });
        return options.files ?? [{ filename: state.frontend ? 'frontend/a.tsx' : 'backend/a.py' }];
      }
      if (route.startsWith(`/issues/${pr}/labels?`))
        return [...state.labels].map(name => ({ name }));
      throw Error('Unexpected GET ' + route);
    },
    async delete(route) {
      assert.equal(route, `/issues/${pr}/labels/${APPROVAL_LABEL}`);
      deletes++;
      if (options.deleteError) throw Object.assign(new Error('DELETE forbidden'), { status: options.deleteError });
      if (options.deleteNoop) return;
      if (!state.labels.has(APPROVAL_LABEL)) throw Object.assign(new Error('404'), { status: 404 });
      state.labels.delete(APPROVAL_LABEL);
    },
    async post() {
      posts++;
      throw Error('SECURITY BLOCKER: no attestation writes allowed');
    },
  };
  const run = (action, more = {}) => runGate({
    api, repo, number: pr, action, eventHead: old,
    eventLabel: APPROVAL_LABEL, eventSender: APPROVER_LOGIN, ...more,
  });
  return {
    state, run,
    get deletes() { return deletes; },
    get posts() { return posts; },
  };
}

test('approves only the genuine owner labeled webhook for the exact SHA, without POST', async () => {
  const f = fixture();
  assert.deepEqual(await f.run('labeled'), { state: 'approved', head: old });
  assert.equal(f.posts, 0);
  assert.equal(f.deletes, 0);
});

test('fails closed for a label added by anyone other than the repo owner', async () => {
  const f = fixture();
  await assert.rejects(f.run('labeled', { eventSender: 'untrusted-contributor' }), /authorized owner/);
  assert.equal(f.posts, 0);
});

test('fails closed for absent webhook sender', async () => {
  const f = fixture();
  await assert.rejects(f.run('labeled', { eventSender: undefined }), /authorized owner/);
});

test('fails closed when an unrelated label triggers the workflow', async () => {
  const f = fixture();
  await assert.rejects(f.run('labeled', { eventLabel: 'green-build' }), /Fresh explicit/);
  assert.equal(f.posts, 0);
});

test('a stale label plus PR reopened event never blesses a head', async () => {
  const f = fixture();
  await assert.rejects(f.run('reopened'), /Fresh explicit/);
});

test('an unrelated label event cannot reuse old approval from the same SHA', async () => {
  const f = fixture();
  await assert.rejects(f.run('labeled', { eventLabel: 'unrelated' }), /Fresh explicit/);
});

test('an unlabeled event is never itself approval', async () => {
  const f = fixture();
  await assert.rejects(f.run('unlabeled'), /Fresh explicit/);
});

test('missing visual label rejects even an owner labeled webhook', async () => {
  const f = fixture({ label: false });
  await assert.rejects(f.run('labeled'), /require explicit visual approval label/);
});

test('stale webhook SHA can never approve a different current HEAD', async () => {
  const f = fixture({ sha: next });
  await assert.rejects(f.run('labeled'), /Stale webhook event/);
});

test('a HEAD race after label inspection fails closed', async () => {
  const f = fixture({ race: true });
  await assert.rejects(f.run('labeled'), /HEAD changed during/);
});

test('synchronize rejects changed UI HEAD, revokes label and confirms absence', async () => {
  const f = fixture();
  await assert.rejects(f.run('synchronize'), /approval revoked/);
  assert.equal(f.deletes, 1);
  assert.equal(f.state.labels.has(APPROVAL_LABEL), false);
});

test('synchronize removes stale label then SKIPS non-visual updates', async () => {
  const f = fixture({ frontend: false });
  assert.deepEqual(await f.run('synchronize'), { state: 'skipped-non-visual', head: old });
  assert.equal(f.deletes, 1);
  assert.equal(f.state.labels.has(APPROVAL_LABEL), false);
});

test('a non-UI synchronize without label skips safely', async () => {
  const f = fixture({ frontend: false, label: false });
  assert.deepEqual(await f.run('synchronize'), { state: 'skipped-non-visual', head: old });
});

test('synchronize with stale webhook fails without revoking a newer HEAD', async () => {
  const f = fixture({ sha: next });
  await assert.rejects(f.run('synchronize'), /Stale synchronize event/);
  assert.equal(f.deletes, 0);
});

test('label DELETE 403 must fail closed: no fake successful revocation', async () => {
  const f = fixture({ deleteError: 403 });
  await assert.rejects(f.run('synchronize'), /Failed to revoke stale visual approval/);
  assert.equal(f.state.labels.has(APPROVAL_LABEL), true);
});

test('DELETE 403 exposes only numeric HTTP status and remains fail closed', async () => {
  const f = fixture({ deleteError: 403 });
  await assert.rejects(f.run('synchronize'), error => {
    assert.equal(error.message, 'Failed to revoke stale visual approval (HTTP 403)');
    assert.doesNotMatch(error.message, /DELETE forbidden|Bearer|token/i);
    return true;
  });
  assert.equal(f.state.labels.has(APPROVAL_LABEL), true);
});

test('DELETE 500 exposes sanitized HTTP status and never approves', async () => {
  const f = fixture({ deleteError: 500 });
  await assert.rejects(f.run('synchronize'), /Failed to revoke stale visual approval \(HTTP 500\)/);
  assert.equal(f.state.labels.has(APPROVAL_LABEL), true);
});

test('label DELETE success without actual removal fails closed', async () => {
  const f = fixture({ deleteNoop: true });
  await assert.rejects(f.run('synchronize'), /label still present/);
});

test('absent label skips DELETE and still rejects changed UI HEAD', async () => {
  const f = fixture({ label: false });
  await assert.rejects(f.run('synchronize'), /approval revoked/);
  assert.equal(f.deletes, 0);
});

test('GitHub GET 503 is not mistaken for approval', async () => {
  const f = fixture({ failGet: true });
  await assert.rejects(f.run('labeled'), /GET unavailable/);
});

test('GitHub pagination overflow fails closed', async () => {
  const f = fixture({ overflow: true });
  await assert.rejects(f.run('labeled'), /pagination exceeds/);
});

test('non-UI open PR does not require visual approval', async () => {
  const f = fixture({ frontend: false, label: false });
  assert.deepEqual(await f.run('opened'), { state: 'skipped-non-visual', head: old });
});

test('the trusted gate workflow checks out ONLY the default-branch code', async () => {
  const { readFile } = await import('node:fs/promises');
  const workflow = await readFile(new URL('../../.github/workflows/ui-human-visual-approval.yml', import.meta.url), 'utf8');
  assert.match(workflow, /pull_request_target:/);
  assert.match(workflow, /ref: \$\{\{ github\.event\.repository\.default_branch \}\}/);
  assert.match(workflow, /persist-credentials: false/);
  assert.doesNotMatch(workflow, /ref:\s*\$\{\{\s*github\.event\.pull_request\.head/);
  assert.match(workflow, /node scripts\/ci\/visual-approval-gate\.mjs/);
});

test('trusted gate never tries posting an issue comment during approval', async () => {
  const f = fixture();
  await f.run('labeled');
  assert.equal(f.posts, 0);
  const { readFile } = await import('node:fs/promises');
  const source = await readFile(new URL('./visual-approval-gate.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /request\('POST',/);
});

function tokenWaiverFixture(options={}) {
  const number=1097, pinned=TOKEN_ONLY_CERTIFIED_WAVES[number], actual=options.actual??pinned.sha;
  const labels=new Set(options.hasLabel?[APPROVAL_LABEL]:[]);
  let deletes=0;
  let headReads=0;
  const api={
    async get(route) {
      if(route===`/pulls/${number}`) {
        headReads++;
        return {head:{sha:options.raceAfterHeadGet&&headReads>=options.raceAfterHeadGet?'d'.repeat(40):actual}};
      }
      if(route.startsWith(`/pulls/${number}/files?`))return (options.files??[
        {filename:'frontend/src/pages/Example.tsx'},
        {filename:pinned.path},
        {filename:'scripts/ci/theme_neutral_batch02.py'}
      ]);
      if(route.startsWith(`/issues/${number}/labels?`))return [...labels].map(name=>({name}));
      if(route===`/actions/runs/${pinned.proof}`)return {
        head_sha:options.proofSha??pinned.sha,
        status:'completed',conclusion:options.proofConclusion??'success',
        event:'pull_request',path:options.workflowPath??pinned.path
      };
      if(route===`/actions/runs/${pinned.scope}`)return {
        head_sha:pinned.sha,status:'completed',
        conclusion:options.scopeConclusion??'success',event:'pull_request',name:'CI Scope Gate'
      };
      throw new Error('Unexpected GitHub API GET '+route);
    },
    async delete(route) {
      assert.equal(route,`/issues/${number}/labels/${APPROVAL_LABEL}`);
      deletes++;labels.delete(APPROVAL_LABEL);
    },
  };
  const run=(action,more={})=>runGate({api,repo,number,action,eventHead:pinned.sha,
    eventLabel:'token-only-evidence',eventSender:'integration-bot',...more});
  return {run,labels,get deletes(){return deletes;}};
}

test('waives human signoff AUTOMATICALLY for unchanged, exact-SHA proven token-only PR',async()=>{
  const f=tokenWaiverFixture();
  assert.deepEqual(await f.run('labeled'),{
    state:'auto-token-only-verified',head:TOKEN_ONLY_CERTIFIED_WAVES[1097].sha
  });
  assert.equal(f.deletes,0);
  assert.equal(f.labels.has(APPROVAL_LABEL),false);
});

test('automatic token-only waiver preserves revocation on synchronize',async()=>{
  const f=tokenWaiverFixture({hasLabel:true});
  assert.equal((await f.run('synchronize')).state,'auto-token-only-verified');
  assert.equal(f.deletes,1);
  assert.equal(f.labels.has(APPROVAL_LABEL),false);
});

test('automatic token-only waiver rejects SHA changes without inheriting consent',async()=>{
  const f=tokenWaiverFixture({actual:'c'.repeat(40)});
  await assert.rejects(f.run('labeled',{eventHead:'c'.repeat(40)}),/require explicit visual approval label/);
});

test('automatic token-only waiver cannot bypass failing exact-diff CI',async()=>{
  const f=tokenWaiverFixture({proofConclusion:'failure'});
  await assert.rejects(f.run('labeled'),/CI proof is absent or not GREEN/);
});

test('automatic token-only waiver cannot bypass failing scope gate',async()=>{
  const f=tokenWaiverFixture({scopeConclusion:'failure'});
  await assert.rejects(f.run('labeled'),/CI proof is absent or not GREEN/);
});

test('automatic token-only waiver refuses backend or unapproved file paths',async()=>{
  const f=tokenWaiverFixture({files:[
    {filename:'frontend/src/pages/Example.tsx'},
    {filename:TOKEN_ONLY_CERTIFIED_WAVES[1097].path},
    {filename:'backend/security.py'}
  ]});
  await assert.rejects(f.run('labeled'),/unapproved path/);
});

test('automatic token-only waiver rejects workflow substitution',async()=>{
  const f=tokenWaiverFixture({workflowPath:'.github/workflows/untrusted.yml'});
  await assert.rejects(f.run('labeled'),/workflow path mismatch/);
});

test('auto-waiver manifest covers only the seven previously verified cosmetic waves',()=>{
  assert.deepEqual(Object.keys(TOKEN_ONLY_CERTIFIED_WAVES).map(Number).sort((a,b)=>a-b),[
    1097,1098,1100,1101,1102,1103,1104
  ]);
  assert.equal(TOKEN_ONLY_CERTIFIED_WAVES[1105],undefined);
});

test('automatic waiver fails closed on a HEAD race during labeled evaluation',async()=>{
  const f=tokenWaiverFixture({raceAfterHeadGet:2});
  await assert.rejects(f.run('labeled'),/HEAD changed during auto token-only validation/);
});

test('automatic waiver fails closed on a HEAD race during synchronize checks',async()=>{
  const f=tokenWaiverFixture({raceAfterHeadGet:3});
  await assert.rejects(f.run('synchronize'),/HEAD changed during auto token-only synchronize checks/);
});


test('visual gate requires review for new or changed visible UI source and media', () => {
  for (const path of [
    'frontend/src/features/imaging/StaffReviewLab.tsx',
    'frontend/src/App.tsx',
    'frontend/src/styles/theme.css',
    'frontend/src/data/copy.ts',
    'frontend/public/logo.svg',
    'frontend/staff-review-lab.html',
    'frontend/vite.config.ts',
  ]) {
    assert.equal(requiresHumanVisualReview([{ filename: path }]), true, path);
  }
});

test('non-rendered frontend files and backend-only changes do not need human screenshots', () => {
  assert.equal(requiresHumanVisualReview([
    { filename: 'backend/services/acquisition.py' },
    { filename: '.github/workflows/ci.yml' },
    { filename: 'docs/imaging.md' },
    { filename: 'frontend/src/features/imaging/StaffReviewLab.test.tsx' },
    { filename: 'frontend/src/features/imaging/StaffReviewLabApi.ts' },
    { filename: 'frontend/src/services/api.ts' },
    { filename: 'frontend/src/types/models.ts' },
    { filename: 'frontend/src/components/__tests__/Preview.test.tsx' },
    { filename: 'frontend/src/test/setup.ts' },
    { filename: 'frontend/src/vite-env.d.ts' },
    { filename: 'frontend/package-lock.json' },
    { filename: 'frontend/README.md' },
  ]), false);
});

test('one UI file dominates mixed technical changes', () => {
  assert.equal(requiresHumanVisualReview([
    { filename: 'backend/security.py' },
    { filename: 'frontend/src/features/imaging/StaffReviewLab.test.tsx' },
    { filename: 'frontend/src/features/imaging/StaffReviewLab.tsx' },
  ]), true);
});

test('renames and deletions of visible components still require exact HEAD approval', () => {
  assert.equal(requiresHumanVisualReview([
    { filename: 'frontend/src/types/Legacy.d.ts',
      status: 'renamed',
      previous_filename: 'frontend/src/pages/Legacy.tsx' },
  ]), true);
  assert.equal(requiresHumanVisualReview([
    { filename: 'frontend/src/pages/Legacy.tsx', status: 'removed' },
  ]), true);
  assert.throws(() => requiresHumanVisualReview([
    { filename: 'frontend/src/types/New.d.ts', status: 'renamed' },
  ]), /previous path/);
});

test('ambiguous frontend script cannot silently escape visual review', () => {
  assert.equal(requiresHumanVisualReview([
    { filename: 'frontend/src/hooks/useOperatorFlow.ts' },
  ]), true);
  assert.equal(requiresHumanVisualReview([
    { filename: 'frontend/src/assets/runtime-copy.json' },
  ]), true);
});

test('missing/invalid GitHub file inventory fails closed', () => {
  assert.throws(() => requiresHumanVisualReview([]), /cannot be classified/);
  assert.throws(() => requiresHumanVisualReview([{ filename: null }]), /invalid filename/);
  assert.throws(() => requiresHumanVisualReview(null), /cannot be classified/);
});

test('technical-only frontend opening skips approval (unlike actual UI TSX)', async () => {
  const f = fixture({ label: false, files: [
    { filename: 'frontend/src/features/imaging/StaffReviewLab.test.tsx' },
    { filename: 'frontend/src/features/imaging/StaffReviewLabApi.ts' },
    { filename: '.github/workflows/v15-06b-preflight.yml' },
  ] });
  assert.deepEqual(await f.run('opened'), { state: 'skipped-non-visual', head: old });
  assert.equal(f.posts, 0);
});

test('UI component mixed with non-visual tests still demands owner label', async () => {
  const f = fixture({ label: false, files: [
    { filename: 'frontend/src/features/imaging/StaffReviewLab.tsx' },
    { filename: 'frontend/src/features/imaging/StaffReviewLab.test.tsx' },
  ] });
  await assert.rejects(f.run('opened'), /require explicit visual approval label/);
});

test('pure test file update revokes stale label but does not demand new approval', async () => {
  const f = fixture({ files: [
    { filename: 'frontend/src/features/imaging/StaffReviewLab.test.tsx' },
  ] });
  assert.deepEqual(await f.run('synchronize'), { state: 'skipped-non-visual', head: old });
  assert.equal(f.deletes, 1);
  assert.equal(f.state.labels.has(APPROVAL_LABEL), false);
});

function isolatedPrototypeFixture(options={}) {
  const number=1133;
  const entry=CERTIFIED_ISOLATED_UI_PROTOTYPES[number];
  const actual=options.sha??entry.sha;
  const labels=new Set(options.label?[APPROVAL_LABEL]:[]);
  const files=options.files??entry.paths.map(filename=>({filename}));
  let deletions=0, headReads=0;
  const api={
    async get(route) {
      if(route===`/pulls/${number}`) {
        headReads++;
        return {head:{sha:options.race&&headReads>1?'c'.repeat(40):actual}};
      }
      if(route.startsWith(`/pulls/${number}/files?`))return files;
      if(route.startsWith(`/issues/${number}/labels?`))
        return [...labels].map(name=>({name}));
      if(route===`/actions/runs/${entry.proof}`)return {
        head_sha:actual,
        status:'completed',conclusion:options.proofConclusion??'success',
        event:options.proofEvent??'pull_request',
        name:options.proofName??'V1.5-06B Imaging Preflight Safety',
      };
      if(route===`/actions/runs/${entry.scope}`)return {
        head_sha:actual,status:'completed',
        conclusion:options.scopeConclusion??'success',
        event:'pull_request',name:'CI Scope Gate',
      };
      if(route===`/actions/runs/${entry.proof}/artifacts`)return {
        artifacts:options.artifacts??[{
          name:entry.artifact,expired:false,id:12771351158
        }],
      };
      throw Error('Unexpected request '+route);
    },
    async delete(route) {
      assert.equal(route,`/issues/${number}/labels/${APPROVAL_LABEL}`);
      deletions++;labels.delete(APPROVAL_LABEL);
    },
  };
  const run=(action='opened',more={})=>runGate({
    api,repo,number,action,eventHead:actual,
    eventLabel:'another-label',eventSender:'some-bot',...more
  });
  return {run,labels,get deletions(){return deletions;}};
}

test('certified isolated DEV preview bypasses owner visual approval WITHOUT asserting product UI approval',async()=>{
  const f=isolatedPrototypeFixture();
  assert.deepEqual(await f.run(), {
    state:'skipped-certified-dev-prototype',
    head:CERTIFIED_ISOLATED_UI_PROTOTYPES[1133].sha,
  });
  assert.equal(f.labels.has(APPROVAL_LABEL),false);
});

test('certified DEV prototype synchronize revokes obsolete visual label before safe skip',async()=>{
  const f=isolatedPrototypeFixture({label:true});
  assert.equal((await f.run('synchronize')).state,'skipped-certified-dev-prototype');
  assert.equal(f.deletions,1);
  assert.equal(f.labels.has(APPROVAL_LABEL),false);
});

test('changing even one byte of the DEV prototype HEAD invalidates exemption',async()=>{
  const f=isolatedPrototypeFixture({sha:'c'.repeat(40)});
  await assert.rejects(f.run(),/require explicit visual approval label/);
});

test('connecting the DEV prototype to App.tsx makes human approval mandatory',async()=>{
  const entry=CERTIFIED_ISOLATED_UI_PROTOTYPES[1133];
  const f=isolatedPrototypeFixture({files:[
    ...entry.paths.map(filename=>({filename})),
    {filename:'frontend/src/App.tsx'}
  ]});
  await assert.rejects(f.run(),/changed file inventory/);
});

test('renamed or removed preview files cannot inherit pinned waiver',async()=>{
  const entry=CERTIFIED_ISOLATED_UI_PROTOTYPES[1133];
  const files=entry.paths.map(filename=>({filename}));
  files[0]={filename:entry.paths[0],status:'renamed',previous_filename:'frontend/src/App.tsx'};
  const f=isolatedPrototypeFixture({files});
  await assert.rejects(f.run(),/changed file inventory/);
});

test('failed React/Chromium run or Scope Gate stops DEV prototype exception',async()=>{
  await assert.rejects(isolatedPrototypeFixture({proofConclusion:'failure'}).run(),/CI evidence missing or RED/);
  await assert.rejects(isolatedPrototypeFixture({scopeConclusion:'failure'}).run(),/CI evidence missing or RED/);
});

test('missing, expired or wrong artifact blocks isolated prototype exemption',async()=>{
  await assert.rejects(isolatedPrototypeFixture({artifacts:[]}).run(),/screenshot evidence missing/);
  await assert.rejects(isolatedPrototypeFixture({
    artifacts:[{name:'lot06b-desktop-staff-review-fixture',expired:true,id:12771351158}]
  }).run(),/screenshot evidence missing/);
  await assert.rejects(isolatedPrototypeFixture({
    artifacts:[{name:'unrelated',expired:false,id:12771351158}]
  }).run(),/screenshot evidence missing/);
});

test('untrusted proof workflow name or event cannot certify DEV prototype',async()=>{
  await assert.rejects(isolatedPrototypeFixture({proofEvent:'workflow_dispatch'}).run(),/CI evidence missing or RED/);
  await assert.rejects(isolatedPrototypeFixture({proofName:'random'}).run(),/CI evidence missing or RED/);
});

test('HEAD race after inspecting certified prototype fails closed',async()=>{
  await assert.rejects(isolatedPrototypeFixture({race:true}).run(),/HEAD changed during isolated prototype validation/);
});

