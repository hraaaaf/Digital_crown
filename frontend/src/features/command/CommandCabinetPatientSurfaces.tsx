/** LOT07 R4 — Command patient surfaces: real backend reads, no editing or fabricated patient/media. */
import { useEffect, useState } from 'react';
import { LockKeyhole, UserRound } from 'lucide-react';
import type { AppUser } from '../../types';
import { api } from '../../services/api';
import { hasAccess } from '../../utils/accessControl';
import { PatientMediaTimeline } from '../patients/components/PatientMediaTimeline';

export type CommandPatientSurface = 'dossier' | 'imagerie';
type PatientReference = { id: number; nom: string; prenom: string; numero_dossier: string };
type ListState = { status: 'loading' | 'ready' | 'error'; patients: PatientReference[] };
type DetailState = { status: 'idle' | 'loading' | 'ready' | 'error'; patient: PatientReference | null };

export function parseCommandPatients(input: unknown): PatientReference[] | null {
  if (!Array.isArray(input)) return null;
  const rows: PatientReference[] = [];
  for (const item of input) {
    if (!item || !Number.isSafeInteger(item.id) || item.id <= 0 ||
        typeof item.nom !== 'string' || typeof item.prenom !== 'string' ||
        !item.nom.trim() || !item.prenom.trim() ||
        !(item.numero_dossier == null || typeof item.numero_dossier === 'string')) return null;
    rows.push({ id: item.id, nom: item.nom, prenom: item.prenom,
      numero_dossier: item.numero_dossier ?? '' });
  }
  return rows;
}

export function CommandCabinetPatientSurfaces({
  user, surface,
}: { user: AppUser; surface: CommandPatientSurface }) {
  const permitted = hasAccess(user, 'patients');
  const [list, setList] = useState<ListState>({ status: 'loading', patients: [] });
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DetailState>({ status: 'idle', patient: null });

  useEffect(() => {
    if (!permitted) return;
    let alive = true;
    setList({ status: 'loading', patients: [] });
    void api.get('/patients/').then(response => {
      if (!alive) return;
      const parsed = parseCommandPatients(response.data);
      setList(parsed === null ? { status: 'error', patients: [] } : { status: 'ready', patients: parsed });
    }).catch(() => { if (alive) setList({ status: 'error', patients: [] }); });
    return () => { alive = false; };
  }, [permitted, user.id, user.employer_id, user.role]);

  useEffect(() => {
    setDetail({ status: selectedId === null ? 'idle' : 'loading', patient: null });
    if (!permitted || selectedId === null || list.status !== 'ready' ||
        !list.patients.some(item => item.id === selectedId)) return;
    let alive = true;
    void api.get(`/patients/${selectedId}`).then(response => {
      if (!alive) return;
      const parsed = parseCommandPatients([response.data]);
      if (!parsed || parsed.length !== 1 || parsed[0].id !== selectedId) {
        setDetail({ status: 'error', patient: null });
      } else {
        setDetail({ status: 'ready', patient: parsed[0] });
      }
    }).catch(() => { if (alive) setDetail({ status: 'error', patient: null }); });
    return () => { alive = false; };
  }, [permitted, selectedId, list.status, list.patients]);

  if (!permitted) {
    return <p role="alert" data-testid="r4-patient-denied">Accès au dossier et à l'imagerie refusé : permission patients requise.</p>;
  }

  const patient = detail.status === 'ready' ? detail.patient : null;
  return (
    <section className="space-y-4" data-testid={`r4-command-${surface}`} aria-label={surface === 'dossier' ? 'Dossier patient Command' : 'Imagerie Command'}>
      <header className="rounded-xl border border-border-main bg-card-bg p-4">
        <h2 className="flex items-center gap-2 text-base font-bold">
          <UserRound size={18} aria-hidden="true" />
          {surface === 'dossier' ? 'Dossier patient' : 'Imagerie clinique'}
        </h2>
        <p className="mt-1 text-xs text-text-muted">Lecture seule · Source Cabinet authentifiée · Patient sélectionné explicitement</p>
        {list.status === 'loading' && <p role="status">Chargement des patients autorisés…</p>}
        {list.status === 'error' && <p role="alert">Liste patient non vérifiable. Aucun patient présumé.</p>}
        {list.status === 'ready' && (
          <label className="mt-3 block space-y-2 text-sm font-semibold">
            <span>Sélectionner un dossier autorisé</span>
            <select className="block min-h-11 w-full rounded-lg border border-border-main bg-card-bg p-2 text-text-main"
              aria-label="Sélectionner un dossier autorisé"
              value={selectedId ?? ''}
              onChange={event => {
                const raw = event.target.value;
                const next = raw === '' ? null : Number(raw);
                setSelectedId(next !== null && list.patients.some(item => item.id === next) ? next : null);
                setDetail({ status: 'idle', patient: null });
              }}>
              <option value="">Aucun patient sélectionné</option>
              {list.patients.map(item => (
                <option key={item.id} value={item.id}>{item.prenom} {item.nom} — {item.numero_dossier || `#${item.id}`}</option>
              ))}
            </select>
          </label>
        )}
      </header>

      {selectedId === null && list.status === 'ready' && (
        <p role="status" className="rounded-xl border border-border-main bg-card-bg p-5 text-sm text-text-muted">
          Aucun dossier ouvert. Choisissez un patient pour consulter une vue autorisée.
        </p>
      )}
      {selectedId !== null && detail.status === 'loading' && <p role="status">Vérification du dossier auprès du Cabinet…</p>}
      {selectedId !== null && detail.status === 'error' && <p role="alert">Accès au dossier non vérifiable ou refusé.</p>}
      {patient && surface === 'dossier' && (
        <article className="rounded-xl border border-border-main bg-card-bg p-5" data-testid="r4-verified-dossier">
          <h3 className="text-lg font-bold">{patient.prenom} {patient.nom}</h3>
          <p className="mt-2 text-sm text-text-muted">N° dossier : {patient.numero_dossier || 'Non renseigné'}</p>
          <p className="mt-4 flex items-center gap-2 text-xs text-text-muted">
            <LockKeyhole size={14} aria-hidden="true" /> Fiche d'identité vérifiée en lecture seule. Aucune commande clinique activée.
          </p>
        </article>
      )}
      {patient && surface === 'imagerie' && (
        <div data-testid="r4-verified-imagerie">
          <PatientMediaTimeline key={patient.id} patientId={patient.id} readOnly />
        </div>
      )}
    </section>
  );
}
