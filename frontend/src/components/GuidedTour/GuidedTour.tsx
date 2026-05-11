import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  X, ChevronRight, ChevronLeft, Map, Sparkles,
  CheckCircle2, Play, SkipForward
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { TOUR_STEPS, TOUR_STORAGE_KEY, TOUR_VERSION, type TourStep } from './tourConfig';

// ─── Tooltip Flèche par placement ──────────────────────────────────────────────
const PLACEMENT_CLASSES: Record<string, string> = {
  top:    '-bottom-2 left-1/2 -translate-x-1/2 rotate-180',
  bottom: '-top-2 left-1/2 -translate-x-1/2',
  left:   '-right-2 top-1/2 -translate-y-1/2 rotate-90',
  right:  '-left-2 top-1/2 -translate-y-1/2 -rotate-90',
  center: 'hidden',
};

// ─── Composant Principal ────────────────────────────────────────────────────────
interface GuidedTourProps {
  isOpen: boolean;
  onClose: () => void;
  startFromStep?: number;
}

export const GuidedTour: React.FC<GuidedTourProps> = ({
  isOpen, onClose, startFromStep = 0,
}) => {
  const [currentIdx, setCurrentIdx] = useState(startFromStep);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const navigate = useNavigate();
  const cardRef = useRef<HTMLDivElement>(null);

  const step = TOUR_STEPS[currentIdx];
  const isFirst = currentIdx === 0;
  const isLast = currentIdx === TOUR_STEPS.length - 1;
  const progress = ((currentIdx + 1) / TOUR_STEPS.length) * 100;

  // Catégories uniques pour la barre de progression segmentée
  const categories = [...new Set(TOUR_STEPS.map(s => s.category))];

  // Navigation vers la page associée à l'étape
  const navigateToStepPage = useCallback(async (s: TourStep) => {
    if (window.location.pathname !== s.page) {
      setIsNavigating(true);
      navigate(s.page);
      await new Promise(r => setTimeout(r, 400));
      setIsNavigating(false);
    }
  }, [navigate]);

  // Résolution du rectangle cible (pour le spotlight)
  const resolveTarget = useCallback((s: TourStep) => {
    if (!s.targetSelector) { setTargetRect(null); return; }
    const el = document.querySelector(s.targetSelector);
    if (el) setTargetRect(el.getBoundingClientRect());
    else setTargetRect(null);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    navigateToStepPage(step).then(() => resolveTarget(step));
  }, [currentIdx, isOpen]);

  const goNext = () => {
    if (isLast) { handleComplete(); return; }
    setCurrentIdx(i => i + 1);
  };

  const goPrev = () => {
    if (isFirst) return;
    setCurrentIdx(i => i - 1);
  };

  const jumpTo = (idx: number) => setCurrentIdx(idx);

  const handleComplete = () => {
    localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
    onClose();
  };

  const handleSkip = () => {
    localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
    onClose();
  };

  if (!isOpen) return null;

  // Calcul de la position de la card selon le placement
  const getCardStyle = (): React.CSSProperties => {
    if (!targetRect || step.placement === 'center' || step.isPageIntro) {
      return {
        top: '50%',
        left: '50%',
        zIndex: 100001,
        maxWidth: '560px',
        width: '90vw',
        maxHeight: '90vh',
      };
    }
    const margin = 20;
    const cardW = 480;
    const cardH = 400; // estimation

    switch (step.placement) {
      case 'bottom': return {
        position: 'fixed',
        top: targetRect.bottom + margin,
        left: Math.min(targetRect.left, window.innerWidth - cardW - margin),
        zIndex: 100001, width: cardW, maxHeight: '90vh',
      };
      case 'top': return {
        position: 'fixed',
        top: Math.max(margin, targetRect.top - cardH - margin),
        left: Math.min(targetRect.left, window.innerWidth - cardW - margin),
        zIndex: 100001, width: cardW, maxHeight: '90vh',
      };
      case 'right': return {
        position: 'fixed',
        top: Math.max(margin, targetRect.top),
        left: targetRect.right + margin,
        zIndex: 100001, width: cardW, maxHeight: '90vh',
      };
      case 'left': return {
        position: 'fixed',
        top: Math.max(margin, targetRect.top),
        left: targetRect.left - cardW - margin,
        zIndex: 100001, width: cardW, maxHeight: '90vh',
      };
      default: return {
        position: 'fixed', top: '50%', left: '50%',
        zIndex: 100001, width: '90vw', maxWidth: '560px',
        maxHeight: '90vh',
      };
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* ── OVERLAY AVEC DÉCOUPE SPOTLIGHT ─────────────────────────── */}
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 z-[100000] pointer-events-auto"
            style={{ background: 'rgba(0, 0, 0, 0.72)', backdropFilter: 'blur(4px)' }}
            onClick={(e) => { if (e.target === e.currentTarget) handleSkip(); }}
          >
            {/* Spotlight sur l'élément cible */}
            {targetRect && !step.isPageIntro && (
              <motion.div
                key={`spotlight-${currentIdx}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                style={{
                  position: 'absolute',
                  top: targetRect.top - 8,
                  left: targetRect.left - 8,
                  width: targetRect.width + 16,
                  height: targetRect.height + 16,
                  borderRadius: 20,
                  boxShadow: '0 0 0 9999px rgba(0,0,0,0.72), 0 0 40px rgba(var(--primary-rgb, 0,51,128), 0.5)',
                  border: '2px solid var(--primary)',
                  pointerEvents: 'none',
                }}
              />
            )}

            {/* Pulse beacon sur l'élément ciblé */}
            {targetRect && !step.isPageIntro && (
              <motion.div
                key={`beacon-${currentIdx}`}
                initial={{ scale: 0 }}
                animate={{ scale: [0, 1.4, 1] }}
                transition={{ duration: 0.5, delay: 0.2 }}
                style={{
                  position: 'absolute',
                  top: targetRect.top - 16,
                  left: targetRect.left - 16,
                  width: 32,
                  height: 32,
                  borderRadius: '50%',
                  background: 'var(--primary)',
                  opacity: 0.9,
                  pointerEvents: 'none',
                  animation: 'tour-beacon-pulse 1.5s ease-in-out infinite',
                }}
              />
            )}
          </motion.div>

          {/* ── CARD PRINCIPALE ─────────────────────────────────────────── */}
          <div 
            className={cn(
              "fixed z-[100001] pointer-events-none flex",
              (!targetRect || step.placement === 'center' || step.isPageIntro) 
                ? "inset-0 items-center justify-center p-4" 
                : ""
            )}
          >
            <motion.div
              key={`card-${currentIdx}`}
              ref={cardRef}
              style={(!targetRect || step.placement === 'center' || step.isPageIntro) ? { maxWidth: '560px', width: '100%', maxHeight: '90vh' } : getCardStyle()}
              initial={{ opacity: 0, y: 20, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.98 }}
              transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
              className="rounded-[2rem] overflow-hidden shadow-[0_40px_120px_rgba(0,0,0,0.5)] pointer-events-auto flex flex-col"
            >
            {/* Arrière-plan glassmorphisme */}
            <div
              className="relative flex flex-col max-h-[90vh]"
              style={{
                background: 'linear-gradient(135deg, rgba(255,255,255,0.97) 0%, rgba(240,245,255,0.97) 100%)',
                backdropFilter: 'blur(40px)',
              }}
            >
              {/* Décoration orbe premium */}
              <div
                className="absolute -top-20 -right-20 w-64 h-64 rounded-full pointer-events-none"
                style={{ background: 'radial-gradient(circle, var(--primary) 0%, transparent 70%)', opacity: 0.08 }}
              />
              <div
                className="absolute -bottom-16 -left-16 w-48 h-48 rounded-full pointer-events-none"
                style={{ background: 'radial-gradient(circle, var(--primary) 0%, transparent 70%)', opacity: 0.05 }}
              />

              {/* ─ EN-TÊTE ─────────────────────────────────────────────── */}
              <div className="relative px-8 pt-7 pb-5 border-b border-slate-100/80">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-4">
                    {/* Icône step */}
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shrink-0 shadow-lg"
                      style={{
                        background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 70%, #6366f1) 100%)',
                        boxShadow: '0 8px 24px -4px color-mix(in srgb, var(--primary) 40%, transparent)',
                      }}
                    >
                      {step.icon}
                    </div>

                    <div>
                      {/* Catégorie */}
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em]" style={{ color: 'var(--primary)' }}>
                          {step.category}
                        </span>
                        {step.badge && (
                          <span
                            className="px-2 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest text-white"
                            style={{
                              background: 'linear-gradient(90deg, var(--primary), color-mix(in srgb, var(--primary) 60%, #6366f1))',
                            }}
                          >
                            {step.badge}
                          </span>
                        )}
                      </div>
                      <h3 className="text-xl font-black text-slate-900 leading-tight">{step.title}</h3>
                      <p className="text-sm font-bold text-slate-500 mt-0.5">{step.subtitle}</p>
                    </div>
                  </div>

                  {/* Bouton fermer */}
                  <button
                    onClick={handleSkip}
                    className="shrink-0 w-9 h-9 rounded-xl bg-slate-100 hover:bg-red-50 hover:text-red-500 flex items-center justify-center transition-all text-slate-400"
                    title="Fermer le guide"
                  >
                    <X size={16} />
                  </button>
                </div>

                {/* Barre de progression */}
                <div className="mt-5 space-y-2">
                  <div className="flex items-center justify-between text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    <span className="flex items-center gap-1.5">
                      <Map size={11} />
                      Étape {currentIdx + 1} / {TOUR_STEPS.length}
                    </span>
                    <span>{Math.round(progress)}% complété</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-100 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full"
                      style={{ background: 'linear-gradient(90deg, var(--primary), color-mix(in srgb, var(--primary) 60%, #6366f1))' }}
                      initial={{ width: `${((currentIdx) / TOUR_STEPS.length) * 100}%` }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </div>
              </div>

              {/* ─ CONTENU (Scrollable if needed) ────────────────────── */}
              <div className="px-8 py-6 overflow-y-auto custom-scrollbar flex-1">
                <p className="text-sm font-medium text-slate-600 leading-relaxed">
                  {step.description}
                </p>

                {step.features && step.features.length > 0 && (
                  <motion.ul
                    className="mt-5 space-y-2.5"
                    initial="hidden"
                    animate="visible"
                    variants={{
                      hidden: {},
                      visible: { transition: { staggerChildren: 0.06 } },
                    }}
                  >
                    {step.features.map((f, i) => (
                      <motion.li
                        key={i}
                        variants={{
                          hidden: { opacity: 0, x: -10 },
                          visible: { opacity: 1, x: 0 },
                        }}
                        className="flex items-start gap-3 text-sm"
                      >
                        <div
                          className="mt-0.5 w-5 h-5 rounded-lg flex items-center justify-center shrink-0"
                          style={{ background: 'color-mix(in srgb, var(--primary) 12%, transparent)' }}
                        >
                          <CheckCircle2 size={12} style={{ color: 'var(--primary)' }} />
                        </div>
                        <span className="font-medium text-slate-700 leading-snug">{f}</span>
                      </motion.li>
                    ))}
                  </motion.ul>
                )}
              </div>

              {/* ─ NAVIGATION MINI (points) ────────────────────────────── */}
              <div className="px-8 pb-2 flex items-center gap-1.5 overflow-x-auto">
                {TOUR_STEPS.map((s, i) => (
                  <button
                    key={s.id}
                    onClick={() => jumpTo(i)}
                    title={s.title}
                    className={cn(
                      'transition-all rounded-full shrink-0',
                      i === currentIdx
                        ? 'w-6 h-2'
                        : i < currentIdx
                          ? 'w-2 h-2'
                          : 'w-2 h-2 opacity-30',
                    )}
                    style={{
                      background: i <= currentIdx ? 'var(--primary)' : '#cbd5e1',
                    }}
                  />
                ))}
              </div>

              {/* ─ FOOTER NAVIGATION ───────────────────────────────────── */}
              <div className="px-8 pb-7 pt-4 flex items-center justify-between gap-4 border-t border-slate-100/80 mt-2">
                {/* Bouton Précédent */}
                <button
                  onClick={goPrev}
                  disabled={isFirst}
                  className={cn(
                    'flex items-center gap-2 px-5 py-2.5 rounded-2xl text-sm font-bold transition-all border',
                    isFirst
                      ? 'opacity-0 pointer-events-none'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 active:scale-95',
                  )}
                >
                  <ChevronLeft size={16} />
                  Précédent
                </button>

                {/* Centre : Skip */}
                <button
                  onClick={handleSkip}
                  className="flex items-center gap-1.5 text-[11px] font-black text-slate-400 hover:text-slate-600 uppercase tracking-widest transition-colors"
                >
                  <SkipForward size={12} />
                  Passer le tour
                </button>

                {/* Bouton Suivant / Terminer */}
                <button
                  onClick={goNext}
                  disabled={isNavigating}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-2xl text-sm font-black text-white transition-all active:scale-95 shadow-lg"
                  style={{
                    background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 70%, #6366f1) 100%)',
                    boxShadow: '0 8px 20px -4px color-mix(in srgb, var(--primary) 35%, transparent)',
                  }}
                >
                  {isLast ? (
                    <>
                      <Sparkles size={15} />
                      Commencer !
                    </>
                  ) : (
                    <>
                      Suivant
                      <ChevronRight size={16} />
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </div>

          {/* ── STYLES ANIMATION BEACON ────────────────────────────────── */}
          <style>{`
            @keyframes tour-beacon-pulse {
              0%, 100% { transform: scale(1); opacity: 0.9; }
              50% { transform: scale(1.6); opacity: 0.3; }
            }
          `}</style>
        </>
      )}
    </AnimatePresence>
  );
};
