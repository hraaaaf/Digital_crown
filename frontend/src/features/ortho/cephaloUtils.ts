import type { Landmark, CVMStage } from './cephaloShared';
import type { DiagnosticTexts, DonneesEtape2, DonneesEtape3 } from './cephaloTypes';
import { serializeClinicianDiagnostic } from './cephaloClinicalEvidence';

/**
 * Legacy compatibility boundary.
 *
 * The previous implementation converted an incisor-angle difference into
 * millimetres of space using a universal 2.5°/mm factor. That relationship is
 * not validated here as a patient-specific space model, so the function fails
 * closed instead of manufacturing a corrected DDM.
 */
export function calcDDMReelle(
  _ddmClinique: number | '',
  _valeurActuelle: number | null,
  _norme: number = 90,
): number | null {
  return null;
}

/** Legacy compatibility boundary for the same unvalidated IMPA -> space rule. */
export function calcDDMCephalo(_impa: number | null): number | null {
  return null;
}

/** CVM is morphology-based and is never inferred from chronological age/sex alone. */
export function estimateCVM(_age: number | '', _sexe: 'M' | 'F'): CVMStage | '' {
  return '';
}

export function computeLocalImpa(lms: Landmark[]): number | null {
  const g = (id: string) => lms.find(l => l.id === id);
  const l1i = g('L1_incisal'); const l1a = g('L1_apex'); const go = g('Go'); const me = g('Me');
  if (!l1i || !l1a || !go || !me) return null;
  const ax = l1i.x - l1a.x; const ay = l1i.y - l1a.y;
  const mx = me.x - go.x; const my = me.y - go.y;
  const ma = Math.sqrt(ax * ax + ay * ay); const mm = Math.sqrt(mx * mx + my * my);
  if (ma < 0.1 || mm < 0.1) return null;
  const cos = Math.max(-1, Math.min(1, (ax * mx + ay * my) / (ma * mm)));
  const rawAngle = Math.acos(cos) * (180 / Math.PI);
  return Math.round((180 - rawAngle) * 10) / 10;
}

export function computeAngle(p1:{x:number;y:number},p2:{x:number;y:number},p3:{x:number;y:number},p4:{x:number;y:number}): number {
  const dx1=p2.x-p1.x,dy1=p2.y-p1.y,dx2=p4.x-p3.x,dy2=p4.y-p3.y;
  const m1=Math.sqrt(dx1*dx1+dy1*dy1),m2=Math.sqrt(dx2*dx2+dy2*dy2);
  if(m1<0.1||m2<0.1)return 0;
  const cos=Math.max(-1,Math.min(1,(dx1*dx2+dy1*dy2)/(m1*m2)));
  return Math.round(Math.acos(cos)*(180/Math.PI)*10)/10;
}

export function computeInterIncisalAngle(u1i:Landmark,u1a:Landmark,l1i:Landmark,l1a:Landmark):number{return 180-computeAngle(u1i,u1a,l1i,l1a);}

export function computeDistanceToVertical(target:{x:number;y:number},origin:{x:number;y:number},refA:{x:number;y:number},refB:{x:number;y:number},ratio:number=1):number{
  const dx=refB.x-refA.x,dy=refB.y-refA.y,len=Math.sqrt(dx*dx+dy*dy); if(len<0.1)return 0;
  const ux=dx/len,uy=dy/len,vx=target.x-origin.x,vy=target.y-origin.y; return (vx*ux+vy*uy)*ratio;
}

export function computeSignedOverbite(upperIncisal:{x:number;y:number}|undefined,lowerIncisal:{x:number;y:number}|undefined,po:{x:number;y:number}|undefined,or_:{x:number;y:number}|undefined,ratio:number|null):number|null{
  if(!upperIncisal||!lowerIncisal||!po||!or_||ratio===null)return null;
  const dx=or_.x-po.x,dy=or_.y-po.y,length=Math.hypot(dx,dy); if(length<0.1)return null;
  let perpX=-dy/length,perpY=dx/length; if(perpY<0){perpX=-perpX;perpY=-perpY;}
  const projection=(upperIncisal.x-lowerIncisal.x)*perpX+(upperIncisal.y-lowerIncisal.y)*perpY;
  return Math.round(projection*ratio*10)/10;
}

