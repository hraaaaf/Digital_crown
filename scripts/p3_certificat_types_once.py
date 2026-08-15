from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

policy_path = ROOT / "frontend/src/features/admin/DocumentStudio/CertificatePolicy.ts"
policy_path.write_text("""export const CERTIFICATE_TYPE_WORK_STOP = 'Arrêt de travail' as const;
export const CERTIFICATE_TYPE_PRESENCE = 'Certificat de Présence' as const;
export const CERTIFICATE_TYPE_FREE = 'Certificat médical' as const;

export const CERTIFICATE_TYPES = [
  CERTIFICATE_TYPE_WORK_STOP,
  CERTIFICATE_TYPE_PRESENCE,
  CERTIFICATE_TYPE_FREE,
] as const;

export type CertificateType = (typeof CERTIFICATE_TYPES)[number];

const LEGACY_WORK_STOP_TYPES = new Set([
  'Repos médical',
  'Certificat de Repos',
  'Repos Post-Opératoire',
  "Suite d'Intervention",
]);

export interface NormalizedCertificateSelection {
  type: CertificateType;
  content: string;
}

export function normalizeCertificateSelection(
  certifType: string,
  customContent: string,
): NormalizedCertificateSelection {
  const rawType = (certifType || '').trim();
  const rawContent = customContent || '';

  if (rawType === CERTIFICATE_TYPE_WORK_STOP || LEGACY_WORK_STOP_TYPES.has(rawType)) {
    return { type: CERTIFICATE_TYPE_WORK_STOP, content: rawContent };
  }

  if (rawType === CERTIFICATE_TYPE_PRESENCE) {
    return { type: CERTIFICATE_TYPE_PRESENCE, content: rawContent };
  }

  if (rawType === CERTIFICATE_TYPE_FREE || rawType === 'Autre') {
    return { type: CERTIFICATE_TYPE_FREE, content: rawContent };
  }

  if (rawType) {
    return {
      type: CERTIFICATE_TYPE_FREE,
      content: rawContent.trim() ? rawContent : rawType,
    };
  }

  return { type: CERTIFICATE_TYPE_WORK_STOP, content: rawContent };
}

export function certificateRequiresDuration(certifType: string): boolean {
  return normalizeCertificateSelection(certifType, '').type === CERTIFICATE_TYPE_WORK_STOP;
}

export function resolveCertificateReason(certifType: string, customContent: string): string | null {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  if (normalized.type === CERTIFICATE_TYPE_FREE && !normalized.content.trim()) return null;
  return normalized.type;
}

export function validateCertificateReason(certifType: string, customContent: string): string | null {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  if (normalized.type === CERTIFICATE_TYPE_FREE && !normalized.content.trim()) {
    return 'Le contenu du certificat médical est requis.';
  }
  if (!resolveCertificateReason(certifType, customContent)) {
    return 'La nature du certificat est requise.';
  }
  return null;
}

export function buildCertificatePayload(
  certifType: string,
  customContent: string,
  certifDays: number,
  startDate: string,
) {
  const normalized = normalizeCertificateSelection(certifType, customContent);
  return {
    reason: normalized.type,
    days: certificateRequiresDuration(normalized.type) ? Number(certifDays) : 0,
    start_date: startDate,
    ...(normalized.type === CERTIFICATE_TYPE_FREE
      ? { content: normalized.content.trim() }
      : {}),
  };
}
""", encoding="utf-8")

