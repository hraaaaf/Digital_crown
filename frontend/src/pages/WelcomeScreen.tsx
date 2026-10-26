import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import Logo from '../assets/logo.png';

export const WelcomeScreen: React.FC = () => {
  const navigate = useNavigate();

  const handleSelectMode = () => {
    localStorage.setItem('appMode', 'prod');
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Background Halos */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-100/40 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[60%] rounded-full bg-indigo-100/30 blur-[150px]" />
      </div>

      <div className="max-w-4xl w-full relative z-10">
        <div className="text-center mb-12">
          <div className="w-48 h-48 flex items-center justify-center mx-auto mb-6 animate-in zoom-in duration-700">
            <img src={Logo} className="w-full h-full object-contain" alt="Digital Crown" />
          </div>
          <h1 className="text-4xl font-black text-text-main mb-4 tracking-tight">
            Digital Crown <span className="text-primary">v1.1</span>
          </h1>
          <p className="text-text-muted text-lg max-w-lg mx-auto">
            Bienvenue dans votre nouvel écosystème clinique intelligent.
          </p>
        </div>

        <div className="max-w-md mx-auto">
          {/* Mode Production (Mon Cabinet) */}
          <button
            onClick={handleSelectMode}
            className="w-full group relative bg-card rounded-3xl border-2 border-border-main p-8 text-left transition-all duration-500 hover:border-primary hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-2 overflow-hidden"
          >
            <div className="relative z-10">
              <div className="w-14 h-14 bg-input-field rounded-2xl flex items-center justify-center mb-6 group-hover:bg-primary group-hover:text-white transition-colors duration-500">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-bold text-text-main mb-2">Mon Cabinet</h2>
              <p className="text-text-muted mb-8">
                Accédez à vos dossiers patients réels et à votre base de données sécurisée.
              </p>
              <div className="flex items-center gap-2 text-primary font-bold group-hover:gap-4 transition-all">
                Démarrer la session
                <ChevronRight className="w-5 h-5" />
              </div>
            </div>
            {/* Background Accent */}
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-background rounded-full group-hover:bg-primary/5 transition-colors duration-500" />
          </button>
        </div>

        <p className="text-center mt-12 text-text-muted text-sm">
          Propulsé par <span className="font-bold text-text-muted">SANINOVA AI Engine</span>
        </p>
      </div>
    </div>
  );
};

