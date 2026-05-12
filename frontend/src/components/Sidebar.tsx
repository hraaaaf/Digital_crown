import React, { useState, useEffect } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Users, 
  Activity, 
  FileText,
  History,
  Calendar,
  Receipt,
  FlaskConical,
  LogOut,
  BookOpen
} from 'lucide-react';
import { cn } from '../utils/cn';
import { authService } from '../services/auth';
import { ClinicalTipBubble } from '../features/clinical_tips/components/ClinicalTipBubble';
import { clinicalTips } from '../data/clinical_tips';

// --- OFFICIAL ASSET IMPORT (Digital Crown Logo) ---
import Logo from '../assets/logo.png';

export const Sidebar = () => {
  const location = useLocation();
  const [isAiActive, setIsAiActive] = useState(false);
  const [isFlipping, setIsFlipping] = useState(false);
  const [showTip, setShowTip] = useState(false);
  const [currentTip, setCurrentTip] = useState("");

  // Cycle tips with Slingshot physics
  useEffect(() => {
    const triggerTip = () => {
      // 1. Tension / Anticipation
      setIsFlipping(true); 
      
      // 2. Mid-tension (randomize tip)
      setTimeout(() => {
        const randomTip = clinicalTips[Math.floor(Math.random() * clinicalTips.length)];
        setCurrentTip(randomTip);
      }, 400);

      // 3. THE LAUNCH (Snap forward)
      setTimeout(() => {
        setShowTip(true);
      }, 600);

      // 4. Reset states
      setTimeout(() => {
        setIsFlipping(false);
      }, 1200);
    };

    // Initial trigger after 10s, then every 2 minutes
    const initialTimeout = setTimeout(triggerTip, 10000);
    const interval = setInterval(triggerTip, 120000);

    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, []);
  
  // CTO Rigor: Global event listener for AI animation
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
      {/* Animation adapted for light background */}
      <style>{`
        @keyframes logo-pulse-light {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px var(--primary-rgb, rgba(0,51,128,0.1))); }
          50% { transform: scale(1.02); filter: drop-shadow(0 0 15px var(--primary-rgb, rgba(0,51,128,0.3))); }
        }
        @keyframes logo-slingshot {
          0% { transform: translateX(0) scale(1); filter: brightness(1); }
          30% { transform: translateX(-25px) scale(0.9) skewX(-5deg); filter: brightness(1.1); } /* Tension */
          50% { transform: translateX(30px) scale(1.1) skewX(10deg); filter: brightness(1.3) drop-shadow(0 0 20px var(--primary)); } /* Launch */
          70% { transform: translateX(-5px) scale(1.05); } /* Rebond */
          100% { transform: translateX(0) scale(1); filter: brightness(1); }
        }
        .animate-logo-pulse-light {
          animation: logo-pulse-light 2s ease-in-out infinite;
        }
        .animate-tooth-slingshot {
          animation: logo-slingshot 1.2s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }
      `}</style>

      {/* SIDEBAR : Clinical Premium Light */}
      <aside className="w-72 bg-sidebar backdrop-blur-2xl border-r border-border-main shadow-[4px_0_24px_rgba(0,0,0,0.02)] flex flex-col h-screen fixed lg:relative z-[10000] shrink-0">
        
        {/* PRODUCT IDENTITY: DIGITAL CROWN LOGO (Centered) */}
        <div className="p-6 flex items-center justify-center border-b border-border-main shrink-0 h-28 relative group/logo">
          <Link 
            to="/dashboard" 
            className="transition-all duration-500 block w-full hover:opacity-80 flex items-center justify-center"
          >
            <img 
              src={Logo} 
              alt="Digital Crown AI" 
              className={cn(
                "h-auto w-full max-w-[190px] object-contain transition-all duration-700", 
                isAiActive && "animate-logo-pulse-light",
                isFlipping && "animate-tooth-slingshot"
              )} 
            />
          </Link>
          
          {/* Elite Clinical Tips Module */}
          <ClinicalTipBubble show={showTip} tip={currentTip} onClose={() => setShowTip(false)} />

        </div>

        {/* STACKED NAVIGATION */}
        <nav className="flex-1 p-5 space-y-2 overflow-y-auto custom-scrollbar">
          <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest px-4 mb-4 mt-2">Navigation</div>
          
          <NavItem to="/dashboard" icon={<LayoutDashboard size={20} />} label="Tableau de bord" />
          <NavItem to="/agenda" icon={<Calendar size={20} />} label="Studio Agenda" />
          <NavItem to="/accounting" icon={<Receipt size={20} />} label="Comptabilité" />
          <NavItem to="/patients" icon={<Users size={20} />} label="Dossiers Patients" />
          <NavItem to="/bibliotheque" icon={<BookOpen size={20} />} label="Bibliothèque Elite" />

          {/* ACTIVE PATIENT NAVIGATION */}
          {currentPatientId && (
            <div className="mt-8 animate-in fade-in slide-in-from-left-4 duration-300">
              <div 
                className="text-[10px] font-black uppercase tracking-widest mx-2 mb-3 border shadow-sm flex items-center gap-2 py-2 px-4 rounded-xl"
                style={{ 
                  backgroundColor: 'var(--primary-bg, #f0f7ff)', 
                  color: 'var(--primary)',
                  borderColor: 'var(--primary-border, #e0e7ff)'
                }}
              >
                <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: 'var(--primary)' }} />
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

          {/* EXPERIMENTAL / DEMO SECTION */}
          <div className="mt-8 pt-8 border-t border-slate-200/60">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 mb-4">Expérimental</div>
            <button
               onClick={() => {
                 localStorage.removeItem('appMode');
                 window.location.href = '/welcome';
               }}
               className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group cursor-pointer hover:bg-slate-100"
               style={{ color: 'var(--primary)' }}
            >
              <FlaskConical size={20} className="group-hover:scale-110 transition-transform" />
              <span className="text-sm font-bold tracking-wide">Activer Lab Mode</span>
            </button>
            <button
               onClick={() => authService.logout()}
               className="w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group cursor-pointer hover:bg-red-50 text-red-500 mt-2"
            >
              <LogOut size={20} className="group-hover:scale-110 transition-transform" />
              <span className="text-sm font-bold tracking-wide">Déconnexion</span>
            </button>
          </div>
        </nav>
      </aside>
    </>
  );
};

// NavItem Component Adapted for Light Theme
const NavItem = ({ to, icon, label, forceActive }: { to: string, icon: React.ReactNode, label: string, forceActive?: boolean }) => (
  <NavLink
    to={to}
    className={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return cn(
        "flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group relative overflow-hidden cursor-pointer mb-1",
          isActuallyActive 
          ? "bg-card shadow-sm border border-border-main" 
          : "text-text-muted hover:bg-card/80"
      );
    }}
    style={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return isActuallyActive ? { color: 'var(--primary)' } : {};
    }}
  >
    {({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return (
        <>
          {isActuallyActive && (
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-8 rounded-r-full" 
              style={{ 
                backgroundColor: 'var(--primary)',
                boxShadow: '0 0 8px var(--primary-glow, rgba(0,51,128,0.2))'
              }} 
            />
          )}
          <span 
            className={cn("relative z-10 transition-transform duration-300", isActuallyActive ? "scale-110" : "group-hover:scale-110")}
            style={isActuallyActive ? { color: 'var(--primary)' } : {}}
          >
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