policy_test_path = ROOT / "frontend/src/features/admin/DocumentStudio/CertificatePolicy.test.ts"
policy_test_path.write_text("""import { describe, expect, it } from 'vitest';
import {
  buildCertificatePayload,
  certificateRequiresDuration,
  normalizeCertificateSelection,
  resolveCertificateReason,
  validateCertificateReason,
} from './CertificatePolicy';

describe('CertificatePolicy P3 — types et contenu libre', () => {
  it('refuse un certificat médical libre sans contenu explicite', () => {
    expect(resolveCertificateReason('Certificat médical', '   ')).toBeNull();
    expect(validateCertificateReason('Certificat médical', '')).toMatch(/contenu.*requis/i);
  });

  it('conserve exactement le contenu libre saisi et le sépare du type', () => {
    const payload = buildCertificatePayload(
      'Certificat médical',
      '  Contrôle post-opératoire sans complication.  ',
      5,
      '2026-08-15',
    );
    expect(payload).toEqual({
      reason: 'Certificat médical',
      days: 0,
      start_date: '2026-08-15',
      content: 'Contrôle post-opératoire sans complication.',
    });
  });

  it('ne demande une durée que pour l’arrêt de travail', () => {
    expect(certificateRequiresDuration('Arrêt de travail')).toBe(true);
    expect(certificateRequiresDuration('Certificat de Présence')).toBe(false);
    expect(certificateRequiresDuration('Certificat médical')).toBe(false);
  });

  it('normalise les anciens repos sans perdre leur intention', () => {
    expect(normalizeCertificateSelection('Repos médical', '')).toEqual({
      type: 'Arrêt de travail',
      content: '',
    });
  });

  it('récupère un ancien motif libre comme contenu de certificat médical', () => {
    expect(normalizeCertificateSelection('Contrôle post-opératoire', '')).toEqual({
      type: 'Certificat médical',
      content: 'Contrôle post-opératoire',
    });
  });

  it('migre le legacy Autre vers le certificat médical libre', () => {
    expect(normalizeCertificateSelection('Autre', 'Texte libre')).toEqual({
      type: 'Certificat médical',
      content: 'Texte libre',
    });
  });
});
""", encoding="utf-8")

