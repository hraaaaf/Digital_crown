import { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Navigation,
  QrCode,
  RefreshCw,
  Shield,
  Smartphone,
  UserRound,
} from 'lucide-react';
import { api } from '../../../services/api';

type BridgeDestination = {
  id: string;
  label: string;
};

type BridgeTarget = {
  id: number;
  name: string;
  email: string;
  role: string;
  is_current_user: boolean;
  destinations: BridgeDestination[];
};

type BridgeOptions = {
  targets: BridgeTarget[];
  expires_in: number;
};

type BridgePairing = {
  qr_code: string;
  token_code: string;
  expires_in: number;
  target_user_id: number;
  target_user_name: string;
  target_role: string;
  destination: string;
  destination_label: string;
  contains_patient_data: boolean;
};

function formatCountdown(seconds: number): string {
  const safe = Math.max(0, seconds);
  const minutes = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${minutes}:${String(remainder).padStart(2, '0')}`;
}

export const MobileSecurity = () => {
  const [targets, setTargets] = useState<BridgeTarget[]>([]);
  const [selectedTargetId, setSelectedTargetId] = useState<number | null>(null);
  const [selectedDestination, setSelectedDestination] = useState('');
  const [pairing, setPairing] = useState<BridgePairing | null>(null);
  const [countdown, setCountdown] = useState(0);
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [isRevoking, setIsRevoking] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const selectedTarget = useMemo(
    () => targets.find(target => target.id === selectedTargetId) ?? null,
    [targets, selectedTargetId],
  );

  const loadBridgeOptions = async () => {
    setIsLoadingOptions(true);
    setOptionsError(null);
    try {
      const response = await api.get<BridgeOptions>('/mobile/bridge-options');
      const nextTargets = response.data.targets ?? [];
      setTargets(nextTargets);
      const preferred = nextTargets.find(target => target.is_current_user) ?? nextTargets[0] ?? null;
      setSelectedTargetId(preferred?.id ?? null);
      setSelectedDestination(preferred?.destinations[0]?.id ?? '');
      if (!preferred) {
        setOptionsError("Aucun utilisateur actif n'est autorisé pour l'expérience mobile.");
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setTargets([]);
      setSelectedTargetId(null);
      setSelectedDestination('');
      setOptionsError(typeof detail === 'string' ? detail : 'Impossible de charger les utilisateurs mobiles autorisés.');
    } finally {
      setIsLoadingOptions(false);
    }
  };

  useEffect(() => {
    void loadBridgeOptions();
  }, []);

  useEffect(() => {
    if (!pairing || countdown <= 0) return;
    const timer = window.setInterval(() => {
      setCountdown(previous => {
        if (previous <= 1) {
          setPairing(null);
          return 0;
        }
        return previous - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [pairing, countdown]);

  const handleTargetChange = (value: string) => {
    const targetId = Number(value);
    const target = targets.find(candidate => candidate.id === targetId) ?? null;
    setSelectedTargetId(target?.id ?? null);
    setSelectedDestination(target?.destinations[0]?.id ?? '');
    setPairing(null);
    setCountdown(0);
  };

  const generateBridge = async () => {
    if (!selectedTarget || !selectedDestination) return;
    setIsGenerating(true);
    setStatus(null);
    try {
      const response = await api.post<BridgePairing>('/mobile/bridge-pairing', {
        target_user_id: selectedTarget.id,
        destination: selectedDestination,
      });
      setPairing(response.data);
      setCountdown(response.data.expires_in || 300);
      if (response.data.contains_patient_data !== false) {
        setPairing(null);
        setCountdown(0);
        throw new Error('Réponse de pont mobile non conforme.');
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Impossible de générer le pont mobile.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevoke = async () => {
    if (!window.confirm("Révoquer immédiatement toutes les sessions mobiles existantes de ce cabinet ? Les téléphones devront être appairés à nouveau.")) return;

    setIsRevoking(true);
    try {
      await api.post('/admin/revoke-mobile');
      setStatus({ type: 'success', msg: "Sessions mobiles révoquées. Un nouvel appairage est nécessaire." });
      setPairing(null);
      setCountdown(0);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      setStatus({ type: 'error', msg: typeof detail === 'string' ? detail : "Impossible de confirmer la révocation mobile." });
    } finally {
      setIsRevoking(false);
      setTimeout(() => setStatus(null), 5000);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-500">
          <Smartphone size={24} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white font-outfit">Compagnon Mobile</h2>
          <p className="text-sm text-slate-500">Créez un pont sécurisé vers une surface mobile précise.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white dark:bg-slate-900/50 rounded-3xl border border-slate-200/60 dark:border-white/5 p-5 sm:p-8 relative overflow-hidden">
          <div className="relative z-10 space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                <Shield size={18} className="text-emerald-500" />
                Pont mobile sécurisé
              </h3>
              <p className="text-sm text-slate-500">
                Choisissez l'utilisateur et la destination. Le QR contient uniquement un secret éphémère ; aucune donnée patient n'y est encodée.
              </p>
            </div>

            {optionsError ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                <p className="font-bold">{optionsError}</p>
                <button
                  type="button"
                  onClick={() => void loadBridgeOptions()}
                  className="mt-3 min-h-11 px-4 rounded-xl border border-rose-200 bg-white font-bold text-xs"
                >
                  Réessayer
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                <label className="space-y-2">
                  <span className="text-[11px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <UserRound size={14} /> Utilisateur
                  </span>
                  <select
                    aria-label="Utilisateur mobile cible"
                    value={selectedTargetId ?? ''}
                    onChange={event => handleTargetChange(event.target.value)}
                    disabled={isLoadingOptions || targets.length === 0}
                    className="w-full min-h-[52px] rounded-2xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-slate-800 px-4 text-sm font-bold text-slate-800 dark:text-white outline-none focus:border-indigo-400 disabled:opacity-60"
                  >
                    {targets.map(target => (
                      <option key={target.id} value={target.id}>
                        {target.name} · {target.role}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="space-y-2">
                  <span className="text-[11px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <Navigation size={14} /> Ouvrir sur
                  </span>
                  <select
                    aria-label="Destination mobile"
                    value={selectedDestination}
                    onChange={event => {
                      setSelectedDestination(event.target.value);
                      setPairing(null);
                      setCountdown(0);
                    }}
                    disabled={!selectedTarget || selectedTarget.destinations.length === 0}
                    className="w-full min-h-[52px] rounded-2xl border border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-slate-800 px-4 text-sm font-bold text-slate-800 dark:text-white outline-none focus:border-indigo-400 disabled:opacity-60"
                  >
                    {(selectedTarget?.destinations ?? []).map(destination => (
                      <option key={destination.id} value={destination.id}>{destination.label}</option>
                    ))}
                  </select>
                </label>

                <button
                  type="button"
                  onClick={() => void generateBridge()}
                  disabled={isGenerating || isLoadingOptions || !selectedTarget || !selectedDestination}
                  className="w-full min-h-[52px] rounded-2xl bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-black text-sm flex items-center justify-center gap-3 shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                >
                  {isGenerating ? <RefreshCw size={18} className="animate-spin" /> : <QrCode size={18} />}
                  Générer le pont mobile
                </button>
              </div>
            )}

            <AnimatePresence mode="wait">
              {pairing && (
                <motion.div
                  key={`${pairing.target_user_id}-${pairing.destination}-${pairing.token_code}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="rounded-3xl border border-indigo-200 bg-indigo-50/70 dark:bg-indigo-500/10 dark:border-indigo-500/20 p-5"
                >
                  <div className="flex flex-col sm:flex-row gap-5 items-center sm:items-start">
                    <img
                      src={pairing.qr_code}
                      alt="Pont QR Digital Crown Mobile"
                      className="w-40 h-40 bg-white rounded-2xl p-2 object-contain border border-indigo-100"
                    />
                    <div className="min-w-0 flex-1 text-center sm:text-left">
                      <p className="text-sm font-black text-indigo-950 dark:text-indigo-100 break-words">
                        {pairing.target_user_name} → {pairing.destination_label}
                      </p>
                      <div className="mt-3 font-black text-2xl tracking-[0.22em] text-indigo-600">
                        {pairing.token_code}
                      </div>
                      <p className="mt-3 text-xs font-bold text-indigo-700 dark:text-indigo-300 flex items-center justify-center sm:justify-start gap-2">
                        <Clock3 size={14} /> Valable {formatCountdown(countdown)}
                      </p>
                      <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
                        Aucune donnée patient dans le QR. La destination est validée côté serveur après l'appairage.
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="absolute -top-10 -right-10 w-40 h-40 bg-indigo-500/5 rounded-full blur-3xl" />
        </div>

        <div className="flex flex-col gap-6">
          <div className="bg-rose-500/5 dark:bg-rose-500/10 rounded-3xl border border-rose-500/20 p-5 sm:p-8">
            <h3 className="text-lg font-semibold text-rose-600 dark:text-rose-400 mb-2 flex items-center gap-2">
              <AlertTriangle size={18} />
              Zone de Danger
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
              En cas de perte ou de vol, révoquez les sessions mobiles existantes. Les anciens jetons seront refusés immédiatement et les codes d'appairage en attente seront invalidés pour ce cabinet.
            </p>

            <button
              onClick={handleRevoke}
              disabled={isRevoking}
              className="w-full min-h-[52px] px-4 bg-rose-500 hover:bg-rose-600 disabled:bg-slate-400 text-white rounded-2xl font-bold flex items-center justify-center gap-3 shadow-lg shadow-rose-500/20 transition-all active:scale-[0.98]"
            >
              {isRevoking ? (
                <RefreshCw size={20} className="animate-spin" />
              ) : (
                <>
                  <RefreshCw size={20} />
                  Révoquer tous les accès mobiles
                </>
              )}
            </button>
          </div>

          <AnimatePresence>
            {status && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className={`p-6 rounded-2xl flex items-center gap-4 ${status.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-600' : 'bg-rose-500/10 border border-rose-500/20 text-rose-600'}`}
              >
                {status.type === 'success' ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
                <p className="text-sm font-medium">{status.msg}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="bg-slate-50 dark:bg-white/5 rounded-2xl p-6 border border-slate-200/60 dark:border-white/5">
        <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-2">Sécurité mobile locale</h4>
        <p className="text-xs text-slate-500 leading-relaxed">
          Les données cliniques restent sur le réseau local du cabinet. Le pont QR transporte uniquement une adresse LAN et un secret temporaire. La clé locale est transmise chiffrée après l'échange ECDH et la destination est revalidée par le backend selon les permissions réelles de l'utilisateur appairé.
        </p>
      </div>
    </div>
  );
};
