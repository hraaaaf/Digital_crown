import { useState } from 'react';
import { ShieldCheck, Wifi, WifiOff, RefreshCw, LogOut, FileText, AlertTriangle } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { Snapshot, SyncStatus } from '../types';

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

  return (
    <div className="space-y-5">
      {/* Shield card */}
      <div className="relative overflow-hidden rounded-[32px] p-8 flex flex-col items-center text-center gap-5 shadow-elite-hover" style={{ backgroundImage: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
        <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full -mr-24 -mt-24 blur-3xl" />
        <div className="w-20 h-20 bg-white/20 backdrop-blur-md border border-white/30 rounded-[24px] flex items-center justify-center text-white shadow-xl z-10">
          <ShieldCheck size={40} />
        </div>
        <div className="z-10">
          <p className="font-black text-white text-xl font-outfit">Terminal Appairé</p>
          <p className="text-[11px] text-white/70 mt-2 leading-relaxed max-w-xs">
            Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/10 border border-white/20 rounded-[16px] z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          <span className="text-[10px] font-black text-white uppercase tracking-widest">Zero-Knowledge · AES-256</span>
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            {isOnline
              ? <Wifi size={14} className="text-emerald-500" />
              : <WifiOff size={14} className="text-rose-500" />
            }
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Réseau</span>
          </div>
          <p className={cn('text-xs font-black', isOnline ? 'text-emerald-600' : 'text-rose-500')}>
            {isOnline ? 'En ligne' : 'Hors ligne'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {isOnline ? 'Temps réel' : 'Cache local'}
          </p>
        </div>
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            <RefreshCw size={14} className="text-primary" />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Sync</span>
          </div>
          <p className="text-xs font-black text-text-main">
            {syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}
          </p>
        </div>
      </div>

      {/* Status system pill */}
      <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <div>
          <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Status Système</p>
          <p className="text-sm font-black text-text-main">Elite Cloud Connecté</p>
        </div>
        <FileText size={16} className="ml-auto text-text-muted" />
      </div>

      {/* Logout — confirmation inline (window.confirm bloqué sur iOS PWA) */}
      {!confirming ? (
        <button
          onClick={() => setConfirming(true)}
          className="w-full py-5 bg-rose-500/5 border border-rose-200 text-rose-500 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all hover:bg-rose-50"
        >
          <LogOut size={16} /> Délier ce téléphone
        </button>
      ) : (
        <div className="bg-rose-50 border border-rose-200 rounded-[24px] p-5 space-y-4">
          <div className="flex items-center gap-3">
            <AlertTriangle size={20} className="text-rose-500 shrink-0" />
            <p className="text-xs font-black text-rose-700 leading-relaxed">
              Cela supprimera les clés de ce téléphone. Il faudra re-scanner le QR Code pour se reconnecter.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setConfirming(false)}
              className="py-4 rounded-[16px] text-xs font-black uppercase tracking-widest border border-slate-200 text-slate-500 bg-white active:scale-95 transition-all"
            >
              Annuler
            </button>
            <button
              onClick={handleLogout}
              className="py-4 rounded-[16px] text-xs font-black uppercase tracking-widest bg-rose-500 text-white active:scale-95 transition-all"
            >
              Confirmer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
