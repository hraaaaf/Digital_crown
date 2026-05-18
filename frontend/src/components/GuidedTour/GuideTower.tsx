import React, { useState, useRef, useEffect } from 'react';
import { Compass, X, Info } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

export const GuideTower: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getPageGuide = (pathname: string) => {
    if (pathname.includes('/dashboard')) {
      return {
        title: "Dashboard",
        desc: "Centre de pilotage. Affiche les statistiques clés (nouveaux patients, actes réalisés) et donne accès aux actions rapides comme la création d'un patient."
      };
    }
    if (pathname.includes('/patients') && pathname.split('/').length === 3) {
      return {
        title: "Dossier Patient",
        desc: "Dossier clinique complet. Gérez les informations, téléversez des radios pour analyse IA (Céphalométrie, Panoramique), et générez des documents (ordonnances, devis, consentements) depuis le hub documentaire."
      };
    }
    if (pathname.includes('/patients')) {
      return {
        title: "Liste des Patients",
        desc: "Recherchez rapidement un patient, accédez à son dossier, ou ajoutez un nouveau patient. Le système détecte automatiquement les doublons pour garder votre base saine."
      };
    }
    if (pathname.includes('/agenda')) {
      return {
        title: "Studio Agenda",
        desc: "Planning intelligent. Vous pouvez ajouter, modifier ou annuler des rendez-vous. La détection des conflits vous empêche de planifier deux rendez-vous en même temps."
      };
    }
    if (pathname.includes('/accounting')) {
      return {
        title: "Ghost Treasury",
        desc: "Pôle comptabilité. Suivez le chiffre d'affaires, gérez les paiements (totaux ou partiels), consultez les plans de traitement et effectuez des relances sur les impayés."
      };
    }
    if (pathname.includes('/bibliotheque')) {
      return {
        title: "Bibliothèque",
        desc: "Votre base de connaissances clinique. Recherchez des actes, des protocoles médicaux ou des modèles de documents préconfigurés."
      };
    }
    if (pathname.includes('/settings')) {
      return {
        title: "Paramètres (Settings)",
        desc: "Configuration du cabinet. Modifiez vos informations, le design des documents (templates, logos, couleurs), vos identifiants légaux et l'accès des praticiens."
      };
    }

    return {
      title: "Page Inconnue",
      desc: "Digital Crown est à votre service. Utilisez le menu latéral pour naviguer dans les différents modules."
    };
  };

  const guide = getPageGuide(location.pathname);

  return (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 text-slate-400 hover:text-primary hover:bg-primary/5 rounded-elite-sm transition-elite group"
        title="Guide Tower (Aide contextuelle)"
      >
        <Compass size={20} className="group-hover:scale-110 transition-elite" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute top-full right-0 mt-3 w-80 bg-card-bg border border-border-main rounded-3xl shadow-elite p-5 z-50 backdrop-blur-xl"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <Info size={16} />
                </div>
                <div>
                  <h4 className="text-[10px] font-black text-text-muted uppercase tracking-widest leading-none">Guide Tower</h4>
                  <h3 className="text-sm font-black text-primary mt-1">{guide.title}</h3>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="text-text-muted hover:text-red-500 transition-colors">
                <X size={16} />
              </button>
            </div>
            <div className="bg-medical-pearl rounded-2xl p-4 border border-border-main mt-3">
              <p className="text-xs font-semibold text-main leading-relaxed">
                {guide.desc}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
