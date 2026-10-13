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

const premiumGlass = 'relative overflow-hidden bg-glass-bg/90 border border-glass-border/90 backdrop-blur-xl shadow-sm';

function GlassReflection() {
  return (
    <>
      <div data-m6i-glass-reflection aria-hidden="true" className="pointer-events-none absolute inset-x-5 top-0 h-px bg-gradient-to-r from-transparent via-border-main to-transparent" />
      <div aria-hidden="true" className="pointer-events-none absolute -top-12 right-3 h-24 w-32 rounded-full bg-card/25 blur-2xl" />
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
  const cabinetConnected = isOnline && syncStatus === 'success';

  return (
    <div className="space-y-5">
      <div className="relative overflow-hidden rounded-[24px] bg-primary p-5 flex flex-col items-center text-center gap-3 shadow-sm" >
        <div data-m6i-glass-reflection aria-hidden="true" className="absolute inset-x-7 top-0 h-px bg-gradient-to-r from-transparent via-on-primary/25 to-transparent" />
        <div aria-hidden="true" className="absolute -top-16 right-3 w-52 h-36 bg-on-primary/15 rounded-full blur-3xl" />
        <div className="absolute top-0 right-0 w-48 h-48 bg-on-primary/10 rounded-full -mr-24 -mt-24 blur-3xl" />
        <div className="w-20 h-20 bg-on-primary/15 backdrop-blur-xl border border-on-primary/20 rounded-[24px] flex items-center justify-center text-on-primary shadow-sm z-10">
          <ShieldCheck size={40} />
        </div>
        <div className="z-10">
          <p className="font-bold text-on-primary text-xl ">Téléphone connecté</p>
          <p className="text-[11px] text-on-primary/80 mt-2 leading-relaxed max-w-xs">
            Connexion directe et sécurisée au cabinet.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-on-primary/10 backdrop-blur-xl border border-on-primary/20 rounded-[16px] shadow-sm z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-card animate-pulse" />
          <span className="text-[10px] font-bold text-on-primary uppercase tracking-widest">Connexion chiffrée</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className={cn(premiumGlass, 'rounded-[20px] p-4')}>
          <GlassReflection />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              {isOnline ? <Wifi size={14} className="text-success" /> : <WifiOff size={14} className="text-danger" />}
              <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest">Réseau</span>
            </div>
            <p className={cn('text-xs font-bold', isOnline ? 'text-success' : 'text-danger')}>{isOnline ? 'En ligne' : 'Hors ligne'}</p>
            <p className="text-[11px] text-text-muted mt-0.5 font-bold">{isOnline ? 'Temps réel' : 'Accès hors connexion'}</p>
          </div>
        </div>
        <div className={cn(premiumGlass, 'rounded-[20px] p-4')}>
          <GlassReflection />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <RefreshCw size={14} className="text-primary" />
              <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest">Mise à jour</span>
            </div>
            <p className="text-xs font-bold text-text-main">{syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}</p>
            <p className="text-[11px] text-text-muted mt-0.5 font-bold">{snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}</p>
          </div>
        </div>
      </div>

      <div className={cn(premiumGlass, 'rounded-[20px] p-4 flex items-center gap-3')}>
        <GlassReflection />
        <div className={cn("relative z-10 h-2 w-2 rounded-full", cabinetConnected ? "bg-success animate-pulse" : "bg-warning")} />
        <div className="relative z-10">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">État de la connexion</p>
          <p className="text-sm font-bold text-text-main">{cabinetConnected ? "Cabinet accessible" : "Connexion cabinet à vérifier"}</p>
        </div>
        <FileText size={16} className="relative z-10 ml-auto text-text-muted" />
      </div>

      <section data-m6i-biometric className={cn(premiumGlass, 'rounded-[24px] p-5')} aria-label="Verrouillage biométrique">
        <GlassReflection />
        <div className="relative z-10">
          <div className="flex items-start gap-4">
            <div className={cn('w-12 h-12 rounded-[16px] flex items-center justify-center shrink-0 border border-glass-border shadow-sm', passkeyEnabled ? 'bg-success-surface text-success' : 'bg-primary/10 text-primary')}>
              {passkeyEnabled ? <CheckCircle2 size={24} /> : <Fingerprint size={25} />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-bold text-text-main">Verrouillage biométrique</p>
                {passkeyEnabled && <span className="px-2 py-1 rounded-full bg-success-surface text-success text-[10px] font-bold uppercase tracking-widest">Activé</span>}
                {passkeyPending && <span className="px-2 py-1 rounded-full bg-warning-surface text-warning text-[10px] font-bold uppercase tracking-widest">À terminer</span>}
              </div>
              <p className="mt-1 text-[10px] leading-relaxed text-text-muted font-semibold">
                {passkeyEnabled
                  ? 'Face ID, empreinte ou verrou sécurisé requis. L’accès reste temporaire et lié à ce téléphone.'
                  : passkeyPending
                    ? 'La biométrie est enregistrée mais son activation doit encore être terminée.'
                    : 'Ajoute une protection biométrique supplémentaire sans modifier votre accès actuel.'}
              </p>
            </div>
            <LockKeyhole size={16} className="text-text-muted shrink-0 mt-1" />
          </div>

          {!passkeyOriginReady && passkey && (
            <div className="mt-4 rounded-[16px] bg-warning-surface border border-warning-border backdrop-blur-md px-4 py-3 shadow-sm">
              <p className="text-[10px] font-bold text-warning">Adresse sécurisée requise</p>
              <p className="text-[11px] text-warning mt-1 font-semibold break-all">{passkey.expected_origin}</p>
            </div>
          )}

          {!passkeyEnabled && passkeyOriginReady && (
            <button data-m6i-activate type="button" onClick={activatePasskey} disabled={passkeyBusy || !passkey} className="relative overflow-hidden mt-4 min-h-[52px] w-full rounded-[18px] bg-primary text-on-primary text-xs font-bold flex items-center justify-center gap-2 shadow-sm active:scale-[0.98] transition-transform disabled:opacity-50">
              <span aria-hidden="true" className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-on-primary/25 to-transparent" />
              <Fingerprint size={18} /> {passkeyBusy ? 'Vérification…' : passkeyPending ? 'Terminer l’activation' : 'Activer Face ID / biométrie'}
            </button>
          )}

          {passkeyEnabled && !confirmingPasskeyDisable && (
            <button type="button" onClick={() => setConfirmingPasskeyDisable(true)} className="mt-4 min-h-[48px] w-full rounded-[18px] border border-border-main bg-card backdrop-blur-xl text-text-muted text-[10px] font-bold uppercase tracking-widest shadow-sm">
              Désactiver le verrou biométrique
            </button>
          )}

          {passkeyEnabled && confirmingPasskeyDisable && (
            <div className="mt-4 rounded-[18px] border border-danger-border bg-danger-surface backdrop-blur-xl p-4 shadow-sm">
              <p className="text-[10px] font-bold text-danger leading-relaxed">Après vérification biométrique, l’accès biométrique sera retiré de cet appareil.</p>
              <div className="grid grid-cols-2 gap-2 mt-3">
                <button type="button" onClick={() => setConfirmingPasskeyDisable(false)} className="min-h-[48px] rounded-[14px] bg-card border border-border-main text-[10px] font-bold text-text-muted">Annuler</button>
                <button type="button" disabled={passkeyBusy} onClick={disablePasskey} className="min-h-[48px] rounded-[14px] bg-danger-surface text-danger text-[10px] font-bold disabled:opacity-50">Confirmer</button>
              </div>
            </div>
          )}

          {passkeyError && <p role="alert" className="mt-3 text-[10px] font-bold text-danger">{passkeyError}</p>}
          <p className="mt-3 text-[11px] text-text-muted leading-relaxed font-semibold">La biométrie reste gérée par votre téléphone. Digital Crown ne reçoit ni empreinte ni donnée Face ID.</p>
        </div>
      </section>

      {!confirming ? (
        <button onClick={() => setConfirming(true)} className="relative overflow-hidden w-full py-5 bg-danger-surface backdrop-blur-xl border border-danger-border text-danger rounded-[24px] font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-3 shadow-sm active:scale-95 transition-all hover:bg-danger-surface">
          <span aria-hidden="true" className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-border-main to-transparent" />
          <LogOut size={16} /> Délier ce téléphone
        </button>
      ) : (
        <div className="bg-danger-surface backdrop-blur-xl border border-danger-border rounded-[24px] p-5 space-y-4 shadow-sm">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-danger shrink-0" />
            <p className="text-xs font-bold text-danger leading-relaxed">Cela supprimera l’accès enregistré sur ce téléphone. Il faudra scanner à nouveau le QR de connexion.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => setConfirming(false)} className="py-4 rounded-[16px] text-xs font-bold uppercase tracking-widest border border-border-main text-text-muted bg-card active:scale-95 transition-all">Annuler</button>
            <button onClick={handleLogout} className="py-4 rounded-[16px] text-xs font-bold uppercase tracking-widest bg-danger-surface text-danger active:scale-95 transition-all">Confirmer</button>
          </div>
        </div>
      )}
    </div>
  );
}