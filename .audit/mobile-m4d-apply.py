from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()


def replace_once(rel, old, new):
    path = root / rel
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{rel}: expected one anchor, found {count}')
    path.write_text(text.replace(old, new, 1))


# Backend: appointment becomes a first-class contextual resource.
replace_once(
    'backend/routers/mobile_resource_bridge.py',
    '"""Contextual mobile resource bridge: patient, panoramic and document resources."""',
    '"""Contextual mobile resource bridge: patient, panoramic, document and appointment resources."""',
)
replace_once(
    'backend/routers/mobile_resource_bridge.py',
    '    "document": {"permission": None, "label": "Document"},\n}',
    '    "document": {"permission": None, "label": "Document"},\n    "appointment": {"permission": "agenda", "label": "Rendez-vous"},\n}',
)
replace_once(
    'backend/routers/mobile_resource_bridge.py',
    '''def _resource_entity(db: Session, user: models.User, resource_type: str, resource_id: int):\n    resource_type = _resource_type(resource_type)\n    if resource_type == "patient":\n        return _patient_resource(db, user, resource_id)\n    if resource_type == "panoramic":\n        return _panoramic_resource(db, user, resource_id)\n    if resource_type == "document":\n        return _document_resource(db, user, resource_id)\n    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")\n''',
    '''def _appointment_resource(db: Session, user: models.User, resource_id: int) -> models.Appointment:\n    if not has_permission(user, "agenda"):\n        raise HTTPException(status_code=403, detail="Accès rendez-vous mobile refusé.")\n    appointment = db.query(models.Appointment).filter(\n        models.Appointment.id == int(resource_id),\n        models.Appointment.employer_id == user.get_employer_id(),\n    ).first()\n    if not appointment:\n        raise HTTPException(status_code=404, detail="Rendez-vous introuvable dans ce cabinet.")\n    if appointment.patient_id:\n        assert_patient_access(appointment.patient_id, user, db)\n        patient = db.query(models.Patient.id).filter(\n            models.Patient.id == appointment.patient_id,\n            models.Patient.employer_id == user.get_employer_id(),\n            models.Patient.deleted_at.is_(None),\n        ).first()\n        if not patient:\n            raise HTTPException(status_code=404, detail="Patient du rendez-vous indisponible.")\n    return appointment\n\n\ndef _resource_entity(db: Session, user: models.User, resource_type: str, resource_id: int):\n    resource_type = _resource_type(resource_type)\n    if resource_type == "patient":\n        return _patient_resource(db, user, resource_id)\n    if resource_type == "panoramic":\n        return _panoramic_resource(db, user, resource_id)\n    if resource_type == "document":\n        return _document_resource(db, user, resource_id)\n    if resource_type == "appointment":\n        return _appointment_resource(db, user, resource_id)\n    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")\n''',
)
replace_once(
    'backend/routers/mobile_resource_bridge.py',
    '''    if resource_type == "document":\n        document = _document_resource(db, mobile_user, int(context["resource_id"]))\n        patient = db.query(models.Patient).filter(\n            models.Patient.id == document.patient_id,\n            models.Patient.employer_id == mobile_user.get_employer_id(),\n            models.Patient.deleted_at.is_(None),\n        ).first()\n        if not patient:\n            raise HTTPException(status_code=404, detail="Patient du document indisponible.")\n        doc_type = getattr(document.document_type, "value", document.document_type)\n        return {\n            "type": "document",\n            "label": "Document",\n            "document": {\n                "patient_name": f"{patient.nom.upper()} {patient.prenom}",\n                "document_type": str(doc_type),\n                "name": document.title or document.original_filename or document.filename,\n                "filename": document.original_filename or document.filename,\n                "created_at": document.created_at.isoformat() if document.created_at else None,\n                "mime_type": mimetypes.guess_type(document.original_filename or document.filename or "")[0] or "application/octet-stream",\n            },\n        }\n\n    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")\n''',
    '''    if resource_type == "document":\n        document = _document_resource(db, mobile_user, int(context["resource_id"]))\n        patient = db.query(models.Patient).filter(\n            models.Patient.id == document.patient_id,\n            models.Patient.employer_id == mobile_user.get_employer_id(),\n            models.Patient.deleted_at.is_(None),\n        ).first()\n        if not patient:\n            raise HTTPException(status_code=404, detail="Patient du document indisponible.")\n        doc_type = getattr(document.document_type, "value", document.document_type)\n        return {\n            "type": "document",\n            "label": "Document",\n            "document": {\n                "patient_name": f"{patient.nom.upper()} {patient.prenom}",\n                "document_type": str(doc_type),\n                "name": document.title or document.original_filename or document.filename,\n                "filename": document.original_filename or document.filename,\n                "created_at": document.created_at.isoformat() if document.created_at else None,\n                "mime_type": mimetypes.guess_type(document.original_filename or document.filename or "")[0] or "application/octet-stream",\n            },\n        }\n\n    if resource_type == "appointment":\n        appointment = _appointment_resource(db, mobile_user, int(context["resource_id"]))\n        patient_name = appointment.patient_name or "Patient externe"\n        if appointment.patient_id:\n            patient = db.query(models.Patient).filter(\n                models.Patient.id == appointment.patient_id,\n                models.Patient.employer_id == mobile_user.get_employer_id(),\n                models.Patient.deleted_at.is_(None),\n            ).first()\n            if not patient:\n                raise HTTPException(status_code=404, detail="Patient du rendez-vous indisponible.")\n            patient_name = f"{patient.nom.upper()} {patient.prenom}"\n        status_value = getattr(appointment.status, "value", appointment.status)\n        scheduling_value = getattr(appointment.scheduling_type, "value", appointment.scheduling_type)\n        return {\n            "type": "appointment",\n            "label": "Rendez-vous",\n            "appointment": {\n                "patient_name": patient_name,\n                "datetime_start": appointment.datetime_start.isoformat() if appointment.datetime_start else None,\n                "duration_minutes": appointment.duration_minutes,\n                "motif": appointment.motif or "",\n                "status": str(status_value),\n                "scheduling_type": str(scheduling_value),\n                "notes": appointment.notes,\n            },\n        }\n\n    raise HTTPException(status_code=422, detail="Type de ressource mobile non pris en charge.")\n''',
)

