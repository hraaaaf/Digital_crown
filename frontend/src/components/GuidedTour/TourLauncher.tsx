import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Compass } from 'lucide-react';
import { cn } from '../../utils/cn';
import { GuidedTour } from './GuidedTour';
import { TOUR_STORAGE_KEY } from './tourConfig';

/**
 * TourLauncher — Bouton flottant + auto-lancement au premier usage.
 * À placer une seule fois dans le MainLayout.
 */
interface TourLauncherProps {
  isEmbedded?: boolean;
}

export const TourLauncher: React.FC<TourLauncherProps> = ({ isEmbedded = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem(TOUR_STORAGE_KEY);
    if (!completed) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
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

  const launcherContent = (
    <>
      <GuidedTour isOpen={isOpen} onClose={handleClose} />

      {/* Bouton flottant */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            key="tour-launcher"
            initial={{ opacity: 0, scale: 0.6, y: isEmbedded ? -20 : 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.6, y: isEmbedded ? -20 : 20 }}
            className={cn(
              isEmbedded ? "relative" : "fixed bottom-8 right-32 z-[499]"
            )}
          >
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setIsOpen(true)}
              className="group relative p-2.5 rounded-xl flex items-center justify-center text-slate-400 hover:text-primary hover:bg-white/80 dark:hover:bg-slate-800 transition-all duration-300 pointer-events-auto"
            >
              <Compass size={20} className="relative z-10 group-hover:scale-110 transition-transform duration-300" />
              {/* Badge "Nouveau" */}
              {isFirstVisit && (
                <span className="absolute top-2 right-2 w-2 h-2 bg-amber-400 rounded-full border-2 border-white dark:border-slate-800 animate-pulse" />
              )}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );

  return launcherContent;
};
