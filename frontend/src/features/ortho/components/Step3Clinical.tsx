import React from 'react';
import { motion } from 'framer-motion';
import { Ruler, Activity, Info, Sparkles, ChevronDown } from 'lucide-react';
import type { DonneesEtape3, DiagnosticTexts } from '../cephaloTypes';
import { fmtNum, generateTreatmentPlan, calcDDMReelle, computeLocalImpa } from '../cephaloUtils';
import { evaluateCase, deriveDentureFromAge, deriveDivision } from '../orthoExpertSystem';
import { cn } from '../../../utils/cn';

import { useOrthoStore } from '../stores/useOrthoStore';

interface Step3ClinicalProps {
  P: any;
}

export const Step3Clinical: React.FC<Step3ClinicalProps> = ({ P }) => {
  const store = useOrthoStore();
  const { etape3Data: data, setEtape3Data: onChange, diag, setDiag: onDiagChange } = store;
  const updateDentaire = (key: keyof typeof data.dentaire, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange(prev => ({ 
      ...prev, 
      dentaire: { ...prev.dentaire, [key]: num } 
    }));
  };


  const updateOsseuse = (key: keyof typeof data.osseuse, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange(prev => ({ 
      ...prev, 
      osseuse: { ...prev.osseuse, [key]: num } 
    }));
  };


  const updateEsthetique = (key: keyof typeof data.esthetique, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange(prev => ({ 
      ...prev, 
      esthetique: { ...prev.esthetique, [key]: num } 
    }));
  };


  const handleDiagChange = (key: keyof DiagnosticTexts, value: string) => {
    onDiagChange(prev => ({ ...prev, [key]: value }));
  };

  const currentAnalysis = data.selectedAnalysis || 'COM';

  const updateEtape3Data = (update: Partial<DonneesEtape3>) => {
    onChange(prev => ({ ...prev, ...update }));
  };

  const setAnalysis = (type: 'COM' | 'STEINER' | 'TWEED') => {
    updateEtape3Data({ selectedAnalysis: type });
  };

  const expertReport = React.useMemo(() => {
    const { ddm, local, anglesData } = store;
    const impa = computeLocalImpa(local.landmarks);
    const iFrancfort = data.dentaire.i_francfort === '' ? null : Number(data.dentaire.i_francfort);
    const ddmMaxReelle = calcDDMReelle(ddm.maxillaire, iFrancfort, 107);
    const ddmMandReelle = calcDDMReelle(ddm.mandibulaire, impa, 90);
    const ddmTot = (ddmMaxReelle !== null && ddmMandReelle !== null) ? ddmMaxReelle + ddmMandReelle : null;
    
    return evaluateCase(data, ddmTot);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, store.ddm, store.local.landmarks]);

  const ddmTotal = Number(data.ddm_clinique) + Number(data.ddm_cephalo);
  const autoDenture = deriveDentureFromAge(data.age);
  const autoDivision = deriveDivision(data.classe_squelettique || '', data.dentaire.surplomb);
  const autoSeverite = ddmTotal < -7 ? 'Sévère' : (ddmTotal <= -4 ? 'Modérée' : 'Légère');
  const typeArcadeEtape2 = store.etape2Data.type_arcade || 'Indéterminé';


  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* SELECTEUR D'ANALYSE */}
      <div className="flex justify-center">
        <div className="inline-flex p-1 rounded-2xl border backdrop-blur-md" style={{ background: `${P.bgCard}80`, borderColor: P.border }}>
          {(['COM', 'STEINER', 'TWEED'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setAnalysis(type)}
              className={cn(
                "px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all",
                currentAnalysis === type 
                  ? "shadow-lg scale-105" 
                  : "opacity-40 hover:opacity-100"
              )}
              style={{ 
                background: currentAnalysis === type ? P.accent : 'transparent',
                color: currentAnalysis === type ? '#fff' : P.text 
              }}
            >
              {type === 'COM' ? 'McNamara (COM)' : type}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        
        {/* COLONNE GAUCHE : DONNÉES PATIENT & ANALYSES */}
        <div className="space-y-6">
          <div className="rounded-2xl p-6" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
            <div className="flex items-center gap-3 mb-6">
              <Activity size={18} style={{ color: P.accent }} />
              <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Données Patient</h3>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Âge (ans)</label>
                <input 
                  type="number" 
                  value={data.age} 
                  onChange={(e) => onChange(prev => ({ ...prev, age: e.target.value === '' ? '' : parseInt(e.target.value) }))}
                  className="w-full bg-transparent font-black text-lg outline-none"
                  style={{ color: P.text }}
                />
              </div>
              <div className="p-4 rounded-xl" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Stade CVM</label>
                <select 
                  value={data.cvm}
                  onChange={(e) => onChange(prev => ({ ...prev, cvm: e.target.value as any }))}
                  className="w-full bg-transparent font-bold text-sm outline-none"
                  style={{ color: P.text }}
                >
                  <option value="">Sélectionner...</option>
                  {['CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6'].map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <AccordionSection
            title="Analyse Dentaire"
            icon={<Ruler size={16} style={{ color: P.accent }} />}
            defaultOpen={true}
            P={P}
          >
            <div className="grid grid-cols-2 gap-4 pt-2">
              {currentAnalysis === 'COM' && (
                <>
                  <MetricInput label="Surplomb" value={data.dentaire.surplomb} unit="mm" normal="1.5 à 3mm" mean={2.2} tol={0.8} P={P} readOnly />
                  <MetricInput label="Recouvrement" value={data.dentaire.recouvrement} unit="mm" normal="1.5 à 3mm" mean={2.2} tol={0.8} P={P} readOnly />
                  <MetricInput label="1 / Mandibulaire (IMPA)" value={data.dentaire.impa} unit="°" normal="90° ± 5" mean={90} tol={5} P={P} readOnly />
                  <MetricInput label="1 / Francfort" value={data.dentaire.i_francfort} unit="°" normal="107° ± 5" mean={107} tol={5} P={P} readOnly />
                  <MetricInput label="Inter Incisif (1/1)" value={data.dentaire.inter_incisif} unit="°" normal="131° ± 13" mean={131} tol={13} P={P} readOnly />
                </>
              )}
              {currentAnalysis === 'STEINER' && (
                <>
                  <MetricInput label="1 / NA (°)" value={data.dentaire.i_na_angle || ''} onChange={(v: string) => updateDentaire('i_na_angle', v)} unit="°" normal="22° ± 2" mean={22} tol={2} P={P} />
                  <MetricInput label="1 / NA (mm)" value={data.dentaire.i_na_mm || ''} onChange={(v: string) => updateDentaire('i_na_mm', v)} unit="mm" normal="4mm ± 1" mean={4} tol={1} P={P} />
                  <MetricInput label="1 / NB (°)" value={data.dentaire.i_nb_angle || ''} onChange={(v: string) => updateDentaire('i_nb_angle', v)} unit="°" normal="25° ± 2" mean={25} tol={2} P={P} />
                  <MetricInput label="1 / NB (mm)" value={data.dentaire.i_nb_mm || ''} onChange={(v: string) => updateDentaire('i_nb_mm', v)} unit="mm" normal="4mm ± 1" mean={4} tol={1} P={P} />
                  <MetricInput label="Inter-Incisif" value={data.dentaire.inter_incisif} onChange={(v: string) => updateDentaire('inter_incisif', v)} unit="°" normal="131° ± 13" mean={131} tol={13} P={P} />
                </>
              )}
              {currentAnalysis === 'TWEED' && (
                <>
                  <MetricInput label="IMPA" value={data.dentaire.impa} onChange={(v: string) => updateDentaire('impa', v)} unit="°" normal="90° ± 5" mean={90} tol={5} P={P} />
                  <MetricInput label="FMIA" value={data.dentaire.fmia || ''} onChange={(v: string) => updateDentaire('fmia', v)} unit="°" normal="65° ± 5" mean={65} tol={5} P={P} />
                </>
              )}
            </div>
          </AccordionSection>

          <AccordionSection
            title="Analyse Osseuse"
            icon={<Activity size={16} style={{ color: P.accent }} />}
            defaultOpen={false}
            P={P}
          >
            <div className="grid grid-cols-2 gap-4 pt-2">
              {(currentAnalysis === 'COM' || currentAnalysis === 'TWEED') && (
                <MetricInput label="Angle de Tweed" value={data.osseuse.angle_tweed} onChange={(v: string) => updateOsseuse('angle_tweed', v)} unit="°" normal="26° ± 4" mean={26} tol={4} P={P} highlight />
              )}
              {currentAnalysis === 'COM' && (
                <>
                  <MetricInput label="Mesure A'B'" value={data.osseuse.decalage_ab} onChange={(v: string) => updateOsseuse('decalage_ab', v)} unit="mm" normal={data.age && Number(data.age) < 13 ? "+4.2 ± 3.2" : "+2.3 ± 3.1"} mean={data.age && Number(data.age) < 13 ? 4.2 : 2.3} tol={3.1} P={P} />
                  <MetricInput label="Situation Point A" value={data.osseuse.situation_a} onChange={(v: string) => updateOsseuse('situation_a', v)} unit="mm" normal={data.age && Number(data.age) < 13 ? "+2.8 ± 3.3" : "+2.3 ± 3"} mean={data.age && Number(data.age) < 13 ? 2.8 : 2.3} tol={3} P={P} />
                  <MetricInput label="Situation Point B" value={data.osseuse.situation_b} onChange={(v: string) => updateOsseuse('situation_b', v)} unit="mm" normal={data.age && Number(data.age) < 13 ? "-1.5 ± 4.5" : "0.0 ± 4.9"} mean={data.age && Number(data.age) < 13 ? -1.5 : 0} tol={4.9} P={P} />
                  <MetricInput label="Profondeur Faciale" value={data.osseuse.profondeur_faciale} onChange={(v: string) => updateOsseuse('profondeur_faciale', v)} unit="mm" normal={data.age && Number(data.age) < 13 ? "61.3 ± 5" : "70.3 ± 5"} mean={data.age && Number(data.age) < 13 ? 61.3 : 70.3} tol={5} P={P} />
                </>
              )}
              {currentAnalysis === 'STEINER' && (
                <>
                  <MetricInput label="SNA" value={data.osseuse.sna} onChange={(v: string) => updateOsseuse('sna', v)} unit="°" normal="82° ± 2" mean={82} tol={2} P={P} />
                  <MetricInput label="SNB" value={data.osseuse.snb} onChange={(v: string) => updateOsseuse('snb', v)} unit="°" normal="80° ± 2" mean={80} tol={2} P={P} />
                  <MetricInput label="ANB" value={data.osseuse.anb} onChange={(v: string) => updateOsseuse('anb', v)} unit="°" normal="2° ± 2" mean={2} tol={2} P={P} highlight />
                </>
              )}
            </div>
          </AccordionSection>

          <AccordionSection
            title="Analyse Esthétique (Ricketts)"
            icon={<Activity size={16} style={{ color: P.accentSuccess }} />}
            defaultOpen={false}
            P={P}
          >
            <div className="grid grid-cols-2 gap-4 pt-2">
              <MetricInput label="Ligne E / Ls" value={data.esthetique?.ligne_e_ls} onChange={(v: string) => updateEsthetique('ligne_e_ls', v)} unit="mm" normal="-2mm ± 2" mean={-2} tol={2} P={P} />
              <MetricInput label="Ligne E / Li" value={data.esthetique?.ligne_e_li} onChange={(v: string) => updateEsthetique('ligne_e_li', v)} unit="mm" normal="-1mm ± 2" mean={-1} tol={2} P={P} />
              <MetricInput label="Angle Nasolabial" value={data.esthetique?.angle_nasolabial} onChange={(v: string) => updateEsthetique('angle_nasolabial', v)} unit="°" normal="102° ± 10" mean={102} tol={10} P={P} />
            </div>
          </AccordionSection>
        </div>

        {/* COLONNE DROITE : SYNTHÈSE DIAGNOSTIC */}
        <div className="space-y-6">
          <div className="rounded-2xl p-6 flex flex-col" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
             <div className="flex items-center gap-3 mb-6">
              <Info size={18} style={{ color: P.accent }} />
              <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Synthèse COM</h3>
            </div>
            
            <div className="space-y-6 flex-1">
              <div className="p-4 rounded-xl flex items-center justify-between" style={{ background: `${P.accent}08`, border: `1px solid ${P.accent}20` }}>
                <div>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.accent }}>Classe Squelettique ✨ IA</label>
                  <div className="text-2xl font-black" style={{ color: P.text }}>{data.classe_squelettique || '---'}</div>
                </div>
                <div className="text-right">
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.accent }}>Pattern Vertical ✨ IA</label>
                  <div className="text-2xl font-black capitalize" style={{ color: P.text }}>{data.pattern_vertical || '---'}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                 <div>
                  <label className="text-[10px] font-bold uppercase tracking-wide block mb-1" style={{ color: P.textMuted }}>DDM Clinique</label>
                  <div className="text-lg font-black" style={{ color: P.text }}>{fmtNum(Number(data.ddm_clinique))} mm</div>
                </div>
                <div>
                  <label className="text-[10px] font-bold uppercase tracking-wide block mb-1" style={{ color: P.textMuted }}>DDM Céphalo</label>
                  <div className="text-lg font-black" style={{ color: P.accent }}>{fmtNum(Number(data.ddm_cephalo))} mm</div>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                 <label className="text-[10px] font-black uppercase tracking-widest text-emerald-600 block mb-1">DDM RÉELLE (Mandibulaire)</label>
                 <div className="text-3xl font-black text-emerald-600">
                  {fmtNum(Number(data.ddm_clinique) + Number(data.ddm_cephalo))} mm
                 </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Denture ✨ IA</label>
                  <div className="w-full bg-transparent font-black text-lg capitalize" style={{ color: P.accent }}>
                    {autoDenture || '---'}
                  </div>
                </div>
                <div className="p-4 rounded-xl" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Technique</label>
                  <select 
                    value={data.preference_technique}
                    onChange={(e) => onChange(prev => ({ ...prev, preference_technique: e.target.value as any }))}
                    className="w-full bg-transparent font-bold text-sm outline-none"
                    style={{ color: P.text }}
                  >
                    <option value="DAMON">Damon (Actif)</option>
                    <option value="CLASSIC">Classique</option>
                    <option value="ALIGNEURS">Aligneurs</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t" style={{ borderColor: P.border }}>
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>Morphologie Dentaire (Auto-Déduit)</label>
                <div className="grid grid-cols-1 gap-3">
                  <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border" style={{ borderColor: P.border }}>
                    <span className="text-xs font-bold" style={{ color: P.textMuted }}>Sens Vertical (Recouvrement) ✨ IA</span>
                    <span className="text-xs font-black capitalize" style={{ color: P.accentSuccess }}>
                      {Number(data.dentaire.recouvrement) > 3.5 ? 'Supraclusie' : Number(data.dentaire.recouvrement) < 1.0 ? 'Infraclusie' : 'Normoclusie'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border" style={{ borderColor: P.border }}>
                    <span className="text-xs font-bold" style={{ color: P.textMuted }}>Sens Sagittal (Surplomb) ✨ IA</span>
                    <span className="text-xs font-black capitalize" style={{ color: P.accentSuccess }}>
                      {Number(data.dentaire.surplomb) > 4 ? 'Proalvéolie' : Number(data.dentaire.surplomb) < 1.5 ? 'Rétroalvéolie' : 'Normal'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border" style={{ borderColor: P.border }}>
                    <span className="text-xs font-bold" style={{ color: P.textMuted }}>Sévérité DDM ✨ IA</span>
                    <span className="text-xs font-black capitalize" style={{ color: P.accent }}>
                      {autoSeverite}
                    </span>
                  </div>
                  {autoDivision && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border" style={{ borderColor: P.border }}>
                      <span className="text-xs font-bold" style={{ color: P.textMuted }}>Division (Cl. II) ✨ IA</span>
                      <span className="text-xs font-black capitalize" style={{ color: P.accent }}>
                        Division {autoDivision}
                      </span>
                    </div>
                  )}
                  <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border" style={{ borderColor: P.border }}>
                    <span className="text-xs font-bold" style={{ color: P.textMuted }}>Type d'Arcade</span>
                    <span className="text-xs font-black" style={{ color: P.text }}>
                      {typeArcadeEtape2 === 'Indéterminé' ? 'Indéterminé' : `Forme en ${typeArcadeEtape2}`}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <AccordionSection
            title="1. Analyse Dentaire et Alvéolaire"
            icon={<Ruler size={14} style={{ color: P.accent }} />}
            defaultOpen={false}
            P={P}
          >
            <textarea
              value={diag.analyse_dentaire}
              onChange={(e) => handleDiagChange('analyse_dentaire', e.target.value)}
              className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2"
              style={{ borderColor: P.border, color: P.text }}
              placeholder="Description des anomalies dentaires, classe canine/molaire, etc..."
            />
          </AccordionSection>

          <AccordionSection
            title="2. Analyse Squelettique"
            icon={<Activity size={14} style={{ color: P.accent }} />}
            defaultOpen={false}
            P={P}
          >
            <textarea
              value={diag.diagnostic_squelettique}
              onChange={(e) => handleDiagChange('diagnostic_squelettique', e.target.value)}
              className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2"
              style={{ borderColor: P.border, color: P.text }}
              placeholder="Description des rapports osseux..."
            />
          </AccordionSection>
        </div>
      </div>

      {/* RAPPORTS TEXTUELS — ACCORDÉONS FULL WIDTH */}
      <div className="space-y-3">
        <AccordionSection
          title="3. Examen des Moulages"
          icon={<Activity size={14} style={{ color: P.accent }} />}
          defaultOpen={false}
          P={P}
        >
          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-xl font-mono text-[11px] leading-relaxed relative overflow-hidden"
                 style={{ background: P.bgInput, border: `1px solid ${P.border}40`, color: P.text }}>
              <div className="absolute top-0 right-0 p-1 px-2 text-[8px] font-black uppercase tracking-widest rounded-bl-lg"
                   style={{ background: `${P.accent}20`, color: P.accent }}>
                Auto Sync Step 2
              </div>
              {data.analyse_moulages_auto ? (
                data.analyse_moulages_auto.split('\n').map((line, i) => <div key={i}>{line}</div>)
              ) : (
                <span className="opacity-40 italic">En attente des données occlusales...</span>
              )}
            </div>
            <textarea
              value={diag.analyse_moulages}
              onChange={(e) => handleDiagChange('analyse_moulages', e.target.value)}
              className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all"
              style={{ borderColor: P.border, color: P.text }}
              placeholder="Notes complémentaires (dentaire, formes d'arcade)..."
            />
          </div>
        </AccordionSection>

        <AccordionSection
          title="4. Diagnostic / Résumé Diagnostique"
          icon={<Info size={14} style={{ color: P.accent }} />}
          defaultOpen={true}
          P={P}
        >
          <textarea
            value={diag.synthese_diagnostique}
            onChange={(e) => handleDiagChange('synthese_diagnostique', e.target.value)}
            className="w-full h-32 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2"
            style={{ borderColor: P.border, color: P.text }}
            placeholder="Résumé clinique et objectifs..."
          />
        </AccordionSection>

        <AccordionSection
          title="5. Bot Expert ODF (Rapport Automatique)"
          icon={<Sparkles size={14} style={{ color: P.accent }} />}
          defaultOpen={false}
          badge={
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleDiagChange('strategie_therapeutique', expertReport.rapportMarkdown); }}
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter transition-all hover:scale-105 active:scale-95 shadow-md ml-2"
              style={{ background: P.accent, color: 'white' }}
            >
              <Sparkles size={11} />
              Générer
            </button>
          }
          P={P}
        >
          <textarea
            value={diag.strategie_therapeutique}
            onChange={(e) => handleDiagChange('strategie_therapeutique', e.target.value)}
            className="w-full h-48 p-4 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all resize-none overflow-y-auto font-mono leading-relaxed mt-2"
            style={{ borderColor: P.border, color: P.text }}
            placeholder="Cliquez sur 'Générer' pour obtenir la synthèse de l'Agent ODF..."
          />
        </AccordionSection>
      </div>
    </div>
  );
};

