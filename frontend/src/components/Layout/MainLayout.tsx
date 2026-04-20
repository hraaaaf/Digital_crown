import React, { useEffect } from 'react';
import { Sidebar } from '../Sidebar';
import { Header } from '../Header';
import { cabinetApi } from '../../services/templateApi';

interface LayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<LayoutProps> = ({ children }) => {
  const isDemoMode = localStorage.getItem('appMode') === 'demo';

  // Rigueur CTO : Application du thème persisté au chargement
  useEffect(() => {
    if (isDemoMode) {
      const updateDemoTheme = () => {
        const storedDemo = sessionStorage.getItem('demoConfig');
        if (storedDemo) {
          try {
            const demoData = JSON.parse(storedDemo);
            document.body.dataset.theme = (demoData.selected_theme && demoData.selected_theme !== 'elite') 
              ? demoData.selected_theme 
              : '';
            
            // Injection des couleurs de démo si présentes
            if (demoData.primary_color) document.documentElement.style.setProperty('--primary', demoData.primary_color);
            if (demoData.secondary_color) document.documentElement.style.setProperty('--secondary', demoData.secondary_color);
            if (demoData.accent_color) document.documentElement.style.setProperty('--accent', demoData.accent_color);
          } catch (e) {}
        }
      };
      
      updateDemoTheme();
      const interval = setInterval(updateDemoTheme, 1000);
      return () => clearInterval(interval);
    }

    const loadTheme = async () => {
      try {
        const config = await cabinetApi.getMine();
        document.body.dataset.theme = (config.selected_theme && config.selected_theme !== 'elite') ? config.selected_theme : '';
        
        // Système de propagation atomique des couleurs d'identité
        if (config.primary_color) document.documentElement.style.setProperty('--primary', config.primary_color);
        if (config.secondary_color) document.documentElement.style.setProperty('--secondary', config.secondary_color);
        if (config.accent_color) document.documentElement.style.setProperty('--accent', config.accent_color);
        
      } catch (error) {
        console.error("Erreur chargement thème:", error);
      }
    };
    loadTheme();
  }, [isDemoMode]);

  const handleExitDemo = () => {
    localStorage.removeItem('appMode');
    window.location.href = '/welcome';
  };

  return (
    <div className="flex flex-row h-screen overflow-hidden font-sans selection:bg-primary selection:text-white relative bg-medical-pearl text-slate-800">
      
      {/* BACKGROUND DYNAMIQUE */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-[100px]" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[30%] h-[50%] rounded-full bg-slate-200/40 blur-[120px]" />
      </div>
      
      <Sidebar />

      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto overflow-x-hidden p-8 pt-0 flex flex-col custom-scrollbar">
          {isDemoMode && (
            <div className="mb-4 bg-primary/10 border border-primary/20 p-2 px-6 rounded-full flex items-center justify-between animate-in slide-in-from-top-4 duration-500">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                <span className="text-[10px] font-black uppercase tracking-widest text-primary">Mode Exploration Actif</span>
              </div>
              <button 
                onClick={handleExitDemo}
                className="text-[10px] font-bold text-primary hover:underline"
              >
                Quitter la démo
              </button>
            </div>
          )}
          
          <div className="flex-1 rounded-3xl bg-white/80 border border-slate-200/60 backdrop-blur-xl shadow-[0_8px_40px_rgba(0,0,0,0.04)] p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};