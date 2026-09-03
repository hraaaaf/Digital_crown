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
  BookOpen,
  Shield,
  Package,
  Store,
  Armchair,
  Construction
} from 'lucide-react';
import { cn } from '../utils/cn';
import { hasAccess as userHasAccess } from '../utils/accessControl';
import { api } from '../services/api';
import { authService } from '../services/auth';
import { useSettingsStore } from '../features/admin/Settings/hooks/useSettingsStore';
import { useAuthStore } from '../stores/useAuthStore';

// --- OFFICIAL ASSET IMPORT (Digital Crown Logo) ---
import Logo from '../assets/logo.png';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar = ({ isOpen = false, onClose }: SidebarProps) => {
  const { activeCabinetId, cabinets, switchCabinet } = useSettingsStore();
  const { user } = useAuthStore();
  const location = useLocation();

  const hasAccess = (permission: string) => userHasAccess(user, permission);

  const [alertCount, setAlertCount] = useState(0);
  useEffect(() => {
    if (!hasAccess('patients')) {
      setAlertCount(0);
      return;
    }
    const fetchCount = () => api.get('/intelligence/alerts/today')
      .then(res => setAlertCount(res.data.total || 0))
      .catch(() => {});
    fetchCount();
    const interval = setInterval(fetchCount, 120000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const [isAiActive, setIsAiActive] = useState(false);
  const [tipsEnabled, setTipsEnabled] = useState(localStorage.getItem('clinical_tips_enabled') !== 'false');
  
  // CTO Rigor: Global event listener for AI animation & Settings changes
  useEffect(() => {
    const handleAiStart = () => setIsAiActive(true);
    const handleAiEnd = () => setIsAiActive(false);
    const handlePrefChange = () => setTipsEnabled(localStorage.getItem('clinical_tips_enabled') !== 'false');
    
    window.addEventListener('ai-generation-start', handleAiStart);
    window.addEventListener('ai-generation-end', handleAiEnd);
    window.addEventListener('clinical-tips-changed', handlePrefChange);
    
    return () => {
      window.removeEventListener('ai-generation-start', handleAiStart);
      window.removeEventListener('ai-generation-end', handleAiEnd);
      window.removeEventListener('clinical-tips-changed', handlePrefChange);
    };
  }, []);


  const pathParts = location.pathname.split('/');
  const isInPatientDossier = Boolean(pathParts[1] === 'patients' && pathParts[2] && pathParts[2] !== 'new');
  const currentPatientId = isInPatientDossier ? pathParts[2] : null;

  const searchParams = new URLSearchParams(location.search);
  const currentTab = searchParams.get('tab') || 'admin';

  return (
    <>
      {/* Backdrop overlay for mobile/tablet */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[9999] lg:hidden"
          onClick={onClose}
        />
      )}
      {/* Animation adaptée pour le fond clair */}
      <style>{`
        @keyframes logo-pulse-light {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px var(--primary)); }
          50% { transform: scale(1.02); filter: drop-shadow(0 0 15px var(--primary)); }
        }
        .animate-logo-pulse-light { animation: logo-pulse-light 2s ease-in-out infinite; }
      `}</style>
      {/* SIDEBAR : Clinical Premium Elite */}
      <aside className={cn(
        "w-72 bg-sidebar backdrop-blur-2xl border-r border-border-main shadow-elite flex flex-col h-screen fixed lg:relative z-[10000] shrink-0 transition-all duration-300",
        isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        
        {/* PRODUCT IDENTITY: DIGITAL CROWN LOGO (Centered) */}
        <div className="p-6 flex items-center justify-center border-b border-border-main shrink-0 h-28 relative group/logo">
          <Link 
            to="/dashboard" 
            className="transition-elite block w-full hover:opacity-80 flex items-center justify-center"
          >
            <img 
              src={Logo} 
              alt="Digital Crown AI" 
              className={cn(
                "h-auto w-full max-w-[190px] object-contain transition-all duration-700", 
                (isAiActive && tipsEnabled) && "animate-logo-pulse-light"
              )} 
              style={{ filter: document.body.dataset.theme === 'dark' ? 'brightness(0) invert(1)' : 'none' }}
            />
          </Link>
        </div>

        {/* CABINET SWITCHER SECTION (Premium Glassmorphic Switcher) */}
        <div className="px-6 py-4 border-b border-border-main shrink-0 bg-white/5 backdrop-blur-md">
          <div className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2 px-1">Cabinet Actif</div>
          <div className="relative group">
            <select
              value={activeCabinetId}
              onChange={(e) => switchCabinet(e.target.value)}
              className="w-full bg-card-bg/60 border border-border-main rounded-elite px-3 py-2.5 text-xs font-black tracking-tight text-text-main cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary/40 transition-elite appearance-none"
              style={{ 
                backgroundImage: 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 20 20\'%3e%3cpath stroke=\'%236b7280\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'1.5\' d=\'M6 8l4 4 4-4\'/%3e%3c/svg%3e")',
                backgroundPosition: 'right 0.75rem center',
                backgroundSize: '1.25em 1.25em',
                backgroundRepeat: 'no-repeat',
                paddingRight: '2rem'
              }}
            >
              {cabinets.map(cab => (
                <option key={cab.id} value={cab.id} className="text-black bg-white font-bold">
                  🏢 {cab.nom}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* STACKED NAVIGATION */}
        <nav className="flex-1 p-5 space-y-1.5 overflow-y-auto custom-scrollbar">
          <div className="text-[10px] font-black text-text-muted uppercase tracking-widest px-4 mb-3 mt-2">Intelligence & Gestion</div>
          
          <NavItem to="/dashboard" icon={<LayoutDashboard size={20} />} label="Tableau de bord" badge={alertCount > 0 ? String(alertCount) : undefined} />
          <NavItem to="/analytics" icon={<Activity size={20} />} label="Analytics" />
          {hasAccess('agenda') && <NavItem to="/agenda" icon={<Calendar size={20} />} label="Studio Agenda" />}
          {hasAccess('accounting') && <NavItem to="/accounting" icon={<Receipt size={20} />} label="Comptabilité" />}
          {hasAccess('patients') && <NavItem to="/patients" icon={<Users size={20} />} label="Dossiers Patients" />}
          <NavItem to="/bibliotheque" icon={<BookOpen size={20} />} label="Bibliothèque Elite" />
          {hasAccess('patients') && <NavItem to="/approvisionnement" icon={<Store size={20} />} label="Marketplace" />}

          <div className="text-[10px] font-black text-amber-500 uppercase tracking-widest px-4 mb-3 mt-6 flex items-center gap-1.5">
            <Construction size={12} /> Bientôt disponible
          </div>
          {hasAccess('patients') && <NavItem to="/stock" icon={<Package size={20} />} label="Gestion Stock" badge="Bientôt" />}
          {hasAccess('agenda') && <NavItem to="/salle-attente" icon={<Armchair size={20} />} label="Salle d'attente" badge="Bientôt" />}
          <NavItem to="/labo" icon={<FlaskConical size={20} />} label="Module Labo" badge="Bientôt" />

          {/* SUPER ADMIN (Hidden for non-admin users) */}
          {user?.is_superadmin && (
            <div className="mt-4 pt-4 border-t border-border-main">
              <NavItem to="/super-admin" icon={<Shield size={20} className="text-amber-500" />} label="Gestion des Dentistes" />
              <NavItem to="/approvisionnement/admin" icon={<Store size={20} className="text-amber-500" />} label="Fournisseurs" />
            </div>
          )}

          {/* ACTIVE PATIENT NAVIGATION */}
          {hasAccess('patients') && currentPatientId && (
            <div className="mt-8 animate-in fade-in slide-in-from-left-4 duration-500">
              <div 
                className="text-[10px] font-black uppercase tracking-widest mx-2 mb-3 shadow-sm flex items-center gap-2 py-2.5 px-4 rounded-elite-sm border transition-elite"
                style={{ 
                  backgroundColor: 'var(--primary-bg, rgba(99, 102, 241, 0.1))', 
                  color: 'var(--primary)',
                  borderColor: 'var(--glass-border)'
                }}
              >
                <div className="w-2 h-2 rounded-full animate-pulse bg-primary" />
                Dossier Actif
              </div>
              
              {hasAccess('cephalo') && (
                <NavItem 
                  to={`/patients/${currentPatientId}?tab=analysis`} 
                  icon={<Activity size={20} />} 
                  label="Studio Céphalométrique"
                  forceActive={isInPatientDossier && currentTab === 'analysis'}
                />
              )}
              
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

// NavItem Component Adapted for Elite Design System
const NavItem = ({ to, icon, label, forceActive, badge }: { to: string, icon: React.ReactNode, label: string, forceActive?: boolean, badge?: string }) => (
  <NavLink
    to={to}
    className={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return cn(
        "flex items-center gap-3 px-4 py-3 rounded-elite-sm transition-elite group relative overflow-hidden cursor-pointer mb-1",
          isActuallyActive 
          ? "shadow-elite border border-border-main" 
          : "text-text-muted hover:bg-primary/5 hover:text-primary"
      );
    }}
    style={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return isActuallyActive ? { backgroundColor: 'var(--card-bg)' } : {};
    }}
  >
    {({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return (
        <>
          {isActuallyActive && (
            <div 
              className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 rounded-r-full" 
              style={{ backgroundColor: 'var(--primary)' }} 
            />
          )}
          <span 
            className={cn("relative z-10 transition-elite", isActuallyActive ? "scale-110 text-primary" : "group-hover:scale-110")}
            style={isActuallyActive ? { color: 'var(--primary)' } : {}}
          >
            {icon}
          </span>
          <span
            className={cn("text-sm relative z-10 tracking-tight transition-elite", isActuallyActive ? "font-black" : "font-bold")}
            style={isActuallyActive ? { color: 'var(--primary)' } : {}}
          >
            {label}
          </span>
          {badge && (
            <span className="relative z-10 ml-auto text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
              {badge}
            </span>
          )}
        </>
      );
    }}
  </NavLink>
);

