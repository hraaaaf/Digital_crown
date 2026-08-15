from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one match, got {count}: {old[:80]!r}')
    p.write_text(text.replace(old, new, 1), encoding='utf-8')


# 1) Central certificate policy: canonical types + safe hydration.
Path('frontend/src/features/admin/DocumentStudio/CertificatePolicy.ts').write_text("""export const CERTIFICATE_TYPES = ['Arrêt de travail', 'Certificat de Présence', 'Autre'] as const;
export type CertificateType = (typeof CERTIFICATE_TYPES)[number];

export interface CertificateDraft {
  certifType: CertificateType | '';
  certifCustomMotif: string;
}

export function isCertificateType(value: string): value is CertificateType {
  return (CERTIFICATE_TYPES as readonly string[]).includes(value);
}

export function isPresenceCertificate(certifType: string): boolean {
  return certifType === 'Certificat de Présence';
}

export function normalizeCertificateDraft(reason: string | null | undefined): CertificateDraft {
  const normalized = (reason || '').trim();
  if (!normalized) return { certifType: '', certifCustomMotif: '' };
  if (normalized === 'Arrêt de travail' || normalized === 'Certificat de Présence') {
    return { certifType: normalized, certifCustomMotif: '' };
  }
  if (normalized === 'Autre') {
    return { certifType: 'Autre', certifCustomMotif: '' };
  }
  // Legacy/custom archived reasons are preserved verbatim instead of being
  // reinterpreted as a different practitioner-controlled certificate type.
  return { certifType: 'Autre', certifCustomMotif: normalized };
}

export function resolveCertificateReason(certifType: string, customMotif: string): string | null {
  if (!isCertificateType(certifType)) return null;
  if (certifType !== 'Autre') return certifType;
  const reason = customMotif.trim();
  return reason || null;
}

export function validateCertificateReason(certifType: string, customMotif: string): string | null {
  if (!certifType.trim()) {
    return 'Le type de certificat est requis.';
  }
  if (!isCertificateType(certifType)) {
    return 'Le type de certificat n’est pas reconnu.';
  }
  if (certifType === 'Autre' && !customMotif.trim()) {
    return 'Le motif personnalisé est requis pour un certificat en modèle libre.';
  }
  return null;
}
""", encoding='utf-8')

Path('frontend/src/features/admin/DocumentStudio/CertificatePolicy.test.ts').write_text("""import { describe, expect, it } from 'vitest';
import {
  isPresenceCertificate,
  normalizeCertificateDraft,
  resolveCertificateReason,
  validateCertificateReason,
} from './CertificatePolicy';

describe('CertificatePolicy P3 section 1', () => {
  it('exige un choix explicite pour un nouveau certificat', () => {
    expect(normalizeCertificateDraft(undefined)).toEqual({ certifType: '', certifCustomMotif: '' });
    expect(resolveCertificateReason('', '')).toBeNull();
    expect(validateCertificateReason('', '')).toMatch(/type de certificat.*requis/i);
  });

  it('refuse un modèle libre sans motif explicite', () => {
    expect(resolveCertificateReason('Autre', '   ')).toBeNull();
    expect(validateCertificateReason('Autre', '')).toMatch(/motif personnalisé.*requis/i);
  });

  it('conserve exactement le motif libre saisi sans fallback clinique', () => {
    expect(resolveCertificateReason('Autre', '  Contrôle post-opératoire  ')).toBe('Contrôle post-opératoire');
    expect(validateCertificateReason('Autre', 'Contrôle post-opératoire')).toBeNull();
  });

  it('conserve les types de certificat explicites', () => {
    expect(resolveCertificateReason('Certificat de Présence', '')).toBe('Certificat de Présence');
    expect(validateCertificateReason('Certificat de Présence', '')).toBeNull();
    expect(isPresenceCertificate('Certificat de Présence')).toBe(true);
  });

  it('réhydrate un motif historique inconnu comme personnalisé sans le réinterpréter', () => {
    expect(normalizeCertificateDraft('  Repos médical  ')).toEqual({
      certifType: 'Autre',
      certifCustomMotif: 'Repos médical',
    });
  });

  it('rejette un type technique inattendu au lieu de le sérialiser silencieusement', () => {
    expect(resolveCertificateReason('Repos médical', '')).toBeNull();
    expect(validateCertificateReason('Repos médical', '')).toMatch(/pas reconnu/i);
  });
});
""", encoding='utf-8')

