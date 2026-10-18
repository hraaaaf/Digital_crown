// LOT07/07-C: limited local OCR of publicly advertised Orthalis Connect demo.
// Never print text recognized in the screenshot, OCR lines, cookies, images, or raw URLs.
// OCR is a weak heuristic to classify an unauthenticated remote GUI, never a business test.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import crypto from "node:crypto";
import {spawnSync} from "node:child_process";
const filename=process.argv[2];
if(!filename) throw new Error("REA browser scenario file required");
const evidence=JSON.parse(fs.readFileSync(filename,"utf8"));
const steps=evidence.normalized_result?.steps || [];
const flags=[
 ["login",/^(?:connexion|connecter|login|sign\s*in|identifiant|password|mot\s+de\s+passe)$/i],
 ["planning",/^(?:planning|agenda)$/i],
 ["patients",/^(?:patient|patients)$/i],
 ["orthalis",/^(?:orthalis)$/i],
 ["kitview",/^(?:kitview)$/i],
 ["ceph",/^(?:ceph)$/i],
 ["disconnect",/^(?:déconnecté|deconnecte|déconnexion|disconnected|disconnection)$/i]
];
function pickScreenshot(st) {
 const obj=st?.artifacts?.screenshot;
 if(obj?.state!=="captured")return null;
 const v=obj.value;
 if(v?.media_type && v.media_type!=="image/png")return null;
 const b64=v?.data_base64;
 if(typeof b64!=="string"||!b64.startsWith("iVBORw0KGgo"))return null;
 const bytes=Buffer.from(b64,"base64");
 if(bytes.length<100||bytes.subarray(0,8).toString("hex")!=="89504e470d0a1a0a")return null;
 return bytes;
}
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),"lot07-07c-rea-ocr-"));
const results=[];
try{
 const bin=spawnSync("which",["tesseract"],{encoding:"utf8",timeout:1500});
 const available=bin.status===0;
 for(const step of steps){
   const bytes=pickScreenshot(step);
   const r={step:step.step_id,screenshot_captured:!!bytes,ocr_engine_available:available,
     ocr_scope:"entire_public_demo_screenshot_NOT_GUI_PROOF",
     recognized_words_count:null,keyword_flags:{},confidence_ge_45_words:null};
   if(!bytes){results.push(r);continue;}
   r.png_sha256=crypto.createHash("sha256").update(bytes).digest("hex");
   if(!available){results.push(r);continue;}
   const file=path.join(tmp,"screen-"+results.length+".png");
   fs.writeFileSync(file,bytes,{mode:0o600});
   const parsed=spawnSync("tesseract",[file,"stdout","--psm","11","tsv"],{encoding:"utf8",timeout:18000,maxBuffer:2_000_000});
   if(parsed.status!==0){r.ocr_failed=true;results.push(r);continue;}
   const lines=(parsed.stdout||"").split(/\r?\n/);
   const words=[];
   for(const line of lines.slice(1)){
     const fields=line.split("\t");
     if(fields.length<12)continue;
     const text=fields.slice(11).join("\t").trim();
     const confidence=Number(fields[10]);
     if(text && Number.isFinite(confidence) && confidence>=45) words.push({text,confidence});
   }
   r.recognized_words_count=words.length;
   r.confidence_ge_45_words=words.length;
   const normalized=words.map(x=>x.text.toLowerCase());
   for(const [name,regex] of flags)r.keyword_flags[name]=normalized.some(x=>regex.test(x));
   results.push(r);
 }
} finally {fs.rmSync(tmp,{recursive:true,force:true});}
console.log("REA_REMOTE_GUI_OCR_HEURISTIC="+JSON.stringify({
  protocol:"LOT07_07C_UNAUTH_DEMO_GUI_READINESS",
  process:"tesseract_LOCAL_ONLY_ON_PUBLIC_REA_SCREENSHOTS",
  images_uploaded:false,
  raw_OCR_text_recorded:false,
  screenshot_count:results.length,
  captures:results,
  warning:"FULL_SNAPSHOT_OCR_INCLUDES_LANDING_PAGE. Even keywords inside GUI cannot establish safe interactions, task flow, native installation or any patient identity."
}));