form_path = ROOT / "frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.tsx"
form_path.write_text("""import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../../utils/cn';
import { CheckCircle2, Clock, Edit3, AlertCircle } from 'lucide-react';
import { api } from '../../../../services/api';
import {
  CERTIFICATE_TYPE_FREE,
  CERTIFICATE_TYPE_PRESENCE,
  CERTIFICATE_TYPE_WORK_STOP,
  certificateRequiresDuration,
  normalizeCertificateSelection,
} from '../CertificatePolicy';

interface CertificateFormProps {
  patientId: string;
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (v: string) => void;
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  patientId,
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  certifCustomMotif,
  setCertifCustomMotif,
}) => {
  const [suggestion, setSuggestion] = React.useState<any>(null);

  React.useEffect(() => {
    if (!patientId) return;
    const fetchSuggestion = async () => {
      try {
        const res = await api.get(`/prescriptions/certif-suggest/${patientId}`);
        setSuggestion(res.data);
      } catch (err) {
        console.error('Certif Suggest Error:', err);
      }
    };
    fetchSuggestion();
  }, [patientId]);

  React.useEffect(() => {
    const normalized = normalizeCertificateSelection(certifType, certifCustomMotif);
    if (normalized.type !== certifType) setCertifType(normalized.type);
    if (normalized.content !== certifCustomMotif) setCertifCustomMotif(normalized.content);
  }, [certifType, certifCustomMotif, setCertifType, setCertifCustomMotif]);

  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";

  const certifTypes = [
    {
      id: CERTIFICATE_TYPE_WORK_STOP,
      label: 'Arrêt de travail',
      icon: <Clock size={14} />,
      description: 'Repos prescrit et daté par le praticien',
    },
    {
      id: CERTIFICATE_TYPE_PRESENCE,
      label: 'Présence (Soin)',
      icon: <CheckCircle2 size={14} />,
      description: 'Justifie la présence effective au cabinet',
    },
    {
      id: CERTIFICATE_TYPE_FREE,
      label: 'Certificat médical',
      icon: <Edit3 size={14} />,
      description: 'Document libre rédigé par le praticien',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-8">
      <div className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-10 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />

        <div className="relative z-10 space-y-10">
          <div>
            <div className="flex items-center justify-between mb-4 gap-4">
              <label className={labelClass + " mb-0"}>Nature du document</label>
              {suggestion && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-[9px] font-bold bg-amber-500/10 text-amber-700 border border-amber-200 max-w-sm"
                >
                  <AlertCircle size={12} className="shrink-0" />
                  <span>
                    Signal documentaire : {suggestion.reason || 'contexte détecté'}. Suggestion non appliquée ; type et durée restent à valider par le praticien.
                  </span>
                </motion.div>
              )}
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              {certifTypes.map((type) => (
                <div key={type.id} className="flex flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setCertifType(type.id)}
                    className={cn(
                      "flex items-center justify-center gap-3 px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm min-w-[180px]",
                      certifType === type.id
                        ? "bg-primary text-white border-primary shadow-xl shadow-primary/20"
                        : "bg-white text-slate-500 border-slate-100 hover:border-primary/30"
                    )}
                    style={certifType === type.id ? { backgroundColor: 'var(--primary)' } : {}}
                    aria-pressed={certifType === type.id}
                  >
                    <span className={cn(certifType === type.id ? "text-white" : "text-primary/40")}>{type.icon}</span>
                    {type.label}
                  </button>
                  <span className="text-[7px] font-black text-slate-300 uppercase tracking-widest text-center px-4 max-w-[210px]">
                    {type.description}
                  </span>
                </div>
              ))}
            </div>

            {certifType === CERTIFICATE_TYPE_FREE && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
                <label className={labelClass}>Contenu du certificat médical</label>
                <textarea
                  className={cn(inputClass, "min-h-40 resize-y leading-relaxed")}
                  placeholder="Rédigez librement le contenu certifié par le praticien..."
                  value={certifCustomMotif}
                  onChange={(e) => setCertifCustomMotif(e.target.value)}
                  autoFocus
                  rows={6}
                />
                <p className="mt-2 px-1 text-[9px] font-bold text-slate-400">
                  Ce texte est repris tel quel dans le corps du certificat. Aucune suggestion clinique n’est injectée automatiquement.
                </p>
              </motion.div>
            )}
          </div>

          {certificateRequiresDuration(certifType) && (
            <div className="pt-8 border-t border-slate-100/50">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <label className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">À déterminer et valider par le praticien.</p>
                </div>
                <span className="text-3xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span>
                </span>
              </div>

              <input
                type="range"
                min="1"
                max="30"
                step="1"
                value={certifDays}
                onChange={(e) => setCertifDays(parseInt(e.target.value))}
                className="w-full h-2.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                style={{ accentColor: 'var(--primary)' }}
                aria-label="Durée du repos en jours"
              />
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-slate-400">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
        <span className="text-[9px] font-black uppercase tracking-[0.3em]">Certificat Médical SÉCURISÉ</span>
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
      </div>
    </div>
  );
};
""", encoding="utf-8")

