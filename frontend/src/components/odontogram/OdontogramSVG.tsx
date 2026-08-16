/**
 * OdontogramSVG.tsx
 * Schéma dentaire anatomique basé sur des images de référence
 * Architecture: Image de fond + Hotzones SVG cliquables + Pastilles de traitement
 * Supporte: Adulte (32 dents) et Pédiatrique (20 dents)
 *
 * FIX ALIGNEMENT: Le SVG utilise les dimensions réelles de l'image (ResizeObserver)
 * et convertit toutes les coordonnées % → px absolus, garantissant un alignement 1:1
 * quelle que soit la résolution ou le ratio d'aspect de l'image affichée.
 */
import React, { useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  ToothNumberFDI,
  PediatricToothNumber,
  ToothSurfaceState,
  SurfaceState,
  OdontogramType,
} from './types';
import {
  SURFACE_COLORS,
  ANATOMICAL_MAPPING,
  ODONTOGRAM_IMAGES,
  TOOTH_NAMES,
  PEDIATRIC_TOOTH_NAMES,
} from './types';

// ============================================================================
// TYPES
// ============================================================================

interface OdontogramSVGProps {
  type?: OdontogramType;
  teethSurfaces: Record<number, ToothSurfaceState>;
  selectedTooth: number | null;
  selectedSurface: 'M' | 'D' | 'O' | 'V' | 'P' | null;
  onSurfaceClick: (
    toothNumber: number,
    surface: 'M' | 'D' | 'O' | 'V' | 'P',
    event: React.MouseEvent
  ) => void;
  onSurfaceHover?: (toothNumber: number | null, surface: string | null) => void;
  showNumbers?: boolean;
  readOnly?: boolean;
  className?: string;
  /**
   * Liste de numéros FDI à afficher en surbrillance verte.
   * Utilisé pour la sélection groupée (bridge, PAP, totale...).
   */
  multiSelectedTeeth?: number[];
  /**
   * Si fourni, tout clic sur une surface appelle cette callback avec le numéro
   * de dent (sans détail de surface). Active le mode sélection directe.
   */
  onToothDirectClick?: (toothNumber: number) => void;
  /**
   * Cache les bordures des faces internes (M,D,O,V,P).
   */
  hideSurfaces?: boolean;
}

/** Dimensions réelles (px) de l'image affichée — alimentées par ResizeObserver */
interface CanvasSize {
  width: number;
  height: number;
}

// ============================================================================
// HOOK: Mesure précise des dimensions du conteneur image
// ============================================================================

/**
 * Observe les dimensions réelles de l'élément `ref` et les met à jour à chaque
 * redimensionnement de la fenêtre ou reflow layout.
 */
function useElementSize(ref: React.RefObject<HTMLElement>): CanvasSize {
  const [size, setSize] = useState<CanvasSize>({ width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current) return;

    const update = (el: Element) => {
      const rect = el.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    };

    // Mesure initiale
    update(ref.current);

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        update(entry.target);
      }
    });

    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);

  return size;
}

// ============================================================================
// UTILITAIRES DE CONVERSION % → PX
// ============================================================================

/** Convertit une coordonnée X exprimée en % vers des pixels absolus */
const pctX = (pct: number, width: number) => (pct / 100) * width;

/** Convertit une coordonnée Y exprimée en % vers des pixels absolus */
const pctY = (pct: number, height: number) => (pct / 100) * height;

/**
 * Convertit un rayon exprimé en % vers des pixels.
 * Utilise la longueur de référence normalisée SVG: sqrt((w²+h²)/2)
 * afin de produire des cercles visuellement cohérents quelle que soit l'image.
 */
const pctR = (pct: number, width: number, height: number) =>
  (pct / 100) * Math.sqrt((width * width + height * height) / 2);

// ============================================================================
// HELPERS GÉOMÉTRIQUES ANATOMIQUES
// ============================================================================

/** Détermine l'orientation visuelle d'une face selon la dent */
const getFaceOrientation = (toothNumber: number, face: 'M' | 'D' | 'O' | 'V' | 'P') => {
  if (face === 'O') return 'center';
  const isUpper = (toothNumber >= 11 && toothNumber <= 28) || (toothNumber >= 51 && toothNumber <= 65);
  // Quadrants 1 et 4 (droite du patient, donc affiché à gauche de l'écran)
  const isRight = (toothNumber >= 11 && toothNumber <= 18) || (toothNumber >= 41 && toothNumber <= 48) || (toothNumber >= 51 && toothNumber <= 55) || (toothNumber >= 81 && toothNumber <= 85);

  if (face === 'V') return isUpper ? 'top' : 'bottom';
  if (face === 'P') return isUpper ? 'bottom' : 'top';
  
  // Pour la droite du patient (affiché à gauche), le milieu est à sa droite.
  if (face === 'M') return isRight ? 'right' : 'left';
  if (face === 'D') return isRight ? 'left' : 'right';

  return 'center';
};

