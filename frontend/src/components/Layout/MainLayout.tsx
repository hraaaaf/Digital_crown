import React from 'react';
import { Sidebar } from '../Sidebar';
import { Header } from '../Header';

interface LayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<LayoutProps> = ({ children }) => {
  return (
    // Rigueur CTO : Flex-Row conservé, passage au thème Clinical Premium Light
    <div className="flex flex-row h-screen overflow-hidden font-sans selection:bg-[#003380] selection:text-white relative bg-[#f8fafc] text-slate-800">
      
      {/* BACKGROUND CLINICAL PREMIUM LIGHT : Halos doux et clairs */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        
        {/* Halo 1 : Haut Gauche (Lumière clinique bleutée) */}
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] rounded-full bg-blue-100/50 blur-[100px]" />
        
        {/* Halo 2 : Bas Droite (Reflet argenté/perle) */}
        <div className="absolute -bottom-[10%] -right-[10%] w-[30%] h-[50%] rounded-full bg-slate-200/50 blur-[120px]" />
        
      </div>
      
      {/* GAUCHE : NAVIGATION LATÉRALE (Z-index 50) */}
      <Sidebar />

      {/* DROITE : HEADER + ESPACE DE TRAVAIL */}
      <div className="flex-1 flex flex-col relative z-10 overflow-hidden">
        
        {/* HEADER INDÉPENDANT (Profil et Statuts) */}
        <Header />

        {/* ZONE DE CONTENU PRINCIPALE */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden p-8 pt-0 flex flex-col custom-scrollbar">
          
          {/* CONTENU ENVELOPPÉ DANS UN PANNEAU GLASSMORPHISM CLAIR */}
          <div className="flex-1 rounded-3xl bg-white/80 border border-slate-200/60 backdrop-blur-xl shadow-[0_8px_40px_rgba(0,0,0,0.04)] p-6">
            {children}
          </div>
          
        </main>

      </div>
    </div>
  );
};