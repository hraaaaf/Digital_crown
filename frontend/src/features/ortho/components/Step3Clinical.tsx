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
    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-center">
        <div className="inline-flex rounded-xl border p-0.5 backdrop-blur-md" style={{ background: `${P.bgCard}80`, borderColor: P.border }}>
          {(['COM', 'STEINER', 'TWEED'] as const).map(type => (
            <button
              key={type}
              type="button"
              onClick={() => setAnalysis(type)}
              className={cn(
                'rounded-lg px-4 py-2 text-[9px] font-black uppercase tracking-[0.16em] transition-all sm:px-5',
                currentAnalysis === type ? 'shadow-sm' : 'opacity-50 hover:opacity-100'
              )}
              style={{ background: currentAnalysis === type ? P.accent : 'transparent', color: currentAnalysis === type ? '#fff' : P.text }}
            >
              {type === 'COM' ? 'McNamara (COM)' : type}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="rounded-xl p-4" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
            <div className="mb-4 flex items-center gap-2.5">
              <Activity size={16} style={{ color: P.accent }} />
              <h3 className="text-[11px] font-black uppercase tracking-[0.14em]" style={{ color: P.text }}>Données Patient</h3>
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <FieldShell label="Âge (ans)" P={P}>
                <input type="number" value={data.age} onChange={e => onChange(prev => ({ ...prev, age: e.target.value === '' ? '' : parseInt(e.target.value) }))} className="w-full bg-transparent text-base font-black outline-none" style={{ color: P.text }} />
              </FieldShell>
              <FieldShell label="Stade CVM — saisie manuelle" P={P}>
                <select value={data.cvm} onChange={e => onChange(prev => ({ ...prev, cvm: e.target.value as any }))} className="w-full bg-transparent text-xs font-bold outline-none" style={{ color: P.text }}>
                  <option value="">Non renseigné</option>
                  {['CS1', 'CS2', 'CS3', 'CS4', 'CS5', 'CS6'].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </FieldShell>
              <FieldShell label="Denture — saisie manuelle" P={P}>
                <select value={data.denture_type || ''} onChange={e => onChange(prev => ({ ...prev, denture_type: e.target.value as any }))} className="w-full bg-transparent text-xs font-bold outline-none" style={{ color: P.text }}>
                  <option value="">Non renseignée</option>
                  <option value="TEMPORAIRE">Temporaire</option>
                  <option value="MIXTE">Mixte</option>
                  <option value="PERMANENTE">Permanente</option>
                </select>
              </FieldShell>
            </div>
            <p className="mt-3 text-[10px] leading-4" style={{ color: P.textMuted }}>
              Le stade CVM n'est jamais déduit de l'âge ou du sexe. Toute valeur affichée ici provient d'une saisie manuelle à confirmer par le praticien.
            </p>
          </div>

          <AccordionSection title="Analyse Dentaire" icon={<Ruler size={14} style={{ color: P.accent }} />} defaultOpen P={P}>
            <div className="grid grid-cols-2 gap-2 pt-1">
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

          <AccordionSection title="Analyse Osseuse" icon={<Activity size={14} style={{ color: P.accent }} />} P={P}>
            <div className="grid grid-cols-2 gap-2 pt-1">
              {(currentAnalysis === 'COM' || currentAnalysis === 'TWEED') && <MetricInput label="Angle de Tweed" value={data.osseuse.angle_tweed} onChange={v => updateOsseuse('angle_tweed', v)} unit="°" P={P} />}
              {currentAnalysis === 'COM' && <>
                <MetricInput label="A′B′" value={data.osseuse.decalage_ab} onChange={v => updateOsseuse('decalage_ab', v)} unit="mm" P={P} />
                <MetricInput label="Situation Point A" value={data.osseuse.situation_a} onChange={v => updateOsseuse('situation_a', v)} unit="mm" P={P} />
                <MetricInput label="Situation Point B" value={data.osseuse.situation_b} onChange={v => updateOsseuse('situation_b', v)} unit="mm" P={P} />
                <MetricInput label="Profondeur Faciale" value={data.osseuse.profondeur_faciale} onChange={v => updateOsseuse('profondeur_faciale', v)} unit="mm" P={P} />
              </>}
              {currentAnalysis === 'STEINER' && <>
                <MetricInput label="SNA" value={data.osseuse.sna} onChange={v => updateOsseuse('sna', v)} unit="°" P={P} />
                <MetricInput label="SNB" value={data.osseuse.snb} onChange={v => updateOsseuse('snb', v)} unit="°" P={P} />
                <MetricInput label="ANB" value={data.osseuse.anb} onChange={v => updateOsseuse('anb', v)} unit="°" P={P} />
              </>}
            </div>
          </AccordionSection>

          {currentAnalysis !== 'COM' && (
            <AccordionSection title="Analyse Esthétique (Ricketts)" icon={<Activity size={14} style={{ color: P.accentSuccess }} />} P={P}>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <MetricInput label="Ligne E / Ls" value={data.esthetique?.ligne_e_ls} onChange={v => updateEsthetique('ligne_e_ls', v)} unit="mm" P={P} />
                <MetricInput label="Ligne E / Li" value={data.esthetique?.ligne_e_li} onChange={v => updateEsthetique('ligne_e_li', v)} unit="mm" P={P} />
              </div>
            </AccordionSection>
          )}
        </div>

        <div className="space-y-4">
          <div className="flex flex-col rounded-xl p-4" style={{ background: P.bgPanel, border: `1px solid ${P.border}`, boxShadow: P.shadow }}>
            <div className="mb-4 flex items-center gap-2.5">
              <Info size={16} style={{ color: P.accent }} />
              <h3 className="text-[11px] font-black uppercase tracking-[0.14em]" style={{ color: P.text }}>Synthèse descriptive</h3>
            </div>
            <div className="space-y-1.5">
              <RawRow label="Classe squelettique · legacy hors R11" value={data.classe_squelettique || 'Non classifiable / non documentée'} P={P} />
              <RawRow label="Pattern vertical · donnée historique" value={data.pattern_vertical || 'Non classifiable / non documenté'} P={P} />
              <RawRow label="DDM clinique" value={raw(data.ddm_clinique, 'mm')} P={P} />
              <RawRow label="Surplomb mesuré" value={raw(data.dentaire.surplomb, 'mm')} P={P} />
              <RawRow label="Recouvrement mesuré" value={raw(data.dentaire.recouvrement, 'mm')} P={P} />
              <RawRow label="IMPA mesuré" value={raw(data.dentaire.impa, '°')} P={P} />
              <RawRow label="Type d'arcade" value={typeArcadeEtape2 === 'Indéterminé' ? 'Indéterminé' : `Forme en ${typeArcadeEtape2}`} P={P} />
            </div>
            <p className="mt-3 text-[10px] leading-4" style={{ color: P.textMuted }}>
              Ces mesures restent descriptives et ne déterminent pas à elles seules un diagnostic ou une indication thérapeutique.
            </p>
          </div>

          <div className="rounded-lg border px-3 py-2.5 text-[10px] leading-4" style={{ borderColor: `${P.accentWarning}45`, background: `${P.accentWarning}09`, color: P.textMuted }}>
            <strong style={{ color: P.text }}>Notes praticien importées : origine non vérifiée.</strong> Ces champs peuvent contenir une saisie manuelle ou un contenu historique dont l'auteur n'est pas vérifié. Ils ne valent ni diagnostic validé ni décision thérapeutique.
          </div>

          <AccordionSection title="1. Note libre — Analyse dentaire et alvéolaire" icon={<Ruler size={13} style={{ color: P.accent }} />} P={P}>
            <textarea value={diag.analyse_dentaire} onChange={e => handleDiagChange('analyse_dentaire', e.target.value)} className="mt-1 h-24 w-full rounded-lg border bg-white/50 p-3 text-sm outline-none transition-all focus:ring-2" style={{ borderColor: P.border, color: P.text }} placeholder="Saisie libre ou contenu historique — origine non vérifiée ; à confirmer par le praticien." />
          </AccordionSection>

          <AccordionSection title="2. Note libre — Analyse squelettique" icon={<Activity size={13} style={{ color: P.accent }} />} P={P}>
            <textarea value={diag.diagnostic_squelettique} onChange={e => handleDiagChange('diagnostic_squelettique', e.target.value)} className="mt-1 h-24 w-full rounded-lg border bg-white/50 p-3 text-sm outline-none transition-all focus:ring-2" style={{ borderColor: P.border, color: P.text }} placeholder="Saisie libre ou contenu historique — origine non vérifiée ; à confirmer par le praticien." />
          </AccordionSection>
        </div>
      </div>

      <div className="space-y-2.5">
        <AccordionSection title="3. Examen des moulages — description + note libre" icon={<Activity size={13} style={{ color: P.accent }} />} P={P}>
          <div className="space-y-3 pt-1">
            <div className="rounded-lg p-3 font-mono text-[10px] leading-4" style={{ background: P.bgInput, border: `1px solid ${P.border}40`, color: P.text }}>
              <div className="mb-1.5 font-sans text-[8px] font-black uppercase tracking-wider" style={{ color: P.textMuted }}>Synthèse occlusale descriptive</div>
              {data.analyse_moulages_auto ? data.analyse_moulages_auto.split('\n').map((line, i) => <div key={i}>{line}</div>) : <span className="opacity-40 italic">En attente des données occlusales...</span>}
            </div>
            <textarea value={diag.analyse_moulages} onChange={e => handleDiagChange('analyse_moulages', e.target.value)} className="h-24 w-full rounded-lg border bg-white/50 p-3 text-sm outline-none transition-all focus:ring-2" style={{ borderColor: P.border, color: P.text }} placeholder="Note libre — auteur non vérifié ; ne vaut pas validation clinique." />
          </div>
        </AccordionSection>

        <AccordionSection title="4. Note diagnostique libre — à valider" icon={<Info size={13} style={{ color: P.accent }} />} defaultOpen P={P}>
          <textarea value={diag.synthese_diagnostique} onChange={e => handleDiagChange('synthese_diagnostique', e.target.value)} className="mt-1 h-32 w-full rounded-lg border bg-white/50 p-3 text-sm outline-none transition-all focus:ring-2" style={{ borderColor: P.border, color: P.text }} placeholder="Note diagnostique libre — à confirmer par le praticien." />
        </AccordionSection>

        <AccordionSection title="5. Note thérapeutique libre — à valider" icon={<Info size={13} style={{ color: P.accent }} />} P={P}>
          <textarea
            value={diag.strategie_therapeutique}
            onChange={e => handleDiagChange('strategie_therapeutique', e.target.value)}
            className="mt-1 h-48 w-full resize-none overflow-y-auto rounded-lg border bg-white/50 p-4 text-sm leading-relaxed outline-none transition-all focus:ring-2"
            style={{ borderColor: P.border, color: P.text }}
            placeholder="Note thérapeutique libre — à confirmer par le praticien."
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
    <div className="overflow-hidden rounded-xl" style={{ background: P.bgCard, border: `1px solid ${P.border}` }}>
      <button type="button" onClick={() => setOpen(o => !o)} className="flex min-h-11 w-full items-center justify-between px-4 py-3 text-left transition-all hover:brightness-105" style={{ background: open ? `${P.accent}07` : 'transparent' }}>
        <div className="flex min-w-0 items-center gap-2.5">{icon}<span className="text-[10px] font-black uppercase tracking-[0.12em] sm:text-[11px]" style={{ color: P.text }}>{title}</span></div>
        <ChevronDown size={15} className="shrink-0 transition-transform duration-300" style={{ color: P.textMuted, transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }} />
      </button>
      {open && <div className="border-t px-4 pb-4 pt-2" style={{ borderColor: P.border }}>{children}</div>}
    </div>
  );
};

const FieldShell: React.FC<{ label: string; P: any; children: React.ReactNode }> = ({ label, P, children }) => (
  <div className="rounded-lg p-3" style={{ background: P.bgInput, border: `1px solid ${P.border}` }}>
    <label className="mb-1.5 block text-[8px] font-black uppercase tracking-[0.1em]" style={{ color: P.textMuted }}>{label}</label>
    {children}
  </div>
);

const RawRow: React.FC<{ label: string; value: string; P: any }> = ({ label, value, P }) => (
  <div className="flex items-center justify-between gap-3 rounded-lg border px-2.5 py-2" style={{ background: P.bgInput, borderColor: P.border }}>
    <span className="text-[10px] font-bold leading-4" style={{ color: P.textMuted }}>{label}</span>
    <span className="text-right text-[10px] font-black leading-4" style={{ color: P.text }}>{value}</span>
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
  <div className="rounded-lg border p-2.5" style={{ background: P.bgInput, borderColor: P.border }}>
    <div className="mb-1 flex items-start justify-between gap-2">
      <span className="text-[8px] font-black uppercase leading-3 tracking-[0.08em]" style={{ color: P.textMuted }}>{label}</span>
      <span className="shrink-0 text-[7px] font-bold opacity-50" style={{ color: P.textDim }}>Brut</span>
    </div>
    <div className="flex items-center gap-1">
      {readOnly ? (
        <div className="w-full bg-transparent text-base font-black" style={{ color: P.text }}>{value !== '' && value !== null && value !== undefined ? value : '-'}</div>
      ) : (
        <input type="text" value={value} onChange={e => onChange?.(e.target.value)} className="w-full bg-transparent text-base font-black outline-none" style={{ color: P.text }} />
      )}
      <span className="text-[10px] font-bold" style={{ color: P.textDim }}>{unit}</span>
    </div>
  </div>
);
