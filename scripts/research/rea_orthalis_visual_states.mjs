// LOT07 / 07-C — REA Orthalis Connect visual-readiness probe.
// Only permitted read-only public demo. NEVER print screenshot data, text,
// URLs, storage, cookies, or patient-identifying information.
import fs from "node:fs";
import crypto from "node:crypto";
const path = process.argv[2];
if (!path) throw new Error("REA scenario JSON path required");
const data = JSON.parse(fs.readFileSync(path, "utf8"));
const steps = data?.normalized_result?.steps || [];
const digest = b => crypto.createHash("sha256").update(b).digest("hex");

function findPng(x, depth=0) {
  if (depth > 8 || !x) return null;
  if (typeof x === "string") {
    const base64 = x.startsWith("data:image/png;base64,") ? x.slice(22) : x;
    if (base64.length > 100 && base64.startsWith("iVBORw0KGgo")) {
      const decoded = Buffer.from(base64, "base64");
      if (decoded.subarray(0,8).toString("hex") === "89504e470d0a1a0a") return decoded;
    }
    return null;
  }
  if (Array.isArray(x)) return null;
  if (typeof x === "object") {
    for (const k of ["data","base64","image_base64","bytes_base64","png_base64","image","png","payload","content","value","artifact","media","screenshot","image_bytes"]) {
      if (k in x) {
        const found=findPng(x[k],depth+1);
        if(found)return found;
      }
    }
  }
  return null;
}
const allowTags=["CANVAS","IFRAME","BUTTON","INPUT","A","IMG","FORM","VIDEO"];
function domCounts(value) {
  const nodes=value?.nodes;
  const counts={};if(!Array.isArray(nodes))return {available:false};
  for(const node of nodes){
    const tag=String(node?.node_name||"").toUpperCase();
    if(allowTags.includes(tag)) counts[tag]=(counts[tag]||0)+1;
  }
  return {available:true,nodes:nodes.length,known_tags:counts};
}
const results=[];
for(const step of steps) {
  const ss=step?.artifacts?.screenshot;
  const png=findPng(ss?.value);
  const d=step?.artifacts?.dom;
  const ax=step?.artifacts?.accessibility;
  const reading={step_id:step?.step_id||"unknown",status:step?.status||"unknown",
    action_status:step?.error?"error":"not_reported_or_none",
    screenshot_state:ss?.state||"absent",
    screenshot_value_structure:ss?.value && typeof ss.value==="object"?Object.keys(ss.value).sort():typeof ss?.value,
    screenshot_png_found:!!png,
    screenshot_png_size:png?.length||null,
    screenshot_png_sha256:png?digest(png):null,
    screenshot_dimensions:png?.length>24?{width:png.readUInt32BE(16),height:png.readUInt32BE(20)}:null,
    dom_state:d?.state||"absent",dom:domCounts(d?.value),
    accessibility_state:ax?.state||"absent",
    accessibility_nodes:Array.isArray(ax?.value?.nodes)?ax.value.nodes.length:null};
  results.push(reading);
}
const hashes=results.map(x=>x.screenshot_png_sha256).filter(Boolean);
console.log("REA_ORTHALIS_RUNTIME_VISUAL_PROOF="+JSON.stringify({
  protocol:"LOT07_07C_ORTHALIS_PUBLIC_DEMO_READ_ONLY",
  source:"REA_capture_browser_scenario",
  step_count:results.length,
  samples:results,
  images_differ_between_observation_steps:new Set(hashes).size>1,
  evidence_bytes_sha256:digest(fs.readFileSync(path)),
  raw_screenshots_uploaded:false,
  native_Orthalis_executable_downloaded:false,
  business_tasks_executed:false,
  interpretation:"SCREEN_PIXELS_AND_HTML_SHELL_ONLY; does not establish interactive Orthalis clinical workflow"}));
