import React, { useCallback, useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { api } from '../../../../services/api';
import { TeamManager } from '../../TeamManager';
import { SettingsReadError } from './SharedUI';

type ReadState = 'loading' | 'ready' | 'error';

const isTeamRead = (url?: string, method?: string) => {
  if ((method || 'get').toLowerCase() !== 'get' || !url) return false;
  return url.startsWith('/team/') || url === '/team' || url.startsWith('/team?');
};

export const TeamReadTruthGate: React.FC = () => {
  const [readState, setReadState] = useState<ReadState>('loading');

  const verifyTeamTruth = useCallback(async () => {
    setReadState('loading');
    try {
      await Promise.all([
        api.get(`/team/?_truth=${Date.now()}`),
        api.get('/team/quota'),
      ]);
      setReadState('ready');
    } catch {
      setReadState('error');
    }
  }, []);

  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (isTeamRead(error?.config?.url, error?.config?.method)) {
          setReadState('error');
        }
        return Promise.reject(error);
      },
    );

    void verifyTeamTruth();
    return () => api.interceptors.response.eject(interceptor);
  }, [verifyTeamTruth]);

  if (readState === 'loading') {
    return (
      <div className="flex justify-center py-20" aria-label="Chargement de l'équipe">
        <Loader2 className="animate-spin" style={{ color: 'var(--primary)' }} size={40} />
      </div>
    );
  }

  if (readState === 'error') {
    return (
      <SettingsReadError
        title="Équipe indisponible"
        message="Impossible de vérifier les membres et les quotas du cabinet. Aucune gestion d’équipe n’est disponible tant que ces données ne sont pas chargées."
        onRetry={verifyTeamTruth}
      />
    );
  }

  return <TeamManager />;
};
