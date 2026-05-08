import { useState, useEffect } from 'react';
import { Bell, UserCircle, Settings, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cabinetApi } from '../services/templateApi';
import { safeStorage } from '../hooks/useLocalStorage';

export const Header = () => {
  const [cabinetName, setCabinetName] = useState('Chargement...');
  const [praticienName, setPraticienName] = useState('Dr. Benmoussa');
  const isDemoMode = safeStorage.get('appMode') === 'demo';

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
    fetchData();
  }, [isDemoMode]);

  const handleLogout = () => {
    safeStorage.remove('appMode');
    sessionStorage.removeItem('demoConfig');
    window.location.href = '/welcome'; 
  };

  return (
    <header className="h-20 bg-transparent flex items-center justify-end gap-6 px-8 shrink-0 relative z-20">
      
      {/* STATUT SYSTÈME - Adapté Light */}
      <div className="hidden xl:flex items-center gap-2 bg-card/80 px-4 py-2 rounded-full border border-border-main shadow-sm backdrop-blur-md">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Système Opérationnel</span>
      </div>

      <div className="hidden md:block w-px h-6 bg-slate-200 mx-2" />

      {/* SETTINGS & NOTIFS - Slate vers Navy */}
      <div className="flex items-center gap-2">
        <Link to="/settings" className="p-2.5 text-slate-400 hover:text-primary hover:bg-white/80 rounded-xl transition-all">
          <Settings size={20} />
        </Link>
        <button className="p-2.5 text-slate-400 hover:text-primary hover:bg-white/80 rounded-xl transition-all relative group">
          <Bell size={20} className="group-hover:scale-110 transition-transform" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-white shadow-sm" />
        </button>
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