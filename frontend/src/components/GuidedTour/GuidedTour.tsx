import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  X, ChevronRight, ChevronLeft, Sparkles,
  CheckCircle2, Compass
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { TOUR_STEPS, TOUR_CATEGORIES, TOUR_STORAGE_KEY, TOUR_VERSION, type TourStep } from './tourConfig';
import { api } from '../../services/api';

// ─── Types ──────────────────────────────────────────────────────────────────────
interface SpotlightRect {
  x: number; y: number; w: number; h: number;
}

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
  const [spotlight, setSpotlight] = useState<SpotlightRect | null>(null);
  const [isNavigating, setIsNavigating] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [firstPatientId, setFirstPatientId] = useState<number | null>(null);
  const navigate = useNavigate();
  const cardRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<MutationObserver | null>(null);

  const step = TOUR_STEPS[currentIdx];
  const isFirst = currentIdx === 0;
  const isLast = currentIdx === TOUR_STEPS.length - 1;
  // const progress = ((currentIdx + 1) / TOUR_STEPS.length) * 100;

  // ─── Résolution dynamique du premier patient ──────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    api.get('/patients/?skip=0&limit=1')
      .then(res => {
        const patients = res.data;
        if (Array.isArray(patients) && patients.length > 0) {
          setFirstPatientId(patients[0].id);
        }
      })
      .catch(() => setFirstPatientId(null));
  }, [isOpen]);

  // ─── Résolution de la route effective ─────────────────────────────────────
  const getEffectivePage = useCallback((s: TourStep): string => {
    if (s.pageDynamic && firstPatientId) {
      return `/patients/${firstPatientId}`;
    }
    return s.page;
  }, [firstPatientId]);

  // ─── PreActions ───────────────────────────────────────────────────────────
  const executePreAction = useCallback((s: TourStep) => {
    if (!s.preAction) return;
    if (s.preAction === 'switch-to-admin-tab') {
      // Inject tab=admin into the URL to show DocumentHub
      const url = new URL(window.location.href);
      url.searchParams.set('tab', 'admin');
      window.history.replaceState({}, '', url.toString());
      // Trigger a popstate to make React Router re-read the URL
      window.dispatchEvent(new PopStateEvent('popstate'));
    }
  }, []);

  // ─── Navigation vers la page ──────────────────────────────────────────────
  const navigateToStepPage = useCallback(async (s: TourStep) => {
    const targetPage = getEffectivePage(s);
    if (window.location.pathname !== targetPage) {
      setIsNavigating(true);
      navigate(targetPage + (s.preAction === 'switch-to-admin-tab' ? '?tab=admin' : ''));
      // Wait for route change and lazy load
      await new Promise(r => setTimeout(r, 500));
      setIsNavigating(false);
    }
    executePreAction(s);
  }, [navigate, getEffectivePage, executePreAction]);

  // ─── Résolution du rectangle cible avec MutationObserver ──────────────────
  const resolveTarget = useCallback((s: TourStep) => {
    if (!s.targetSelector) { setSpotlight(null); return; }

    const tryResolve = () => {
      const el = document.querySelector(s.targetSelector!);
      if (el) {
        const rect = el.getBoundingClientRect();
        setSpotlight({ x: rect.left, y: rect.top, w: rect.width, h: rect.height });
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Re-resolve after scroll settles
        setTimeout(() => {
          const r2 = el.getBoundingClientRect();
          setSpotlight({ x: r2.left, y: r2.top, w: r2.width, h: r2.height });
        }, 400);
        return true;
      }
      return false;
    };

    if (tryResolve()) return;

    // DOM not ready — use MutationObserver
    observerRef.current?.disconnect();
    observerRef.current = new MutationObserver(() => {
      if (tryResolve()) {
        observerRef.current?.disconnect();
      }
    });
    observerRef.current.observe(document.body, { childList: true, subtree: true });

    // Safety timeout — stop observing after 3s
    setTimeout(() => observerRef.current?.disconnect(), 3000);
  }, []);

  // Cleanup observer on unmount
  useEffect(() => () => observerRef.current?.disconnect(), []);

  // ─── Réactivité (scroll/resize) ───────────────────────────────────────────
  useEffect(() => {
    if (!isOpen || !step.targetSelector) return;
    const update = () => {
      const el = document.querySelector(step.targetSelector!);
      if (el) {
        const r = el.getBoundingClientRect();
        setSpotlight({ x: r.left, y: r.top, w: r.width, h: r.height });
      }
    };
    window.addEventListener('scroll', update, true);
    window.addEventListener('resize', update);
    return () => {
      window.removeEventListener('scroll', update, true);
      window.removeEventListener('resize', update);
    };
  }, [currentIdx, isOpen, step.targetSelector]);

  // ─── Navigation step change ───────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    setSpotlight(null);
    navigateToStepPage(step).then(() => {
      setTimeout(() => resolveTarget(step), 150);
    });
  }, [currentIdx, isOpen, navigateToStepPage, resolveTarget, step]);

  // ─── Keyboard ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { handleSkip(); }
      else if (e.key === 'ArrowRight' || e.key === 'Enter') { goNext(); }
      else if (e.key === 'ArrowLeft') { goPrev(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  });

  // ─── Actions ──────────────────────────────────────────────────────────────
  const goNext = () => {
    if (isLast) { handleComplete(); return; }
    setCurrentIdx(i => i + 1);
  };

  const goPrev = () => {
    if (isFirst) return;
    setCurrentIdx(i => i - 1);
  };

  const handleComplete = () => {
    setShowCelebration(true);
    setTimeout(() => {
      localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
      setShowCelebration(false);
      onClose();
    }, 2200);
  };

  const handleSkip = () => {
    localStorage.setItem(TOUR_STORAGE_KEY, TOUR_VERSION);
    onClose();
  };

  // ─── Barre segmentée ─────────────────────────────────────────────────────
  const segmentedProgress = useMemo(() => {
    const cats = TOUR_CATEGORIES;
    return cats.map(cat => {
      const stepsInCat = TOUR_STEPS.filter(s => s.category === cat);
      const firstIdx = TOUR_STEPS.findIndex(s => s.category === cat);
      const lastIdx = firstIdx + stepsInCat.length - 1;
      const isActive = currentIdx >= firstIdx && currentIdx <= lastIdx;
      const isCompleted = currentIdx > lastIdx;
      return { label: cat, isActive, isCompleted, count: stepsInCat.length };
    }).filter(s => s.count > 0);
  }, [currentIdx]);

  // ─── Positionnement de la card ────────────────────────────────────────────
  const getCardStyle = (): React.CSSProperties => {
    if (!spotlight || step.placement === 'center' || step.isPageIntro) {
      return {
        position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        zIndex: 100001, maxWidth: 520, width: '92vw', maxHeight: '90vh',
      };
    }

    const margin = 24;
    const cardW = 420;
    const cardH = cardRef.current?.offsetHeight || 360;

    // Calcul des espaces disponibles
    const spaceBottom = window.innerHeight - (spotlight.y + spotlight.h);
    const spaceTop = spotlight.y;
    const spaceRight = window.innerWidth - (spotlight.x + spotlight.w);
    const spaceLeft = spotlight.x;

    // Choix intelligent du placement
    type Dir = 'bottom' | 'top' | 'right' | 'left';
    const preferred = step.placement as Dir;
    const spaces: Record<Dir, number> = { bottom: spaceBottom, top: spaceTop, right: spaceRight, left: spaceLeft };
    const needs: Record<Dir, number> = { bottom: cardH + margin, top: cardH + margin, right: cardW + margin, left: cardW + margin };

    let dir: Dir = preferred;
    if (spaces[dir] < needs[dir]) {
      // Fallback: pick direction with most space
      dir = (Object.entries(spaces) as [Dir, number][])
        .filter(([d]) => spaces[d] >= needs[d])
        .sort(([, a], [, b]) => b - a)[0]?.[0] || 'bottom';
    }

    const centerX = spotlight.x + spotlight.w / 2;
    const centerY = spotlight.y + spotlight.h / 2;

    switch (dir) {
      case 'bottom': return {
        position: 'fixed',
        top: Math.min(window.innerHeight - cardH - margin, spotlight.y + spotlight.h + margin),
        left: Math.max(margin, Math.min(centerX - cardW / 2, window.innerWidth - cardW - margin)),
        zIndex: 100001, width: cardW, maxHeight: '80vh',
      };
      case 'top': return {
        position: 'fixed',
        top: Math.max(margin, spotlight.y - cardH - margin),
        left: Math.max(margin, Math.min(centerX - cardW / 2, window.innerWidth - cardW - margin)),
        zIndex: 100001, width: cardW, maxHeight: '80vh',
      };
      case 'right': return {
        position: 'fixed',
        top: Math.max(margin, Math.min(centerY - cardH / 2, window.innerHeight - cardH - margin)),
        left: Math.min(window.innerWidth - cardW - margin, spotlight.x + spotlight.w + margin),
        zIndex: 100001, width: cardW, maxHeight: '80vh',
      };
      case 'left': return {
        position: 'fixed',
        top: Math.max(margin, Math.min(centerY - cardH / 2, window.innerHeight - cardH - margin)),
        left: Math.max(margin, spotlight.x - cardW - margin),
        zIndex: 100001, width: cardW, maxHeight: '80vh',
      };
    }
  };

  if (!isOpen) return null;

  // Spotlight padding
  const pad = 10;
  const spotX = spotlight ? spotlight.x - pad : 0;
  const spotY = spotlight ? spotlight.y - pad : 0;
  const spotW = spotlight ? spotlight.w + pad * 2 : 0;
  const spotH = spotlight ? spotlight.h + pad * 2 : 0;

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* ── OVERLAY SVG ANIMÉ ─────────────────────────────────────────── */}
            <div className="fixed inset-0 z-[100000]" style={{ pointerEvents: 'none' }}>
              <svg className="w-full h-full" style={{ pointerEvents: 'none' }}>
                <defs>
                  <mask id="tour-mask">
                    <rect x="0" y="0" width="100%" height="100%" fill="white" />
                    {spotlight && !step.isPageIntro && (
                      <motion.rect
                        initial={{ x: spotX, y: spotY, width: spotW, height: spotH, opacity: 0 }}
                        animate={{ x: spotX, y: spotY, width: spotW, height: spotH, opacity: 1 }}
                        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                        rx="16"
                        fill="black"
                      />
                    )}
                  </mask>
                </defs>
                <rect
                  x="0" y="0" width="100%" height="100%"
                  fill={step.isPageIntro ? "rgba(15, 23, 42, 0.75)" : "rgba(15, 23, 42, 0.6)"}
                  mask="url(#tour-mask)"
                  style={{
                    pointerEvents: 'auto',
                    backdropFilter: step.isPageIntro ? 'blur(12px)' : 'none',
                  }}
                  onClick={handleSkip}
                />
              </svg>

              {/* Spotlight border glow */}
              {spotlight && !step.isPageIntro && (
                <motion.div
                  key={`glow-${currentIdx}`}
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.35, delay: 0.15 }}
                  className="pointer-events-none"
                  style={{
                    position: 'absolute',
                    top: spotY, left: spotX,
                    width: spotW, height: spotH,
                    borderRadius: 16,
                    border: '2px solid var(--primary)',
                    boxShadow: '0 0 30px color-mix(in srgb, var(--primary) 25%, transparent), inset 0 0 20px color-mix(in srgb, var(--primary) 8%, transparent)',
                  }}
                />
              )}
            </div>

            {/* ── CARD ──────────────────────────────────────────────────────── */}
            <div
              className={cn(
                "fixed z-[100001] pointer-events-none flex",
                (!spotlight || step.placement === 'center' || step.isPageIntro)
                  ? "inset-0 items-center justify-center p-6"
                  : ""
              )}
            >
              <motion.div
                key={`card-${currentIdx}`}
                ref={cardRef}
                style={getCardStyle()}
                initial={{ opacity: 0, y: 24, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -12, scale: 0.97 }}
                transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                className="rounded-[1.75rem] overflow-hidden pointer-events-auto flex flex-col"
              >
                <div
                  className="relative flex flex-col max-h-[88vh] overflow-hidden"
                  style={{
                    background: 'linear-gradient(160deg, rgba(255,255,255,0.98) 0%, rgba(248,250,255,0.98) 100%)',
                    boxShadow: '0 32px 80px -12px rgba(0,0,0,0.35), 0 0 0 1px rgba(255,255,255,0.1)',
                    backdropFilter: 'blur(40px)',
                  }}
                >
                  {/* Orbe décorative */}
                  <div
                    className="absolute -top-16 -right-16 w-48 h-48 rounded-full pointer-events-none"
                    style={{ background: 'radial-gradient(circle, var(--primary) 0%, transparent 70%)', opacity: 0.07 }}
                  />

                  {/* ─ HEADER ─────────────────────────────────────────────── */}
                  <div className="relative px-7 pt-6 pb-4">
                    {/* Skip discret (en haut à droite, sous le ✕) */}
                    <div className="absolute top-5 right-5 flex flex-col items-end gap-1.5">
                      <button
                        onClick={handleSkip}
                        className="w-8 h-8 rounded-xl bg-slate-100/80 hover:bg-red-50 hover:text-red-500 flex items-center justify-center transition-all text-slate-400"
                        title="Fermer (Échap)"
                      >
                        <X size={14} />
                      </button>
                      <button
                        onClick={handleSkip}
                        className="text-[9px] font-bold text-slate-300 hover:text-slate-500 uppercase tracking-widest transition-colors"
                      >
                        Passer
                      </button>
                    </div>

                    {/* Icône + Titre */}
                    <div className="flex items-center gap-3.5 pr-20">
                      <div
                        className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0"
                        style={{
                          background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 65%, #6366f1) 100%)',
                          boxShadow: '0 6px 20px -4px color-mix(in srgb, var(--primary) 35%, transparent)',
                        }}
                      >
                        {step.icon}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-[9px] font-black uppercase tracking-[0.2em] truncate" style={{ color: 'var(--primary)' }}>
                            {step.category}
                          </span>
                          {step.badge && (
                            <span
                              className="px-1.5 py-0.5 rounded-md text-[7px] font-black uppercase tracking-wider text-white shrink-0"
                              style={{ background: 'linear-gradient(90deg, var(--primary), color-mix(in srgb, var(--primary) 55%, #6366f1))' }}
                            >
                              {step.badge}
                            </span>
                          )}
                        </div>
                        <h3 className="text-lg font-black text-slate-900 leading-tight truncate">{step.title}</h3>
                        <p className="text-xs font-bold text-slate-400 mt-0.5 truncate">{step.subtitle}</p>
                      </div>
                    </div>

                    {/* Barre segmentée */}
                    <div className="mt-4 flex gap-1">
                      {segmentedProgress.map((seg, i) => (
                        <div key={i} className="flex-1 flex flex-col items-center gap-1">
                          <div
                            className={cn(
                              "w-full h-1 rounded-full transition-all duration-500",
                              seg.isCompleted ? "opacity-100" : seg.isActive ? "opacity-100" : "opacity-20"
                            )}
                            style={{
                              background: seg.isCompleted || seg.isActive
                                ? 'linear-gradient(90deg, var(--primary), color-mix(in srgb, var(--primary) 60%, #6366f1))'
                                : '#cbd5e1',
                            }}
                          />
                          <span className={cn(
                            "text-[7px] font-bold uppercase tracking-wider truncate max-w-full",
                            seg.isActive ? "text-slate-600" : "text-slate-300"
                          )}>
                            {seg.label === 'Bienvenue' ? '🏠' : seg.label === 'Tour Terminé' ? '🏁' : seg.label}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* ─ CONTENU ──────────────────────────────────────────── */}
                  <div className="px-7 py-4 overflow-y-auto custom-scrollbar flex-1 border-t border-slate-100/60">
                    <p className="text-[13px] font-medium text-slate-600 leading-relaxed">
                      {step.description}
                    </p>

                    {step.features && step.features.length > 0 && (
                      <motion.ul
                        className="mt-4 space-y-2"
                        initial="hidden"
                        animate="visible"
                        variants={{
                          hidden: {},
                          visible: { transition: { staggerChildren: 0.05 } },
                        }}
                      >
                        {step.features.map((f, i) => (
                          <motion.li
                            key={i}
                            variants={{
                              hidden: { opacity: 0, x: -8 },
                              visible: { opacity: 1, x: 0 },
                            }}
                            className="flex items-start gap-2.5 text-[13px]"
                          >
                            <div
                              className="mt-0.5 w-4 h-4 rounded-md flex items-center justify-center shrink-0"
                              style={{ background: 'color-mix(in srgb, var(--primary) 10%, transparent)' }}
                            >
                              <CheckCircle2 size={10} style={{ color: 'var(--primary)' }} />
                            </div>
                            <span className="font-medium text-slate-700 leading-snug">{f}</span>
                          </motion.li>
                        ))}
                      </motion.ul>
                    )}
                  </div>

                  {/* ─ FOOTER ───────────────────────────────────────────── */}
                  <div className="px-7 pb-5 pt-3 flex items-center justify-between gap-3 border-t border-slate-100/60">
                    {/* Précédent */}
                    <button
                      onClick={goPrev}
                      disabled={isFirst}
                      className={cn(
                        'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all border',
                        isFirst
                          ? 'opacity-0 pointer-events-none border-transparent'
                          : 'border-slate-200 text-slate-500 hover:bg-slate-50 hover:border-slate-300 active:scale-95',
                      )}
                    >
                      <ChevronLeft size={14} />
                      Retour
                    </button>

                    {/* Compteur central */}
                    <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest flex items-center gap-1.5">
                      <Compass size={10} />
                      {currentIdx + 1} / {TOUR_STEPS.length}
                    </span>

                    {/* Suivant / Terminer */}
                    <button
                      onClick={goNext}
                      disabled={isNavigating}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-black text-white transition-all active:scale-95"
                      style={{
                        background: 'linear-gradient(135deg, var(--primary) 0%, color-mix(in srgb, var(--primary) 65%, #6366f1) 100%)',
                        boxShadow: '0 6px 16px -3px color-mix(in srgb, var(--primary) 30%, transparent)',
                      }}
                    >
                      {isLast ? (
                        <>
                          <Sparkles size={13} />
                          Terminer
                        </>
                      ) : (
                        <>
                          Suivant
                          <ChevronRight size={14} />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* ── CELEBRATION ────────────────────────────────────────────── */}
            <AnimatePresence>
              {showCelebration && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-[100002] flex items-center justify-center pointer-events-none"
                >
                  {[...Array(12)].map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{
                        x: 0, y: 0, scale: 0, opacity: 1,
                      }}
                      animate={{
                        x: (Math.random() - 0.5) * 400,
                        y: (Math.random() - 0.5) * 400,
                        scale: [0, 1.5, 0],
                        opacity: [1, 1, 0],
                        rotate: Math.random() * 720,
                      }}
                      transition={{ duration: 1.8, ease: 'easeOut', delay: i * 0.04 }}
                      className="absolute w-3 h-3 rounded-sm"
                      style={{
                        background: i % 3 === 0
                          ? 'var(--primary)'
                          : i % 3 === 1
                            ? 'color-mix(in srgb, var(--primary) 60%, #6366f1)'
                            : '#fbbf24',
                      }}
                    />
                  ))}
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: [0, 1.2, 1], opacity: 1 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="text-6xl"
                  >
                    🎉
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