form_test_path = ROOT / "frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.p3a.test.tsx"
form_test_path.write_text("""import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('CertificateForm P3', () => {
  it('n’applique jamais automatiquement type ou durée depuis une suggestion haute confiance', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        confidence: 'high',
        type: 'Arrêt de travail',
        days: 3,
        reason: 'Contexte chirurgical détecté',
      },
    } as never);

    const setCertifType = vi.fn();
    const setCertifDays = vi.fn();

    render(
      <CertificateForm
        patientId="42"
        certifType="Certificat de Présence"
        setCertifType={setCertifType}
        certifDays={1}
        setCertifDays={setCertifDays}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/prescriptions/certif-suggest/42'));

    expect(setCertifType).not.toHaveBeenCalled();
    expect(setCertifDays).not.toHaveBeenCalled();
    expect(screen.getByText(/Suggestion non appliquée/i)).toBeTruthy();
    expect(screen.getByText(/valider.*praticien/i)).toBeTruthy();
  });

  it('affiche Certificat médical comme dernier choix et ouvre une rédaction libre', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: null } as never);
    const setCertifType = vi.fn();

    const { rerender } = render(
      <CertificateForm
        patientId="42"
        certifType="Arrêt de travail"
        setCertifType={setCertifType}
        certifDays={2}
        setCertifDays={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    const choices = screen.getAllByRole('button');
    expect(choices[choices.length - 1].textContent).toMatch(/Certificat médical/i);
    fireEvent.click(screen.getByRole('button', { name: /Certificat médical/i }));
    expect(setCertifType).toHaveBeenCalledWith('Certificat médical');

    rerender(
      <CertificateForm
        patientId="42"
        certifType="Certificat médical"
        setCertifType={setCertifType}
        certifDays={2}
        setCertifDays={vi.fn()}
        certifCustomMotif="Texte rédigé par le praticien"
        setCertifCustomMotif={vi.fn()}
      />,
    );

    expect(screen.getByRole('textbox', { name: /Contenu du certificat médical/i })).toHaveValue('Texte rédigé par le praticien');
    expect(screen.queryByLabelText(/Durée du repos/i)).toBeNull();
  });
});
""", encoding="utf-8")

# DocumentHub: visible default + restore free content on archive edit.
hub_path = ROOT / "frontend/src/features/admin/DocumentHub.tsx"
hub = hub_path.read_text(encoding="utf-8")
old = "const [certifType, setCertifType] = useState('Repos médical');"
assert old in hub, "DocumentHub default certificate type not found"
hub = hub.replace(old, "const [certifType, setCertifType] = useState('Arrêt de travail');", 1)
old = """        setCertifType(d.reason || 'Certificat de Repos');
        setCertifDays(d.days || 0);"""
new = """        setCertifType(d.reason || 'Arrêt de travail');
        setCertifDays(d.days ?? 0);
        setCertifCustomMotif(d.content || '');"""
assert old in hub, "DocumentHub certificate hydration block not found"
hub = hub.replace(old, new, 1)
hub_path.write_text(hub, encoding="utf-8")

# Generator hook: duration only when applicable + explicit free-content payload.
gen_hook_path = ROOT / "frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts"
gen_hook = gen_hook_path.read_text(encoding="utf-8")
old = "import { resolveCertificateReason, validateCertificateReason } from './CertificatePolicy';"
new = "import { buildCertificatePayload, certificateRequiresDuration, validateCertificateReason } from './CertificatePolicy';"
assert old in gen_hook, "CertificatePolicy import not found"
gen_hook = gen_hook.replace(old, new, 1)
old = """  if (activeTab === 'certificat') {
    if (!Number.isInteger(certifDays) || certifDays < 1) {
      errors.push({ field: 'certifDays', message: 'Le nombre de jours doit être un entier positif (minimum 1).' });
    }
    if (certifDays > 365) {
      errors.push({ field: 'certifDays', message: 'Le nombre de jours ne peut pas dépasser 365.' });
    }
    const reasonError = validateCertificateReason(params.certifType, params.certifCustomMotif);
    if (reasonError) {
      errors.push({ field: 'certifCustomMotif', message: reasonError });
    }
  }"""
new = """  if (activeTab === 'certificat') {
    if (certificateRequiresDuration(params.certifType)) {
      if (!Number.isInteger(certifDays) || certifDays < 1) {
        errors.push({ field: 'certifDays', message: 'Le nombre de jours doit être un entier positif (minimum 1).' });
      }
      if (certifDays > 365) {
        errors.push({ field: 'certifDays', message: 'Le nombre de jours ne peut pas dépasser 365.' });
      }
    }
    const reasonError = validateCertificateReason(params.certifType, params.certifCustomMotif);
    if (reasonError) {
      errors.push({ field: 'certifCustomMotif', message: reasonError });
    }
  }"""
