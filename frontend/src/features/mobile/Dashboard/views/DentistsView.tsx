import { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, User, Calendar, RefreshCw, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { Skeleton } from '../components/Skeleton';

interface Dentist {
  id: number;
  name: string;
  email: string;
  today_appointments: number;
}

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}

export function DentistsView() {
  const navigate = useNavigate();
  const [dentists, setDentists] = useState<Dentist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDentists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Non appairé');
      const res = await fetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/dentists`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const data = await res.json();
      setDentists(data.dentists ?? []);
    } catch (e: any) {
      setError(e.message ?? 'Erreur réseau');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDentists();
  }, [fetchDentists]);

  return (
    <div className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit select-none" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      {/* Header */}
      <div className="px-6 pt-14 pb-6 relative z-10">
        <div className="flex items-center gap-3 mb-8">
          <button
            onClick={() => navigate('/mobile/dashboard')}
            className="w-10 h-10 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-90 transition-transform"
          >
            <ArrowLeft size={16} className="text-primary" />
          </button>
          <button
            onClick={fetchDentists}
            disabled={loading}
            className="w-10 h-10 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-90 transition-transform disabled:opacity-40 ml-auto"
          >
            <RefreshCw size={14} className={`text-text-muted ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary/10 rounded-[14px] flex items-center justify-center">
            <Users size={18} className="text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight text-primary font-outfit leading-none">Équipe</h1>
            <p className="text-[10px] font-black text-text-muted uppercase tracking-widest mt-0.5">Praticiens du cabinet</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="flex-1 px-6 pb-10 space-y-4">
        {error && (
          <div className="p-4 bg-rose-500/5 border border-rose-200 rounded-[16px]">
            <p className="text-xs font-black text-rose-600">{error}</p>
          </div>
        )}

        {loading && !dentists.length ? (
          <div className="space-y-3">
            {[1, 2].map(i => (
              <Skeleton key={i} className="h-24 w-full rounded-[20px]" />
            ))}
          </div>
        ) : dentists.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Users size={32} className="text-text-muted/30" />
            <p className="text-sm font-black text-text-muted">Aucun praticien trouvé</p>
          </div>
        ) : (
          dentists.map((d, i) => (
            <div
              key={d.id}
              className="bg-card border border-glass-border rounded-[20px] p-5 shadow-elite"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-[16px] flex items-center justify-center shrink-0"
                  style={{ background: i === 0 ? 'linear-gradient(135deg, var(--primary), var(--secondary))' : 'var(--primary-10, rgba(0,51,128,0.10))' }}
                >
                  <User size={20} className={i === 0 ? 'text-white' : 'text-primary'} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-black text-text-main truncate">{d.name}</p>
                  <p className="text-[10px] font-bold text-text-muted truncate">{d.email}</p>
                  {i === 0 && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-primary/10 border border-primary/20 rounded-full text-[9px] font-black text-primary uppercase tracking-widest">
                      Praticien principal
                    </span>
                  )}
                </div>
                {d.today_appointments > 0 && (
                  <div className="shrink-0 flex flex-col items-center gap-0.5">
                    <div className="w-9 h-9 bg-primary/10 rounded-[12px] flex items-center justify-center">
                      <Calendar size={14} className="text-primary" />
                    </div>
                    <span className="text-[9px] font-black text-primary">{d.today_appointments} RDV</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </main>
    </div>
  );
}
