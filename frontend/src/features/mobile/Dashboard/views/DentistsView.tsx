import { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, User, Calendar, RefreshCw, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
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

function TeamContent({
  dentists,
  loading,
  error,
  onRefresh,
}: {
  dentists: Dentist[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  return (
    <section data-mob5a-team className="w-full max-w-[720px] mx-auto pb-6">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 bg-primary/10 rounded-[14px] flex items-center justify-center shrink-0">
            <Users size={18} className="text-primary" />
          </div>
          <div className="min-w-0">
            <h1 className="text-[24px] font-black tracking-tight text-primary leading-none">Équipe</h1>
            <p className="text-[10px] font-black text-text-muted uppercase tracking-widest mt-1">Praticiens du cabinet</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          aria-label="Rafraîchir la liste des praticiens"
          className="w-11 h-11 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-95 transition-transform disabled:opacity-40 shrink-0"
        >
          <RefreshCw size={15} className={`text-text-muted ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/5 border border-rose-200 rounded-[16px] mb-4">
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
        <div className="flex flex-col items-center justify-center py-16 gap-3 rounded-[20px] border border-glass-border bg-card">
          <Users size={32} className="text-text-muted/30" />
          <p className="text-sm font-black text-text-muted">Aucun praticien trouvé</p>
        </div>
      ) : (
        <div className="space-y-3">
          {dentists.map((d, i) => (
            <article key={d.id} className="bg-card border border-glass-border rounded-[20px] p-4 shadow-elite">
              <div className="flex items-center gap-3.5">
                <div
                  className="w-12 h-12 rounded-[16px] flex items-center justify-center shrink-0"
                  style={{ background: i === 0 ? 'linear-gradient(135deg, var(--primary), var(--secondary))' : 'color-mix(in srgb, var(--primary) 10%, transparent)' }}
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
                    <span className="text-[9px] font-black text-primary whitespace-nowrap">{d.today_appointments} RDV</span>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export function DentistsView({ embedded = false }: { embedded?: boolean }) {
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
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/dentists`, {
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
    void fetchDentists();
  }, [fetchDentists]);

  const content = <TeamContent dentists={dentists} loading={loading} error={error} onRefresh={() => void fetchDentists()} />;

  if (embedded) return content;

  return (
    <div
      className="min-h-[100dvh] bg-background text-text-main flex flex-col select-none"
      style={{
        backgroundColor: 'var(--bg-medical-pearl)',
        fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)',
      }}
    >
      <div className="px-6 pt-12 pb-4 max-w-[720px] w-full mx-auto">
        <button
          type="button"
          onClick={() => navigate('/mobile/dashboard?tab=agenda')}
          aria-label="Retour au tableau de bord mobile"
          className="w-11 h-11 bg-card border border-glass-border rounded-[14px] shadow-elite flex items-center justify-center active:scale-95 transition-transform"
        >
          <ArrowLeft size={16} className="text-primary" />
        </button>
      </div>
      <main className="flex-1 px-6 overflow-x-hidden">
        {content}
      </main>
    </div>
  );
}
