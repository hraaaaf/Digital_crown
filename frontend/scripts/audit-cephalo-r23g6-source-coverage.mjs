/**
 * R23-G6 atlas dependency truth audit. Registry membership is not evidence
 * of numerical availability, anatomical calibration or a clinical conclusion.
 */
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const cwd=process.cwd();
const atlas=JSON.parse(await readFile(join(cwd,'../backend/data/cephalometry/ricketts_atlas2009_complete33_protocol_profile_v1.json'),'utf8'));
const registry=await readFile(join(cwd,'src/features/ortho/cephaloLot06FocusRegistry.generated.ts'),'utf8');
const registryIds=new Set([...registry.matchAll(/^  "(M_[A-Z0-9_]+)": \{/gm)].map(x=>x[1]));
const measurements=atlas.measurements;
if(atlas.protocol_id!=='RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1'||!Array.isArray(measurements)||measurements.length!==33)
  throw new Error('Atlas source contract composition drift: NOT CERTIFIED');
const unique=new Set(measurements.map(x=>x.measurement_id));
if(unique.size!==33)throw new Error('Atlas duplicate measurement identities');
const withPinned=[],notPinned=[];
for(const row of measurements){
  if(!['EXECUTABLE','CONDITIONAL_EXECUTABLE'].includes(row.state))
    throw new Error('Atlas gate unexpectedly changed: '+row.measurement_id);
  const entry={order:row.order,id:row.measurement_id,sourceContractState:row.state,
    hasPublishedLot06FocusDependencies:registryIds.has(row.measurement_id),
    clinicalMeasurementAuthority:false,reason:registryIds.has(row.measurement_id)
      ? 'LOT06_DEPENDENCY_REGISTRY_ONLY__REQUIRES_ACTIVE_TYPED_EVIDENCE'
      : 'NO_PUBLISHED_LOT06_FOCUS_DEPENDENCIES__NEVER_INFER_LANDMARKS'};
  (entry.hasPublishedLot06FocusDependencies?withPinned:notPinned).push(entry);
}
if(withPinned.length!==8||notPinned.length!==25)
  throw new Error('Atlas 8/25 dependency inventory changed; requires explicit review');
const out={head:process.env.PRODUCT_HEAD??null,source:atlas.protocol_id,
  scope:'SOURCE_DEPENDENCY_COVERAGE_ONLY__NOT_CLINICAL_AVAILABILITY',
  counts:{total:33,lot06Pinned:8,noPublishedLot06Focus:25},
  withPinned,notPinned,clinicalRelease:false};
await mkdir(join(cwd,'cephalo-r23g6-science-evidence'),{recursive:true});
await writeFile(join(cwd,'cephalo-r23g6-science-evidence','atlas33-dependency-inventory.json'),JSON.stringify(out,null,2));
console.log('R23-G6 Atlas source coverage: 8 published LOT06 dependencies / 25 UNKNOWN; zero promoted clinical values.');
