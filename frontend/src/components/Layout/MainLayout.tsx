import React, { useEffect } from 'react';
import { Sidebar } from '../Sidebar';
import { Header } from '../Header';
import { cabinetApi } from '../../services/templateApi';
import { safeStorage } from '../../hooks/useLocalStorage';
import { useEliteStore } from '../../stores/useEliteStore';
import { useLocation } from 'react-router-dom';

import { motion, AnimatePresence } from 'framer-motion';

interface LayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<LayoutProps> = ({ children }) => {
  const isDemoMode = safeStorage.get('appMode') === 'demo';
  const { fetchPatientIntelligence } = useEliteStore();
  const location = useLocation();
  
  // Détection du patient_id dans l'URL pour rafraîchir l'intelligence
  useEffect(() => {
    const match = location.pathname.match(/\/patients\/(\d+)/);
    if (match && match[1]) {
      fetchPatientIntelligence(parseInt(match[1], 10));
    }
  }, [location.pathname, fetchPatientIntelligence]);

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
    safeStorage.remove('appMode');
    window.location.href = '/welcome';
  };

  return (
    <div className="flex flex-row h-screen overflow-hidden font-sans selection:bg-primary selection:text-white relative bg-medical-pearl" style={{ color: 'var(--text-main)' }}>
      
      {/* BACKGROUND DYNAMIQUE */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-primary/10 blur-[100px]" />
        <div className="absolute -bottom-[10%] -right-[10%] w-[30%] h-[50%] rounded-full opacity-20 blur-[120px]" style={{ backgroundColor: 'var(--accent)' }} />
      </div>
      
      <Sidebar />

      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        <Header />

        <main className="flex-1 overflow-y-auto overflow-x-hidden p-8 pt-0 flex flex-col custom-scrollbar">
          {isDemoMode && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 bg-primary/10 border border-primary/20 p-2 px-6 rounded-full flex items-center justify-between"
            >
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
            </motion.div>
          )}
          
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="flex-1 rounded-elite border backdrop-blur-xl shadow-elite p-6 transition-elite"
              style={{ 
                backgroundColor: 'var(--glass-bg)',
                borderColor: 'var(--glass-border)'
              }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};