export function computeMcNamaraProjections(lms:Landmark[]):{N_prime?:[number,number];A_prime?:[number,number];B_prime?:[number,number]}{
  const g=(id:string)=>lms.find(l=>l.id===id),po=g('Po'),or_=g('Or'),n=g('N'),a=g('A'),b=g('B'); if(!po||!or_)return{};
  const projections:{N_prime?:[number,number];A_prime?:[number,number];B_prime?:[number,number]}={};
  const project=(px:number,py:number,ax:number,ay:number,bx:number,by:number):[number,number]|null=>{const dx=bx-ax,dy=by-ay,lenSq=dx*dx+dy*dy;if(lenSq===0)return null;const t=((px-ax)*dx+(py-ay)*dy)/lenSq;return[ax+t*dx,ay+t*dy];};
  if(n)projections.N_prime=project(n.x,n.y,po.x,po.y,or_.x,or_.y)||undefined;
  if(a)projections.A_prime=project(a.x,a.y,po.x,po.y,or_.x,or_.y)||undefined;
  if(b)projections.B_prime=project(b.x,b.y,po.x,po.y,or_.x,or_.y)||undefined;
  return projections;
}

export function fmtNum(v:number|null,dec=1):string{if(v===null||Number.isNaN(v))return'-';return(v>=0?'+':'')+v.toFixed(dec);}
export function initializeDefaultApexes(landmarks:Landmark[]):Landmark[]{return[...landmarks];}

export function computeDistanceToLine(p:Landmark,l1:Landmark,l2:Landmark,ratio:number,signed:boolean=false):number{
  const x0=p.x,y0=p.y,x1=l1.x,y1=l1.y,x2=l2.x,y2=l2.y;
  const num=(x2-x1)*(y1-y0)-(x1-x0)*(y2-y1),den=Math.sqrt(Math.pow(x2-x1,2)+Math.pow(y2-y1,2)); if(den===0)return 0;
  return signed?(num/den)*ratio:(Math.abs(num)/den)*ratio;
}

export function computeSignedELineDistance(lip:{x:number;y:number}|undefined,prn:{x:number;y:number}|undefined,pogSoft:{x:number;y:number}|undefined,po:{x:number;y:number}|undefined,or_:{x:number;y:number}|undefined,ratio:number|null):number|null{
  if(!lip||!prn||!pogSoft||!po||!or_||ratio===null)return null; const epsilon=1e-6;
  const eX=pogSoft.x-prn.x,eY=pogSoft.y-prn.y,eLengthSq=eX*eX+eY*eY,aX=or_.x-po.x,aY=or_.y-po.y,aLength=Math.hypot(aX,aY);
  if(eLengthSq<=epsilon*epsilon||aLength<=epsilon)return null; const t=((lip.x-prn.x)*eX+(lip.y-prn.y)*eY)/eLengthSq,qX=prn.x+t*eX,qY=prn.y+t*eY,rX=lip.x-qX,rY=lip.y-qY,magnitudePx=Math.hypot(rX,rY);
  if(magnitudePx<=epsilon)return 0; const anteriorScore=rX*(aX/aLength)+rY*(aY/aLength); if(Math.abs(anteriorScore)<=epsilon)return null; return Math.sign(anteriorScore)*magnitudePx*ratio;
}

