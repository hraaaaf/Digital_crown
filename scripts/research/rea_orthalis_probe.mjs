// LOT07/07-C research-only shape audit. Never logs field values, names,
// complete URLs, headers, cookies, screenshots, or patient content.
import fs from 'node:fs';
import crypto from 'node:crypto';
const files = process.argv.slice(2);
if (files.length < 2) throw new Error('inspection and scenario files required');
const get = p => JSON.parse(fs.readFileSync(p,'utf8'));
const inspection=get(files[0]);
const scenario=get(files[1]);
const kind=v=>v===null?'null':Array.isArray(v)?'array':typeof v;
const keys=o=>(o && typeof o==='object' && !Array.isArray(o))?Object.keys(o).sort().slice(0,32):[];
const structuralKeys=['frames','frame','childFrames','dom','accessibility','ax','nodes','documents','screenshot','result','steps','scenario','captures','artifacts','iframe','url','navigation','session','network','targets'];
const counters={};
const evidenceShapes=[];
const hasTerms=new Set();
const approvedTerms=['orthalis','kitview','ceph','dentapoche','fiche de synthese','fiche de synthèse','planning','rendez-vous','agenda','patient','aide'];
let visited=0;
function walk(v,p='',d=0){
 if(!v || d>13 || visited++>90000)return;
 if(typeof v==='string'){
   if(v.length>4000)return; // never inspect image or large content
   const lc=v.toLocaleLowerCase('fr');
   for (const t of approvedTerms) if(lc.includes(t))hasTerms.add(t);
   return;
 }
 if(Array.isArray(v)) {
   if(v.length && structuralKeys.some(k=>p.toLowerCase().includes(k.toLowerCase())))
     evidenceShapes.push([p,'array',v.length]);
   for(const x of v.slice(0,1500))walk(x,p+'[]',d+1);
   return;
 }
 if(typeof v==='object'){
   for(const [k,x] of Object.entries(v)){
     if(/(body|content|screenshot|base64|bytes|headers|cookies|storage|rawhtml|token|secret|password|credentials|user_data)/i.test(k)) continue;
     if(structuralKeys.includes(k)||structuralKeys.includes(k.toLowerCase())){
        counters[k]=(counters[k]||0)+1;
        if(evidenceShapes.length<45) evidenceShapes.push([p+'.'+k,kind(x),Array.isArray(x)?x.length:undefined]);
     }
     walk(x,p? p+'.'+k:k,d+1);
   }
 }
}
walk(inspection,'inspect');
walk(scenario,'scenario');
const safe={
 task:'LOT07-07C_REA_ORTHALIS_PUBLIC_DEMO_STRUCTURE',
 interpretation:'field_name_inventory_only_NOT_interactive_business_proof',
 inspection_keys:keys(inspection), inspection_raw_result_keys:keys(inspection.raw_result),
 inspection_normalized_result_keys:keys(inspection.normalized_result),
 scenario_keys:keys(scenario), scenario_raw_result_keys:keys(scenario.raw_result),
 scenario_normalized_result_keys:keys(scenario.normalized_result),
 visited_nodes_bounded:visited,
 structure_key_hits:counters,
 structural_shape_samples:evidenceShapes.slice(0,35),
 approved_terms_present_anywhere:Array.from(hasTerms).sort(),
 limitations:'term presence could be code/resources, NOT necessarily visible UI; all raw evidence local only',
 output_file_sha256:files.map(f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex'))
};
console.log('REA_SAFE_STRUCTURAL_AUDIT='+JSON.stringify(safe));
