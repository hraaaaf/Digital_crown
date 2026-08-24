import { useEffect, useState } from 'react';
import { Loader2, QrCode, RefreshCcw, ShieldCheck, Smartphone, X } from 'lucide-react';
import { api } from '../../../services/api';

interface BridgeTarget {
  id: number;
  name: string;
  email: string;
  role: string;
  is_current_user: boolean;
}

interface BridgeOptions {
  resource_type: 'patient';
  resource_label: string;
  targets: BridgeTarget[];
  expires_in: number;
  contains_patient_data: false;
}

interface BridgeResult {
  qr_code: string;
  expires_in: number;
  token_code: string;
  target_user_id: number;
  target_user_name: string;
  target_role: string;
  resource_type: 'patient';
  resource_label: string;
  contains_patient_data: false;
}

export const PatientMobileBridge = ({ patientId, patientName }: { patientId: number; patientName: string }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<BridgeOptions | null>(null);
  const [targetUserId, setTargetUserId] = useState<number | null>(null);
  const [bridge, setBridge] = useState<BridgeResult | null>(null);

  const loadOptions = async () => {
    setLoading(true);
    setError(null);
    setBridge(null);
    try {
      const response = await api.get('/mobile/resource-bridge-options', {
        params: { resource_type: 'patient', resource_id: patientId },
      });
      const data = response.data as BridgeOptions;
      if (data.resource_type !== 'patient' || data.contains_patient_data !== false) {
        throw new Error('Réponse de pont mobile non sûre.');
      }
      setOptions(data);
      setTargetUserId(data.targets.find(target => target.is_current_user)?.id ?? data.targets[0]?.id ?? null);
      if (!data.targets.length) setError("Aucun utilisateur mobile autorisé pour ce dossier.");
    } catch (err: any) {
      setOptions(null);
      setTargetUserId(null);
      setError(err?.response?.data?.detail || err?.message || "Impossible de préparer le pont mobile.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) void loadOptions();
    // Patient change while the modal is closed must never preserve a previous QR.
    if (!open) {
      setBridge(null);
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, patientId]);

  const generate = async () => {
    if (!targetUserId) return;
    setGenerating(true);
    setError(null);
    try {
      const response = await api.post('/mobile/resource-bridge-pairing', {
        resource_type: 'patient',
        resource_id: patientId,
        target_user_id: targetUserId,
      });
      const data = response.data as BridgeResult;
      if (data.resource_type !== 'patient' || data.contains_patient_data !== false) {
        throw new Error('Réponse de pont mobile non sûre.');
      }
      setBridge(data);
    } catch (err: any) {
      setBridge(null);
      setError(err?.response?.data?.detail || err?.message || "Impossible de générer le QR mobile.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <>
      <button
        data-m4a-touch
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Ouvrir ce patient sur mobile"
        className="min-h-11 px-3 inline-flex items-center gap-2 text-[10px] font-black uppercase tracking-widest rounded-xl border border-primary/20 bg-primary/5 hover:bg-primary/10 transition-colors"
        style={{ color: 'var(--primary)' }}
      >
        <Smartphone size={16} />
        <span>Ouvrir sur mobile</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-[700] bg-slate-950/45 backdrop-blur-sm p-3 sm:p-6 flex items-center justify-center" role="dialog" aria-modal="true" aria-label="Pont mobile patient">
          <section data-m4a-bridge className="w-full max-w-xl max-h-[92dvh] overflow-y-auto rounded-[2rem] border border-border-main bg-card-bg shadow-2xl p-5 sm:p-7">
            <div className="flex items-start justify-between gap-4 mb-5">
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-primary mb-1">
                  <QrCode size={18} />
                  <p className="text-[10px] font-black uppercase tracking-[0.18em]">Pont mobile</p>
                </div>
                <h2 className="text-xl font-black text-text-main">Ouvrir ce dossier sur mobile</h2>
                <p className="text-xs font-bold text-text-muted mt-1 truncate">{patientName}</p>
              </div>
              <button data-m4a-touch type="button" onClick={() => setOpen(false)} aria-label="Fermer le pont mobile" className="min-w-11 min-h-11 rounded-xl border border-border-main inline-flex items-center justify-center text-text-muted hover:text-text-main">
                <X size={18} />
              </button>
            </div>

            {loading ? (
              <div className="min-h-40 flex items-center justify-center gap-3 text-text-muted font-bold text-sm">
                <Loader2 className="animate-spin" size={20} /> Préparation sécurisée…
              </div>
            ) : error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
                <p className="text-sm font-bold text-rose-700">{error}</p>
                <button data-m4a-touch type="button" onClick={() => void loadOptions()} className="mt-3 min-h-11 px-4 rounded-xl border border-rose-200 bg-white text-rose-700 font-black text-xs inline-flex items-center gap-2">
                  <RefreshCcw size={15} /> Réessayer
                </button>
              </div>
            ) : (
              <div className="space-y-5">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-border-main bg-background/60 p-4">
                    <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Contexte</p>
                    <p className="mt-1 font-black text-text-main">Dossier patient</p>
                  </div>
                  <label className="rounded-2xl border border-border-main bg-background/60 p-3 block">
                    <span className="text-[10px] font-black uppercase tracking-widest text-text-muted block mb-1">Utilisateur mobile</span>
                    {options && options.targets.length > 1 ? (
                      <select
                        data-m4a-touch
                        aria-label="Utilisateur mobile cible du dossier patient"
                        value={targetUserId ?? ''}
                        onChange={event => { setTargetUserId(Number(event.target.value)); setBridge(null); }}
                        className="w-full min-h-11 rounded-xl border border-border-main bg-card-bg px-3 font-bold text-sm outline-none focus:border-primary"
                      >
                        {options.targets.map(target => <option key={target.id} value={target.id}>{target.name} · {target.role}</option>)}
                      </select>
                    ) : (
                      <p className="min-h-11 flex items-center font-black text-sm text-text-main">{options?.targets[0]?.name || 'Aucune cible'}</p>
                    )}
                  </label>
                </div>

                {!bridge ? (
                  <button
                    data-m4a-touch
                    type="button"
                    onClick={() => void generate()}
                    disabled={!targetUserId || generating}
                    className="w-full min-h-[52px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest inline-flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {generating ? <Loader2 className="animate-spin" size={17} /> : <QrCode size={17} />}
                    Générer le QR
                  </button>
                ) : (
                  <div className="rounded-[1.75rem] border border-primary/15 bg-primary/[0.035] p-5 text-center">
                    <img src={bridge.qr_code} alt="QR de pont mobile patient" className="w-52 h-52 max-w-full mx-auto rounded-2xl bg-white p-2 border border-border-main" />
                    <p className="mt-4 text-xs text-text-muted font-bold">Ou code manuel</p>
                    <p className="mt-1 text-2xl font-black tracking-[0.24em] text-text-main">{bridge.token_code}</p>
                    <p className="mt-3 text-xs font-black text-text-main">Cible : {bridge.target_user_name}</p>
                    <p className="mt-1 text-[11px] font-bold text-text-muted">Expire dans {Math.round(bridge.expires_in / 60)} min · usage unique</p>
                  </div>
                )}

                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 flex gap-3">
                  <ShieldCheck size={19} className="text-emerald-600 shrink-0" />
                  <div>
                    <p className="text-xs font-black text-emerald-800">QR sans donnée patient</p>
                    <p className="mt-1 text-[11px] font-bold leading-relaxed text-emerald-700">Le QR contient uniquement un secret temporaire. Le dossier est résolu et contrôlé côté serveur après l’appairage.</p>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </>
  );
};