# Month view: appointment chip selects the exact appointment instead of bubbling to day/new-RDV.
replace_once(
    'frontend/src/features/agenda/MonthlyView.tsx',
    '''  const [isModalOpen, setIsModalOpen] = useState(false);\n  const [modalDate, setModalDate] = useState<Date | null>(null);\n\n  const handleDayClick = (day: Date) => {\n    setModalDate(day);\n    setIsModalOpen(true);\n  };\n''',
    '''  const [isModalOpen, setIsModalOpen] = useState(false);\n  const [modalDate, setModalDate] = useState<Date | null>(null);\n  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null);\n\n  const handleDayClick = (day: Date) => {\n    setEditingAppointment(null);\n    setModalDate(day);\n    setIsModalOpen(true);\n  };\n\n  const handleAppointmentClick = (event: React.MouseEvent, appointment: Appointment) => {\n    event.stopPropagation();\n    setEditingAppointment(appointment);\n    setModalDate(new Date(appointment.datetime_start));\n    setIsModalOpen(true);\n  };\n''',
)
replace_once(
    'frontend/src/features/agenda/MonthlyView.tsx',
    '''        <button onClick={() => setIsModalOpen(true)} className="px-6 py-3 bg-[#003380] text-white font-bold rounded-2xl shadow-xl shadow-blue-900/10 hover:bg-blue-900 transition-all flex items-center gap-2">\n          <Plus size={18} /> Nouveau RV\n        </button>''',
    '''        <button onClick={() => { setEditingAppointment(null); setModalDate(selectedDate); setIsModalOpen(true); }} className="px-6 py-3 bg-[#003380] text-white font-bold rounded-2xl shadow-xl shadow-blue-900/10 hover:bg-blue-900 transition-all flex items-center gap-2">\n          <Plus size={18} /> Nouveau RV\n        </button>''',
)
replace_once(
    'frontend/src/features/agenda/MonthlyView.tsx',
    '''                    return (\n                      <div key={a.id} className="text-[9px] font-bold bg-white border border-slate-100 p-1 rounded-md text-slate-700 truncate shadow-sm">\n                        {timeLabel} - {a.patient_name}\n                      </div>\n                    );''',
    '''                    return (\n                      <button\n                        key={a.id}\n                        type="button"\n                        data-m4d-month-appointment\n                        onClick={(event) => handleAppointmentClick(event, a)}\n                        className="w-full min-h-11 text-left text-[9px] font-bold bg-white border border-slate-100 px-2 py-1 rounded-md text-slate-700 truncate shadow-sm hover:border-blue-300 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-400/40"\n                        aria-label={`Modifier le rendez-vous de ${a.patient_name || 'patient'} à ${timeLabel}`}\n                      >\n                        {timeLabel} - {a.patient_name}\n                      </button>\n                    );''',
)
replace_once(
    'frontend/src/features/agenda/MonthlyView.tsx',
    '''      <AgendaModal \n        isOpen={isModalOpen} \n        onClose={() => setIsModalOpen(false)} \n        onSaved={fetchAppointments} \n        selectedDate={modalDate || selectedDate} \n      />''',
    '''      <AgendaModal \n        isOpen={isModalOpen} \n        onClose={() => { setIsModalOpen(false); setEditingAppointment(null); }} \n        onSaved={fetchAppointments} \n        selectedDate={modalDate || selectedDate}\n        editingAppointment={editingAppointment}\n      />''',
)

