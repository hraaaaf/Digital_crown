import { useEffect, useRef, useState } from 'react';
import type { AppUser } from '../../../types';
import { api } from '../../../services/api';
import { hasAccess } from '../../../utils/accessControl';
import type { SearchPatientResult } from '../types';

export const usePatientSearch = (user: AppUser | null) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchPatientResult[]>([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const canReadPatients = hasAccess(user, 'patients');

  const close = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    setIsExpanded(false);
    setQuery('');
    setResults([]);
    setLoading(false);
  };

  const open = () => {
    if (canReadPatients) setIsExpanded(true);
  };

  const change = (value: string) => {
    if (!canReadPatients) return;
    setQuery(value);

    if (timerRef.current) clearTimeout(timerRef.current);
    if (!value.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    timerRef.current = setTimeout(async () => {
      try {
        const response = await api.get(`/patients/?search=${encodeURIComponent(value.trim())}&limit=6`);
        setResults(response.data || []);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  };

  useEffect(() => {
    if (!canReadPatients) close();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // close est volontairement local : le nettoyage dépend uniquement du droit patient.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canReadPatients]);

  return {
    canSearch: canReadPatients,
    isExpanded,
    query,
    results,
    loading,
    open,
    close,
    change,
  };
};