/**
 * Retourne le SVG path d'une section.
 * Le `clipPath` circulaire s'assurera que le rendu extérieur est arrondi.
 */
const getFacePath = (orientation: 'top' | 'bottom' | 'left' | 'right' | 'center', r: number) => {
  const d = r * 0.45; // Taille du carré central
  switch (orientation) {
    case 'center': return `M ${-d},${-d} L ${d},${-d} L ${d},${d} L ${-d},${d} Z`;
    case 'top':    return `M ${-r},${-r} L ${r},${-r} L ${d},${-d} L ${-d},${-d} Z`;
    case 'bottom': return `M ${-r},${r} L ${r},${r} L ${d},${d} L ${-d},${d} Z`;
    case 'left':   return `M ${-r},${-r} L ${-d},${-d} L ${-d},${d} L ${-r},${r} Z`;
    case 'right':  return `M ${r},${-r} L ${d},${-d} L ${d},${d} L ${r},${r} Z`;
  }
};

// ============================================================================
// COMPOSANT FACE ANATOMIQUE (SVG Polygon)
// ============================================================================

interface AnatomicFaceProps {
  cx: number;
  cy: number;
  r: number;
  face: 'M' | 'D' | 'O' | 'V' | 'P';
  orientation: 'top' | 'bottom' | 'left' | 'right' | 'center';
  state: SurfaceState;
  isSelected: boolean;
  isHovered: boolean;
  onClick: (e: React.MouseEvent) => void;
  onHover: (surface: string | null) => void;
  readOnly: boolean;
  hideSurfaces?: boolean;
}

const AnatomicFace: React.FC<AnatomicFaceProps> = ({
  cx, cy, r, face, orientation, state, isSelected, isHovered, onClick, onHover, readOnly, hideSurfaces
}) => {
  const path = getFacePath(orientation, r);
  
  // Déterminer la couleur de fond
  let fill = 'transparent';
  let opacity = 0;
  
  if (state !== 'HEALTHY' && state !== 'SELECTED' && state !== 'ABSENT' && state !== 'CROWN' && state !== 'ROOT_CANAL') {
    fill = SURFACE_COLORS[state]?.fill || 'transparent';
    opacity = 0.85;
  }
  
  // Apparence si sélectionné ou survolé
  const isHighlight = isSelected || isHovered;

  return (
    <motion.path
      d={path}
      fill={fill}
      fillOpacity={opacity}
      stroke={isHighlight ? 'rgba(59, 130, 246, 0.5)' : (hideSurfaces ? 'transparent' : 'rgba(200, 200, 200, 0.3)')}
      strokeWidth={isHighlight ? 2 : (hideSurfaces ? 0 : 1)}
      className={`transition-colors duration-200 ${readOnly ? 'cursor-default' : 'cursor-pointer'}`}
      style={{ transform: `translate(${cx}px, ${cy}px)` }}
      onClick={onClick}
      onMouseEnter={() => onHover(face)}
      onMouseLeave={() => onHover(null)}
      whileHover={!readOnly ? { fillOpacity: Math.max(opacity, 0.4), fill: fill !== 'transparent' ? fill : 'rgba(59, 130, 246, 0.2)' } : {}}
      animate={{ fillOpacity: isSelected ? Math.max(opacity, 0.6) : opacity, fill: isSelected && fill === 'transparent' ? 'rgba(59, 130, 246, 0.3)' : fill }}
    />
  );
};


// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

