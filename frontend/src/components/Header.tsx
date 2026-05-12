import { useState, useEffect, useRef } from 'react';
import { Bell, UserCircle, Settings, LogOut, Calculator } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cabinetApi } from '../services/templateApi';
import { api } from '../services/api';
import { safeStorage } from '../hooks/useLocalStorage';

export const Header = () => {
  const [cabinetName, setCabinetName] = useState('Chargement...');
  const [praticienName, setPraticienName] = useState('Dr. Benmoussa');
  const [treasuryCount, setTreasuryCount] = useState(0);
  const [showNotifs, setShowNotifs] = useState(false);
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
    <header className="h-20 bg-transparent flex items-center justify-end gap-6 px-8 shrink-0 relative z-20">
      


      {/* SETTINGS & NOTIFS - Slate vers Navy */}
      <div className="flex items-center gap-2">
        <Link to="/settings" className="p-2.5 text-slate-400 hover:text-primary hover:bg-white/80 rounded-xl transition-all">
          <Settings size={20} />
        </Link>
        <div className="relative" ref={notifRef}>
          <button 
            onClick={() => setShowNotifs(!showNotifs)}
            className="p-2.5 text-slate-400 hover:text-primary hover:bg-white/80 rounded-xl transition-all relative group"
          >
            <Bell size={20} className="group-hover:scale-110 transition-transform" />
            {treasuryCount > 0 && (
              <span className="absolute top-2 right-2 w-4 h-4 bg-red-500 text-white text-[8px] font-black rounded-full border-2 border-white flex items-center justify-center animate-bounce">
                {treasuryCount}
              </span>
            )}
          </button>

          {showNotifs && (
            <div className="absolute top-full right-0 mt-2 w-72 bg-white border border-slate-200 rounded-3xl shadow-2xl p-4 animate-in slide-in-from-top-2 duration-300 z-50">
               <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3 px-2">Alertes Ghost Treasury</h4>
               {treasuryCount > 0 ? (
                 <Link 
                   to="/accounting?tab=treasury" 
                   onClick={() => setShowNotifs(false)}
                   className="flex items-center gap-4 p-3 hover:bg-indigo-50 rounded-2xl transition-all border border-transparent hover:border-indigo-100"
                 >
                   <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-xl flex items-center justify-center">
                     <Calculator size={18} />
                   </div>
                   <div>
                     <p className="text-xs font-black text-indigo-900 leading-tight">Relances en attente</p>
                     <p className="text-[10px] text-indigo-500 font-bold mt-0.5">{treasuryCount} dossiers à encaisser</p>
                   </div>
                 </Link>
               ) : (
                 <div className="text-center py-6">
                    <p className="text-[10px] font-bold text-slate-400 italic">Trésorerie saine. Aucune alerte.</p>
                 </div>
               )}
               <div className="mt-3 pt-3 border-t border-slate-100">
                  <Link to="/accounting" className="block text-center text-[9px] font-black text-slate-400 hover:text-primary uppercase tracking-tighter transition-colors">
                    Voir toute la comptabilité
                  </Link>
               </div>
            </div>
          )}
        </div>
      </div>

      <div className="hidden md:block w-px h-6 bg-slate-200 mx-2" />

      {/* USER PROFILE - Contraste Navy */}
      <div className="flex items-center gap-4">
        <div className="text-right hidden lg:block">
          <p className="text-sm font-black text-primary leading-none tracking-tight">{praticienName}</p>
          <p className="text-[10px] font-bold text-slate-400 mt-1 uppercase">{cabinetName}</p>
        </div>
        <div className="w-11 h-11 rounded-xl bg-input-field border border-border-main flex items-center justify-center text-primary shadow-sm backdrop-blur-md">
          <UserCircle size={24} />
        </div>
      </div>

      {/* LOGOUT */}
      <button 
        onClick={handleLogout} 
        className="ml-2 p-2.5 text-slate-400 hover:text-red-600 hover:bg-red-50/50 rounded-xl transition-all group"
        title="Déconnexion"
      >
        <LogOut size={20} className="group-hover:scale-110 transition-transform" /> 
      </button>

    </header>
  );
};