# 2) DocumentHub: explicit fresh state + deterministic edit hydration + inline errors.
hub = 'frontend/src/features/admin/DocumentHub.tsx'
replace_once(
    hub,
    "import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';\n",
    "import { useDocumentGenerator } from './DocumentStudio/useDocumentGenerator';\nimport { normalizeCertificateDraft } from './DocumentStudio/CertificatePolicy';\n",
)
replace_once(
    hub,
    "  const [certifType, setCertifType] = useState('Repos médical');\n",
    "  const [certifType, setCertifType] = useState('');\n",
)
replace_once(
    hub,
    "      } else if (type === 'certificat') {\n        setActiveTab('certificat');\n        setCertifType(d.reason || 'Certificat de Repos');\n        setCertifDays(d.days || 0);\n",
    "      } else if (type === 'certificat') {\n        setActiveTab('certificat');\n        const certificateDraft = normalizeCertificateDraft(d.reason);\n        setCertifType(certificateDraft.certifType);\n        setCertifCustomMotif(certificateDraft.certifCustomMotif);\n        setCertifDays(d.days ?? 0);\n",
)
replace_once(
    hub,
    "              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}\n            />",
    "              certifCustomMotif={certifCustomMotif} setCertifCustomMotif={setCertifCustomMotif}\n              validationErrors={generator.validationErrors}\n            />",
)

# 3) Certificate form: correct semantic label, explicit buttons, inline validation,
# hide duration until a type is chosen.
form = 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.tsx'
replace_once(
    form,
    "  setCertifCustomMotif: (v: string) => void;\n}",
    "  setCertifCustomMotif: (v: string) => void;\n  validationErrors?: Array<{ field: string; message: string }>;\n}",
)
replace_once(
    form,
    "  setCertifCustomMotif,\n}) => {\n  const [suggestion, setSuggestion] = React.useState<any>(null);",
    "  setCertifCustomMotif,\n  validationErrors = [],\n}) => {\n  const [suggestion, setSuggestion] = React.useState<any>(null);\n  const typeError = validationErrors.find((error) => error.field === 'certifType');\n  const customMotifError = validationErrors.find((error) => error.field === 'certifCustomMotif');",
)
replace_once(form, '>Motif Clinique</label>', '>Type de certificat</label>')
replace_once(
    form,
    "                  <button\n                    onClick={() => setCertifType(type.id)}",
    "                  <button\n                    type=\"button\"\n                    aria-pressed={certifType === type.id}\n                    onClick={() => setCertifType(type.id)}",
)
replace_once(
    form,
    "            </div>\n\n            {certifType === 'Autre' && (",
    "            </div>\n            {typeError && (\n              <p role=\"alert\" className=\"mt-4 text-xs font-bold text-rose-600 text-center\">{typeError.message}</p>\n            )}\n\n            {certifType === 'Autre' && (",
)
replace_once(
    form,
    "                  value={certifCustomMotif}\n                  onChange={(e) => setCertifCustomMotif(e.target.value)}\n                  autoFocus\n                />",
    "                  value={certifCustomMotif}\n                  onChange={(e) => setCertifCustomMotif(e.target.value)}\n                  aria-invalid={Boolean(customMotifError)}\n                  aria-describedby={customMotifError ? 'certif-custom-motif-error' : undefined}\n                  autoFocus\n                />\n                {customMotifError && (\n                  <p id=\"certif-custom-motif-error\" role=\"alert\" className=\"mt-2 text-xs font-bold text-rose-600\">\n                    {customMotifError.message}\n                  </p>\n                )}",
)
replace_once(
    form,
    "          {certifType !== 'Certificat de Présence' && (",
    "          {Boolean(certifType) && certifType !== 'Certificat de Présence' && (",
)

# 4) Generator: presence has no artificial duration, errors point at the right field,
# incomplete auto-preview is silent, and payload stores days=0 for presence.
generator = 'frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts'
replace_once(
    generator,
    "import { resolveCertificateReason, validateCertificateReason } from './CertificatePolicy';",
    "import { isPresenceCertificate, resolveCertificateReason, validateCertificateReason } from './CertificatePolicy';",
)
old_validation = """  if (activeTab === 'certificat') {
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
  }
"""
new_validation = """  if (activeTab === 'certificat') {
    if (!isPresenceCertificate(params.certifType)) {
      if (!Number.isInteger(certifDays) || certifDays < 1) {
        errors.push({ field: 'certifDays', message: 'Le nombre de jours doit être un entier positif (minimum 1).' });
      }
      if (certifDays > 365) {
        errors.push({ field: 'certifDays', message: 'Le nombre de jours ne peut pas dépasser 365.' });
      }
    }
    const reasonError = validateCertificateReason(params.certifType, params.certifCustomMotif);
    if (reasonError) {
      errors.push({
        field: params.certifType === 'Autre' ? 'certifCustomMotif' : 'certifType',
        message: reasonError,
      });
    }
  }
"""
replace_once(generator, old_validation, new_validation)
replace_once(
    generator,
    "      payload.data = { reason, days: Number(certifDays), start_date: docDate };",
    "      payload.data = { reason, days: isPresenceCertificate(certifType) ? 0 : Number(certifDays), start_date: docDate };",
)
replace_once(
    generator,
    "    if (activeTab === 'plan') return;\n\n    // Flux dédié échéancier",
    "    if (activeTab === 'plan') return;\n    if (activeTab === 'certificat' && isPreview) {\n      const reasonError = validateCertificateReason(params.certifType, params.certifCustomMotif);\n      if (reasonError) {\n        setPdfUrl(null);\n        return;\n      }\n    }\n\n    // Flux dédié échéancier",
)

