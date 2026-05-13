import { useAuthStore } from '../stores/useAuthStore';
import { ShieldAlert, Clock, CreditCard, Mail, ArrowLeft } from 'lucide-react';

export const LicenseStatusPage = () => {
  const { user, logout } = useAuthStore();

  // Détection du mode
  // Si license_expires_at existe et est passé -> EXPIRED
  // Sinon -> WAITING
  const isExpired = user?.license_expires_at && new Date(user.license_expires_at) < new Date();
  const mode = isExpired ? 'EXPIRED' : 'WAITING';

  const config = {
    WAITING: {
      icon: <Clock className="w-10 h-10 text-amber-500" />,
      iconBg: "bg-amber-500/20",
      iconBorder: "border-amber-500/30",
      title: "Activation en cours",
      description: "Votre configuration est terminée. Votre dossier est actuellement en cours de validation par nos services. Cette étape prend généralement moins de 24h.",
      buttonText: "Contacter le support",
      buttonColor: "bg-amber-600 hover:bg-amber-500",
      buttonIcon: <Mail className="w-5 h-5" />
    },
    EXPIRED: {
      icon: <ShieldAlert className="w-10 h-10 text-red-500" />,
      iconBg: "bg-red-500/20",
      iconBorder: "border-red-500/30",
      title: "Licence Expirée",
      description: `Votre licence Elite a expiré le ${user?.license_expires_at ? new Date(user.license_expires_at).toLocaleDateString() : '---'}. L'accès aux fonctionnalités cliniques est suspendu.`,
      buttonText: "Renouveler maintenant",
      buttonColor: "bg-blue-600 hover:bg-blue-500",
      buttonIcon: <CreditCard className="w-5 h-5" />
    }
  }[mode];

  return (
    <div className="fixed inset-0 z-[9999] bg-slate-900 flex items-center justify-center p-6 overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] animate-pulse" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/10 rounded-full blur-[120px] animate-pulse" />

      <div className="max-w-md w-full bg-slate-800/50 backdrop-blur-2xl border border-slate-700/50 rounded-[3rem] p-12 text-center shadow-2xl relative z-10">
        <div className={`w-24 h-24 ${config.iconBg} rounded-[2rem] flex items-center justify-center mx-auto mb-10 border ${config.iconBorder} shadow-inner`}>
          {config.icon}
        </div>
        
        <h1 className="text-4xl font-black text-white mb-6 tracking-tight leading-tight">
          {config.title}
        </h1>
        
        <p className="text-slate-400 font-medium mb-12 leading-relaxed text-lg">
          {config.description}
        </p>

        <div className="space-y-4">
          <button 
            className={`w-full py-5 ${config.buttonColor} text-white rounded-[1.5rem] font-bold transition-all flex items-center justify-center gap-3 shadow-xl`}
            onClick={() => mode === 'EXPIRED' ? window.open('https://digitalcrown.ma/pricing', '_blank') : window.location.href = 'mailto:support@digitalcrown.ma'}
          >
            {config.buttonIcon}
            {config.buttonText}
          </button>
          
          <button 
            className="w-full py-5 bg-white/5 hover:bg-white/10 text-slate-300 rounded-[1.5rem] font-bold transition-all flex items-center justify-center gap-3 border border-white/5"
            onClick={logout}
          >
            <ArrowLeft className="w-5 h-5" />
            Retour à la connexion
          </button>
        </div>
        
        <div className="mt-12 pt-10 border-t border-slate-700/50">
          <div className="flex justify-between items-center px-4">
            <div className="text-left">
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1">ID Cabinet</p>
              <p className="text-slate-300 font-mono text-sm">#DC-{user?.id || '---'}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-slate-500 font-black uppercase tracking-widest mb-1">Statut</p>
              <p className={`text-sm font-bold ${isExpired ? 'text-red-400' : 'text-amber-400'}`}>
                {isExpired ? 'Inactif' : 'En attente'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
