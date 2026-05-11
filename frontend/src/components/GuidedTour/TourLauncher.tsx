import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Map, Sparkles, ChevronRight } from 'lucide-react';
import { GuidedTour } from './GuidedTour';
import { TOUR_STORAGE_KEY, TOUR_VERSION } from './tourConfig';

/**
 * TourLauncher — Bouton flottant + auto-lancement au premier usage.
 * À placer une seule fois dans le MainLayout.
 */
export const TourLauncher: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showBadge, setShowBadge] = useState(false);

  useEffect(() => {
    // Auto-lancement au premier accès (jamais vu le tour)
    const completed = localStorage.getItem(TOUR_STORAGE_KEY);
    if (!completed) {
      // Petit délai pour laisser le layout se charger
      const timer = setTimeout(() => setIsOpen(true), 1200);
      return () => clearTimeout(timer);
    } else {
      // Tour déjà complété → affiche juste le bouton sans notification
      setShowBadge(false);
    }
  }, []);

  return (
    <>
      {/* Tour modal */}
      <GuidedTour isOpen={isOpen} onClose={() => setIsOpen(false)} />

      {/* Bouton flottant "Lancer le Tour" */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            key="tour-launcher"
            initial={{ opacity: 0, scale: 0.7, x: 40 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.7, x: 40 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1], delay: 0.3 }}
            className="fixed bottom-8 right-8 z-[9999]"
          >
            <button
              onClick={() => setIsOpen(true)}
              className="group relative flex items-center gap-3 px-5 py-3.5 rounded-2xl text-white text-sm font-black shadow-2xl transition-all hover:scale-105 active:scale-95"
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 65%, #6366f1) 100%)',
                boxShadow: '0 12px 40px -8px color-mix(in srgb, var(--primary) 50%, transparent)',
              }}
              title="Lancer le guide interactif"
            >
              {/* Orbe animée en arrière-plan */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                style={{
                  background: 'linear-gradient(135deg, color-mix(in srgb, var(--primary) 80%, #6366f1) 0%, var(--primary) 100%)',
                }}
              />

              <span className="relative z-10 flex items-center gap-2.5">
                <Map size={16} className="shrink-0" />
                <span className="hidden sm:block">Guide Interactif</span>
                <ChevronRight size={14} className="opacity-70 group-hover:translate-x-0.5 transition-transform" />
              </span>

              {/* Badge "Nouveau" si tour non vu */}
              {showBadge && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-amber-400 border-2 border-white flex items-center justify-center"
                >
                  <Sparkles size={10} className="text-white" />
                </motion.div>
              )}

              {/* Pulse ring animation */}
              <div
                className="absolute inset-0 rounded-2xl animate-ping opacity-20 pointer-events-none"
                style={{ background: 'var(--primary)', animationDuration: '2.5s' }}
              />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
