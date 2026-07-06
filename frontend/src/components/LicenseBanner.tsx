import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';
import { useAuthStore } from '../stores/useAuthStore';
import { differenceInDays, parseISO } from 'date-fns';

export const LicenseBanner: React.FC = () => {
  const { user } = useAuthStore();

  if (!user || user.role === 'SUPERADMIN' || user.is_superadmin) return null;

  const isLicensed = user.is_licensed;
  const expiresAt = user.license_expires_at ? parseISO(user.license_expires_at) : null;
  
  if (!isLicensed) {
    return (
      <div className="bg-red-500 text-white px-4 py-2 text-sm font-medium flex items-center justify-center gap-2 shadow-sm z-50 relative">
        <ShieldAlert className="w-4 h-4" />
        Mode Lecture Seule : Votre licence a expiré. Vous pouvez consulter vos dossiers, mais toute modification est bloquée.
        <a href="tel:0600000000" className="underline ml-2 hover:text-red-100">Contactez le support pour renouveler.</a>
      </div>
    );
  }

  if (expiresAt) {
    const daysLeft = differenceInDays(expiresAt, new Date());
    if (daysLeft <= 7 && daysLeft >= 0) {
      return (
        <div className="bg-amber-500 text-white px-4 py-2 text-sm font-medium flex items-center justify-center gap-2 shadow-sm z-50 relative">
          <Info className="w-4 h-4" />
          Attention : Votre période d'essai ou licence expire dans {daysLeft} jour{daysLeft > 1 ? 's' : ''}.
          <a href="tel:0600000000" className="underline ml-2 hover:text-amber-100">Renouvelez maintenant pour éviter toute interruption.</a>
        </div>
      );
    }
  }

  return null;
};
