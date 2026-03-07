import React, { useState, useEffect } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  FileText,
  History 
} from 'lucide-react';
import { cn } from '../utils/cn';

// --- IMPORTATION DE L'ASSET OFFICIEL (Digital Crown Logo) ---
import Logo from '../assets/logo.png';

export const Sidebar = () => {
  const location = useLocation();
  const [isAiActive, setIsAiActive] = useState(false);
  
  // Rigueur CTO : Écouteur d'événements global pour l'animation IA
  useEffect(() => {
    const handleAiStart = () => setIsAiActive(true);
    const handleAiEnd = () => setIsAiActive(false);
    
    window.addEventListener('ai-generation-start', handleAiStart);
    window.addEventListener('ai-generation-end', handleAiEnd);
    
    return () => {
      window.removeEventListener('ai-generation-start', handleAiStart);
      window.removeEventListener('ai-generation-end', handleAiEnd);
    };
  }, []);

  const pathParts = location.pathname.split('/');
  const isInPatientDossier = Boolean(pathParts[1] === 'patients' && pathParts[2] && pathParts[2] !== 'new');
  const currentPatientId = isInPatientDossier ? pathParts[2] : null;

  const searchParams = new URLSearchParams(location.search);
  const currentTab = searchParams.get('tab') || 'admin';

  return (
    <>
      {/* Animation adaptée pour fond clair */}
      <style>{`
        @keyframes logo-pulse-light {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px rgba(0,51,128,0.1)); }
          50% { transform: scale(1.02); filter: drop-shadow(0 0 15px rgba(0,51,128,0.3)); }
        }
        .animate-logo-pulse-light {
          animation: logo-pulse-light 2s ease-in-out infinite;
        }
      `}</style>

      {/* SIDEBAR : Clinical Premium Light */}
      <aside className="w-72 bg-slate-50/50 backdrop-blur-2xl border-r border-slate-200 shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col h-screen relative z-50 shrink-0">
        
        {/* IDENTITÉ PRODUIT : LOGO DIGITAL CROWN (Centré) */}
        <div className="p-6 flex items-center justify-center border-b border-slate-200/60 shrink-0 h-28">
          <Link 
            to="/dashboard" 
            className="transition-all duration-500 block w-full hover:opacity-80 flex items-center justify-center"
          >
            <img 
              src={Logo} 
              alt="Digital Crown AI" 
              className={cn(
                "h-auto w-full max-w-[190px] object-contain transition-all duration-500", 
                isAiActive && "animate-logo-pulse-light"
              )} 
            />
          </Link>
        </div>

        {/* NAVIGATION EMPILÉE */}
        <nav className="flex-1 p-5 space-y-2 overflow-y-auto custom-scrollbar">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 mb-4 mt-2">Navigation</div>
          
          <NavItem to="/dashboard" icon={<LayoutDashboard size={20} />} label="Tableau de bord" />
          <NavItem to="/patients" icon={<Users size={20} />} label="Dossiers Patients" />

          {/* NAVIGATION CONTEXTUELLE DU DOSSIER ACTIF */}
          {currentPatientId && (
            <div className="mt-8 animate-in fade-in slide-in-from-left-4 duration-300">
              <div className="text-[10px] font-black text-[#003380] bg-blue-50/80 py-2 px-4 rounded-xl uppercase tracking-widest mx-2 mb-3 border border-blue-100/50 shadow-sm flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                Dossier Actif
              </div>
              
              <NavItem 
                to={`/patients/${currentPatientId}?tab=analysis`} 
                icon={<Activity size={20} />} 
                label="Studio Céphalométrique"
                forceActive={isInPatientDossier && currentTab === 'analysis'}
              />
              
              <NavItem 
                to={`/patients/${currentPatientId}?tab=admin`} 
                icon={<FileText size={20} />} 
                label="Hub Documentaire"
                forceActive={isInPatientDossier && currentTab === 'admin'}
              />

              <NavItem 
                to={`/patients/${currentPatientId}?tab=archives`} 
                icon={<History size={20} />} 
                label="Archives & Historique"
                forceActive={isInPatientDossier && currentTab === 'archives'}
              />
            </div>
          )}
        </nav>
      </aside>
    </>
  );
};

// Composant NavItem Adapté Thème Light
const NavItem = ({ to, icon, label, forceActive }: { to: string, icon: React.ReactNode, label: string, forceActive?: boolean }) => (
  <NavLink
    to={to}
    className={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return cn(
        "flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group relative overflow-hidden cursor-pointer mb-1",
        isActuallyActive 
          ? "bg-white text-[#003380] shadow-sm border border-slate-200/60" 
          : "text-slate-600 hover:bg-white/80 hover:text-[#003380]"
      );
    }}
  >
    {({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return (
        <>
          {isActuallyActive && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-[#003380] rounded-r-full shadow-[0_0_8px_rgba(0,51,128,0.2)]" />}
          <span className={cn("relative z-10 transition-transform duration-300", isActuallyActive ? "scale-110 text-[#003380]" : "group-hover:scale-110")}>
            {icon}
          </span>
          <span className={cn("text-sm relative z-10 tracking-wide", isActuallyActive ? "font-black" : "font-bold")}>
            {label}
          </span>
        </>
      );
    }}
  </NavLink>
);