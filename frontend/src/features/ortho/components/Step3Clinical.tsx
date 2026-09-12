import React from 'react';
import { Activity, ChevronDown, Info, Ruler } from 'lucide-react';
import type { DiagnosticTexts, DonneesEtape3 } from '../cephaloTypes';
import { fmtNum } from '../cephaloUtils';
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
    onChange(prev => ({ ...prev, dentaire: { ...prev.dentaire, [key]: num } }));
  };

  const updateOsseuse = (key: keyof typeof data.osseuse, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange(prev => ({ ...prev, osseuse: { ...prev.osseuse, [key]: num } }));
  };

  const updateEsthetique = (key: keyof typeof data.esthetique, val: string) => {
    const num = val === '' ? '' : parseFloat(val);
    onChange(prev => ({ ...prev, esthetique: { ...prev.esthetique, [key]: num } }));
  };

  const handleDiagChange = (key: keyof DiagnosticTexts, value: string) => {
    onDiagChange(prev => ({ ...prev, [key]: value }));
  };

  const currentAnalysis = data.selectedAnalysis || 'COM';
  const updateEtape3Data = (update: Partial<DonneesEtape3>) => onChange(prev => ({ ...prev, ...update }));
  const setAnalysis = (type: 'COM' | 'STEINER' | 'TWEED') => updateEtape3Data({ selectedAnalysis: type });
  const typeArcadeEtape2 = store.etape2Data.type_arcade || 'Indéterminé';

  const raw = (value: number | '' | null | undefined, unit: string) => {
    if (value === '' || value === null || value === undefined || Number.isNaN(Number(value))) return '---';
    return `${fmtNum(Number(value))} ${unit}`;
  };

  return (
    <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-center">
        <div className="inline-flex p-1 rounded-2xl border backdrop-blur-md" style={{ background: `${P.bgCard}80`, borderColor: P.border }}>
          {(['COM', 'STEINER', 'TWEED'] as const).map(type => (
            <button
              key={type}
              onClick={() => setAnalysis(type)}
              className={cn(
                'px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] transition-all',
                currentAnalysis === type ? 'shadow-lg scale-105' : 'opacity-40 hover:opacity-100'
              )}
              style={{ background: currentAnalysis === type ? P.accent : 'transparent', color: currentAnalysis === type ? '#fff' : P.text }}
            >
              {type === 'COM' ? 'McNamara (COM)' : type}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="rounded-2xl p-6" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
            <div className="flex items-center gap-3 mb-6">
              <Activity size={18} style={{ color: P.accent }} />
              <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Données Patient</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <FieldShell label="Âge (ans)" P={P}>
                <input type="number" value={data.age} onChange={e => onChange(prev => ({ ...prev, age: e.target.value === '' ? '' : parseInt(e.target.value) }))} className="w-full bg-transparent font-black text-lg outline-none" style={{ color: P.text }} />
              </FieldShell>
              <FieldShell label="Stade CVM — praticien" P={P}>
                <select value={data.cvm} onChange={e => onChange(prev => ({ ...prev, cvm: e.target.value as any }))} className="w-full bg-transparent font-bold text-sm outline-none" style={{ color: P.text }}>
                  <option value="">Non renseigné</option>
                  {['CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6'].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </FieldShell>
              <FieldShell label="Denture — praticien" P={P}>
                <select value={data.denture_type || ''} onChange={e => onChange(prev => ({ ...prev, denture_type: e.target.value as any }))} className="w-full bg-transparent font-bold text-sm outline-none" style={{ color: P.text }}>
                  <option value="">Non renseignée</option>
                  <option value="TEMPORAIRE">Temporaire</option>
                  <option value="MIXTE">Mixte</option>
                  <option value="PERMANENTE">Permanente</option>
                </select>
              </FieldShell>
            </div>
            <p className="mt-4 text-[11px] leading-relaxed" style={{ color: P.textMuted }}>
              Le stade CVM n'est jamais déduit de l'âge ou du sexe. Toute valeur CVM affichée ici est une saisie clinique du praticien.
            </p>
          </div>

          <AccordionSection title="Analyse Dentaire" icon={<Ruler size={16} style={{ color: P.accent }} />} defaultOpen P={P}>
            <div className="grid grid-cols-2 gap-4 pt-2">
              {currentAnalysis === 'COM' && <>
                <MetricInput label="Surplomb" value={data.dentaire.surplomb} unit="mm" P={P} readOnly />
                <MetricInput label="Recouvrement" value={data.dentaire.recouvrement} unit="mm" P={P} readOnly />
                <MetricInput label="1 / Mandibulaire (IMPA)" value={data.dentaire.impa} unit="°" P={P} readOnly />
                <MetricInput label="1 / Francfort" value={data.dentaire.i_francfort} unit="°" P={P} readOnly />
                <MetricInput label="Inter Incisif (1/1)" value={data.dentaire.inter_incisif} unit="°" P={P} readOnly />
              </>}
              {currentAnalysis === 'STEINER' && <>
                <MetricInput label="1 / NA (°)" value={data.dentaire.i_na_angle || ''} onChange={v => updateDentaire('i_na_angle', v)} unit="°" P={P} />
                <MetricInput label="1 / NA (mm)" value={data.dentaire.i_na_mm || ''} onChange={v => updateDentaire('i_na_mm', v)} unit="mm" P={P} />
                <MetricInput label="1 / NB (°)" value={data.dentaire.i_nb_angle || ''} onChange={v => updateDentaire('i_nb_angle', v)} unit="°" P={P} />
                <MetricInput label="1 / NB (mm)" value={data.dentaire.i_nb_mm || ''} onChange={v => updateDentaire('i_nb_mm', v)} unit="mm" P={P} />
                <MetricInput label="Inter-Incisif" value={data.dentaire.inter_incisif} onChange={v => updateDentaire('inter_incisif', v)} unit="°" P={P} />
              </>}
              {currentAnalysis === 'TWEED' && <>
                <MetricInput label="IMPA" value={data.dentaire.impa} onChange={v => updateDentaire('impa', v)} unit="°" P={P} />
                <MetricInput label="FMIA" value={data.dentaire.fmia || ''} onChange={v => updateDentaire('fmia', v)} unit="°" P={P} />
              </>}
            </div>
          </AccordionSection>

          <AccordionSection title="Analyse Osseuse" icon={<Activity size={16} style={{ color: P.accent }} />} P={P}>
            <div className="grid grid-cols-2 gap-4 pt-2">
              {(currentAnalysis === 'COM' || currentAnalysis === 'TWEED') && <MetricInput label="Angle de Tweed" value={data.osseuse.angle_tweed} onChange={v => updateOsseuse('angle_tweed', v)} unit="°" P={P} />}
              {currentAnalysis === 'COM' && <>
                <MetricInput label="Situation Point A" value={data.osseuse.situation_a} onChange={v => updateOsseuse('situation_a', v)} unit="mm" P={P} />
                <MetricInput label="Profondeur Faciale" value={data.osseuse.profondeur_faciale} onChange={v => updateOsseuse('profondeur_faciale', v)} unit="mm" P={P} />
              </>}
              {currentAnalysis === 'STEINER' && <>
                <MetricInput label="SNA" value={data.osseuse.sna} onChange={v => updateOsseuse('sna', v)} unit="°" P={P} />
                <MetricInput label="SNB" value={data.osseuse.snb} onChange={v => updateOsseuse('snb', v)} unit="°" P={P} />
                <MetricInput label="ANB" value={data.osseuse.anb} onChange={v => updateOsseuse('anb', v)} unit="°" P={P} />
              </>}
            </div>
          </AccordionSection>

          <AccordionSection title="Analyse Esthétique (Ricketts)" icon={<Activity size={16} style={{ color: P.accentSuccess }} />} P={P}>
            <div className="grid grid-cols-2 gap-4 pt-2">
              <MetricInput label="Ligne E / Ls" value={data.esthetique?.ligne_e_ls} onChange={v => updateEsthetique('ligne_e_ls', v)} unit="mm" P={P} />
              <MetricInput label="Ligne E / Li" value={data.esthetique?.ligne_e_li} onChange={v => updateEsthetique('ligne_e_li', v)} unit="mm" P={P} />
            </div>
          </AccordionSection>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl p-6 flex flex-col" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
            <div className="flex items-center gap-3 mb-6">
              <Info size={18} style={{ color: P.accent }} />
              <h3 className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>Synthèse descriptive</h3>
            </div>
            <div className="space-y-4">
              <RawRow label="Classe squelettique" value={data.classe_squelettique || 'Non classifiable / non documentée'} P={P} />
              <RawRow label="Pattern vertical" value={data.pattern_vertical || 'Non classifiable / non documenté'} P={P} />
              <RawRow label="DDM clinique" value={raw(data.ddm_clinique, 'mm')} P={P} />
              <RawRow label="Surplomb mesuré" value={raw(data.dentaire.surplomb, 'mm')} P={P} />
              <RawRow label="Recouvrement mesuré" value={raw(data.dentaire.recouvrement, 'mm')} P={P} />
              <RawRow label="IMPA mesuré" value={raw(data.dentaire.impa, '°')} P={P} />
              <RawRow label="Type d'arcade" value={typeArcadeEtape2 === 'Indéterminé' ? 'Indéterminé' : `Forme en ${typeArcadeEtape2}`} P={P} />
            </div>
            <p className="mt-5 text-[11px] leading-relaxed" style={{ color: P.textMuted }}>
              Aucune sévérité DDM, division de Classe II, proalvéolie, supra/infraclusie ou indication thérapeutique n'est déduite localement de ces mesures.
            </p>
          </div>

          <AccordionSection title="1. Analyse Dentaire et Alvéolaire" icon={<Ruler size={14} style={{ color: P.accent }} />} P={P}>
            <textarea value={diag.analyse_dentaire} onChange={e => handleDiagChange('analyse_dentaire', e.target.value)} className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2" style={{ borderColor: P.border, color: P.text }} placeholder="Description clinique du praticien..." />
          </AccordionSection>

          <AccordionSection title="2. Analyse Squelettique" icon={<Activity size={14} style={{ color: P.accent }} />} P={P}>
            <textarea value={diag.diagnostic_squelettique} onChange={e => handleDiagChange('diagnostic_squelettique', e.target.value)} className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2" style={{ borderColor: P.border, color: P.text }} placeholder="Description clinique du praticien..." />
          </AccordionSection>
        </div>
      </div>

      <div className="space-y-3">
        <div className="rounded-xl border px-4 py-3 text-[11px] leading-5" style={{ borderColor: `${P.accentWarning}45`, background: `${P.accentWarning}09`, color: P.textMuted }}>
          <strong style={{ color: P.text }}>Notes praticien non autoritaires.</strong> Les champs libres ci-dessous documentent le raisonnement clinique mais ne créent aucune preuve R11, sélection R13 ou validation R14.
        </div>

        <AccordionSection title="3. Examen des Moulages — note praticien" icon={<Activity size={14} style={{ color: P.accent }} />} P={P}>
          <div className="space-y-4 pt-2">
            <div className="p-4 rounded-xl font-mono text-[11px] leading-relaxed" style={{ background: P.bgInput, border: `1px solid ${P.border}40`, color: P.text }}>
              {data.analyse_moulages_auto ? data.analyse_moulages_auto.split('\n').map((line, i) => <div key={i}>{line}</div>) : <span className="opacity-40 italic">En attente des données occlusales...</span>}
            </div>
            <textarea value={diag.analyse_moulages} onChange={e => handleDiagChange('analyse_moulages', e.target.value)} className="w-full h-24 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all" style={{ borderColor: P.border, color: P.text }} placeholder="Note libre du praticien — hors preuve scientifique autoritaire..." />
          </div>
        </AccordionSection>

        <AccordionSection title="4. Note diagnostique praticien — hors R11" icon={<Info size={14} style={{ color: P.accent }} />} defaultOpen P={P}>
          <textarea value={diag.synthese_diagnostique} onChange={e => handleDiagChange('synthese_diagnostique', e.target.value)} className="w-full h-32 p-3 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all mt-2" style={{ borderColor: P.border, color: P.text }} placeholder="Note diagnostique libre du praticien. Ne vaut pas diagnostic R11 autoritaire." />
        </AccordionSection>

        <AccordionSection title="5. Note thérapeutique praticien — hors R13/R14" icon={<Info size={14} style={{ color: P.accent }} />} P={P}>
          <textarea
            value={diag.strategie_therapeutique}
            onChange={e => handleDiagChange('strategie_therapeutique', e.target.value)}
            className="w-full h-48 p-4 rounded-xl bg-white/50 border text-sm focus:ring-2 outline-none transition-all resize-none overflow-y-auto leading-relaxed mt-2"
            style={{ borderColor: P.border, color: P.text }}
            placeholder="Note thérapeutique libre. Elle ne sélectionne aucune option R13 et ne valide aucune stratégie R14."
          />
        </AccordionSection>
      </div>
    </div>
  );
};

const AccordionSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  P: any;
  children: React.ReactNode;
}> = ({ title, icon, defaultOpen = false, P, children }) => {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className="rounded-2xl overflow-hidden" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
      <button type="button" onClick={() => setOpen(o => !o)} className="w-full flex items-center justify-between px-6 py-4 transition-all hover:brightness-110" style={{ background: open ? `${P.accent}08` : 'transparent' }}>
        <div className="flex items-center gap-3">{icon}<span className="text-sm font-black uppercase tracking-widest" style={{ color: P.text }}>{title}</span></div>
        <ChevronDown size={16} className="transition-transform duration-300" style={{ color: P.textMuted, transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }} />
      </button>
      {open && <div className="px-6 pb-6 pt-2 border-t" style={{ borderColor: P.border }}>{children}</div>}
    </div>
  );
};

const FieldShell: React.FC<{ label: string; P: any; children: React.ReactNode }> = ({ label, P, children }) => (
  <div className="p-4 rounded-xl" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
    <label className="text-[10px] font-black uppercase tracking-widest block mb-2" style={{ color: P.textMuted }}>{label}</label>
    {children}
  </div>
);

const RawRow: React.FC<{ label: string; value: string; P: any }> = ({ label, value, P }) => (
  <div className="flex items-center justify-between gap-4 p-3 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
    <span className="text-xs font-bold" style={{ color: P.textMuted }}>{label}</span>
    <span className="text-xs font-black text-right" style={{ color: P.text }}>{value}</span>
  </div>
);

const MetricInput = ({ label, value, onChange, unit, P, readOnly }: {
  label: string;
  value: any;
  onChange?: (v: string) => void;
  unit: string;
  P: any;
  readOnly?: boolean;
}) => (
  <div className="p-4 rounded-xl border" style={{ background: P.bgInput, borderColor: P.border }}>
    <div className="flex justify-between items-center mb-2">
      <span className="text-[9px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>{label}</span>
      <span className="text-[8px] font-bold opacity-50" style={{ color: P.textDim }}>Valeur brute</span>
    </div>
    <div className="flex items-center gap-1">
      {readOnly ? (
        <div className="w-full bg-transparent font-black text-lg" style={{ color: P.text }}>{value !== '' && value !== null && value !== undefined ? value : '-'}</div>
      ) : (
        <input type="text" value={value} onChange={e => onChange?.(e.target.value)} className="w-full bg-transparent font-black text-lg outline-none" style={{ color: P.text }} />
      )}
      <span className="text-xs font-bold" style={{ color: P.textDim }}>{unit}</span>
    </div>
  </div>
);
