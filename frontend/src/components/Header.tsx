import { useState, useEffect, useRef } from 'react';
import { Bell, UserCircle, Settings, LogOut, Calculator } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { cabinetApi } from '../services/templateApi';
import { api } from '../services/api';
import { safeStorage } from '../hooks/useLocalStorage';
import { EliteAssistant } from '../features/admin/DocumentStudio/EliteAssistant';
import { TourLauncher } from './GuidedTour/TourLauncher';

export const Header = () => {
  const [cabinetName, setCabinetName] = useState('Chargement...');
  const [praticienName, setPraticienName] = useState('Dr. Benmoussa');
  const [treasuryCount, setTreasuryCount] = useState(0);
  const [showNotifs, setShowNotifs] = useState(false);
  const [hoveredOrb, setHoveredOrb] = useState<'brain' | 'guide' | null>('brain');
  const notifRef = useRef<HTMLDivElement>(null);
  const isDemoMode = safeStorage.get('appMode') === 'demo';

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
        setShowNotifs(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (isDemoMode) {
        const storedDemo = sessionStorage.getItem('demoConfig');
        if (storedDemo) {
          try {
            const demoData = JSON.parse(storedDemo);
            setCabinetName(demoData.nom_cabinet || 'Cabinet Démo');
            setPraticienName(demoData.nomPraticien || 'Dr. Exploration');
          } catch (e) {}
        }
        return;
      }

      try {
        const config = await cabinetApi.getMine();
        setCabinetName(config.nom_cabinet || 'Mon Cabinet');
        // On suppose que le premier nom dans header_lines_fr est le nom du praticien
        if (config.header_lines_fr && config.header_lines_fr.length > 0) {
          setPraticienName(config.header_lines_fr[0]);
        }
      } catch (error) {
        console.error("Erreur header config:", error);
      }
    };
    const fetchTreasury = async () => {
      if (isDemoMode) return;
      try {
        const res = await api.get('/documents/accounting/treasury-hub');
        setTreasuryCount(res.data.pending_count || 0);
      } catch (e) {}
    };

    fetchData();
    fetchTreasury();

    const interval = setInterval(fetchTreasury, 60000); // Rafraîchissement toutes les 60s
    return () => clearInterval(interval);
  }, [isDemoMode]);

  const handleLogout = () => {
    safeStorage.remove('appMode');
    sessionStorage.removeItem('demoConfig');
    window.location.href = '/welcome'; 
  };

  return (
    <header className="h-20 bg-transparent flex items-center justify-end gap-6 px-8 shrink-0 relative z-[1000]">
      
      {/* ELITE ORBS & SETTINGS & NOTIFS */}
      <div className="flex items-center gap-3">
        
        {/* Elite Orbs Group */}
        <motion.div 
          layout 
          className="flex items-center gap-1 bg-white/10 dark:bg-black/10 backdrop-blur-md rounded-2xl p-1 border border-white/10 shadow-sm mr-2 min-h-[44px] justify-center overflow-visible relative group/capsule cursor-pointer"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            setHoveredOrb(x < rect.width / 2 ? 'guide' : 'brain');
          }}
          onMouseLeave={() => setHoveredOrb('brain')}
        >
           <AnimatePresence>
             {(!hoveredOrb || hoveredOrb === 'guide') && (
               <motion.div 
                 layout
                 key="guide"
                 initial={{ opacity: 0, scale: 0.8, width: 0 }}
                 animate={{ opacity: 1, scale: 1, width: 'auto' }}
                 exit={{ opacity: 0, scale: 0.8, width: 0 }}
                 className="relative z-10 overflow-hidden pointer-events-auto"
               >
                 <TourLauncher isEmbedded />
               </motion.div>
             )}
             
             {(!hoveredOrb || hoveredOrb === 'brain') && (
               <motion.div 
                 layout
                 key="brain"
                 initial={{ opacity: 0, scale: 0.8, width: 0 }}
                 animate={{ opacity: 1, scale: 1, width: 'auto' }}
                 exit={{ opacity: 0, scale: 0.8, width: 0 }}
                 className="relative z-10 overflow-hidden pointer-events-auto"
               >
                 <EliteAssistant isEmbedded />
               </motion.div>
             )}
           </AnimatePresence>
        </motion.div>

        <Link to="/settings" className="p-2.5 text-text-muted hover:text-primary hover:bg-primary/5 rounded-elite-sm transition-elite">
          <Settings size={20} />
        </Link>
        <div className="relative" ref={notifRef}>
          <button 
            onClick={() => setShowNotifs(!showNotifs)}
            className="p-2.5 text-text-muted hover:text-primary hover:bg-primary/5 rounded-elite-sm transition-elite relative group"
          >
            <Bell size={20} className="group-hover:scale-110 transition-elite" />
            {treasuryCount > 0 && (
              <span className="absolute top-2.5 right-2.5 w-3 h-3 bg-red-500 text-white text-[7px] font-black rounded-full border-2 border-card-bg flex items-center justify-center animate-pulse">
                {treasuryCount}
              </span>
            )}
          </button>


          {showNotifs && (
            <div className="absolute top-full right-0 mt-2 w-72 bg-card-bg border border-border-main rounded-3xl shadow-elite p-4 animate-in slide-in-from-top-2 duration-300 z-50 backdrop-blur-xl">
               <h4 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3 px-2">Alertes Ghost Treasury</h4>
               {treasuryCount > 0 ? (
                 <Link 
                   to="/accounting?tab=treasury" 
                   onClick={() => setShowNotifs(false)}
                   className="flex items-center gap-4 p-3 hover:bg-primary/5 rounded-2xl transition-all border border-transparent hover:border-primary/10"
                 >
                   <div className="w-10 h-10 bg-primary/10 text-primary rounded-xl flex items-center justify-center">
                     <Calculator size={18} />
                   </div>
                   <div>
                     <p className="text-xs font-black text-main leading-tight" style={{ color: 'var(--text-main)' }}>Relances en attente</p>
                     <p className="text-[10px] text-primary font-bold mt-0.5">{treasuryCount} dossiers à encaisser</p>
                   </div>
                 </Link>
               ) : (
                 <div className="text-center py-6">
                    <p className="text-[10px] font-bold text-text-muted italic">Trésorerie saine. Aucune alerte.</p>
                 </div>
               )}
               <div className="mt-3 pt-3 border-t border-border-main">
                  <Link to="/accounting" className="block text-center text-[9px] font-black text-text-muted hover:text-primary uppercase tracking-tighter transition-colors">
                    Voir toute la comptabilité
                  </Link>
               </div>
            </div>
          )}
        </div>
      </div>

      <div className="hidden md:block w-px h-6 bg-border-main mx-2" />

      {/* USER PROFILE */}
      <div className="flex items-center gap-4">
        <div className="text-right hidden lg:block">
          <p className="text-sm font-black text-primary leading-none tracking-tight font-outfit">{praticienName}</p>
          <p className="text-[10px] font-bold text-text-muted mt-1 uppercase tracking-tighter">{cabinetName}</p>
        </div>
        <div className="w-11 h-11 rounded-elite-sm bg-card-bg border border-border-main flex items-center justify-center text-primary shadow-elite transition-elite hover:scale-105">
          <UserCircle size={24} />
        </div>
      </div>

      {/* LOGOUT */}
      <button 
        onClick={handleLogout} 
        className="ml-2 p-2.5 text-text-muted hover:text-red-600 hover:bg-red-500/10 rounded-elite-sm transition-elite group"
        title="Déconnexion"
      >
        <LogOut size={20} className="group-hover:scale-110 transition-elite" /> 
      </button>


    </header>
  );
};