// ── AccordionSection ──────────────────────────────────────────────────────────

const AccordionSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  badge?: React.ReactNode;
  P: any;
  children: React.ReactNode;
}> = ({ title, icon, defaultOpen = false, badge, P, children }) => {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-6 py-4 transition-all hover:brightness-110"
        style={{ background: open ? `${P.accent}08` : 'transparent' }}
      >
        <div className="flex items-center gap-3">
          {icon}
          <span className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>{title}</span>
          {badge}
        </div>
        <ChevronDown
          size={16}
          className="transition-transform duration-300"
          style={{ color: P.textMuted, transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </button>
      {open && (
        <div className="px-6 pb-6 pt-2 border-t" style={{ borderColor: P.border }}>
          {children}
        </div>
      )}
    </div>
  );
};

const getMetricColor = (val: any, mean: number, tol: number, P: any) => {
  if (val === '' || val === null || val === undefined) return P.text;
  const num = parseFloat(val);
  if (isNaN(num)) return P.text;
  
  const diff = Math.abs(num - mean);
  if (diff <= tol) return P.accentSuccess;
  if (diff <= tol * 2) return P.accentWarning;
  return P.accentError;
};

const MetricInput = ({ 
  label, value, onChange, unit, normal, P, highlight, mean, tol, readOnly 
}: { 
  label: string, value: any, onChange?: (v: string) => void, unit: string, normal: string, P: any, highlight?: boolean, mean?: number, tol?: number, readOnly?: boolean
}) => {
  const [shouldPulse, setShouldPulse] = React.useState(false);
  const prevValue = React.useRef(value);

  React.useEffect(() => {
    if ((prevValue.current === '' || prevValue.current === null) && value !== '' && value !== null) {
      setShouldPulse(true);
      const timer = setTimeout(() => setShouldPulse(false), 2000);
      return () => clearTimeout(timer);
    }
    prevValue.current = value;
  }, [value]);

  const color = (mean !== undefined && tol !== undefined) 
    ? getMetricColor(value, mean, tol, P) 
    : (highlight ? P.accent : P.text);

  return (
    <div className={cn(
      "p-4 rounded-xl border transition-all duration-500 relative overflow-hidden", 
      highlight ? "ring-2 ring-blue-500/20" : "",
      shouldPulse ? "ring-2 ring-emerald-500/50 scale-[1.02] shadow-lg shadow-emerald-500/10" : ""
    )} style={{ background: P.bgInput, borderColor: shouldPulse ? P.accentSuccess : P.border }}>
      {shouldPulse && (
        <motion.div 
          initial={{ x: '-100%' }}
          animate={{ x: '100%' }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          className="absolute inset-0 bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent pointer-events-none"
        />
      )}
      <div className="flex justify-between items-center mb-2">
        <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: shouldPulse ? P.accentSuccess : P.textMuted }}>
          {label} {shouldPulse && "✨ IA"}
        </span>
        <span className="text-[8px] font-bold opacity-50" style={{ color: P.textDim }}>{normal}</span>
      </div>
      <div className="flex items-center gap-1">
        {readOnly ? (
          <div className="w-full bg-transparent font-black text-lg" style={{ color: shouldPulse ? P.accentSuccess : color }}>
            {value !== '' && value !== null ? value : '-'}
          </div>
        ) : (
          <input 
            type="text" 
            value={value} 
            onChange={(e) => onChange && onChange(e.target.value)}
            className="w-full bg-transparent font-black text-lg outline-none"
            style={{ color: shouldPulse ? P.accentSuccess : color }}
          />
        )}
        <span className="text-xs font-bold" style={{ color: P.textDim }}>{unit}</span>
      </div>
    </div>
  );
};
