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
  BookOpen,
  Shield,
  Store,
  PanelLeftClose,
  PanelLeftOpen,
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
  const [desktopPinned, setDesktopPinned] = useState(() => localStorage.getItem('sidebar_desktop_pinned') === 'true');
  const [desktopHovered, setDesktopHovered] = useState(false);
  const desktopExpanded = desktopPinned || desktopHovered;

  useEffect(() => {
    localStorage.setItem('sidebar_desktop_pinned', String(desktopPinned));
  }, [desktopPinned]);

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
  const [aiActivityAnimationEnabled, setAiActivityAnimationEnabled] = useState(localStorage.getItem('clinical_tips_enabled') !== 'false');
  
  // CTO Rigor: Global event listener for AI animation & Settings changes
  useEffect(() => {
    const handleAiStart = () => setIsAiActive(true);
    const handleAiEnd = () => setIsAiActive(false);
    const handlePrefChange = () => setAiActivityAnimationEnabled(localStorage.getItem('clinical_tips_enabled') !== 'false');
    
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
        .sidebar-cabinet-compact { display: none; }
        @media (min-width: 1024px) {
          .sidebar-shell {
            transition: width 340ms cubic-bezier(0.16, 1, 0.3, 1), transform 220ms ease-out;
            will-change: width;
          }
          .sidebar-surface {
            transition: background-color 280ms ease, border-color 280ms ease, box-shadow 340ms cubic-bezier(0.16, 1, 0.3, 1), backdrop-filter 280ms ease;
          }
          .sidebar-logo-wrap {
            transition: height 300ms cubic-bezier(0.16, 1, 0.3, 1), padding 300ms cubic-bezier(0.16, 1, 0.3, 1);
          }
          .sidebar-logo,
          .sidebar-brand-compact {
            transition: opacity 160ms ease, transform 300ms cubic-bezier(0.16, 1, 0.3, 1);
          }
          .sidebar-brand-compact {
            display: flex;
            position: absolute;
            left: 50%;
            top: 50%;
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.9);
            pointer-events: none;
          }
          .sidebar-label,
          .sidebar-section-label,
          .sidebar-expanded-only {
            opacity: 1;
            transform: translateX(0);
            transition: opacity 150ms ease 125ms, transform 260ms cubic-bezier(0.16, 1, 0.3, 1) 90ms;
          }
          .sidebar-label {
            max-width: 190px;
            overflow: hidden;
            white-space: nowrap;
            transition: max-width 280ms cubic-bezier(0.16, 1, 0.3, 1) 80ms, opacity 150ms ease 125ms, transform 260ms cubic-bezier(0.16, 1, 0.3, 1) 90ms;
          }
          .sidebar-cabinet-section {
            min-height: 94px;
            transition: min-height 300ms cubic-bezier(0.16, 1, 0.3, 1);
          }
          .sidebar-cabinet-full {
            max-height: 84px;
            opacity: 1;
            transform: translateX(0);
            overflow: hidden;
            transition: max-height 280ms cubic-bezier(0.16, 1, 0.3, 1) 50ms, opacity 150ms ease 110ms, transform 260ms cubic-bezier(0.16, 1, 0.3, 1) 80ms;
          }
          .sidebar-cabinet-compact {
            display: flex;
            position: absolute;
            left: 50%;
            top: 50%;
            opacity: 0;
            transform: translate(-50%, -50%) scale(0.92);
            transition: opacity 140ms ease, transform 240ms cubic-bezier(0.16, 1, 0.3, 1);
          }
          .sidebar-pin-toggle {
            opacity: 1;
            transform: translateX(0) scale(1);
            transition: opacity 140ms ease 150ms, transform 240ms cubic-bezier(0.16, 1, 0.3, 1) 120ms, color 150ms ease, background-color 150ms ease;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-label,
          .sidebar-shell[data-expanded="false"] .sidebar-section-label,
          .sidebar-shell[data-expanded="false"] .sidebar-expanded-only {
            opacity: 0;
            transform: translateX(-10px);
            pointer-events: none;
            transition-delay: 0ms;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-label { max-width: 0; }
          .sidebar-shell[data-expanded="false"] .sidebar-section-label,
          .sidebar-shell[data-expanded="false"] .sidebar-expanded-only { visibility: hidden; }
          .sidebar-shell[data-expanded="false"] .sidebar-cabinet-full {
            max-height: 0;
            opacity: 0;
            transform: translateX(-10px);
            pointer-events: none;
            transition-delay: 0ms;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-cabinet-compact {
            display: flex;
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
            transition-delay: 110ms;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-logo {
            opacity: 0;
            transform: scale(0.92);
            pointer-events: none;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-brand-compact {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
            transition-delay: 110ms;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-pin-toggle {
            opacity: 0;
            pointer-events: none;
            transform: translateX(-5px) scale(0.94);
            transition-delay: 0ms;
          }
          .sidebar-shell[data-expanded="false"] .sidebar-nav-item { gap: 0; }
          .sidebar-shell[data-expanded="false"] .sidebar-badge { position: absolute; top: 0.35rem; right: 0.35rem; width: 0.5rem; height: 0.5rem; padding: 0; font-size: 0; border-radius: 999px; }
          @media (prefers-reduced-motion: reduce) {
            .sidebar-shell,
            .sidebar-surface,
            .sidebar-logo-wrap,
            .sidebar-logo,
            .sidebar-brand-compact,
            .sidebar-label,
            .sidebar-section-label,
            .sidebar-expanded-only,
            .sidebar-cabinet-section,
            .sidebar-cabinet-full,
            .sidebar-cabinet-compact,
            .sidebar-pin-toggle { transition-duration: 1ms !important; transition-delay: 0ms !important; }
          }
        }
      `}</style>
      {/* SIDEBAR : Clinical Premium Elite */}
      <aside
        className={cn(
          "sidebar-shell w-72 lg:w-[68px] h-screen fixed lg:relative z-[10000] shrink-0",
          desktopExpanded && "lg:w-72",
          isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        data-expanded={desktopExpanded ? "true" : "false"}
        onMouseEnter={() => setDesktopHovered(true)}
        onMouseLeave={() => setDesktopHovered(false)}
        onFocusCapture={() => setDesktopHovered(true)}
        onBlurCapture={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDesktopHovered(false);
        }}
      >
        <div className={cn(
          "sidebar-surface h-full w-full bg-sidebar border-r border-border-main shadow-elite flex flex-col overflow-hidden",
          desktopExpanded && "lg:shadow-2xl"
        )}
        style={{
          background: desktopExpanded ? 'color-mix(in srgb, var(--sidebar-bg) 92%, transparent)' : 'var(--sidebar-bg)',
          borderColor: desktopExpanded ? 'var(--glass-border)' : 'var(--border-color)',
          backdropFilter: desktopExpanded ? 'blur(24px) saturate(160%)' : undefined,
          WebkitBackdropFilter: desktopExpanded ? 'blur(24px) saturate(160%)' : undefined,
        }}>
        <button
          type="button"
          onClick={() => {
            setDesktopPinned(value => !value);
            setDesktopHovered(false);
          }}
          className="sidebar-pin-toggle hidden lg:flex absolute right-2 top-2 z-20 h-7 w-7 items-center justify-center rounded-lg border border-border-main bg-card-bg/90 text-text-muted shadow-sm transition-[opacity,transform,color,background-color] duration-150 hover:text-primary hover:bg-card-bg focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-pressed={desktopPinned}
          aria-label={desktopPinned ? 'R?duire la barre lat?rale' : 'D?ployer la barre lat?rale'}
          title={desktopPinned ? 'R?duire la barre lat?rale' : 'D?ployer la barre lat?rale'}
        >
          {desktopPinned ? <PanelLeftClose size={14} /> : <PanelLeftOpen size={14} />}
        </button>
        
        {/* PRODUCT IDENTITY: DIGITAL CROWN LOGO (Centered) */}
        <div className="sidebar-logo-wrap p-6 flex items-center justify-center border-b border-border-main shrink-0 h-28 relative group/logo transition-all duration-200">
          <Link 
            to="/dashboard" 
            className="transition-elite block w-full hover:opacity-80 flex items-center justify-center"
          >
            <span className="sidebar-brand-compact relative h-10 w-10 items-center justify-center rounded-xl border border-border-main bg-card-bg/80 shadow-sm overflow-hidden" aria-hidden="true">
              <img src={Logo} alt="" className="absolute left-1/2 top-[-8px] w-[180px] max-w-none -translate-x-1/2 object-contain" />
            </span>
            <img 
              src={Logo} 
              alt="Digital Crown" 
              className={cn(
                "sidebar-logo h-auto w-full max-w-[190px] object-contain transition-all duration-700",
                (isAiActive && aiActivityAnimationEnabled) && "animate-logo-pulse-light"
              )} 
              style={{ filter: document.body.dataset.theme === 'dark' ? 'brightness(0) invert(1)' : 'none' }}
            />
          </Link>
        </div>

        {/* CABINET SWITCHER SECTION (Premium Glassmorphic Switcher) */}
        <div className="sidebar-cabinet-section relative px-3 lg:px-2 py-4 border-b border-border-main shrink-0 bg-white/5 backdrop-blur-md">
          <div
            className="sidebar-cabinet-compact h-10 w-10 mx-auto items-center justify-center rounded-xl border border-border-main bg-card-bg/60 text-base"
            aria-hidden="true"
            title={cabinets.find(cab => String(cab.id) === String(activeCabinetId))?.nom || 'Cabinet actif'}
          ><Store size={18} strokeWidth={1.8} /></div>
          <div className="sidebar-cabinet-full">
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
        </div>

        {/* STACKED NAVIGATION */}
        <nav className="sidebar-nav flex-1 px-2 py-5 space-y-1.5 overflow-y-auto custom-scrollbar">
          <div className="sidebar-section-label text-[10px] font-black text-text-muted uppercase tracking-widest px-4 mb-3 mt-2">Cabinet</div>
          
          <NavItem to="/dashboard" icon={<LayoutDashboard size={20} />} label="Tableau de bord" badge={alertCount > 0 ? String(alertCount) : undefined} />
          <NavItem to="/analytics" icon={<Activity size={20} />} label="Indicateurs" />
          {hasAccess('agenda') && <NavItem to="/agenda" icon={<Calendar size={20} />} label="Agenda" />}
          {hasAccess('accounting') && <NavItem to="/accounting" icon={<Receipt size={20} />} label="Comptabilité" />}
          {hasAccess('patients') && <NavItem to="/patients" icon={<Users size={20} />} label="Patients" />}
          <NavItem to="/bibliotheque" icon={<BookOpen size={20} />} label="Bibliothèque clinique" />
          {hasAccess('patients') && <NavItem to="/approvisionnement" icon={<Store size={20} />} label="Approvisionnement" />}

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
                className="sidebar-expanded-only text-[10px] font-black uppercase tracking-widest mx-2 mb-3 shadow-sm flex items-center gap-2 py-2.5 px-4 rounded-elite-sm border transition-elite"
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
                  label="Céphalométrie"
                  forceActive={isInPatientDossier && currentTab === 'analysis'}
                />
              )}
              
              <NavItem 
                to={`/patients/${currentPatientId}?tab=admin`} 
                icon={<FileText size={20} />} 
                label="Documents"
                forceActive={isInPatientDossier && currentTab === 'admin'}
              />

              <NavItem 
                to={`/patients/${currentPatientId}?tab=archives`} 
                icon={<History size={20} />} 
                label="Archives"
                forceActive={isInPatientDossier && currentTab === 'archives'}
              />
            </div>
          )}

        </nav>
        </div>
      </aside>
    </>
  );
};

// NavItem Component Adapted for Elite Design System
const NavItem = ({ to, icon, label, forceActive, badge }: { to: string, icon: React.ReactNode, label: string, forceActive?: boolean, badge?: string }) => (
  <NavLink
    to={to}
    aria-label={label}
    title={label}
    className={({ isActive }) => {
      const isActuallyActive = forceActive !== undefined ? forceActive : isActive;
      return cn(
        "sidebar-nav-item flex items-center gap-3 px-4 py-3 rounded-elite-sm transition-elite group relative overflow-hidden cursor-pointer mb-1",
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
            className={cn("sidebar-label text-sm relative z-10 tracking-tight transition-elite", isActuallyActive ? "font-black" : "font-bold")}
            style={isActuallyActive ? { color: 'var(--primary)' } : {}}
          >
            {label}
          </span>
          {badge && (
            <span className="sidebar-badge relative z-10 ml-auto text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20">
              {badge}
            </span>
          )}
        </>
      );
    }}
  </NavLink>
);