# Appointment bridge component, aligned with the certified resource bridge pattern.
bridge_path = root / 'frontend/src/features/agenda/AppointmentMobileBridge.tsx'
bridge_path.write_text(r'''import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { CalendarClock, Loader2, QrCode, RefreshCcw, ShieldCheck, Smartphone, X } from 'lucide-react';
import { api } from '../../services/api';

interface BridgeTarget { id: number; name: string; email: string; role: string; is_current_user: boolean; }
interface BridgeOptions { resource_type: 'appointment'; resource_label: string; targets: BridgeTarget[]; expires_in: number; contains_patient_data: false; contains_resource_data: false; }
interface BridgeResult { qr_code: string; expires_in: number; token_code: string; target_user_id: number; target_user_name: string; target_role: string; resource_type: 'appointment'; resource_label: string; contains_patient_data: false; contains_resource_data: false; }

export const AppointmentMobileBridge = ({ appointmentId, appointmentLabel }: { appointmentId: number; appointmentLabel: string }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<BridgeOptions | null>(null);
  const [targetUserId, setTargetUserId] = useState<number | null>(null);
  const [bridge, setBridge] = useState<BridgeResult | null>(null);

  const loadOptions = async () => {
    setLoading(true); setError(null); setBridge(null);
    try {
      const response = await api.get('/mobile/resource-bridge-options', { params: { resource_type: 'appointment', resource_id: appointmentId } });
      const data = response.data as BridgeOptions;
      if (data.resource_type !== 'appointment' || data.contains_patient_data !== false || data.contains_resource_data !== false) throw new Error('Réponse de pont rendez-vous non sûre.');
      setOptions(data);
      setTargetUserId(data.targets.find(target => target.is_current_user)?.id ?? data.targets[0]?.id ?? null);
      if (!data.targets.length) setError('Aucun utilisateur mobile autorisé pour ce rendez-vous.');
    } catch (err: any) {
      setOptions(null); setTargetUserId(null);
      setError(err?.response?.data?.detail || err?.message || 'Impossible de préparer le pont mobile.');
    } finally { setLoading(false); }
  };

  useEffect(() => {
    if (open) void loadOptions();
    if (!open) { setBridge(null); setError(null); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, appointmentId]);

  const generate = async () => {
    if (!targetUserId) return;
    setGenerating(true); setError(null);
    try {
      const response = await api.post('/mobile/resource-bridge-pairing', { resource_type: 'appointment', resource_id: appointmentId, target_user_id: targetUserId });
      const data = response.data as BridgeResult;
      if (data.resource_type !== 'appointment' || data.contains_patient_data !== false || data.contains_resource_data !== false) throw new Error('Réponse de pont rendez-vous non sûre.');
      setBridge(data);
    } catch (err: any) {
      setBridge(null);
      setError(err?.response?.data?.detail || err?.message || 'Impossible de générer le QR mobile.');
    } finally { setGenerating(false); }
  };

  const modal = open && typeof document !== 'undefined' ? createPortal(
    <div className="fixed inset-0 z-[750] bg-slate-950/45 backdrop-blur-sm p-3 sm:p-6 flex items-center justify-center" role="dialog" aria-modal="true" aria-label="Pont mobile rendez-vous" onClick={(event) => event.stopPropagation()}>
      <section data-m4d-bridge className="w-full max-w-xl max-h-[92dvh] overflow-y-auto rounded-[2rem] border border-border-main bg-card-bg shadow-2xl p-5 sm:p-7">
        <div className="flex items-start justify-between gap-4 mb-5">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary mb-1"><QrCode size={18}/><p className="text-[10px] font-black uppercase tracking-[0.18em]">Pont mobile</p></div>
            <h2 className="text-xl font-black text-text-main">Ouvrir ce RDV sur mobile</h2>
            <p className="text-xs font-bold text-text-muted mt-1 truncate">{appointmentLabel}</p>
          </div>
          <button data-m4d-touch type="button" onClick={() => setOpen(false)} aria-label="Fermer le pont mobile rendez-vous" className="min-w-11 min-h-11 rounded-xl border border-border-main inline-flex items-center justify-center text-text-muted hover:text-text-main"><X size={18}/></button>
        </div>
        {loading ? <div className="min-h-40 flex items-center justify-center gap-3 text-text-muted font-bold text-sm"><Loader2 className="animate-spin" size={20}/> Préparation sécurisée…</div> : error ? <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4"><p className="text-sm font-bold text-rose-700">{error}</p><button data-m4d-touch type="button" onClick={() => void loadOptions()} className="mt-3 min-h-11 px-4 rounded-xl border border-rose-200 bg-white text-rose-700 font-black text-xs inline-flex items-center gap-2"><RefreshCcw size={15}/> Réessayer</button></div> : <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-border-main bg-background/60 p-4"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Contexte</p><p className="mt-1 font-black text-text-main inline-flex items-center gap-2"><CalendarClock size={17} className="text-primary"/> Rendez-vous</p></div>
            <label className="rounded-2xl border border-border-main bg-background/60 p-3 block"><span className="text-[10px] font-black uppercase tracking-widest text-text-muted block mb-1">Utilisateur mobile</span>{options && options.targets.length > 1 ? <select data-m4d-touch aria-label="Utilisateur mobile cible du rendez-vous" value={targetUserId ?? ''} onChange={event => { setTargetUserId(Number(event.target.value)); setBridge(null); }} className="w-full min-h-11 rounded-xl border border-border-main bg-card-bg px-3 font-bold text-sm outline-none focus:border-primary">{options.targets.map(target => <option key={target.id} value={target.id}>{target.name} · {target.role}</option>)}</select> : <p className="min-h-11 flex items-center font-black text-sm text-text-main">{options?.targets[0]?.name || 'Aucune cible'}</p>}</label>
          </div>
          {!bridge ? <button data-m4d-touch type="button" onClick={() => void generate()} disabled={!targetUserId || generating} className="w-full min-h-[52px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest inline-flex items-center justify-center gap-2 disabled:opacity-50">{generating ? <Loader2 className="animate-spin" size={17}/> : <QrCode size={17}/>} Générer le QR</button> : <div className="rounded-[1.75rem] border border-primary/15 bg-primary/[0.035] p-5 text-center"><img src={bridge.qr_code} alt="QR de pont mobile rendez-vous" className="w-52 h-52 max-w-full mx-auto rounded-2xl bg-white p-2 border border-border-main"/><p className="mt-4 text-xs text-text-muted font-bold">Ou code manuel</p><p className="mt-1 text-2xl font-black tracking-[0.24em] text-text-main">{bridge.token_code}</p><p className="mt-3 text-xs font-black text-text-main">Cible : {bridge.target_user_name}</p><p className="mt-1 text-[11px] font-bold text-text-muted">Expire dans {Math.round(bridge.expires_in / 60)} min · usage unique</p></div>}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 flex gap-3"><ShieldCheck size={19} className="text-emerald-600 shrink-0"/><div><p className="text-xs font-black text-emerald-800">QR sans donnée de rendez-vous</p><p className="mt-1 text-[11px] font-bold leading-relaxed text-emerald-700">Le QR contient seulement un secret temporaire. Le rendez-vous exact et la permission Agenda sont résolus côté serveur après l’appairage.</p></div></div>
        </div>}
      </section>
    </div>,
    document.body,
  ) : null;

  return <>
    <button data-m4d-touch type="button" onClick={() => setOpen(true)} aria-label={`Ouvrir le rendez-vous ${appointmentLabel} sur mobile`} className="w-full min-h-[52px] rounded-2xl bg-slate-950 text-white hover:bg-slate-800 inline-flex items-center justify-center gap-2 font-black text-xs uppercase tracking-widest transition-colors">
      <Smartphone size={17}/><span>Ouvrir sur mobile</span>
    </button>
    {modal}
  </>;
};
''')