export const OdontogramSVG: React.FC<OdontogramSVGProps> = ({
  type = 'ADULT',
  teethSurfaces,
  selectedTooth,
  selectedSurface,
  onSurfaceClick,
  onSurfaceHover,
  showNumbers = false,
  readOnly = false,
  className = '',
  multiSelectedTeeth = [],
  onToothDirectClick,
  hideSurfaces = false,
}) => {
  const [hoveredTooth, setHoveredTooth] = useState<number | null>(null);
  const [hoveredSurface, setHoveredSurface] = useState<string | null>(null);
  const [focusedTooth, setFocusedTooth] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const canvasSize = useElementSize(containerRef as React.RefObject<HTMLElement>);

  const backgroundImage = useMemo(
    () => (type === 'ADULT' ? ODONTOGRAM_IMAGES.ADULT : ODONTOGRAM_IMAGES.PEDIATRIC),
    [type]
  );

  const teethList = useMemo(
    () => type === 'ADULT' ? Object.keys(ANATOMICAL_MAPPING.ADULT).map(Number) : Object.keys(ANATOMICAL_MAPPING.PEDIATRIC).map(Number),
    [type]
  );

  const surfaces: ('M' | 'D' | 'O' | 'V' | 'P')[] = ['M', 'D', 'O', 'V', 'P'];

  const getToothPosition = useCallback(
    (toothNum: number) =>
      type === 'ADULT'
        ? ANATOMICAL_MAPPING.ADULT[toothNum as ToothNumberFDI]
        : ANATOMICAL_MAPPING.PEDIATRIC[toothNum as PediatricToothNumber],
    [type]
  );

  const toothPx = useCallback(
    (toothNum: number) => {
      const pos = getToothPosition(toothNum);
      if (!pos || canvasSize.width === 0 || canvasSize.height === 0) return null;
      const { width: W, height: H } = canvasSize;
      return { cx: pctX(pos.x, W), cy: pctY(pos.y, H), r: pctR(pos.r ?? 3, W, H) };
    },
    [canvasSize, getToothPosition]
  );

  const handleSurfaceClick = useCallback(
    (toothNumber: number, surface: 'M' | 'D' | 'O' | 'V' | 'P') =>
      (e: React.MouseEvent) => {
        if (readOnly) return;
        e.stopPropagation();
        if (onToothDirectClick) {
          onToothDirectClick(toothNumber);
          return;
        }
        onSurfaceClick(toothNumber, surface, e);
      },
    [readOnly, onSurfaceClick, onToothDirectClick]
  );

  const handleHover = useCallback(
    (toothNumber: number, surface: string | null) => {
      setHoveredTooth(surface ? toothNumber : null);
      setHoveredSurface(surface);
      onSurfaceHover?.(surface ? toothNumber : null, surface);
    },
    [onSurfaceHover]
  );

  const getToothAccessibleName = useCallback((toothNumber: number) => {
    const name = type === 'ADULT'
      ? TOOTH_NAMES[toothNumber as ToothNumberFDI]
      : PEDIATRIC_TOOTH_NAMES[toothNumber as PediatricToothNumber];
    return `Dent ${toothNumber}${name ? `, ${name}` : ''}`;
  }, [type]);

  const handleToothKeyDown = useCallback((toothNumber: number) => (event: React.KeyboardEvent<SVGGElement>) => {
    if (readOnly || !onToothDirectClick) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onToothDirectClick(toothNumber);
    }
  }, [readOnly, onToothDirectClick]);

  return (
    <div ref={containerRef} className={`relative w-full max-w-[480px] mx-auto ${className}`}>
      <img
        src={backgroundImage}
        alt={`Schéma dentaire ${type === 'ADULT' ? 'adulte' : 'pédiatrique'}`}
        className="w-full h-auto block select-none pointer-events-none opacity-0"
      />

      {canvasSize.width > 0 && canvasSize.height > 0 && (
        <svg
          className="absolute inset-0 z-10"
          width={canvasSize.width}
          height={canvasSize.height}
          viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`}
          style={{ overflow: 'hidden', display: 'block' }}
        >
          <defs>
            <filter id="extractLines">
              <feColorMatrix type="matrix" values="
                0.33 0.33 0.33 0 0
                0.33 0.33 0.33 0 0
                0.33 0.33 0.33 0 0
                0 0 0 1 0" />
              <feComponentTransfer>
                <feFuncR type="linear" slope="-3" intercept="2.8" />
                <feFuncG type="linear" slope="-3" intercept="2.8" />
                <feFuncB type="linear" slope="-3" intercept="2.8" />
              </feComponentTransfer>
            </filter>
            <mask id="blueprint-mask">
              <image href={backgroundImage} width="100%" height="100%" filter="url(#extractLines)" preserveAspectRatio="none" />
            </mask>

            {/* Clips circulaires pour chaque dent */}
            {teethList.map((toothNumber) => {
              const px = toothPx(toothNumber);
              if (!px) return null;
              return (
                <clipPath id={`clip-tooth-${toothNumber}`} key={`clip-${toothNumber}`}>
                  <circle cx={px.cx} cy={px.cy} r={px.r} />
                </clipPath>
              );
            })}
          </defs>

          <rect 
            width="100%" 
            height="100%" 
            className="fill-primary opacity-90 transition-colors duration-500"
            mask="url(#blueprint-mask)" 
          />

          {/* Rendu des Dents */}
          {teethList.map((toothNumber) => {
            const px = toothPx(toothNumber);
            if (!px) return null;

            const toothStates = teethSurfaces[toothNumber] || { M: 'HEALTHY', D: 'HEALTHY', O: 'HEALTHY', V: 'HEALTHY', P: 'HEALTHY' };

            // Détection globale
            const isAbsent = Object.values(toothStates).some(s => s === 'ABSENT' || s === 'EXTRACTED' || s === 'ABSENT_TO_EXTRACT');
            const isCrown = Object.values(toothStates).some(s => s === 'CROWN' || s === 'CROWN_CERAMIC');
            const isRootCanal = Object.values(toothStates).some(s => s === 'ROOT_CANAL');

            const isMultiSelected = multiSelectedTeeth.includes(toothNumber);
            const isToothSelected = selectedTooth === toothNumber;
            const isKeyboardFocused = focusedTooth === toothNumber;

            return (
              <g
                key={`tooth-group-${toothNumber}`}
                tabIndex={!readOnly && onToothDirectClick ? 0 : undefined}
                role={!readOnly && onToothDirectClick ? 'button' : undefined}
                aria-label={!readOnly && onToothDirectClick ? getToothAccessibleName(toothNumber) : undefined}
                aria-pressed={!readOnly && onToothDirectClick ? (isMultiSelected || isToothSelected) : undefined}
                onFocus={() => {
                  if (!readOnly && onToothDirectClick) {
                    setFocusedTooth(toothNumber);
                    handleHover(toothNumber, 'O');
                  }
                }}
                onBlur={() => {
                  setFocusedTooth(null);
                  handleHover(toothNumber, null);
                }}
                onKeyDown={handleToothKeyDown(toothNumber)}
              >
                {isKeyboardFocused && (
                  <circle
                    cx={px.cx}
                    cy={px.cy}
                    r={px.r * 1.35}
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth={2}
                    strokeDasharray="4 3"
                    className="text-primary pointer-events-none"
                  />
                )}
                
                {/* Effet de sélection groupée ou globale */}
                {isMultiSelected && (
                  <circle
                    cx={px.cx} cy={px.cy} r={px.r * 1.2}
                    fill="rgba(34, 197, 94, 0.18)"
                    stroke="#22c55e" strokeWidth={2}
                  />
                )}

                {/* Si ABSENT, on dessine juste une grosse croix et on arrête le rendu des faces */}
                {isAbsent ? (
                  <g 
                    onClick={handleSurfaceClick(toothNumber, 'O')}
                    onMouseEnter={() => handleHover(toothNumber, 'O')}
                    onMouseLeave={() => handleHover(toothNumber, null)}
                    className={readOnly ? 'cursor-default' : 'cursor-pointer'}
                  >
                    <circle cx={px.cx} cy={px.cy} r={px.r} fill="transparent" />
                    <line x1={px.cx - px.r} y1={px.cy - px.r} x2={px.cx + px.r} y2={px.cy + px.r} stroke="#ef4444" strokeWidth={3} strokeLinecap="round" />
                    <line x1={px.cx - px.r} y1={px.cy + px.r} x2={px.cx + px.r} y2={px.cy - px.r} stroke="#ef4444" strokeWidth={3} strokeLinecap="round" />
                  </g>
                ) : (
                  <>
                    {/* Conteneur clippé en cercle pour les faces */}
                    <g clipPath={`url(#clip-tooth-${toothNumber})`}>
                      {surfaces.map((surface) => {
                        const state = toothStates[surface];
                        const orientation = getFaceOrientation(toothNumber, surface);
                        const isSurfaceSelected = isToothSelected && selectedSurface === surface;
                        const isSurfaceHovered = hoveredTooth === toothNumber && hoveredSurface === surface;

                        return (
                          <AnatomicFace
                            key={`face-${toothNumber}-${surface}`}
                            cx={px.cx} cy={px.cy} r={px.r}
                            face={surface}
                            orientation={orientation}
                            state={state}
                            isSelected={isSurfaceSelected}
                            isHovered={isSurfaceHovered}
                            onClick={handleSurfaceClick(toothNumber, surface)}
                            onHover={(surf) => handleHover(toothNumber, surf)}
                            readOnly={readOnly}
                            hideSurfaces={hideSurfaces}
                          />
                        );
                      })}
                    </g>

                    {/* Statuts Globaux Superposés (ex: Couronne, Endo) */}
                    {isCrown && (
                      <circle
                        cx={px.cx} cy={px.cy} r={px.r}
                        fill="rgba(253, 230, 138, 0.4)" // fde68a transparent
                        stroke="#d97706" strokeWidth={2}
                        className="pointer-events-none"
                      />
                    )}

                    {isRootCanal && (
                      <circle
                        cx={px.cx} cy={px.cy} r={px.r * 0.25}
                        fill="#64748b"
                        className="pointer-events-none"
                      />
                    )}
                  </>
                )}
              </g>
            );
          })}
        </svg>
      )}

      {/* Tooltip */}
      <AnimatePresence>
        {hoveredTooth && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-xl shadow-lg border border-gray-200 z-20 pointer-events-none"
          >
            <p className="text-sm font-black text-primary whitespace-nowrap">
              {type === 'ADULT' ? TOOTH_NAMES[hoveredTooth as ToothNumberFDI] : PEDIATRIC_TOOTH_NAMES[hoveredTooth as PediatricToothNumber]}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default OdontogramSVG;