/**
 * Disposable GitHub Actions lab FUE contract check, never real cabinet.
 * Exercise actual ECDH envelope, encrypted Pocket permissions, device revoke.
 * No secret, JWT, manual token or PHI is printed.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  createECDH, createDecipheriv, hkdfSync,
} from 'node:crypto';

const host='http://127.0.0.1:5173';
async function request(url,options={}) {
  const response=await fetch(host+url,options);
  const body=await response.json();
  return { status:response.status, body };
}
const keyPair=createECDH('prime256v1');
keyPair.generateKeys();
const code=fs.readFileSync('/tmp/cpv2-fue-code.txt','utf8').trim();
const claim=await request('/api/mobile/claim-token',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({token:code,client_public_key_hex:keyPair.getPublicKey('hex','uncompressed')}),
});
assert.equal(claim.status,200,'Synthetic mobile ECDH claim must succeed');
assert.equal('masterKey' in claim.body,false,'Never send masterKey in clear');
const {server_public_key_hex,encrypted_master_key_hex,access_token,refresh_token,device_id}=claim.body;
assert.ok(server_public_key_hex && encrypted_master_key_hex && access_token && refresh_token && device_id);
const shared=keyPair.computeSecret(Buffer.from(server_public_key_hex,'hex'));
const wrapKey=Buffer.from(hkdfSync('sha256',shared,Buffer.alloc(32),Buffer.from('zka_mobile_bridge'),32));
function decryptGcm(blob,key) {
  const iv=blob.subarray(0,12),tag=blob.subarray(blob.length-16),ciphertext=blob.subarray(12,blob.length-16);
  const decipher=createDecipheriv('aes-256-gcm',key,iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(ciphertext),decipher.final()]);
}
const master=decryptGcm(Buffer.from(encrypted_master_key_hex,'hex'),wrapKey).toString('utf8');
assert.match(master,/^[0-9a-f]{64}$/);
const h={Authorization:'Bearer '+access_token};
const permissions=await request('/api/mobile/capabilities',{headers:h});
assert.equal(permissions.status,200);
assert.equal(typeof permissions.body.payload,'string','Pocket requires encrypted rights envelope');
const rights=JSON.parse(decryptGcm(Buffer.from(permissions.body.payload,'base64'),Buffer.from(master,'hex')));
assert.equal(rights.version,1);
assert.equal(rights.principal_kind,'staff');
for(const key of ['agenda.read','cabinet.patients.read','cabinet.clinical.read','cabinet.finance.read']){
  assert.deepEqual(rights.capabilities[key],{allowed:true,scope:'cabinet',reason:null});
}
const snapshot=await request('/api/mobile/snapshot',{headers:h});
assert.equal(snapshot.status,200);
assert.equal(snapshot.body.appointments[0].patient_name,'Patient TEST 01');
const revoked=await request('/api/mobile/revoke-device',{method:'POST',headers:h});
assert.equal(revoked.status,200);
assert.equal(revoked.body.revoked,true);
assert.equal((await request('/api/mobile/capabilities',{headers:h})).status,401);
const refreshed=await request('/api/mobile/refresh-token',{
  method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({refresh_token}),
});
assert.equal(refreshed.status,401);
const manualPage=await fetch(host+'/lab/pair');
assert.equal(manualPage.status,200);
assert.notEqual(fs.readFileSync('/tmp/cpv2-fue-code.txt','utf8').trim(),code,'A fresh code must be ready for actual phone user');
console.log('PASS SYNTHETIC FUE: ECDH encrypted pairing, AES-GCM rights, patient TEST snapshot, revocation, old refresh denied, new code ready');