# 5) Backend generator: use the actual Studio certificate date (`start_date`) consistently.
backend_gen = 'backend/services/generators/certificat_gen.py'
replace_once(
    backend_gen,
    "def _days_in_words(n: int) -> str:\n    return _DAYS_WORDS.get(n, str(n))\n\n\nclass CertificatGenerator:",
    "def _days_in_words(n: int) -> str:\n    return _DAYS_WORDS.get(n, str(n))\n\n\ndef _resolve_certificate_date(data) -> date:\n    value = getattr(data, 'start_date', None) or getattr(data, 'doc_date', None)\n    if isinstance(value, datetime):\n        return value.date()\n    if isinstance(value, date):\n        return value\n    if isinstance(value, str):\n        try:\n            return datetime.strptime(value, '%Y-%m-%d').date()\n        except ValueError:\n            pass\n    return date.today()\n\n\nclass CertificatGenerator:",
)
replace_once(
    backend_gen,
    "        doc_date = getattr(data, 'doc_date', None) or date.today()\n        if isinstance(doc_date, str):\n            try:\n                doc_date = datetime.strptime(doc_date, '%Y-%m-%d').date()\n            except Exception:\n                doc_date = date.today()\n",
    "        doc_date = _resolve_certificate_date(data)\n",
)
replace_once(
    backend_gen,
    "        doc_date_obj = getattr(data, 'doc_date', None) or date.today()\n        if isinstance(doc_date_obj, str):\n            try:\n                doc_date_obj = datetime.strptime(doc_date_obj, '%Y-%m-%d').date()\n            except Exception:\n                doc_date_obj = date.today()\n",
    "        doc_date_obj = _resolve_certificate_date(data)\n",
)

# 6) Focused tests for UI contract and backend date policy.
Path('frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.section1.test.tsx').write_text("""import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({ api: { get: vi.fn().mockRejectedValue(new Error('offline test')) } }));

const baseProps = {
  patientId: '',
  certifDays: 5,
  setCertifDays: vi.fn(),
  certifCustomMotif: '',
  setCertifCustomMotif: vi.fn(),
};

describe('CertificateForm section 1', () => {
  it('présente le type de certificat comme choix explicite et masque la durée tant qu’il manque', () => {
    render(<CertificateForm {...baseProps} certifType="" setCertifType={vi.fn()} />);
    expect(screen.getByText('Type de certificat')).toBeTruthy();
    expect(screen.queryByText('Durée du repos')).toBeNull();
  });

  it('expose le choix comme bouton explicite non-submit', () => {
    const setCertifType = vi.fn();
    render(<CertificateForm {...baseProps} certifType="" setCertifType={setCertifType} />);
    const button = screen.getByRole('button', { name: /Arrêt de travail/i });
    expect(button.getAttribute('type')).toBe('button');
    fireEvent.click(button);
    expect(setCertifType).toHaveBeenCalledWith('Arrêt de travail');
  });

  it('affiche les erreurs de type et de motif libre sur leurs contrôles', () => {
    const { rerender } = render(
      <CertificateForm
        {...baseProps}
        certifType=""
        setCertifType={vi.fn()}
        validationErrors={[{ field: 'certifType', message: 'Le type de certificat est requis.' }]}
      />,
    );
    expect(screen.getByRole('alert').textContent).toMatch(/type de certificat est requis/i);

    rerender(
      <CertificateForm
        {...baseProps}
        certifType="Autre"
        setCertifType={vi.fn()}
        validationErrors={[{ field: 'certifCustomMotif', message: 'Le motif personnalisé est requis.' }]}
      />,
    );
    const input = screen.getByPlaceholderText(/motif personnalisé/i);
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByText(/motif personnalisé est requis/i)).toBeTruthy();
  });

  it('ne demande aucune durée pour un certificat de présence', () => {
    render(<CertificateForm {...baseProps} certifType="Certificat de Présence" setCertifType={vi.fn()} />);
    expect(screen.queryByText('Durée du repos')).toBeNull();
  });
});
""", encoding='utf-8')

Path('backend/tests/test_certificate_date_policy.py').write_text("""from datetime import date, datetime
from types import SimpleNamespace

from backend.services.generators.certificat_gen import _resolve_certificate_date


def test_certificate_date_prefers_start_date_from_document_studio():
    data = SimpleNamespace(start_date=date(2026, 8, 10), doc_date=date(2026, 8, 1))
    assert _resolve_certificate_date(data) == date(2026, 8, 10)


def test_certificate_date_accepts_legacy_doc_date_when_start_date_missing():
    data = SimpleNamespace(start_date=None, doc_date='2026-08-09')
    assert _resolve_certificate_date(data) == date(2026, 8, 9)


def test_certificate_date_accepts_datetime_values():
    data = SimpleNamespace(start_date=datetime(2026, 8, 8, 12, 30), doc_date=None)
    assert _resolve_certificate_date(data) == date(2026, 8, 8)
""", encoding='utf-8')

print('P3 Certificate section 1 patch applied')
