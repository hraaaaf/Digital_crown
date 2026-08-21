from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_exact(rel: str, old: str, new: str, expected: int = 1) -> None:
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{rel}: expected {expected} occurrence(s), found {count}: {old[:100]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


write("backend/services/patient_scoring_service.py", '''from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models


class PatientScoringService:
    """Expose des repères patient factuels sans produire de note comportementale."""

    @staticmethod
    def _details(
        *,
        rdv_honores: int,
        rdv_annules: int,
        total_facture: float,
        total_encaisse: float,
        has_billing_data: bool,
    ) -> dict:
        remaining_due = (
            round(max(total_facture - total_encaisse, 0.0), 2)
            if has_billing_data
            else None
        )
        return {
            # Anciens champs conservés explicitement nuls pour compatibilité de contrat :
            # ils ne doivent plus être interprétés comme des scores.
            "assiduite_score": None,
            "solvabilite_score": None,
            "rdv_honores": int(rdv_honores),
            "rdv_annules": int(rdv_annules),
            "rdv_total_observe": int(rdv_honores + rdv_annules),
            "total_facture": round(float(total_facture), 2),
            "total_encaisse": round(float(total_encaisse), 2),
            "remaining_due": remaining_due,
            "has_billing_data": bool(has_billing_data),
        }

    def calculate_score(self, db: Session, patient_id: int) -> dict:
        """Retourne les faits historiques ; aucun score/grade automatique n'est calculé."""
        appointments = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id
        ).all()
        rdv_honores = sum(
            1 for appt in appointments if appt.status == models.AppointmentStatus.TERMINE
        )
        rdv_annules = sum(
            1 for appt in appointments if appt.status == models.AppointmentStatus.ANNULE
        )

        actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
        payments = db.query(models.Payment).filter(models.Payment.patient_id == patient_id).all()
        total_facture = sum(float(acte.montant or 0.0) for acte in actes)
        total_encaisse = sum(float(payment.amount or 0.0) for payment in payments)
        has_billing_data = len(actes) > 0

        return {
            "score": None,
            "grade": None,
            "details": self._details(
                rdv_honores=rdv_honores,
                rdv_annules=rdv_annules,
                total_facture=total_facture,
                total_encaisse=total_encaisse,
                has_billing_data=has_billing_data,
            ),
        }

    def calculate_scores_bulk(self, db: Session, employer_id: int) -> dict:
        """Agrège les mêmes faits en batch, sans N appels ni notation automatique."""
        patient_ids = [
            pid
            for (pid,) in db.query(models.Patient.id)
            .filter(models.Patient.employer_id == employer_id)
            .all()
        ]
        if not patient_ids:
            return {}

        appt_rows = (
            db.query(
                models.Appointment.patient_id,
                models.Appointment.status,
                func.count().label("c"),
            )
            .filter(models.Appointment.patient_id.in_(patient_ids))
            .group_by(models.Appointment.patient_id, models.Appointment.status)
            .all()
        )
        honores: dict[int, int] = {}
        annules: dict[int, int] = {}
        for pid, status, count in appt_rows:
            name = status.name if hasattr(status, "name") else str(status)
            if name == "TERMINE":
                honores[pid] = honores.get(pid, 0) + int(count)
            elif name == "ANNULE":
                annules[pid] = annules.get(pid, 0) + int(count)

        acte_rows = (
            db.query(
                models.Acte.patient_id,
                func.count(models.Acte.id),
                func.coalesce(func.sum(models.Acte.montant), 0),
            )
            .filter(models.Acte.patient_id.in_(patient_ids))
            .group_by(models.Acte.patient_id)
            .all()
        )
        billing = {
            pid: {"count": int(count), "total": float(total or 0.0)}
            for pid, count, total in acte_rows
        }
        pay_rows = (
            db.query(
                models.Payment.patient_id,
                func.coalesce(func.sum(models.Payment.amount), 0),
            )
            .filter(models.Payment.patient_id.in_(patient_ids))
            .group_by(models.Payment.patient_id)
            .all()
        )
        encaisses = {pid: float(total or 0.0) for pid, total in pay_rows}

        result: dict[int, dict] = {}
        for pid in patient_ids:
            billing_row = billing.get(pid, {"count": 0, "total": 0.0})
            result[pid] = {
                "score": None,
                "grade": None,
                "details": self._details(
                    rdv_honores=honores.get(pid, 0),
                    rdv_annules=annules.get(pid, 0),
                    total_facture=billing_row["total"],
                    total_encaisse=encaisses.get(pid, 0.0),
                    has_billing_data=billing_row["count"] > 0,
                ),
            }
        return result


patient_scoring_service = PatientScoringService()
''')

write("backend/tests/test_patient_scoring_service.py", '''"""Patient indicators: factual contracts, no automatic behavioral score."""
from datetime import datetime

from backend import models
from backend.services.patient_scoring_service import PatientScoringService


def _patient(db, dentiste, name="INDICATOR"):
    patient = models.Patient(
        nom=name,
        prenom="Test",
        date_naissance=datetime(1985, 5, 5),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.flush()
    db.add(models.DossierClinique(patient_id=patient.id, is_ortho_active=False))
    db.commit()
    db.refresh(patient)
    return patient


def _appointment(db, patient_id, status, employer_id):
    item = models.Appointment(
        patient_id=patient_id,
        employer_id=employer_id,
        datetime_start=datetime.now(),
        duration_minutes=30,
        status=status,
        motif="Test",
    )
    db.add(item)
    db.commit()


def _act(db, patient_id, practitioner_id, amount):
    item = models.Acte(
        patient_id=patient_id,
        praticien_id=practitioner_id,
        libelle="Consultation",
        type_acte=models.ActeType.SOIN,
        montant=amount,
        date_debut=datetime.now(),
    )
    db.add(item)
    db.commit()


def _payment(db, patient_id, amount):
    item = models.Payment(
        patient_id=patient_id,
        amount=amount,
        payment_method=models.PaymentMethod.ESPECES,
        payment_date=datetime.now(),
    )
    db.add(item)
    db.commit()


def test_new_patient_has_no_automatic_score_or_grade(db, dentiste):
    patient = _patient(db, dentiste, "NEWFACT")
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["score"] is None
    assert result["grade"] is None
    assert result["details"]["rdv_honores"] == 0
    assert result["details"]["rdv_annules"] == 0
    assert result["details"]["has_billing_data"] is False
    assert result["details"]["remaining_due"] is None
    assert result["details"]["assiduite_score"] is None
    assert result["details"]["solvabilite_score"] is None


def test_appointments_are_counts_not_behavioral_penalties(db, dentiste):
    patient = _patient(db, dentiste, "RDVFACT")
    _appointment(db, patient.id, models.AppointmentStatus.TERMINE, dentiste.id)
    _appointment(db, patient.id, models.AppointmentStatus.ANNULE, dentiste.id)
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["score"] is None
    assert result["details"]["rdv_honores"] == 1
    assert result["details"]["rdv_annules"] == 1
    assert result["details"]["rdv_total_observe"] == 2


def test_finance_is_factual_and_fail_closed_without_billing(db, dentiste):
    patient = _patient(db, dentiste, "PAYONLY")
    _payment(db, patient.id, 200.0)
    result = PatientScoringService().calculate_score(db, patient.id)
    assert result["details"]["has_billing_data"] is False
    assert result["details"]["total_encaisse"] == 200.0
    assert result["details"]["remaining_due"] is None


def test_finance_reports_billed_collected_and_remaining(db, dentiste):
    patient = _patient(db, dentiste, "BILLFACT")
    _act(db, patient.id, dentiste.id, 1000.0)
    _payment(db, patient.id, 400.0)
    result = PatientScoringService().calculate_score(db, patient.id)
    details = result["details"]
    assert details["has_billing_data"] is True
    assert details["total_facture"] == 1000.0
    assert details["total_encaisse"] == 400.0
    assert details["remaining_due"] == 600.0


def test_bulk_matches_factual_individual_contract(db, dentiste):
    patient = _patient(db, dentiste, "BULKFACT")
    _appointment(db, patient.id, models.AppointmentStatus.TERMINE, dentiste.id)
    _act(db, patient.id, dentiste.id, 500.0)
    _payment(db, patient.id, 500.0)
    service = PatientScoringService()
    individual = service.calculate_score(db, patient.id)
    bulk = service.calculate_scores_bulk(db, dentiste.id)[patient.id]
    assert bulk["score"] is None
    assert bulk["grade"] is None
    assert bulk["details"] == individual["details"]


def test_empty_cabinet_bulk_is_empty(db):
    service = PatientScoringService()
    assert service.calculate_scores_bulk(db, -999999) == {}
''')

write("backend/tests/test_patient_indicators_explainable.py", '''from pathlib import Path
from types import SimpleNamespace

from backend.services.rag_context import _extract_cephalo_trend


BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend" / "src"


def test_cephalo_trend_is_factual_delta_not_improvement_judgment():
    recent = SimpleNamespace(angles_data={"IMPA": {"valeur": 98.0}})
    previous = SimpleNamespace(angles_data={"IMPA": {"valeur": 94.5}})
    assert _extract_cephalo_trend([recent, previous]) == "ΔIMPA +3.5° entre les deux dernières analyses"


def test_habits_language_describes_observed_facts():
    text = (BACKEND / "services" / "habits_engine.py").read_text(encoding="utf-8")
    assert "Risque No-Show Élevé" not in text
    assert "Risque Perte Patient" not in text
    assert "Gap Ortho Critique" not in text
    assert "Annulations fréquentes" in text
    assert "Annulations consécutives sans rebooking" in text
    assert "Suivi ortho à replanifier" in text


def test_global_intelligence_score_is_no_longer_computed_or_presented():
    elite = (BACKEND / "services" / "elite_manager.py").read_text(encoding="utf-8")
    assert "intel_score = self._calculate_intelligence_score" not in elite
    hover = (FRONTEND / "features" / "patients" / "components" / "PatientSummaryHoverCard.tsx").read_text(encoding="utf-8")
    assert "data.intelligence_score" not in hover
    assert "Assistant Virtuel ODF" not in hover
    assert "Alertes IA & Suggestion" not in hover


def test_patient_page_surfaces_nba_reason_and_unmounts_dead_flash_summary():
    details = (FRONTEND / "features" / "patients" / "PatientDetailsInner.tsx").read_text(encoding="utf-8")
    assert "res.data.nba.message" in details
    assert "<FlashSummary" not in details
    assert "import { FlashSummary }" not in details
''')

write("frontend/src/stores/usePatientScoresStore.ts", '''import { create } from 'zustand';
import { api } from '../services/api';

export interface PatientScoreData {
  score: number | null;
  grade: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE' | null;
  is_manual: boolean;
  comment?: string | null;
  details: {
    assiduite_score?: null;
    solvabilite_score?: null;
    rdv_honores: number;
    rdv_annules: number;
    rdv_total_observe: number;
    total_facture: number;
    total_encaisse: number;
    remaining_due: number | null;
    has_billing_data: boolean;
  };
}

interface PatientScoresState {
  scores: Record<number, PatientScoreData>;
  loading: boolean;
  loaded: boolean;
  fetchScores: (force?: boolean) => Promise<void>;
}

let inflight: Promise<void> | null = null;

export const usePatientScoresStore = create<PatientScoresState>((set, get) => ({
  scores: {},
  loading: false,
  loaded: false,

  fetchScores: async (force = false) => {
    if (!force && (get().loaded || get().loading)) return;
    if (inflight) return inflight;

    set({ loading: true });
    inflight = (async () => {
      try {
        const res = await api.get('/patients/scores');
        const map: Record<number, PatientScoreData> = {};
        for (const [key, value] of Object.entries(res.data || {})) {
          map[Number(key)] = value as PatientScoreData;
        }
        set({ scores: map, loaded: true });
      } catch (err) {
        console.error('Erreur chargement repères patients', err);
      } finally {
        set({ loading: false });
        inflight = null;
      }
    })();
    return inflight;
  },
}));
''')

write("frontend/src/features/patients/components/PatientScoreBadge.tsx", '''import { useEffect, useRef, useState } from 'react';
import { CalendarCheck2, Loader2, RefreshCcw, Tag, WalletCards } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { usePatientScoresStore } from '../../../stores/usePatientScoresStore';

interface PatientScoreBadgeProps {
  patientId: number;
  className?: string;
  onUpdate?: () => void;
}

const MANUAL_TAGS = {
  PLATINUM: 'VIP',
  GOLD: 'Fidèle',
  SILVER: 'Standard',
  BRONZE: 'À recontacter',
} as const;

const money = (value: number) => value.toLocaleString('fr-MA', { maximumFractionDigits: 0 });

export const PatientScoreBadge = ({ patientId, className, onUpdate }: PatientScoreBadgeProps) => {
  const data = usePatientScoresStore(state => state.scores[patientId]) || null;
  const storeLoading = usePatientScoresStore(state => state.loading);
  const loaded = usePatientScoresStore(state => state.loaded);
  const fetchScores = usePatientScoresStore(state => state.fetchScores);
  const [showMenu, setShowMenu] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loaded && !storeLoading) fetchScores();
  }, [loaded, storeLoading, fetchScores]);

  useEffect(() => {
    if (!showMenu) return;
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setShowMenu(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [showMenu]);

  const updateManualTag = async (grade: keyof typeof MANUAL_TAGS | null) => {
    setIsUpdating(true);
    try {
      await api.patch(`/patients/${patientId}/grade`, {
        grade,
        comment: grade ? 'Tag cabinet manuel.' : null,
      });
      await fetchScores(true);
      onUpdate?.();
      setShowMenu(false);
    } catch (error) {
      console.error('Erreur mise à jour tag cabinet', error);
    } finally {
      setIsUpdating(false);
    }
  };

  if (!loaded && !data) {
    return <Loader2 size={14} className={cn('animate-spin text-slate-300', className)} />;
  }
  if (!data) return null;

  const { rdv_honores, rdv_annules, has_billing_data, total_facture, total_encaisse } = data.details;
  const hasRdvHistory = rdv_honores + rdv_annules > 0;
  const manualLabel = data.is_manual && data.grade ? MANUAL_TAGS[data.grade] : null;

  return (
    <div className={cn('relative inline-flex max-w-full flex-wrap items-center gap-1.5', className)} ref={menuRef}>
      <span className="inline-flex max-w-full items-center gap-1 rounded-lg border border-indigo-100 bg-indigo-50 px-2 py-1 text-[9px] font-black text-indigo-700 whitespace-nowrap">
        <CalendarCheck2 size={11} />
        {hasRdvHistory ? `${rdv_honores} RDV honoré${rdv_honores > 1 ? 's' : ''} · ${rdv_annules} annulé${rdv_annules > 1 ? 's' : ''}` : 'Aucun historique RDV'}
      </span>

      <span className="inline-flex max-w-full items-center gap-1 rounded-lg border border-emerald-100 bg-emerald-50 px-2 py-1 text-[9px] font-black text-emerald-700 whitespace-nowrap">
        <WalletCards size={11} />
        {has_billing_data ? `${money(total_encaisse)} / ${money(total_facture)} MAD encaissés` : 'Facturation indéterminée'}
      </span>

      <button
        type="button"
        onClick={(event) => { event.stopPropagation(); setShowMenu(value => !value); }}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[9px] font-black text-slate-500 hover:bg-slate-50 whitespace-nowrap"
        aria-label="Tag cabinet manuel"
        title="Tag cabinet manuel"
      >
        <Tag size={10} /> {manualLabel ? `Tag cabinet · ${manualLabel}` : 'Tag cabinet'}
      </button>

      {showMenu && (
        <div onClick={event => event.stopPropagation()} className="absolute left-0 top-full z-[9999] mt-2 w-64 rounded-2xl border border-slate-100 bg-white p-3 text-left shadow-2xl">
          <p className="px-2 pb-2 text-[9px] font-black uppercase tracking-widest text-slate-400">Tag cabinet manuel</p>
          <p className="px-2 pb-3 text-[10px] font-medium leading-relaxed text-slate-500">Ce tag est choisi par le cabinet. Il n'est jamais calculé automatiquement.</p>
          <div className="space-y-1">
            {(Object.keys(MANUAL_TAGS) as Array<keyof typeof MANUAL_TAGS>).map(grade => (
              <button
                key={grade}
                type="button"
                disabled={isUpdating}
                onClick={() => updateManualTag(grade)}
                className="w-full rounded-xl px-3 py-2 text-left text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                {MANUAL_TAGS[grade]}
              </button>
            ))}
          </div>
          {data.is_manual && (
            <button
              type="button"
              disabled={isUpdating}
              onClick={() => updateManualTag(null)}
              className="mt-2 flex w-full items-center justify-center gap-1 border-t border-slate-100 pt-3 text-[9px] font-black uppercase tracking-wider text-blue-600"
            >
              <RefreshCcw size={11} /> Retirer le tag
            </button>
          )}
        </div>
      )}
    </div>
  );
};
''')

write("frontend/src/features/patients/components/PatientSummaryHoverCard.tsx", '''import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Activity, Calendar, Clock, DollarSign, Loader2, ShieldAlert } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface PatientSummaryHoverCardProps {
  patientId: number;
  patientName: string;
  patientDossier: string;
  triggerRect: DOMRect | null;
}

interface IntelligenceData {
  patient_summary: {
    last_visit: { date: string; acte: string; days_ago: number } | null;
    next_visit: { date: string; time: string; motif: string } | null;
    clinical_summary: string;
    alerts: string[];
    risk_level: 'low' | 'moderate' | 'high';
    acts_last_90d: number;
    last_panoramic_findings: string[];
    cephalo_trend: string;
  };
  insights: Array<{
    id: string;
    type: string;
    title: string;
    content: string;
    actionLabel?: string;
    source_type?: string;
    trust_level?: number;
  }>;
  intelligence_score: number | null;
  timestamp: string;
}

export const PatientSummaryHoverCard = ({ patientId, patientName, patientDossier, triggerRect }: PatientSummaryHoverCardProps) => {
  const [data, setData] = useState<IntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [frame, setFrame] = useState({ top: 0, left: 0, width: 380 });

  useEffect(() => {
    if (!patientId) return;
    let mounted = true;
    setLoading(true);
    setError(false);
    api.get(`/intelligence/patient/${patientId}`)
      .then(res => {
        if (!mounted) return;
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching patient dossier markers:', err);
        if (!mounted) return;
        setError(true);
        setLoading(false);
      });
    return () => { mounted = false; };
  }, [patientId]);

  useEffect(() => {
    if (!triggerRect) return;
    const padding = 12;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const width = Math.min(380, Math.max(280, viewportWidth - padding * 2));
    const estimatedHeight = 430;
    let left = triggerRect.right + padding + window.scrollX;
    let top = triggerRect.top + window.scrollY;

    if (left + width > viewportWidth + window.scrollX) {
      left = triggerRect.left - width - padding + window.scrollX;
    }
    if (left < window.scrollX + padding) {
      left = window.scrollX + padding;
      top = triggerRect.bottom + padding + window.scrollY;
    }
    if (top + estimatedHeight > viewportHeight + window.scrollY) {
      top = Math.max(window.scrollY + padding, viewportHeight + window.scrollY - estimatedHeight - padding);
    }
    setFrame({ top, left, width });
  }, [triggerRect]);

  if (!triggerRect) return null;

  const otherInsights = data?.insights.filter(i => !['financial_risk', 'financial', 'safety'].includes(i.type)) ?? [];
  const financialInsights = data?.insights.filter(i => i.type === 'financial_risk' || i.type === 'financial') ?? [];

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.97, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.97, y: 8 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        style={{ position: 'absolute', top: frame.top, left: frame.left, width: frame.width, zIndex: 99999 }}
        className="pointer-events-none flex max-w-[calc(100vw-24px)] select-none flex-col gap-4 rounded-[2rem] border border-border-main/80 bg-card-bg/95 p-5 font-sans text-text-main shadow-[0_20px_50px_rgba(0,0,0,0.15)] backdrop-blur-2xl dark:border-white/10 dark:bg-[#0f172a]/95"
      >
        <div className="border-b border-border-main/50 pb-3">
          <p className="text-[9px] font-black uppercase tracking-widest text-text-muted">Repères du dossier</p>
          <h4 className="mt-1 break-words text-base font-black leading-tight tracking-tight text-primary uppercase">{patientName}</h4>
          <span className="font-mono text-[10px] font-bold tracking-wider text-text-muted">{patientDossier}</span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8">
            <Loader2 className="animate-spin text-primary" size={24} />
            <span className="text-[9px] font-black uppercase tracking-widest text-text-muted">Chargement des repères...</span>
          </div>
        ) : error || !data ? (
          <div className="py-4 text-center text-xs italic text-text-muted">Impossible de charger les repères du dossier.</div>
        ) : (
          <div className="space-y-4 text-xs">
            {data.patient_summary.alerts?.length > 0 && (
              <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 p-3">
                <ShieldAlert className="mt-0.5 flex-shrink-0 text-red-500" size={16} />
                <div>
                  <h5 className="text-[10px] font-black uppercase tracking-wider text-red-500">Vigilance dossier</h5>
                  <p className="mt-1 text-[10px] font-bold leading-normal text-red-500">{data.patient_summary.alerts.join(', ')}</p>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="block text-[9px] font-black uppercase tracking-widest text-text-muted">Résumé du dossier</span>
              <p className="rounded-xl border border-primary/5 bg-primary/5 p-2.5 text-[11px] font-medium leading-relaxed">
                {data.patient_summary.clinical_summary || 'Aucune information clinique disponible.'}
              </p>
              {data.patient_summary.cephalo_trend && data.patient_summary.cephalo_trend !== 'données insuffisantes' && (
                <p className="text-[9px] font-bold text-text-muted">Céphalométrie : {data.patient_summary.cephalo_trend}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex min-w-0 items-start gap-2 rounded-xl border border-border-main bg-card-bg p-2.5">
                <Clock className="mt-0.5 flex-shrink-0 text-blue-500" size={14} />
                <div className="min-w-0">
                  <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Dernière visite</span>
                  {data.patient_summary.last_visit ? (
                    <><span className="mt-0.5 block truncate text-[10px] font-bold">{data.patient_summary.last_visit.acte}</span><span className="font-mono text-[9px] text-text-muted">il y a {data.patient_summary.last_visit.days_ago} jours</span></>
                  ) : <span className="mt-0.5 block text-[10px] text-text-muted">—</span>}
                </div>
              </div>
              <div className="flex min-w-0 items-start gap-2 rounded-xl border border-border-main bg-card-bg p-2.5">
                <Calendar className="mt-0.5 flex-shrink-0 text-emerald-500" size={14} />
                <div className="min-w-0">
                  <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Prochain RDV</span>
                  {data.patient_summary.next_visit ? (
                    <><span className="mt-0.5 block truncate text-[10px] font-bold">{data.patient_summary.next_visit.motif || 'Soin'}</span><span className="mt-0.5 block font-mono text-[9px] text-text-muted">{new Date(data.patient_summary.next_visit.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })} à {data.patient_summary.next_visit.time}</span></>
                  ) : <span className="mt-0.5 block text-[10px] font-bold text-amber-600">Aucun RDV futur</span>}
                </div>
              </div>
            </div>

            {financialInsights.length > 0 && (
              <div className="space-y-1 border-t border-border-main/50 pt-3">
                {financialInsights.map(i => (
                  <div key={i.id} className={cn('flex items-start gap-2 rounded-xl border px-3 py-2 text-[10px]', i.type === 'financial_risk' ? 'border-amber-500/20 bg-amber-500/10 font-black text-amber-600' : 'border-primary/10 bg-primary/5 font-bold text-primary')}>
                    <DollarSign size={14} className="mt-0.5 flex-shrink-0" />
                    <span className="flex-1">{i.content}</span>
                  </div>
                ))}
              </div>
            )}

            {otherInsights.length > 0 && (
              <div className="space-y-2 border-t border-border-main/50 pt-3">
                <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Repères & actions</span>
                <div className="max-h-28 space-y-2 overflow-y-auto pr-1">
                  {otherInsights.slice(0, 3).map(i => (
                    <div key={i.id} className="flex items-start gap-2 rounded-lg bg-primary/[0.03] p-2">
                      <Activity className="mt-0.5 flex-shrink-0 text-primary" size={12} />
                      <div className="min-w-0 leading-tight">
                        <span className="block text-[9px] font-bold text-primary">{i.title}</span>
                        <p className="mt-0.5 text-[9px] font-medium leading-normal text-text-muted">{i.content}</p>
                        <p className="mt-1 text-[8px] font-bold text-slate-400">{i.source_type === 'DETERMINISTIC' ? 'Source : dossier · règle déterministe' : 'Source : dossier'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-1 text-center text-[8px] font-bold uppercase tracking-widest text-text-muted">Données du dossier • règles déterministes</div>
      </motion.div>
    </AnimatePresence>,
    document.body,
  );
};
''')

write("frontend/src/features/patients/PatientIndicatorsExplainable.test.ts", '''import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const read = (relative: string) => readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('patient indicators explainable source contracts', () => {
  it('removes automatic VIP language from patient markers', () => {
    const badge = read('./components/PatientScoreBadge.tsx');
    expect(badge).not.toMatch(/Platinum Elite|Gold Status|Bronze \(Vigilance\)|Excellence clinique|Engagement exemplaire/);
    expect(badge).toContain('Aucun historique RDV');
    expect(badge).toContain('Facturation indéterminée');
    expect(badge).toContain('Tag cabinet manuel');
  });

  it('makes the hover factual and responsive', () => {
    const hover = read('./components/PatientSummaryHoverCard.tsx');
    expect(hover).toContain('Repères du dossier');
    expect(hover).toContain('Repères & actions');
    expect(hover).toContain('Données du dossier • règles déterministes');
    expect(hover).not.toContain('data.intelligence_score');
    expect(hover).not.toContain('Alertes IA & Suggestion');
    expect(hover).not.toContain('Assistant Virtuel ODF');
    expect(hover).toContain('viewportWidth - padding * 2');
  });

  it('shows the NBA reason and removes the dead FlashSummary mount', () => {
    const details = read('./PatientDetailsInner.tsx');
    expect(details).toContain('res.data.nba.message');
    expect(details).not.toContain('<FlashSummary');
    expect(details).not.toContain("import { FlashSummary }");
  });

  it('renames the operational no-future-appointment marker', () => {
    const list = read('./PatientList.tsx');
    expect(list).toContain('Sans RDV futur');
    expect(list).not.toContain('> Fantôme<');
  });
});
''')

replace_exact(
    "frontend/src/features/patients/PatientDetailsInner.tsx",
    "import { FlashSummary } from '../../components/clinical/FlashSummary';\n",
    "",
)
replace_exact(
    "frontend/src/features/patients/PatientDetailsInner.tsx",
    "if (res.data.nba) toast(`💡 ${res.data.nba.title} — ${res.data.nba.action}`, { duration: 6000 });",
    "if (res.data.nba) toast(`💡 ${res.data.nba.title} — ${res.data.nba.message}${res.data.nba.action ? ` · Action : ${res.data.nba.action}` : ''}`, { duration: 7000 });",
)
replace_exact(
    "frontend/src/features/patients/PatientDetailsInner.tsx",
    "{activeTab === 'tracking' && <FlashSummary patientId={Number(id)} patientName={fullName} />}\n",
    "",
)
replace_exact(
    "frontend/src/features/patients/PatientList.tsx",
    "Fantôme",
    "Sans RDV futur",
    expected=2,
)

replace_exact("backend/services/habits_engine.py", '"title": "Gap Ortho Critique"', '"title": "Suivi ortho à replanifier"', expected=2)
replace_exact("backend/services/habits_engine.py", '"title": "Risque Perte Patient"', '"title": "Annulations consécutives sans rebooking"')
replace_exact("backend/services/habits_engine.py", '"title": "Risque No-Show Élevé"', '"title": "Annulations fréquentes"')
replace_exact("backend/services/habits_engine.py", '"title": "Sécurité Clinique"', '"title": "Dossier à compléter"')
replace_exact("backend/services/habits_engine.py", '"message": "Antécédents médicaux non renseignés. Risque de contre-indication."', '"message": "Antécédents médicaux non renseignés dans le dossier."')
replace_exact("backend/services/habits_engine.py", '"title": "Traitement Non Commencé"', '"title": "Devis sans acte commencé"')

replace_exact(
    "backend/services/rag_context.py",
    '''def _extract_cephalo_trend(cephalos: list) -> str:\n    """Compare IMPA between last 2 cephalo analyses to detect instability."""\n    if len(cephalos) < 2:\n        return "données insuffisantes"\n    a1 = (cephalos[0].angles_data or {})\n    a2 = (cephalos[1].angles_data or {})\n    impa1 = a1.get("IMPA", {}).get("valeur")\n    impa2 = a2.get("IMPA", {}).get("valeur")\n    if impa1 is None or impa2 is None:\n        return "données insuffisantes"\n    diff = impa1 - impa2\n    if abs(diff) <= 2:\n        return "stable"\n    return "amélioration" if diff < 0 else "dégradation"''',
    '''def _extract_cephalo_trend(cephalos: list) -> str:\n    """Expose uniquement la variation IMPA brute entre les deux dernières analyses."""\n    if len(cephalos) < 2:\n        return "données insuffisantes"\n    a1 = (cephalos[0].angles_data or {})\n    a2 = (cephalos[1].angles_data or {})\n    impa1 = a1.get("IMPA", {}).get("valeur")\n    impa2 = a2.get("IMPA", {}).get("valeur")\n    if impa1 is None or impa2 is None:\n        return "données insuffisantes"\n    diff = float(impa1) - float(impa2)\n    return f"ΔIMPA {diff:+.1f}° entre les deux dernières analyses"''',
)

replace_exact(
    "backend/services/clinical_intelligence.py",
    '''        # Check last analysis for instability\n        last_analyses = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).order_by(desc(models.CephaloAnalysis.created_at)).limit(2).all()\n        if len(last_analyses) >= 2:\n            a1 = last_analyses[0].angles_data\n            a2 = last_analyses[1].angles_data\n            if a1 and a2 and 'IMPA' in a1 and 'IMPA' in a2:\n                diff = abs(a1['IMPA'].get('valeur', 0) - a2['IMPA'].get('valeur', 0))\n                if diff > 3:\n                    alerts.append("IMPA instable sur les dernières analyses.")\n\n''',
    "",
)
replace_exact(
    "backend/services/clinical_intelligence.py",
    '''                diff = impa1 - impa2\n                cephalo_trend = "stable" if abs(diff) <= 2 else ("amélioration" if diff < 0 else "dégradation")''',
    '''                diff = float(impa1) - float(impa2)\n                cephalo_trend = f"ΔIMPA {diff:+.1f}° entre les deux dernières analyses"''',
)

replace_exact(
    "backend/services/elite_manager.py",
    "            # 4. Score d'intelligence globale\n            intel_score = self._calculate_intelligence_score(db, patient_id, summary, insights, solde_impaye)\n",
    "            # Aucun score global : les dimensions clinique, documentaire et financière restent séparées.\n            intel_score = None\n",
)
replace_exact(
    "backend/services/elite_manager.py",
    '                "intelligence_score": 0,',
    '                "intelligence_score": None,',
)

# Le composant FlashSummary reste physiquement présent pour le lot de reachability backend/frontend,
# mais il n'est plus importé ni monté dans la page patient.

# Le mutateur est volontairement auto-nettoyant : le commit produit final ne conserve
# ni script de mutation ni workflow de préparation.
(ROOT / ".github/scripts/apply_patient_indicators.py").unlink(missing_ok=True)
(ROOT / ".github/workflows/patient-indicators-product-commit.yml").unlink(missing_ok=True)

print("Patient indicators product transformation applied.")
