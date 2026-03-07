
import { Bell, UserCircle, Settings, LogOut } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header = () => {
  const handleLogout = () => {
    window.location.href = '/login'; 
  };

  return (
    <header className="h-20 bg-transparent flex items-center justify-end gap-6 px-8 shrink-0 relative z-20">
      
      {/* STATUT SYSTÈME - Adapté Light */}
      <div className="hidden xl:flex items-center gap-2 bg-white/80 px-4 py-2 rounded-full border border-slate-200 shadow-sm backdrop-blur-md">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
        <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Système Opérationnel</span>
      </div>

      <div className="hidden md:block w-px h-6 bg-slate-200 mx-2" />

      {/* SETTINGS & NOTIFS - Slate vers Navy */}
      <div className="flex items-center gap-2">
        <Link to="/settings" className="p-2.5 text-slate-400 hover:text-[#003380] hover:bg-white/80 rounded-xl transition-all">
          <Settings size={20} />
        </Link>
        <button className="p-2.5 text-slate-400 hover:text-[#003380] hover:bg-white/80 rounded-xl transition-all relative group">
          <Bell size={20} className="group-hover:scale-110 transition-transform" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-blue-600 rounded-full border-2 border-white shadow-sm" />
        </button>
      </div>

      <div className="hidden md:block w-px h-6 bg-slate-200 mx-2" />

      {/* USER PROFILE - Contraste Navy */}
      <div className="flex items-center gap-4">
        <div className="text-right hidden lg:block">
          <p className="text-sm font-black text-[#003380] leading-none tracking-tight">Dr. Benmoussa</p>
          <p className="text-[10px] font-bold text-slate-400 mt-1 uppercase">Directeur Médical</p>
        </div>
        <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-50 to-slate-100 border border-slate-200 flex items-center justify-center text-[#003380] shadow-sm backdrop-blur-md">
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