assert old in gen_hook, "certificate validation block not found"
gen_hook = gen_hook.replace(old, new, 1)
old = """    } else if (activeTab === 'certificat') {
      const reason = resolveCertificateReason(certifType, certifCustomMotif);
      if (!reason) throw new Error('Le motif du certificat est requis.');
      payload.data = { reason, days: Number(certifDays), start_date: docDate };"""
new = """    } else if (activeTab === 'certificat') {
      payload.data = buildCertificatePayload(certifType, certifCustomMotif, certifDays, docDate);"""
assert old in gen_hook, "certificate payload block not found"
gen_hook = gen_hook.replace(old, new, 1)
gen_hook_path.write_text(gen_hook, encoding="utf-8")

# Backend schema: explicit practitioner-authored free content.
schema_path = ROOT / "backend/schemas/documents.py"
schema = schema_path.read_text(encoding="utf-8")
old = """class CertificatData(BaseModel):
    reason: Optional[str] = \"Certificat Médical\"
    days: Optional[int] = 1
    start_date: Optional[datetime.date] = None
    is_work_stop: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None
"""
new = """class CertificatData(BaseModel):
    reason: Optional[str] = \"Arrêt de travail\"
    days: Optional[int] = 1
    start_date: Optional[datetime.date] = None
    content: Optional[str] = None
    is_work_stop: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None
"""
assert old in schema, "CertificatData block not found"
schema = schema.replace(old, new, 1)
schema_path.write_text(schema, encoding="utf-8")

# Backend PDF: free certificate body is exact practitioner text, escaped for ReportLab.
cert_gen_path = ROOT / "backend/services/generators/certificat_gen.py"
cert_gen = cert_gen_path.read_text(encoding="utf-8")
old = "from datetime import datetime, date\n"
new = "from datetime import datetime, date\nfrom xml.sax.saxutils import escape\n"
assert old in cert_gen, "certificat_gen datetime import not found"
cert_gen = cert_gen.replace(old, new, 1)
anchor = """def _days_in_words(n: int) -> str:
    return _DAYS_WORDS.get(n, str(n))


class CertificatGenerator:"""
replacement = """def _days_in_words(n: int) -> str:
    return _DAYS_WORDS.get(n, str(n))


def _is_free_medical_certificate(reason: str) -> bool:
    return (reason or '').strip().casefold() in {'certificat médical', 'certificat medical'}


def _format_free_certificate_content(content: str) -> str:
    cleaned = (content or '').strip()
    if not cleaned:
        raise ValueError('Le contenu du certificat médical est requis.')
    return '<br/>'.join(escape(line) for line in cleaned.splitlines())


class CertificatGenerator:"""
assert anchor in cert_gen, "certificat_gen helper anchor not found"
cert_gen = cert_gen.replace(anchor, replacement, 1)
old = """        reason = (getattr(data, 'reason', \"Repos médical\") or \"Repos médical\").strip()
        days = getattr(data, 'days', 1)
        observations = getattr(data, 'observations', '').strip()
        reason_lower = reason.lower()"""
new = """        reason = (getattr(data, 'reason', \"Arrêt de travail\") or \"Arrêt de travail\").strip()
        days = getattr(data, 'days', 1)
        free_content = getattr(data, 'content', None)
        observations = getattr(data, 'observations', '').strip()
        reason_lower = reason.lower()
        is_free_medical = _is_free_medical_certificate(reason)"""
