import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Compass, Sparkles } from 'lucide-react';
import { GuidedTour } from './GuidedTour';
import { TOUR_STORAGE_KEY } from './tourConfig';

/**
 * TourLauncher — Bouton flottant + auto-lancement au premier usage.
 * À placer une seule fois dans le MainLayout.
 */
export const TourLauncher: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem(TOUR_STORAGE_KEY);
    if (!completed) {
      setIsFirstVisit(true);
      // Auto-lancement au premier accès (délai pour le layout)
      const timer = setTimeout(() => setIsOpen(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleClose = () => {
    setIsOpen(false);
    setIsFirstVisit(false);
  };

  return (
    <>
      <GuidedTour isOpen={isOpen} onClose={handleClose} />

      {/* Bouton flottant */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            key="tour-launcher"
            initial={{ opacity: 0, scale: 0.6, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.6, y: 20 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1], delay: 0.5 }}
            className="fixed bottom-6 right-6 z-[9999]"
          >
            <button
              onClick={() => setIsOpen(true)}
              className="group relative flex items-center gap-2.5 pl-4 pr-5 py-3 rounded-2xl text-white text-[13px] font-black transition-all hover:scale-[1.03] active:scale-95"
              style={{
                background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 60%, #6366f1) 100%)',
                boxShadow: '0 10px 32px -6px color-mix(in srgb, var(--primary) 45%, transparent)',
              }}
              title="Lancer le guide interactif"
            >
              {/* Hover overlay */}
              <div
                className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-400"
                style={{ background: 'linear-gradient(135deg, color-mix(in srgb, var(--primary) 80%, #6366f1) 0%, var(--primary) 100%)' }}
              />

              <span className="relative z-10 flex items-center gap-2">
                <Compass size={15} className="shrink-0" />
                <span className="hidden sm:block">Guide</span>
              </span>

              {/* Badge "Nouveau" pour première visite */}
              {isFirstVisit && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-amber-400 border-2 border-white flex items-center justify-center z-20"
                >
                  <Sparkles size={8} className="text-white" />
                </motion.div>
              )}

              {/* Pulse ring subtil */}
              {isFirstVisit && (
                <div
                  className="absolute inset-0 rounded-2xl animate-ping opacity-15 pointer-events-none"
                  style={{ background: 'var(--primary)', animationDuration: '3s' }}
                />
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
