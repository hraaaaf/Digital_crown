import { useEffect, useState } from 'react';
import { ShieldCheck, Wifi, WifiOff, RefreshCw, LogOut, FileText, AlertTriangle, Fingerprint, LockKeyhole, CheckCircle2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { Snapshot, SyncStatus } from '../types';
import {
  activateMobilePasskey,
  disableMobilePasskey,
  getMobilePasskeyStatus,
  type MobilePasskeyStatus,
} from '../../../../services/zka/mobilePasskey';

const premiumGlass = 'relative overflow-hidden bg-glass-bg/90 border border-glass-border/90 backdrop-blur-xl shadow-[0_16px_40px_rgba(15,23,42,0.08),inset_0_1px_0_rgba(255,255,255,0.86)]';

function GlassReflection() {
  return (
    <>
      <div data-m6i-glass-reflection aria-hidden="true" className="pointer-events-none absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-white/95 to-transparent" />
      <div aria-hidden="true" className="pointer-events-none absolute -top-12 right-3 h-24 w-32 rounded-full bg-white/45 blur-2xl" />
    </>
  );
}

export function SecuriteView({
  snapshot,
  syncStatus,
  isOnline,
  handleLogout
}: {
  snapshot: Snapshot | null;
  syncStatus: SyncStatus;
  isOnline: boolean;
  handleLogout: () => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [passkey, setPasskey] = useState<MobilePasskeyStatus | null>(null);
  const [passkeyBusy, setPasskeyBusy] = useState(false);
  const [passkeyError, setPasskeyError] = useState('');
  const [confirmingPasskeyDisable, setConfirmingPasskeyDisable] = useState(false);

  const refreshPasskey = async () => {
    try {
      const status = await getMobilePasskeyStatus();
      setPasskey(status);
      setPasskeyError('');
    } catch (error) {
      setPasskeyError(error instanceof Error ? error.message : 'État biométrique indisponible.');
    }
  };

  useEffect(() => { void refreshPasskey(); }, []);

  const activatePasskey = async () => {
    setPasskeyBusy(true);
    setPasskeyError('');
    try {
      const status = await activateMobilePasskey();
      setPasskey(status);
    } catch (error) {
      setPasskeyError(error instanceof Error ? error.message : 'Activation biométrique impossible.');
    } finally {
      setPasskeyBusy(false);
    }
  };

  const disablePasskey = async () => {
    setPasskeyBusy(true);
    setPasskeyError('');
    try {
      await disableMobilePasskey();
      setPasskey(await getMobilePasskeyStatus());
      setConfirmingPasskeyDisable(false);
    } catch (error) {
      setPasskeyError(error instanceof Error ? error.message : 'Désactivation biométrique impossible.');
    } finally {
      setPasskeyBusy(false);
    }
  };

  const passkeyEnabled = passkey?.state === 'enabled';
  const passkeyPending = passkey?.state === 'pending';
  const passkeyOriginReady = passkey?.origin_ready !== false;

  return (
    <div className="space-y-5">
      <div className="relative overflow-hidden rounded-[32px] p-8 flex flex-col items-center text-center gap-5 shadow-[0_20px_44px_rgba(30,64,175,0.18),inset_0_1px_0_rgba(255,255,255,0.38)]" style={{ backgroundImage: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
        <div data-m6i-glass-reflection aria-hidden="true" className="absolute inset-x-7 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent" />
        <div aria-hidden="true" className="absolute -top-16 right-3 w-52 h-36 bg-white/20 rounded-full blur-3xl" />
        <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full -mr-24 -mt-24 blur-3xl" />
        <div className="w-20 h-20 bg-white/20 backdrop-blur-xl border border-white/35 rounded-[24px] flex items-center justify-center text-white shadow-[0_12px_26px_rgba(15,23,42,0.18),inset_0_1px_0_rgba(255,255,255,0.5)] z-10">
          <ShieldCheck size={40} />
        </div>
        <div className="z-10">
          <p className="font-black text-white text-xl font-outfit">Terminal Appairé</p>
          <p className="text-[11px] text-white/70 mt-2 leading-relaxed max-w-xs">
            Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/12 backdrop-blur-xl border border-white/25 rounded-[16px] shadow-[inset_0_1px_0_rgba(255,255,255,0.34)] z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          <span className="text-[10px] font-black text-white uppercase tracking-widest">Zero-Knowledge · AES-256</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className={cn(premiumGlass, 'rounded-[20px] p-4')}>
          <GlassReflection />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              {isOnline ? <Wifi size={14} className="text-emerald-500" /> : <WifiOff size={14} className="text-rose-500" />}
              <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Réseau</span>
            </div>
            <p className={cn('text-xs font-black', isOnline ? 'text-emerald-600' : 'text-rose-500')}>{isOnline ? 'En ligne' : 'Hors ligne'}</p>
            <p className="text-[9px] text-text-muted mt-0.5 font-bold">{isOnline ? 'Temps réel' : 'Cache local'}</p>
          </div>
        </div>
        <div className={cn(premiumGlass, 'rounded-[20px] p-4')}>
          <GlassReflection />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <RefreshCw size={14} className="text-primary" />
              <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Sync</span>
            </div>
            <p className="text-xs font-black text-text-main">{syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}</p>
            <p className="text-[9px] text-text-muted mt-0.5 font-bold">{snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}</p>
          </div>
        </div>
      </div>

      <div className={cn(premiumGlass, 'rounded-[20px] p-4 flex items-center gap-3')}>
        <GlassReflection />
        <div className="relative z-10 w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <div className="relative z-10">
          <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Status Système</p>
          <p className="text-sm font-black text-text-main">Serveur local opérationnel</p>
        </div>
        <FileText size={16} className="relative z-10 ml-auto text-text-muted" />
      </div>

      <section data-m6i-biometric className={cn(premiumGlass, 'rounded-[24px] p-5')} aria-label="Verrouillage biométrique">
        <GlassReflection />
        <div className="relative z-10">
          <div className="flex items-start gap-4">
            <div className={cn('w-12 h-12 rounded-[16px] flex items-center justify-center shrink-0 border border-white/60 shadow-[0_8px_20px_rgba(15,23,42,0.08),inset_0_1px_0_rgba(255,255,255,0.92)]', passkeyEnabled ? 'bg-emerald-500/10 text-emerald-600' : 'bg-primary/10 text-primary')}>
              {passkeyEnabled ? <CheckCircle2 size={24} /> : <Fingerprint size={25} />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-black text-text-main">Verrouillage biométrique</p>
                {passkeyEnabled && <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-700 text-[8px] font-black uppercase tracking-widest">Activé</span>}
                {passkeyPending && <span className="px-2 py-1 rounded-full bg-amber-500/10 text-amber-700 text-[8px] font-black uppercase tracking-widest">À terminer</span>}
              </div>
              <p className="mt-1 text-[10px] leading-relaxed text-text-muted font-semibold">
                {passkeyEnabled
                  ? 'Face ID, empreinte ou verrou sécurisé requis. La session UV reste courte et liée à ce téléphone.'
                  : passkeyPending
                    ? 'La passkey est créée mais le coffre local doit encore être scellé avant activation.'
                    : 'Ajoute un second verrou local sans remplacer le QR d’appairage ni la révocation du cabinet.'}
              </p>
            </div>
            <LockKeyhole size={16} className="text-text-muted shrink-0 mt-1" />
          </div>

          {!passkeyOriginReady && passkey && (
            <div className="mt-4 rounded-[16px] bg-amber-500/8 border border-amber-200/90 backdrop-blur-md px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
              <p className="text-[10px] font-black text-amber-700">Adresse sécurisée requise</p>
              <p className="text-[9px] text-amber-700/80 mt-1 font-semibold break-all">{passkey.expected_origin}</p>
            </div>
          )}

          {!passkeyEnabled && passkeyOriginReady && (
            <button data-m6i-activate type="button" onClick={activatePasskey} disabled={passkeyBusy || !passkey} className="relative overflow-hidden mt-4 min-h-[52px] w-full rounded-[18px] bg-primary text-white text-xs font-black flex items-center justify-center gap-2 shadow-[0_12px_28px_rgba(30,64,175,0.22),inset_0_1px_0_rgba(255,255,255,0.34)] active:scale-[0.98] transition-transform disabled:opacity-50">
              <span aria-hidden="true" className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent" />
              <Fingerprint size={18} /> {passkeyBusy ? 'Vérification…' : passkeyPending ? 'Terminer l’activation' : 'Activer Face ID / biométrie'}
            </button>
          )}

          {passkeyEnabled && !confirmingPasskeyDisable && (
            <button type="button" onClick={() => setConfirmingPasskeyDisable(true)} className="mt-4 min-h-[48px] w-full rounded-[18px] border border-white/70 bg-white/70 backdrop-blur-xl text-text-muted text-[10px] font-black uppercase tracking-widest shadow-[0_8px_20px_rgba(15,23,42,0.06),inset_0_1px_0_rgba(255,255,255,0.95)]">
              Désactiver le verrou biométrique
            </button>
          )}

          {passkeyEnabled && confirmingPasskeyDisable && (
            <div className="mt-4 rounded-[18px] border border-rose-200 bg-rose-50/80 backdrop-blur-xl p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]">
              <p className="text-[10px] font-black text-rose-700 leading-relaxed">Après vérification biométrique, le coffre local sera restauré puis la passkey sera déliée de cet appareil.</p>
              <div className="grid grid-cols-2 gap-2 mt-3">
                <button type="button" onClick={() => setConfirmingPasskeyDisable(false)} className="min-h-[48px] rounded-[14px] bg-white border border-slate-200 text-[10px] font-black text-text-muted">Annuler</button>
                <button type="button" disabled={passkeyBusy} onClick={disablePasskey} className="min-h-[48px] rounded-[14px] bg-rose-500 text-white text-[10px] font-black disabled:opacity-50">Confirmer</button>
              </div>
            </div>
          )}

          {passkeyError && <p role="alert" className="mt-3 text-[10px] font-bold text-rose-600">{passkeyError}</p>}
          <p className="mt-3 text-[9px] text-text-muted leading-relaxed font-semibold">Origine passkey stable : <span className="font-black">digitalcrown.local</span>. Aucune empreinte ni donnée Face ID n’est reçue par Digital Crown.</p>
        </div>
      </section>

      {!confirming ? (
        <button onClick={() => setConfirming(true)} className="relative overflow-hidden w-full py-5 bg-rose-500/5 backdrop-blur-xl border border-rose-200 text-rose-500 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 shadow-[0_10px_26px_rgba(244,63,94,0.07),inset_0_1px_0_rgba(255,255,255,0.88)] active:scale-95 transition-all hover:bg-rose-50">
          <span aria-hidden="true" className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-white/90 to-transparent" />
          <LogOut size={16} /> Délier ce téléphone
        </button>
      ) : (
        <div className="bg-rose-50/85 backdrop-blur-xl border border-rose-200 rounded-[24px] p-5 space-y-4 shadow-[0_12px_30px_rgba(244,63,94,0.08),inset_0_1px_0_rgba(255,255,255,0.9)]">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-rose-500 shrink-0" />
            <p className="text-xs font-black text-rose-700 leading-relaxed">Cela supprimera les clés de ce téléphone. Il faudra re-scanner le QR Code pour se reconnecter.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => setConfirming(false)} className="py-4 rounded-[16px] text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 bg-white active:scale-95 transition-all">Annuler</button>
            <button onClick={handleLogout} className="py-4 rounded-[16px] text-xs font-black uppercase tracking-widest bg-rose-500 text-white active:scale-95 transition-all">Confirmer</button>
          </div>
        </div>
      )}
    </div>
  );
}