export function computeStep3Data(lms:Landmark[],age:number|'',_sexe:'M'|'F',mmPerPixel:number|null,_etape2:DonneesEtape2|null=null):Partial<DonneesEtape3>{
  const g=(id:string)=>lms.find(l=>l.id.toLowerCase()===id.toLowerCase()); const po=g('po'),or_=g('or'),n=g('n'),a=g('a'),b=g('b'),s=g('s'),go=g('go'),me=g('me');
  const prn=g('prn')||g('nose_tip'),ls=g('ls_soft')||g('ls')||g('ul'),li=g('li_soft')||g('li')||g('ll'),pogSoft=g('pog_soft')||g('stpog');
  const u1i=g('u1_incisal')||g('u1i'),u1a=g('u1_apex')||g('u1a'),l1i=g('l1_incisal')||g('l1i'),l1a=g('l1_apex')||g('l1a'),ratio=mmPerPixel;
  const results:Partial<DonneesEtape3>={age,cvm:'',denture_type:'',dentaire:{surplomb:'',recouvrement:'',impa:'',i_francfort:'',inter_incisif:''},osseuse:{angle_tweed:'',decalage_ab:'',situation_a:'',situation_b:'',profondeur_faciale:'',sna:'',snb:'',anb:''},esthetique:{ligne_e_ls:'',ligne_e_li:'',angle_nasolabial:''},analyse_moulages_auto:''};
  if(po&&or_&&go&&me)results.osseuse!.angle_tweed=Math.round(computeAngle(po,or_,go,me));
  if(s&&n&&a&&b){const sna=computeAngle(n,s,n,a),snb=computeAngle(n,s,n,b);results.osseuse!.sna=Math.round(sna*10)/10;results.osseuse!.snb=Math.round(snb*10)/10;results.osseuse!.anb=Math.round((sna-snb)*10)/10;}
  if(ratio!==null&&n&&po&&or_){if(a)results.osseuse!.situation_a=Math.round(computeDistanceToVertical(a,n,po,or_,ratio)*10)/10;if(b)results.osseuse!.situation_b=Math.round(computeDistanceToVertical(b,n,po,or_,ratio)*10)/10;if(a&&b){const distA=computeDistanceToVertical(a,n,po,or_,ratio),distB=computeDistanceToVertical(b,n,po,or_,ratio);results.osseuse!.decalage_ab=Math.round((distA-distB)*10)/10;}if(s)results.osseuse!.profondeur_faciale=Math.round(Math.abs(computeDistanceToVertical(s,n,po,or_,ratio))*10)/10;}
  if(u1i&&u1a&&l1i&&l1a){results.dentaire!.inter_incisif=Math.round(computeInterIncisalAngle(u1i,u1a,l1i,l1a));if(n&&a){results.dentaire!.i_na_angle=Math.round(computeAngle(n,a,u1a,u1i));if(ratio!==null)results.dentaire!.i_na_mm=Math.round(computeDistanceToLine(u1i,n,a,ratio)*10)/10;}if(n&&b){results.dentaire!.i_nb_angle=Math.round(computeAngle(n,b,l1a,l1i));if(ratio!==null)results.dentaire!.i_nb_mm=Math.round(computeDistanceToLine(l1i,n,b,ratio)*10)/10;}}
  if(l1i&&l1a&&go&&me)results.dentaire!.impa=computeLocalImpa(lms)||''; if(po&&or_&&l1i&&l1a)results.dentaire!.fmia=Math.round(computeAngle(po,or_,l1a,l1i)); if(u1i&&u1a&&po&&or_)results.dentaire!.i_francfort=computeAngle(u1a,u1i,po,or_);
  if(ratio!==null&&u1i&&l1i&&po&&or_){const overjet=computeDistanceToVertical(l1i,u1i,po,or_,ratio);results.dentaire!.surplomb=Math.round(Math.abs(overjet)*10)/10;const overbite=computeSignedOverbite(u1i,l1i,po,or_,ratio);if(overbite!==null)results.dentaire!.recouvrement=overbite;}
  const anb=results.osseuse!.anb!==''?Number(results.osseuse!.anb):null; results.classe_squelettique=anb!==null?'Non classifiable':'Indéterminée';
  if(ratio!==null&&prn&&pogSoft&&po&&or_){const eLineLs=computeSignedELineDistance(ls,prn,pogSoft,po,or_,ratio),eLineLi=computeSignedELineDistance(li,prn,pogSoft,po,or_,ratio);if(eLineLs!==null)results.esthetique!.ligne_e_ls=Math.round(eLineLs*10)/10;if(eLineLi!==null)results.esthetique!.ligne_e_li=Math.round(eLineLi*10)/10;}
  return results;
}

/** Compatibility export: neutral context only, never a treatment plan. */
export function generateTreatmentPlan(_data:DonneesEtape3):string{
  return 'Classification squelettique non disponible.\nGESTION VERTICALE : Typologie verticale non disponible.\nAucune stratégie thérapeutique n’est générée automatiquement.';
}

export const buildPayload=(lms:Landmark[],max:number|null,mand:number|null,real:number|null,diag:DiagnosticTexts,projections:Record<string,any>,ratio:number|null=null,etape2:DonneesEtape2|null=null,etape3:DonneesEtape3|null=null)=>({landmarks:lms,mm_per_pixel:ratio,clinical_data:{ddm_maxillaire:max!==null?{espace_disponible:0,espace_necessaire:0,calcul_ddm:max}:null,ddm_mandibulaire:mand!==null?{espace_disponible:0,espace_necessaire:0,calcul_ddm:mand}:null,ddm_reelle:real,plan_traitement:diag.strategie_therapeutique||'',classe_molaire_droite:etape2?.occlusal.molaire_droite||null,classe_molaire_gauche:etape2?.occlusal.molaire_gauche||null,classe_canine_droite:etape2?.occlusal.canine_droite||null,classe_canine_gauche:etape2?.occlusal.canine_gauche||null,subdivision:etape2?Boolean(etape2.occlusal.molaire_droite&&etape2.occlusal.molaire_gauche&&etape2.occlusal.molaire_droite!==etape2.occlusal.molaire_gauche)||Boolean(etape2.occlusal.canine_droite&&etape2.occlusal.canine_gauche&&etape2.occlusal.canine_droite!==etape2.occlusal.canine_gauche):null,forme_arcade:etape2?.type_arcade||null,age:etape3?.age!==undefined&&etape3.age!==''?Number(etape3.age):null,cvm:etape3?.cvm||null,denture_type:etape3?.denture_type||null,preference_technique:etape3?.preference_technique||null},ai_diagnostic:serializeClinicianDiagnostic(diag),mcnmara_projections:projections});