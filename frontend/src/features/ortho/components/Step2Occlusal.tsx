import React, { useMemo } from 'react';
import type { ClasseAngle, TypeArcade } from '../cephaloTypes';
import { fmtNum, calcDDMReelle, computeLocalImpa } from '../cephaloUtils';
import { cn } from '../../../utils/cn';

import { useOrthoStore } from '../stores/useOrthoStore';


interface Step2OcclusalProps {
  P: any;
}

export const Step2Occlusal: React.FC<Step2OcclusalProps> = ({ P }) => {
  const store = useOrthoStore();
  const { etape2Data: data, ddm, setDdm: onDdmChange, setEtape2Data: onChange, local, anglesData, etape3Data } = store;

  // Re-calcul des dépendances locales si nécessaire (IMPA, I-Francfort)
  const localImpa = useMemo(() => computeLocalImpa(local.landmarks), [local.landmarks]);
  const serverImpa = useMemo(() => {
    const v1 = anglesData?.metrics?.analyse_dentaire?.IMPA?.value;
    if (v1 !== undefined && v1 !== null) return v1 as number;
    const v2 = anglesData?.IMPA?.valeur;
    if (v2 !== undefined && v2 !== null) return v2 as number;
    return null;
  }, [anglesData]);

  const impa = serverImpa ?? localImpa;
  const iFrancfort = etape3Data.dentaire.i_francfort === '' ? null : Number(etape3Data.dentaire.i_francfort);
  const updateOcclusal = (key: string, val: ClasseAngle) => {
    onChange({ ...data, occlusal: { ...data.occlusal, [key]: val } });
  };

  const hasSubdivision = useMemo(() => {
    const { molaire_gauche, molaire_droite, canine_gauche, canine_droite } = data.occlusal;
    return molaire_gauche !== molaire_droite || canine_gauche !== canine_droite;
  }, [data.occlusal]);

  // Calculs DDM en temps réel avec les utilitaires centraux
  const ddmMaxReelle = useMemo(() => calcDDMReelle(ddm.maxillaire, iFrancfort, 107), [ddm.maxillaire, iFrancfort]);
  const ddmMandReelle = useMemo(() => calcDDMReelle(ddm.mandibulaire, impa, 90), [ddm.mandibulaire, impa]);
  const ddmReelleTotale = useMemo(() => 
    (ddmMaxReelle !== null && ddmMandReelle !== null) ? ddmMaxReelle + ddmMandReelle : null
  , [ddmMaxReelle, ddmMandReelle]);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      
      {/* SECTION 1: DDM (MOULAGES) */}
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-black uppercase tracking-[0.2em]" style={{ color: P.accent }}>01. Analyse des Moulages</h3>
          <p className="text-sm opacity-60" style={{ color: P.text }}>Mesurez les encombrements sur plâtre pour calculer la DDM Réelle.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Maxillaire */}
          <div className="p-6 rounded-3xl space-y-4" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl flex items-center justify-center font-black" style={{ background: `${P.accent}20`, color: P.accent }}>M</div>
              <span className="font-bold" style={{ color: P.text }}>DDM Maxillaire</span>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-black opacity-40" style={{ color: P.text }}>Déficit Clinique (mm)</label>
              <input
                type="number"
                step="0.1"
                value={ddm.maxillaire}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => onDdmChange({ ...ddm, maxillaire: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                className="w-full px-4 py-3 rounded-2xl text-lg font-bold outline-none transition-all focus:ring-2"
                style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
                placeholder="0.0"
              />
            </div>
            {ddmMaxReelle !== null && (
              <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: P.bgPanel }}>
                <span className="text-xs opacity-50" style={{ color: P.text }}>Céphalo-corrigé :</span>
                <span className="font-black" style={{ color: P.accent }}>{fmtNum(ddmMaxReelle)} mm</span>
              </div>
            )}
          </div>

          {/* Mandibulaire */}
          <div className="p-6 rounded-3xl space-y-4" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl flex items-center justify-center font-black" style={{ background: `${P.accentSuccess}20`, color: P.accentSuccess }}>m</div>
              <span className="font-bold" style={{ color: P.text }}>DDM Mandibulaire</span>
            </div>
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-black opacity-40" style={{ color: P.text }}>Déficit Clinique (mm)</label>
              <input
                type="number"
                step="0.1"
                value={ddm.mandibulaire}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => onDdmChange({ ...ddm, mandibulaire: e.target.value === '' ? '' : parseFloat(e.target.value) })}
                className="w-full px-4 py-3 rounded-2xl text-lg font-bold outline-none transition-all focus:ring-2"
                style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.text }}
                placeholder="0.0"
              />
            </div>
            {ddmMandReelle !== null && (
              <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: P.bgPanel }}>
                <span className="text-xs opacity-50" style={{ color: P.text }}>Céphalo-corrigé :</span>
                <span className="font-black" style={{ color: P.accentSuccess }}>{fmtNum(ddmMandReelle)} mm</span>
              </div>
            )}
          </div>
        </div>

        {ddmReelleTotale !== null && (
          <div className="p-8 rounded-[2rem] flex items-center justify-between shadow-2xl transition-all" 
               style={{ background: `linear-gradient(135deg, ${P.accent}10, ${P.accentSuccess}10)`, border: `2px solid ${P.accent}30` }}>
            <div className="space-y-1">
              <h4 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>DDM Réelle Totale</h4>
              <p className="text-xs opacity-60" style={{ color: P.text }}>Somme des déficits corrigés par l'inclinaison incisive.</p>
            </div>
            <div className="text-5xl font-black italic tracking-tighter" style={{ color: P.accent }}>
              {fmtNum(ddmReelleTotale)}<span className="text-xl ml-1 not-italic">mm</span>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-black uppercase tracking-[0.2em]" style={{ color: P.accent }}>02. Examen Occlusal & Forme d'Arcade</h3>
          <p className="text-sm opacity-60" style={{ color: P.text }}>Évaluez les rapports molaires/canins et la forme d'arcade.</p>
        </div>

        {/* Type d'arcade */}
        <div className="p-6 rounded-3xl space-y-4" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
          <h4 className="text-[10px] font-black uppercase opacity-40" style={{ color: P.text }}>Forme d'Arcade Dominante</h4>
          <div className="flex flex-wrap gap-3">
            {(['U', 'V', 'CARREE'] as TypeArcade[]).map(type => (
              <button
                key={type}
                onClick={() => onChange({ ...data, type_arcade: type })}
                className={cn(
                  "px-6 py-3 rounded-xl text-xs font-black transition-all",
                  data.type_arcade === type ? "shadow-lg scale-105" : "opacity-50 hover:opacity-100"
                )}
                style={{
                  background: data.type_arcade === type ? P.accent : P.bgInput,
                  color: data.type_arcade === type ? 'white' : P.text,
                  border: `1px solid ${data.type_arcade === type ? P.accent : P.border}`
                }}
              >
                Forme en {type}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <h4 className="text-[10px] font-black uppercase opacity-40 px-2" style={{ color: P.text }}>Classes Molaires</h4>
            <div className="space-y-3">
              <OcclusalSelector label="Molaire Droite" value={data.occlusal.molaire_droite} onChange={(v: ClasseAngle) => updateOcclusal('molaire_droite', v)} P={P} />
              <OcclusalSelector label="Molaire Gauche" value={data.occlusal.molaire_gauche} onChange={(v: ClasseAngle) => updateOcclusal('molaire_gauche', v)} P={P} />
            </div>
          </div>
          <div className="space-y-4">
            <h4 className="text-[10px] font-black uppercase opacity-40 px-2" style={{ color: P.text }}>Classes Canines</h4>
            <div className="space-y-3">
              <OcclusalSelector label="Canine Droite" value={data.occlusal.canine_droite} onChange={(v: ClasseAngle) => updateOcclusal('canine_droite', v)} P={P} />
              <OcclusalSelector label="Canine Gauche" value={data.occlusal.canine_gauche} onChange={(v: ClasseAngle) => updateOcclusal('canine_gauche', v)} P={P} />
            </div>
          </div>
        </div>

        {hasSubdivision && (
          <div className="p-4 rounded-2xl flex items-center gap-3 animate-pulse" style={{ background: `${P.accentWarning}15`, border: `1px solid ${P.accentWarning}40`, color: P.accentWarning }}>
            <span className="text-xs font-black uppercase tracking-wider">⚠ Subdivision détectée</span>
            <div className="h-px flex-1" style={{ background: P.accentWarning, opacity: 0.2 }}></div>
            <span className="text-[10px] font-bold">Asymétrie droite/gauche confirmée</span>
          </div>
        )}
      </div>
    </div>
  );
};

const OcclusalSelector = ({ label, value, onChange, P }: { label: string, value: ClasseAngle, onChange: (v: ClasseAngle) => void, P: any }) => (
  <div className="flex items-center justify-between p-4 rounded-2xl group transition-all" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
    <span className="text-sm font-bold" style={{ color: P.text }}>{label}</span>
    <div className="flex gap-1 p-1 rounded-xl shadow-inner" style={{ background: P.bgInput }}>
      {(['I', 'II', 'III'] as ClasseAngle[]).map((cls) => (
        <button
          key={cls}
          onClick={() => onChange(cls)}
          className={cn(
            "px-4 py-2 rounded-lg text-xs font-black transition-all duration-300",
            value === cls ? "shadow-xl scale-110 z-10" : "opacity-30 hover:opacity-100"
          )}
          style={{
            background: value === cls ? P.accent : 'transparent',
            color: value === cls ? 'white' : P.text,
          }}
        >
          {cls}
        </button>
      ))}
    </div>
  </div>
);