assert old in cert_gen, "certificate reason block not found"
cert_gen = cert_gen.replace(old, new, 1)
old = "        days_int = int(days)\n"
new = "        days_int = int(days or 0)\n"
assert old in cert_gen, "days conversion not found"
cert_gen = cert_gen.replace(old, new, 1)
old = """        if \"présence\" in reason_lower:
            spec = \"orthodontiques\" if is_ortho else \"bucco-dentaires\"
            certif_text = (
                f\"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que \"
                f\"{hon} <b>{nom_complet}</b> a été <b>{pres} à notre cabinet</b> \"
                f\"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> de façon effective, pour y recevoir des soins {spec}.<br/><br/>\"
            )
        else:
            # Fallback par défaut (Repos, Autre, etc.)
            certif_text = (
                f\"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que l'état de santé de \"
                f\"{hon} <b>{nom_complet}</b>{age_text}, nécessite <b>{eviction_term}</b> \"
                f\"{date_phrase} {days_label}.<br/><br/>\"
            )"""
new = """        if is_free_medical:
            certif_text = _format_free_certificate_content(free_content)
        elif \"présence\" in reason_lower:
            spec = \"orthodontiques\" if is_ortho else \"bucco-dentaires\"
            certif_text = (
                f\"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que \"
                f\"{hon} <b>{nom_complet}</b> a été <b>{pres} à notre cabinet</b> \"
                f\"le <b>{doc_date_obj.strftime('%d/%m/%Y')}</b> de façon effective, pour y recevoir des soins {spec}.<br/><br/>\"
            )
        else:
            certif_text = (
                f\"Je soussigné Dr <b>{dr_name_clean}</b>, chirurgien-dentiste, certifie que l'état de santé de \"
                f\"{hon} <b>{nom_complet}</b>{age_text}, nécessite <b>{eviction_term}</b> \"
                f\"{date_phrase} {days_label}.<br/><br/>\"
            )"""
assert old in cert_gen, "certificate body branch not found"
cert_gen = cert_gen.replace(old, new, 1)
old = """        certif_text += (
            f\"Ce certificat est délivré à {int_}, remis en main propre à sa demande, \"
            f\"pour servir et valoir ce que de droit.\"
        )"""
new = """        if not is_free_medical:
            certif_text += (
                f\"Ce certificat est délivré à {int_}, remis en main propre à sa demande, \"
                f\"pour servir et valoir ce que de droit.\"
            )"""
assert old in cert_gen, "certificate closing block not found"
cert_gen = cert_gen.replace(old, new, 1)
cert_gen_path.write_text(cert_gen, encoding="utf-8")

backend_test = ROOT / "backend/tests/test_certificat_free_content_p3.py"
backend_test.write_text("""from backend.schemas.documents import CertificatData
from backend.services.generators.certificat_gen import (
    _format_free_certificate_content,
    _is_free_medical_certificate,
)


def test_certificat_data_accepts_explicit_practitioner_content():
    data = CertificatData(
        reason='Certificat médical',
        days=0,
        content='Texte libre du praticien',
    )
    assert data.reason == 'Certificat médical'
    assert data.content == 'Texte libre du praticien'
    assert data.days == 0


def test_free_certificate_reason_is_explicit_not_fuzzy():
    assert _is_free_medical_certificate('Certificat médical') is True
    assert _is_free_medical_certificate('CERTIFICAT MEDICAL') is True
    assert _is_free_medical_certificate('Certificat de Présence') is False
    assert _is_free_medical_certificate('Arrêt de travail') is False


def test_free_certificate_content_is_preserved_but_reportlab_markup_is_escaped():
    rendered = _format_free_certificate_content('Ligne 1\n<diagnostic> & contrôle')
    assert rendered == 'Ligne 1<br/>&lt;diagnostic&gt; &amp; contrôle'


def test_free_certificate_rejects_empty_content():
    try:
        _format_free_certificate_content('   ')
    except ValueError as exc:
        assert 'contenu du certificat médical' in str(exc).lower()
    else:
        raise AssertionError('Un certificat médical libre vide doit être refusé')
""", encoding="utf-8")

# The one-shot patch machinery must not remain in the PR.
for rel in [
    "scripts/p3_certificat_types_once.py",
    ".github/workflows/p3-certificat-types-once.yml",
]:
    target = ROOT / rel
    if target.exists():
        target.unlink()
