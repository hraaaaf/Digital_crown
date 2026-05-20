import { useState, useEffect } from 'react';
import {
  Smartphone, LogOut, Calendar, TrendingUp,
  AlertTriangle, Phone, MessageSquare, ChevronRight,
  Clock, Wallet, ShieldCheck, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { supabase } from '../../../services/zka/supabaseClient';
import { ZKAEngine } from '../../../services/zka/zka-engine';

type Tab = 'agenda' | 'finance' | 'securite';

export const MobileDashboard = () => {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [syncStatus, setSyncStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [decryptedData, setDecryptedData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // 1. CHARGEMENT SWR (Stale-While-Revalidate)
  useEffect(() => {
    const init = async () => {
      // Charger le cache immédiatement
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) {
        setDecryptedData(cached);
        setSyncStatus('success');
      }
      // Lancer le rafraîchissement en arrière-plan
      fetchAndDecrypt();
    };
    init();
  }, []);

  const fetchAndDecrypt = async () => {
    try {
      setSyncStatus('loading');
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error("Non appairé");

      const { data, error: sbError } = await supabase
        .from('cabinet_snapshots')
        .select('encrypted_data')
        .eq('public_id', creds.publicId)
        .single();

      if (sbError || !data) throw new Error("Snapshot introuvable");

      const rawData = await ZKAEngine.decryptPayload(data.encrypted_data, creds.masterKey);

      // Mise à jour de l'état et du cache
      setDecryptedData(rawData);
      await MobileStorage.saveLastSnapshot(rawData);

      setSyncStatus('success');
      setError(null);
    } catch (err: any) {
      console.error("Sync Error:", err);
      setError(err.message || "Erreur de synchro");
      setSyncStatus('error');
    }
  };

  const handleLogout = async () => {
    if (window.confirm("Déconnexion sécurisée ? La clé sera supprimée de ce téléphone.")) {
      await MobileStorage.clearAll();
      window.location.reload();
    }
  };

  // Helpers pour WhatsApp
  const openWhatsApp = (phone: string, message: string) => {
    const cleanPhone = phone.replace(/\D/g, '');
    window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`, '_blank');
  };

  // --- SKELETON ---
  const SkeletonCard = () => (
    <div className="bg-white/5 border border-white/5 rounded-[2rem] p-5 space-y-3 animate-pulse">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-white/10 rounded-2xl" />
        <div className="space-y-2 flex-1">
          <div className="h-3 bg-white/10 rounded-full w-2/3" />
          <div className="h-2 bg-white/5 rounded-full w-1/3" />
        </div>
      </div>
      <div className="h-10 bg-white/5 rounded-2xl" />
    </div>
  );

  // --- RENDU : AGENDA ---
  const AgendaView = () => (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between px-1 mb-6">
        <h2 className="text-2xl font-black">Agenda du Jour</h2>
        <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-[10px] font-black uppercase tracking-widest">
          {decryptedData?.appointments?.length || 0} RDV
        </span>
      </div>

      {syncStatus === 'loading' && !decryptedData ? (
        <div className="space-y-4">
          <SkeletonCard /><SkeletonCard /><SkeletonCard />
        </div>
      ) : !decryptedData?.appointments?.length ? (
        <div className="py-20 text-center opacity-30 flex flex-col items-center gap-4">
          <Calendar size={48} />
          <p className="text-sm font-bold">Aucun rendez-vous aujourd'hui</p>
        </div>
      ) : (
        decryptedData.appointments.map((apt: any, idx: number) => (
          <div key={idx} className="bg-white/5 border border-white/5 rounded-[2rem] p-5 flex flex-col gap-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-indigo-500/10 rounded-2xl flex flex-col items-center justify-center text-indigo-400 border border-indigo-500/20">
                  <Clock size={16} />
                  <span className="text-[10px] font-black mt-1">{apt.time}</span>
                </div>
                <div>
                  <h3 className="font-bold text-slate-100">{apt.patient_name}</h3>
                  <p className="text-[10px] text-slate-500 font-black uppercase tracking-wider mt-0.5">{apt.motif || 'Consultation'}</p>
                </div>
              </div>
              <ChevronRight size={18} className="text-slate-700 mt-2" />
            </div>

            <div className="flex gap-3 mt-2">
              <a
                href={`tel:${apt.phone}`}
                className="flex-1 py-3 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center gap-3 transition-all border border-white/5"
              >
                <Phone size={16} className="text-emerald-400" />
                <span className="text-[10px] font-black uppercase tracking-widest">Appeler</span>
              </a>
              <button
                onClick={() => openWhatsApp(apt.phone, `Bonjour ${apt.patient_name}, nous vous confirmons votre RDV de ${apt.time}.`)}
                className="flex-1 py-3 bg-white/5 hover:bg-white/10 rounded-2xl flex items-center justify-center gap-3 transition-all border border-white/5"
              >
                <MessageSquare size={16} className="text-indigo-400" />
                <span className="text-[10px] font-black uppercase tracking-widest">WhatsApp</span>
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );

  // --- RENDU : FINANCE ---
  const FinanceView = () => {
    const finance = decryptedData?.finance || {};
    const debtors = decryptedData?.debtors || [];

    return (
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="px-1">
          <h2 className="text-2xl font-black">Performance</h2>
          <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-1">Cabinet Analytics</p>
        </div>

        {/* KPIs Financement */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 p-6 rounded-[2rem] border border-white/5 flex flex-col">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-xl flex items-center justify-center text-emerald-400 mb-4">
              <Wallet size={20} />
            </div>
            <p className="text-2xl font-black tracking-tight">{new Intl.NumberFormat('fr-FR').format(finance.today_revenue || 0)}</p>
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Jour (MAD)</p>
          </div>
          <div className="bg-white/5 p-6 rounded-[2rem] border border-white/5 flex flex-col">
            <div className="w-10 h-10 bg-amber-500/10 rounded-xl flex items-center justify-center text-amber-400 mb-4">
              <TrendingUp size={20} />
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-black tracking-tight">{new Intl.NumberFormat('fr-FR').format(finance.month_revenue || 0)}</p>
              {finance.month_variation && (
                <span className={`text-[10px] font-black flex items-center ${finance.month_variation > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {finance.month_variation > 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                  {Math.abs(finance.month_variation)}%
                </span>
              )}
            </div>
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">Recettes Mois</p>
          </div>
        </div>

        {/* Liste Rouge (Débiteurs) */}
        <div>
          <div className="flex items-center justify-between mb-4 px-1">
            <h3 className="text-sm font-black text-rose-400 uppercase tracking-widest flex items-center gap-2">
              <AlertTriangle size={14} /> Liste Rouge
            </h3>
            <span className="text-[10px] font-bold text-slate-500">{debtors.length} dossiers</span>
          </div>

          <div className="space-y-3">
            {debtors.map((d: any, idx: number) => (
              <div key={idx} className="bg-rose-500/5 border border-rose-500/10 rounded-2xl p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-slate-200">{d.name}</p>
                  <p className="text-[10px] font-black text-rose-400/60 mt-0.5">{new Intl.NumberFormat('fr-FR').format(d.amount)} MAD</p>
                </div>
                <button
                  onClick={() => openWhatsApp(d.phone, `Bonjour ${d.name}, nous vous contactons concernant un solde en attente de ${d.amount} MAD.`)}
                  className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center text-slate-400 hover:text-indigo-400 transition-colors"
                >
                  <MessageSquare size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col font-outfit pb-24">
      {/* Top Bar Navigation */}
      <div className="p-6 pb-0 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <Smartphone size={16} />
          </div>
          <span className="text-xs font-black uppercase tracking-[0.2em]">Elite Mobile</span>
        </div>

        {/* Sync Indicator */}
        <button onClick={fetchAndDecrypt} className="flex items-center gap-2 px-3 py-1.5 bg-white/5 rounded-full border border-white/5">
          <div className={`w-1.5 h-1.5 rounded-full ${syncStatus === 'loading' ? 'bg-indigo-400 animate-pulse' : syncStatus === 'error' ? 'bg-rose-500' : 'bg-emerald-500'}`} />
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">
            {syncStatus === 'loading' ? 'Sync...' : syncStatus === 'error' ? 'Offline' : 'À jour'}
          </span>
        </button>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-y-auto">
        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
            <AlertTriangle size={18} className="text-rose-500" />
            <p className="text-[10px] font-black text-rose-500 uppercase tracking-widest">{error}</p>
          </div>
        )}
        {activeTab === 'agenda' && <AgendaView />}
        {activeTab === 'finance' && <FinanceView />}
        {activeTab === 'securite' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
            <div className="px-1">
              <h2 className="text-2xl font-black">Sécurité</h2>
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mt-1">Contrôle Air-Gapped</p>
            </div>

            <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-[2rem] p-8 flex flex-col items-center text-center gap-4">
              <div className="w-20 h-20 bg-indigo-500/10 rounded-3xl flex items-center justify-center text-indigo-400 shadow-xl shadow-indigo-500/10">
                <ShieldCheck size={40} />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-200">Terminal Appairé</p>
                <p className="text-[10px] text-slate-500 mt-2 leading-relaxed">
                  Ce téléphone possède une clé AES-256 unique. Aucune donnée ne peut être lue sans ce terminal.
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="w-full py-5 bg-rose-500/10 border border-rose-500/20 text-rose-500 rounded-[2rem] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all"
            >
              <LogOut size={18} /> Révoquer cet accès
            </button>
          </div>
        )}
      </main>

      {/* Bottom Nav Dock (Thumb-Ready) */}
      <nav className="fixed bottom-6 left-6 right-6 h-20 bg-slate-900/80 backdrop-blur-2xl border border-white/5 rounded-[2.5rem] flex items-center justify-around px-4 shadow-2xl shadow-black">
        <button
          onClick={() => setActiveTab('agenda')}
          className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'agenda' ? 'text-indigo-400 scale-110' : 'text-slate-600'}`}
        >
          <Calendar size={22} />
          <span className="text-[9px] font-black uppercase tracking-widest">Agenda</span>
        </button>
        <button
          onClick={() => setActiveTab('finance')}
          className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'finance' ? 'text-amber-400 scale-110' : 'text-slate-600'}`}
        >
          <TrendingUp size={22} />
          <span className="text-[9px] font-black uppercase tracking-widest">Finance</span>
        </button>
        <button
          onClick={() => setActiveTab('securite')}
          className={`flex flex-col items-center gap-1 transition-all ${activeTab === 'securite' ? 'text-indigo-400 scale-110' : 'text-slate-600'}`}
        >
          <ShieldCheck size={22} />
          <span className="text-[9px] font-black uppercase tracking-widest">Sécurité</span>
        </button>
      </nav>
    </div>
  );
};
