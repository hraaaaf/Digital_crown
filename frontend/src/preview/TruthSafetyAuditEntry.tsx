import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '../index.css';
import { LicenseStatusPage } from '../pages/LicenseStatusPage';
import { StockPage } from '../pages/StockPage';
import { useAuthStore } from '../stores/useAuthStore';

const scenario = new URLSearchParams(window.location.search).get('scenario') || 'license-expired';

useAuthStore.setState({
  user: {
    id: 77,
    email: 'audit@digitalcrown.local',
    nom_complet: 'Dr Audit',
    role: 'ADMIN',
    is_superadmin: false,
    permissions: {},
    license_expires_at: '2025-01-01T00:00:00Z',
  } as any,
  isAuthenticated: true,
  isLoading: false,
  error: null,
  logout: () => {},
});

const client = new QueryClient({
  defaultOptions: { queries: { retry: false, staleTime: 60_000 } },
});

const App = () => {
  if (scenario === 'license-expired') return <LicenseStatusPage />;
  return (
    <QueryClientProvider client={client}>
      <div className="min-h-screen bg-slate-50">
        <StockPage />
      </div>
    </QueryClientProvider>
  );
};

createRoot(document.getElementById('root')!).render(<App />);