# Appointment modal: add the contextual bridge only when editing an existing RDV.
replace_once(
    'frontend/src/features/agenda/AgendaModal.tsx',
    "import { useEscapeKey } from '../../hooks/useEscapeKey';",
    "import { useEscapeKey } from '../../hooks/useEscapeKey';\nimport { AppointmentMobileBridge } from './AppointmentMobileBridge';",
)
replace_once(
    'frontend/src/features/agenda/AgendaModal.tsx',
    '''          </div>\n\n          <div className="pt-6 sm:pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 border-t border-slate-100">''',
    '''          </div>\n\n          {editingAppointment && (\n            <div data-m4d-bridge-slot className="pt-2">\n              <AppointmentMobileBridge\n                appointmentId={Number(editingAppointment.id)}\n                appointmentLabel={`${editingAppointment.patient_name || 'Rendez-vous'} · ${editingAppointment.motif || 'Sans motif'}`}\n              />\n            </div>\n          )}\n\n          <div className="pt-6 sm:pt-8 flex flex-col sm:flex-row justify-between items-center gap-4 border-t border-slate-100">''',
)

# Mobile context: appointment gets an explicit, non-media card.
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    '''interface MobileDocument {\n  patient_name: string;\n  document_type: string;\n  name: string;\n  filename: string;\n  created_at?: string | null;\n  mime_type?: string | null;\n}\n''',
    '''interface MobileDocument {\n  patient_name: string;\n  document_type: string;\n  name: string;\n  filename: string;\n  created_at?: string | null;\n  mime_type?: string | null;\n}\n\ninterface MobileAppointment {\n  patient_name: string;\n  datetime_start?: string | null;\n  duration_minutes: number;\n  motif: string;\n  status: string;\n  scheduling_type: string;\n  notes?: string | null;\n}\n''',
)
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    '''  const [documentData, setDocumentData] = useState<MobileDocument | null>(null);\n  const [mediaUrl, setMediaUrl] = useState<string | null>(null);''',
    '''  const [documentData, setDocumentData] = useState<MobileDocument | null>(null);\n  const [appointment, setAppointment] = useState<MobileAppointment | null>(null);\n  const [mediaUrl, setMediaUrl] = useState<string | null>(null);''',
)
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    '''    setDocumentData(null);\n    clearMedia();\n    const stored = await MobileStorage.getBridgeContext().catch(() => null);\n    setContext(stored);\n    if (!stored || !['patient', 'panoramic', 'document'].includes(stored.type)) {''',
    '''    setDocumentData(null);\n    setAppointment(null);\n    clearMedia();\n    const stored = await MobileStorage.getBridgeContext().catch(() => null);\n    setContext(stored);\n    if (!stored || !['patient', 'panoramic', 'document', 'appointment'].includes(stored.type)) {''',
)
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    '''      if (payload.type === 'document' && payload.document && stored.type === 'document') {\n        await loadMedia();\n        setDocumentData(payload.document as MobileDocument);\n        setPhase('ready');\n        return;\n      }\n\n      throw new Error('Réponse de contexte mobile invalide.');''',
    '''      if (payload.type === 'document' && payload.document && stored.type === 'document') {\n        await loadMedia();\n        setDocumentData(payload.document as MobileDocument);\n        setPhase('ready');\n        return;\n      }\n\n      if (payload.type === 'appointment' && payload.appointment && stored.type === 'appointment') {\n        setAppointment(payload.appointment as MobileAppointment);\n        setPhase('ready');\n        return;\n      }\n\n      throw new Error('Réponse de contexte mobile invalide.');''',
)
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    "  if (phase === 'error' || (!patient && !panoramic && !documentData)) {",
    "  if (phase === 'error' || (!patient && !panoramic && !documentData && !appointment)) {",
)
replace_once(
    'frontend/src/features/mobile/Context/MobileContext.tsx',
    '''  if (documentData) {\n    const isImage = mediaType.startsWith('image/');''',
    '''  if (appointment) {\n    const schedulingLabels: Record<string, string> = { EXACT_TIME: 'Heure précise', MORNING: 'Matin', AFTERNOON: 'Après-midi', FULL_DAY: 'Toute la journée' };\n    return (\n      <div data-m4d-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>\n        <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />\n        <div className="max-w-md mx-auto relative z-10">\n          <button data-m4d-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted"><ArrowLeft size={17} /> Retour</button>\n          <div className="mt-4 flex items-center gap-2 text-primary"><ShieldCheck size={18} /><p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p></div>\n          <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Rendez-vous</h1>\n          <p className="mt-1 text-lg font-black text-text-main">{appointment.patient_name}</p>\n          <section className="mt-5 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-5">\n            <div><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Date & heure</p><p className="mt-1 text-lg font-black text-text-main">{formatDate(appointment.datetime_start)}</p><p className="mt-1 text-sm font-bold text-text-muted">{appointment.duration_minutes} min · {schedulingLabels[appointment.scheduling_type] || appointment.scheduling_type}</p></div>\n            <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Motif</p><p className="mt-1 text-base font-black text-text-main">{appointment.motif || 'Non renseigné'}</p></div>\n            <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Statut</p><p className="mt-1 inline-flex min-h-11 items-center rounded-xl bg-primary/10 px-3 text-sm font-black text-primary">{appointment.status}</p></div>\n            {appointment.notes && <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Notes</p><p className="mt-1 text-sm font-bold text-text-main whitespace-pre-wrap">{appointment.notes}</p></div>}\n          </section>\n          <p className="mt-4 text-[11px] font-bold text-text-muted text-center">Contexte résolu côté serveur · aucun identifiant rendez-vous dans l’URL</p>\n          <button data-m4d-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest">Retour au mobile</button>\n        </div>\n      </div>\n    );\n  }\n\n  if (documentData) {\n    const isImage = mediaType.startsWith('image/');''',
)

