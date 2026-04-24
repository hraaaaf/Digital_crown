import React from 'react';
import { Ruler, Activity, Info } from 'lucide-react';
import type { DonneesEtape3 } from '../cephaloTypes';
import { fmtNum } from '../cephaloUtils';
import { cn } from '../../../utils/cn';

interface Step3ClinicalProps {
  data: DonneesEtape3;
  onChange: (newData: Partial<DonneesEtape3>) => void;
  P: any;
}

export const Step3Clinical: React.FC<Step3ClinicalProps> = ({ data, onChange, P }) => {
  const updateDentaire = (key: keyof typeof data.dentaire, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange({ dentaire: { ...data.dentaire, [key]: num } });
  };

  const updateOsseuse = (key: keyof typeof data.osseuse, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange({ osseuse: { ...data.osseuse, [key]: num } });
  };

  const updateEsthetique = (key: keyof typeof data.esthetique, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange({ esthetique: { ...data.esthetique, [key]: num } });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* COLONNE GAUCHE : ANALYSES AUTOMATIQUES */}
      <div className="space-y-6">
        <div className="rounded-2xl p-6" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3 mb-6">
            <Ruler size={18} style={{ color: P.accent }} />
            <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Analyse Dentaire</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
             <MetricInput label="IMPA" value={data.dentaire.impa} onChange={(v: string) => updateDentaire('impa', v)} unit="°" normal="90° ± 5" mean={90} tol={5} P={P} />
             <MetricInput label="I / Francfort" value={data.dentaire.i_francfort} onChange={(v: string) => updateDentaire('i_francfort', v)} unit="°" normal="107° ± 5" mean={107} tol={5} P={P} />
             <MetricInput label="Surplomb" value={data.dentaire.surplomb} onChange={(v: string) => updateDentaire('surplomb', v)} unit="mm" normal="2mm ± 1" mean={2} tol={1} P={P} />
             <MetricInput label="Recouvrement" value={data.dentaire.recouvrement} onChange={(v: string) => updateDentaire('recouvrement', v)} unit="mm" normal="2mm ± 1" mean={2} tol={1} P={P} />
          </div>
        </div>

        <div className="rounded-2xl p-6" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3 mb-6">
            <Activity size={18} style={{ color: P.accent }} />
            <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Analyse Osseuse</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
             <MetricInput label="SNA" value={data.osseuse.situation_a} onChange={(v: string) => updateOsseuse('situation_a', v)} unit="°" normal="82° ± 2" mean={82} tol={2} P={P} />
             <MetricInput label="SNB" value={data.osseuse.situation_b} onChange={(v: string) => updateOsseuse('situation_b', v)} unit="°" normal="80° ± 2" mean={80} tol={2} P={P} />
             <MetricInput label="ANB" value={data.osseuse.decalage_ab} onChange={(v: string) => updateOsseuse('decalage_ab', v)} unit="°" normal="2° ± 2" mean={2} tol={2} P={P} highlight />
             <MetricInput label="Tweed (FMA)" value={data.osseuse.angle_tweed} onChange={(v: string) => updateOsseuse('angle_tweed', v)} unit="°" normal="25° ± 3" mean={25} tol={3} P={P} />
          </div>
        </div>

        <div className="rounded-2xl p-6" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <div className="flex items-center gap-3 mb-6">
            <Activity size={18} style={{ color: P.accentSuccess }} />
            <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Analyse Esthétique (Ricketts)</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
             <MetricInput label="Ligne E / Ls" value={data.esthetique?.ligne_e_ls} onChange={(v: string) => updateEsthetique('ligne_e_ls', v)} unit="mm" normal="-2mm ± 2" mean={-2} tol={2} P={P} />
             <MetricInput label="Ligne E / Li" value={data.esthetique?.ligne_e_li} onChange={(v: string) => updateEsthetique('ligne_e_li', v)} unit="mm" normal="-1mm ± 2" mean={-1} tol={2} P={P} />
          </div>
        </div>
      </div>

      {/* COLONNE DROITE : SYNTHÈSE DIAGNOSTIC */}
      <div className="space-y-6">
        <div className="rounded-2xl p-6 h-full flex flex-col" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
           <div className="flex items-center gap-3 mb-6">
            <Info size={18} style={{ color: P.accent }} />
            <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Synthèse COM</h3>
          </div>
          
          <div className="space-y-6 flex-1">
            <div className="p-4 rounded-xl" style={{ background: `${P.accent}08`, border: `1px solid ${P.accent}20` }}>
              <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.accent }}>Classe Squelettique</label>
              <div className="text-2xl font-black" style={{ color: P.text }}>{data.classe_squelettique || '---'}</div>
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
          </div>
        </div>
      </div>
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
  label, value, onChange, unit, normal, P, highlight, mean, tol 
}: { 
  label: string, value: any, onChange: (v: string) => void, unit: string, normal: string, P: any, highlight?: boolean, mean?: number, tol?: number 
}) => {
  const color = (mean !== undefined && tol !== undefined) 
    ? getMetricColor(value, mean, tol, P) 
    : (highlight ? P.accent : P.text);

  return (
    <div className={cn("p-4 rounded-xl border transition-all", highlight ? "ring-2 ring-blue-500/20" : "")} style={{ background: P.bgInput, borderColor: P.border }}>
      <div className="flex justify-between items-center mb-2">
        <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>{label}</span>
        <span className="text-[8px] font-bold opacity-50" style={{ color: P.textDim }}>{normal}</span>
      </div>
      <div className="flex items-center gap-1">
        <input 
          type="text" 
          value={value} 
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-transparent font-black text-lg outline-none"
          style={{ color }}
        />
        <span className="text-xs font-bold" style={{ color: P.textDim }}>{unit}</span>
      </div>
    </div>
  );
};
