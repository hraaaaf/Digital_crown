import React from 'react';
import { useAuthStore } from '../../stores/useAuthStore';
import { LicenseStatusPage } from '../../pages/LicenseStatusPage';

interface LicenseGuardProps {
  children: React.ReactNode;
}

export const LicenseGuard: React.FC<LicenseGuardProps> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) return null;

  // Si pas authentifié, on laisse ProtectedRoute gérer
  if (!isAuthenticated || !user) return <>{children}</>;

  // Les administrateurs ont toujours accès complet
  if (user.role === 'ADMIN') return <>{children}</>;
  if (user.is_superadmin) return <>{children}</>;

  // Vérification de la licence
  if (!user.is_licensed) {
    return <LicenseStatusPage />;
  }

  // Vérification de l'expiration (si is_licensed est true mais date passée)
  if (user.license_expires_at && new Date(user.license_expires_at) < new Date()) {
    return <LicenseStatusPage />;
  }

  return <>{children}</>;
};
