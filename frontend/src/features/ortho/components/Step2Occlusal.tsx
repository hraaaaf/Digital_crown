import React, { useMemo } from 'react';
import type { ClasseAngle, TypeArcade } from '../cephaloTypes';
import { fmtNum, computeClinicalDdmMm } from '../cephaloUtils';
import { cn } from '../../../utils/cn';

import { useOrthoStore } from '../stores/useOrthoStore';
import { OrthoMediaRecordPanel } from './OrthoMediaRecordPanel';


interface Step2OcclusalProps {
  P: any;
  patientId: number;
}

export const Step2Occlusal: React.FC<Step2OcclusalProps> = ({ P, patientId }) => {
  const store = useOrthoStore();
  const { etape2Data: data, setEtape2Data: onChange } = store;
  const spaces = data.espaces_moulages ?? {
    maxillaire: { disponible: '' as const, necessaire: '' as const },
    mandibulaire: { disponible: '' as const, necessaire: '' as const },
  };
  const updateSpace = (jaw: 'maxillaire' | 'mandibulaire', field: 'disponible' | 'necessaire', raw: string) => {
    const value = raw === '' ? '' : Number(raw);
    onChange({ ...data, espaces_moulages: {
      ...spaces, [jaw]: { ...spaces[jaw], [field]: value },
    } });
  };
  const updateOcclusal = (key: string, val: ClasseAngle) => {
    onChange({ ...data, occlusal: { ...data.occlusal, [key]: val } });
  };

  const hasSubdivision = useMemo(() => {
    const { molaire_gauche, molaire_droite, canine_gauche, canine_droite } = data.occlusal;
    return molaire_gauche !== molaire_droite || canine_gauche !== canine_droite;
  }, [data.occlusal]);

  const ddmMaxReelle = computeClinicalDdmMm(spaces.maxillaire.disponible, spaces.maxillaire.necessaire);
  const ddmMandReelle = computeClinicalDdmMm(spaces.mandibulaire.disponible, spaces.mandibulaire.necessaire);
  const ddmReelleTotale = ddmMaxReelle !== null && ddmMandReelle !== null
    ? ddmMaxReelle + ddmMandReelle : null;

  return (
    <>
      <OrthoMediaRecordPanel patientId={patientId} P={P} />
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      
      {/* SECTION 1: DDM (MOULAGES) */}
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-black uppercase tracking-[0.2em]" style={{ color: P.accent }}>01. Analyse des Moulages</h3>
          <p className="text-sm opacity-60" style={{ color: P.text }}>Mesurez ED et EN directement sur les moulages (mm). DDM = ED − EN ; aucune correction céphalométrique.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(['maxillaire', 'mandibulaire'] as const).map(jaw => {
            const ddmValue = jaw === 'maxillaire' ? ddmMaxReelle : ddmMandReelle;
            return <div key={jaw} className="p-6 rounded-3xl space-y-4" style={{background:P.bgCard,border:`1px solid ${P.border}`}}>
              <h4 className="font-bold capitalize" style={{color:P.text}}>Arcade {jaw}</h4>
              {([['disponible','Espace disponible (ED)'],['necessaire','Espace nécessaire (EN)']] as const).map(([field,label]) => (
                <label key={field} className="block space-y-2">
                  <span className="text-xs font-bold" style={{color:P.text}}>{label} · mm</span>
                  <input type="number" inputMode="decimal" min="0" step="0.1"
                    value={spaces[jaw][field]}
                    onChange={e=>updateSpace(jaw,field,e.target.value)}
                    className="w-full px-4 py-3 rounded-xl text-base font-bold focus:ring-2"
                    style={{background:P.bgInput,border:`1px solid ${P.border}`,color:P.text}}
                    aria-label={`${label} — arcade ${jaw}`} placeholder="Non mesuré" />
                </label>
              ))}
              <div className="rounded-xl p-3" style={{background:P.bgPanel,color:P.text}}>
                <span className="text-xs">DDM = ED − EN : </span>
                <strong>{ddmValue === null ? 'Non calculable' : `${fmtNum(ddmValue)} mm`}</strong>
              </div>
            </div>;
          })}
        </div>
        <div className="rounded-2xl p-4" style={{background:P.bgPanel,color:P.text}}>
          <strong>DDM totale : {ddmReelleTotale === null ? 'Non calculable' : `${fmtNum(ddmReelleTotale)} mm`}</strong>
          <p className="text-xs mt-2 opacity-70">Les valeurs absentes restent non mesurées, jamais 0 par défaut. Aucune conversion angle incisif→mm.</p>
        </div>
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
    </>
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
