import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { MousePointer2, X, Sparkles } from 'lucide-react';

interface DemoStep {
  path?: string;
  targetSelector?: string;
  x?: number; // relative to window width (0-100)
  y?: number; // relative to window height (0-100)
  message: string;
  title: string;
  duration: number;
}

const DEMO_STEPS: DemoStep[] = [
  {
    path: '/dashboard',
    title: 'Bienvenue sur Digital Crown',
    message: 'Le système complet de gestion. L\'écosystème IA qui transforme votre cabinet en une clinique de classe mondiale.',
    x: 50, y: 30,
    duration: 4000
  },
  {
    path: '/patients',
    title: 'Base de Données Épurée',
    message: 'Une interface professionnelle, sans fioritures : nom, prénom, assurance et contact. Droit au but.',
    duration: 4500
  },
  {
    path: '/patients/1',
    title: 'Dossier Patient 360°',
    message: 'Une vue holistique : Odontogramme en temps réel, Alertes médicales, Facturation, et Analyses IA.',
    x: 50, y: 40,
    duration: 4500
  },
  {
    path: '/patients/1?tab=radiology',
    title: 'Agent Vision X-Ray',
    message: 'Notre pipeline Loki-Silvres V8 analyse vos panoramiques en 1 milliseconde avec une précision SOTA.',
    x: 70, y: 60,
    duration: 4500
  },
  {
    path: '/patients/1?tab=radiology',
    title: 'Génération Déterministe',
    message: 'Sécurité médico-légale absolue : les rapports cliniques et ordonnances sont générés sans aucune hallucination.',
    x: 50, y: 80,
    duration: 4500
  }
];

export const MarketingDemo: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [cursorPos, setCursorPos] = useState({ x: window.innerWidth / 2, y: window.innerHeight / 2 });
  const navigate = useNavigate();
  const location = useLocation();

  // Listen for the secret keyboard shortcut to start demo (Ctrl + Shift + D)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        setIsActive(prev => {
          if (!prev) setCurrentStep(0);
          return !prev;
        });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (!isActive) return;

    const step = DEMO_STEPS[currentStep];
    if (!step) {
      // Fin de la démo
      setTimeout(() => setIsActive(false), 2000);
      return;
    }

    // 1. Navigation
    if (step.path && location.pathname !== step.path) {
      navigate(step.path);
    }

    // 2. Position du curseur
    let targetX = (window.innerWidth * (step.x || 50)) / 100;
    let targetY = (window.innerHeight * (step.y || 50)) / 100;

    if (step.targetSelector) {
      const selector = step.targetSelector;
      setTimeout(() => {
        const el = document.querySelector(selector);
        if (el) {
          const rect = el.getBoundingClientRect();
          setCursorPos({
            x: rect.left + rect.width / 2,
            y: rect.top + rect.height / 2
          });
        }
      }, 500);
    } else {
      setCursorPos({ x: targetX, y: targetY });
    }

    // 3. Auto-avance
    const timer = setTimeout(() => {
      setCurrentStep(prev => prev + 1);
    }, step.duration);

    return () => clearTimeout(timer);
  }, [isActive, currentStep, navigate, location.pathname]);

  if (!isActive) return null;

  const currentStepData = DEMO_STEPS[currentStep];

  return (
    <div className="fixed inset-0 z-[9999] pointer-events-none overflow-hidden">
      {/* Overlay protecteur */}
      <div className="absolute inset-0 pointer-events-auto cursor-none bg-slate-900/10 backdrop-blur-[2px]" />
      
      {/* Curseur fantôme */}
      <motion.div
        animate={{ x: cursorPos.x, y: cursorPos.y }}
        transition={{ type: "spring", stiffness: 40, damping: 20, mass: 1 }}
        className="absolute top-0 left-0 flex items-center justify-center pointer-events-none z-[10000]"
        style={{ translateX: '-50%', translateY: '-50%' }}
      >
        <div className="relative">
          <MousePointer2 className="text-white drop-shadow-lg w-10 h-10 relative z-10" fill="#4f46e5" />
          <motion.div
            animate={{ scale: [1, 1.8, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-indigo-500 rounded-full blur-md -z-10"
          />
        </div>
      </motion.div>

      {/* Panneau d'explication */}
      <AnimatePresence mode="wait">
        {currentStepData && (
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -30, scale: 0.95 }}
            className="absolute bottom-12 left-1/2 -translate-x-1/2 bg-slate-900/95 backdrop-blur-xl border border-white/10 p-6 rounded-3xl shadow-2xl max-w-lg w-[90%] pointer-events-auto"
          >
            <button 
              onClick={() => setIsActive(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                <Sparkles size={24} />
              </div>
              <div className="flex-1">
                <h3 className="text-white font-bold text-xl leading-tight">{currentStepData.title}</h3>
                <div className="flex gap-1.5 mt-2">
                  {DEMO_STEPS.map((_, i) => (
                    <div key={i} className={`h-1.5 rounded-full transition-all ${i === currentStep ? 'w-6 bg-indigo-500' : 'w-2 bg-slate-700'}`} />
                  ))}
                </div>
              </div>
            </div>
            <p className="text-slate-300 font-medium text-lg leading-relaxed">{currentStepData.message}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