# Backend contract tests.
test_path = root / 'backend/tests/test_mobile_m4d_appointment_context.py'
test_path.write_text(r'''from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import parse_qs, urlsplit

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from backend import models
from backend.routers import mobile_resource_bridge
from backend.routers.mobile_resource_bridge import BRIDGE_CONTEXT_TABLE  # noqa: F401
from backend.security import get_password_hash


@pytest.fixture(autouse=True)
def _isolate_mobile_runtime_state(tmp_path, monkeypatch):
    from backend.main import _license_cache
    from backend.utils import rate_limit
    _license_cache.clear()
    monkeypatch.setattr(rate_limit, '_store_path', str(tmp_path / 'm4d-rate-limit.json'))
    yield
    _license_cache.clear()


def _user(db, *, email, role=models.UserRole.DENTISTE, employer_id=None, permissions=None):
    user = models.User(email=email, hashed_password=get_password_hash('TestPass123!'), role=role, nom_complet='M4D User', is_active=True, is_licensed=True, license_expires_at=datetime.utcnow() + timedelta(days=30), employer_id=employer_id, permissions=permissions or {}, approval_status='approved')
    db.add(user); db.commit(); db.refresh(user); return user


def _patient(db, owner, *, dossier='M4D-0042'):
    patient = models.Patient(numero_dossier=dossier, nom='BENNANI', prenom='Sara', date_naissance=datetime(1992, 5, 18), sexe='F', employer_id=owner.id, telephone='0612345678')
    db.add(patient); db.commit(); db.refresh(patient); return patient


def _appointment(db, owner, patient=None):
    appt = models.Appointment(patient_id=patient.id if patient else None, patient_name='BENNANI Sara' if patient else 'Visiteur externe', datetime_start=datetime(2026, 8, 25, 10, 30), duration_minutes=60, motif='Contrôle implant 36', status=models.AppointmentStatus.CONFIRME, scheduling_type=models.SchedulingType.EXACT_TIME, notes='RDV M4-D exact', employer_id=owner.id)
    db.add(appt); db.commit(); db.refresh(appt); return appt


def _cabinet(db, owner, public_id='abcdef1234567890'):
    cfg = models.CabinetConfig(owner_id=owner.id, public_id=public_id)
    db.add(cfg); db.commit(); db.refresh(cfg); return cfg


def _auth(client, user):
    response = client.post('/api/auth/login', data={'username': user.email, 'password': 'TestPass123!'})
    assert response.status_code == 200, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


def _client_public_key():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key.public_key().public_bytes(encoding=serialization.Encoding.X962, format=serialization.PublicFormat.UncompressedPoint).hex()


def _claim(client, credential):
    return client.post('/api/mobile/claim-token', json={'token': credential, 'client_public_key_hex': _client_public_key()})


def _issue(client, headers, appointment_id, target_user_id=None):
    payload = {'resource_type': 'appointment', 'resource_id': appointment_id}
    if target_user_id is not None:
        payload['target_user_id'] = target_user_id
    return client.post('/api/mobile/resource-bridge-pairing', json=payload, headers=headers)


def test_appointment_bridge_full_protocol_and_qr_are_opaque(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64)
    dentiste.nom_complet = 'Dr M4D'; dentiste.is_licensed = True; dentiste.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(dentiste); db.commit(); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    appointment = _appointment(db, dentiste, patient)

    captured_qr = {}
    def _capture(payload, **_kwargs):
        captured_qr['payload'] = payload
        return BytesIO(b'm4d-qr')
    monkeypatch.setattr(mobile_resource_bridge._admin_legacy.QRService, 'generate_qr_bytes', staticmethod(_capture))

    options = client.get(f'/api/mobile/resource-bridge-options?resource_type=appointment&resource_id={appointment.id}', headers=auth_headers)
    assert options.status_code == 200, options.text
    assert options.json()['resource_type'] == 'appointment'
    assert options.json()['resource_label'] == 'Rendez-vous'
    assert options.json()['contains_patient_data'] is False
    assert options.json()['contains_resource_data'] is False

    issued = _issue(client, auth_headers, appointment.id)
    assert issued.status_code == 200, issued.text
    assert issued.json()['contains_patient_data'] is False
    assert issued.json()['contains_resource_data'] is False
    assert 'appointment_id' not in issued.json()
    assert 'patient_id' not in issued.json()

    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    parsed = urlsplit(captured_qr['payload'])
    query = parse_qs(parsed.query, strict_parsing=True)
    assert parsed.path == '/mobile/onboarding'
    assert set(query) == {'token'}
    assert query['token'] == [pairing.token]
    lowered = captured_qr['payload'].lower()
    for forbidden in ('appointment_id=', 'resource_id=', 'patient_id=', 'bennani', 'implant', '10:30'):
        assert forbidden not in lowered

    claimed = _claim(client, pairing.token)
    assert claimed.status_code == 200, claimed.text
    mobile_headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=mobile_headers)
    assert destination.status_code == 200, destination.text
    resolved = destination.json()
    assert resolved['destination'] == 'context'
    assert resolved['fallback'] is False
    assert resolved['context']['type'] == 'appointment'
    assert resolved['context']['state'] == 'ready'

    context = client.post('/api/mobile/resource-context', json={'context_key': resolved['context']['key']}, headers=mobile_headers)
    assert context.status_code == 200, context.text
    data = context.json()
    assert data['type'] == 'appointment'
    assert data['appointment']['patient_name'] == 'BENNANI Sara'
    assert data['appointment']['datetime_start'].startswith('2026-08-25T10:30')
    assert data['appointment']['duration_minutes'] == 60
    assert data['appointment']['motif'] == 'Contrôle implant 36'
    assert data['appointment']['status'] == models.AppointmentStatus.CONFIRME.value
    assert data['appointment']['scheduling_type'] == models.SchedulingType.EXACT_TIME.value
    assert 'id' not in data['appointment']
    assert 'patient_id' not in data['appointment']


def test_appointment_target_requires_agenda_and_revocation_fails_closed(client, db, dentiste, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    patient = _patient(db, dentiste)
    appointment = _appointment(db, dentiste, patient)
    allowed = _user(db, email='m4d-agenda@cabinet.ma', employer_id=dentiste.id, permissions={'agenda': True, 'patients': False})
    denied = _user(db, email='m4d-noagenda@cabinet.ma', employer_id=dentiste.id, permissions={'agenda': False, 'patients': True})
    owner_headers = _auth(client, dentiste)

    denied_issue = _issue(client, owner_headers, appointment.id, denied.id)
    assert denied_issue.status_code == 403
    issued = _issue(client, owner_headers, appointment.id, allowed.id)
    assert issued.status_code == 200, issued.text
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}

    allowed.permissions = {'agenda': False, 'patients': False}; db.commit()
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200
    assert destination.json()['context']['state'] == 'unavailable'
    refused = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert refused.status_code == 403


def test_appointment_deleted_and_cross_tenant_are_denied(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv('CABINET_MASTER_KEY_HEX', 'a' * 64); _cabinet(db, dentiste)
    other = _user(db, email='m4d-other@cabinet.ma')
    other_patient = _patient(db, other, dossier='OTHER-M4D')
    other_appt = _appointment(db, other, other_patient)
    denied = _issue(client, auth_headers, other_appt.id)
    assert denied.status_code in (403, 404)

    patient = _patient(db, dentiste, dossier='OWN-M4D')
    appointment = _appointment(db, dentiste, patient)
    issued = _issue(client, auth_headers, appointment.id); assert issued.status_code == 200
    pairing = db.query(models.ZKAPairingToken).order_by(models.ZKAPairingToken.id.desc()).first()
    claimed = _claim(client, pairing.token); assert claimed.status_code == 200
    headers = {'Authorization': f"Bearer {claimed.json()['access_token']}"}
    destination = client.post('/api/mobile/resource-bridge-destination', json={'credential': pairing.token}, headers=headers)
    assert destination.status_code == 200
    db.delete(appointment); db.commit()
    missing = client.post('/api/mobile/resource-context', json={'context_key': destination.json()['context']['key']}, headers=headers)
    assert missing.status_code == 404
''')

# AFTER harness source and dedicated exact-head workflow are generated separately by CI prep.
print('M4-D product patch materialized successfully.')
