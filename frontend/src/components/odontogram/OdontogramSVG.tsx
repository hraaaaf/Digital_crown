/**
 * OdontogramSVG.tsx
 * Renderer FDI compact, vectoriel et interactif.
 * Supporte les arcades adulte (32 dents) et pédiatrique (20 dents),
 * les cinq surfaces M/D/O/V/P, les états cliniques et la sélection clavier/souris.
 *
 * Le SVG est responsive : ResizeObserver mesure le conteneur puis les coordonnées
 * normalisées sont converties en pixels pour conserver la géométrie à tout viewport.
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

const ADULT_TOP = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28] as const;
const ADULT_BOTTOM = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38] as const;
const PEDIATRIC_TOP = [55, 54, 53, 52, 51, 61, 62, 63, 64, 65] as const;
const PEDIATRIC_BOTTOM = [85, 84, 83, 82, 81, 71, 72, 73, 74, 75] as const;

type ToothGlyphKind = 'INCISOR' | 'CANINE' | 'PREMOLAR' | 'MOLAR';

const TOOTH_POSITION_PATHS: Record<number, string> = {
  1: 'M -0.58,-0.86 C -0.48,-1.02 -0.26,-1.08 0,-1.08 C 0.26,-1.08 0.48,-1.02 0.58,-0.86 C 0.62,-0.54 0.54,-0.30 0.37,-0.14 C 0.24,0.00 0.20,0.30 0.16,0.58 C 0.12,0.84 0.07,1.07 0,1.22 C -0.07,1.07 -0.12,0.84 -0.16,0.58 C -0.20,0.30 -0.24,0.00 -0.37,-0.14 C -0.54,-0.30 -0.62,-0.54 -0.58,-0.86 Z',
  2: 'M -0.50,-0.84 C -0.40,-1.00 -0.20,-1.06 0,-1.06 C 0.20,-1.06 0.40,-1.00 0.50,-0.84 C 0.54,-0.56 0.47,-0.30 0.32,-0.12 C 0.22,0.04 0.18,0.33 0.14,0.60 C 0.10,0.84 0.06,1.04 0,1.18 C -0.06,1.04 -0.10,0.84 -0.14,0.60 C -0.18,0.33 -0.22,0.04 -0.32,-0.12 C -0.47,-0.30 -0.54,-0.56 -0.50,-0.84 Z',
  3: 'M -0.55,-0.68 C -0.40,-0.82 -0.18,-0.94 0,-1.10 C 0.18,-0.94 0.40,-0.82 0.55,-0.68 C 0.58,-0.40 0.49,-0.18 0.34,-0.02 C 0.22,0.14 0.17,0.42 0.13,0.70 C 0.09,0.95 0.05,1.17 0,1.33 C -0.05,1.17 -0.09,0.95 -0.13,0.70 C -0.17,0.42 -0.22,0.14 -0.34,-0.02 C -0.49,-0.18 -0.58,-0.40 -0.55,-0.68 Z',
  4: 'M -0.66,-0.70 C -0.58,-0.90 -0.38,-1.00 -0.16,-0.94 C -0.04,-0.88 0.04,-0.88 0.16,-0.94 C 0.38,-1.00 0.58,-0.90 0.66,-0.70 C 0.68,-0.42 0.58,-0.18 0.40,-0.02 C 0.26,0.12 0.20,0.39 0.15,0.64 C 0.10,0.88 0.05,1.05 0,1.17 C -0.05,1.05 -0.10,0.88 -0.15,0.64 C -0.20,0.39 -0.26,0.12 -0.40,-0.02 C -0.58,-0.18 -0.68,-0.42 -0.66,-0.70 Z',
  5: 'M -0.70,-0.68 C -0.60,-0.90 -0.38,-1.00 -0.15,-0.92 C -0.04,-0.86 0.04,-0.86 0.15,-0.92 C 0.38,-1.00 0.60,-0.90 0.70,-0.68 C 0.72,-0.40 0.60,-0.16 0.42,0.00 C 0.28,0.14 0.22,0.38 0.17,0.62 C 0.12,0.84 0.06,1.02 0,1.12 C -0.06,1.02 -0.12,0.84 -0.17,0.62 C -0.22,0.38 -0.28,0.14 -0.42,0.00 C -0.60,-0.16 -0.72,-0.40 -0.70,-0.68 Z',
  6: 'M -0.86,-0.60 C -0.83,-0.84 -0.68,-0.98 -0.48,-0.96 C -0.30,-1.03 -0.12,-0.98 0,-0.88 C 0.14,-0.99 0.34,-1.02 0.51,-0.94 C 0.72,-0.96 0.86,-0.82 0.86,-0.58 C 0.84,-0.28 0.70,-0.08 0.48,0.07 C 0.38,0.19 0.34,0.42 0.30,0.68 C 0.26,0.90 0.20,1.08 0.13,1.16 C 0.05,1.04 0.02,0.83 0,0.64 C -0.02,0.83 -0.05,1.04 -0.13,1.16 C -0.20,1.08 -0.26,0.90 -0.30,0.68 C -0.34,0.42 -0.38,0.19 -0.48,0.07 C -0.70,-0.08 -0.84,-0.28 -0.86,-0.60 Z',
  7: 'M -0.88,-0.58 C -0.84,-0.82 -0.66,-0.98 -0.44,-0.94 C -0.28,-1.02 -0.10,-0.98 0.02,-0.88 C 0.18,-1.00 0.38,-1.00 0.54,-0.91 C 0.76,-0.92 0.90,-0.76 0.88,-0.54 C 0.84,-0.26 0.68,-0.06 0.46,0.08 C 0.36,0.22 0.31,0.45 0.27,0.68 C 0.23,0.88 0.18,1.04 0.11,1.12 C 0.04,1.00 0.02,0.82 0,0.66 C -0.02,0.82 -0.04,1.00 -0.11,1.12 C -0.18,1.04 -0.23,0.88 -0.27,0.68 C -0.31,0.45 -0.36,0.22 -0.46,0.08 C -0.68,-0.06 -0.84,-0.26 -0.88,-0.58 Z',
  8: 'M -0.82,-0.56 C -0.78,-0.78 -0.62,-0.92 -0.42,-0.90 C -0.26,-0.98 -0.10,-0.94 0.02,-0.85 C 0.16,-0.94 0.34,-0.95 0.49,-0.87 C 0.69,-0.88 0.82,-0.73 0.81,-0.52 C 0.78,-0.25 0.64,-0.05 0.44,0.09 C 0.34,0.23 0.30,0.44 0.26,0.64 C 0.22,0.82 0.17,0.98 0.10,1.05 C 0.04,0.94 0.02,0.78 0,0.64 C -0.02,0.78 -0.04,0.94 -0.10,1.05 C -0.17,0.98 -0.22,0.82 -0.26,0.64 C -0.30,0.44 -0.34,0.23 -0.44,0.09 C -0.64,-0.05 -0.78,-0.25 -0.82,-0.56 Z',
};

const toothGlyphKind = (toothNumber: number): ToothGlyphKind => {
  const position = toothNumber % 10;
  if (position >= 6) return 'MOLAR';
  if (position >= 4) return 'PREMOLAR';
  if (position === 3) return 'CANINE';
  return 'INCISOR';
};

const toothGlyphScale = (toothNumber: number) => {
  const position = Math.min(8, Math.max(1, toothNumber % 10));
  const scales: Record<number, { x: number; y: number }> = {
    1: { x: 0.90, y: 1.10 },
    2: { x: 0.82, y: 1.06 },
    3: { x: 0.86, y: 1.15 },
    4: { x: 0.85, y: 0.99 },
    5: { x: 0.89, y: 0.97 },
    6: { x: 1.00, y: 0.92 },
    7: { x: 1.03, y: 0.90 },
    8: { x: 0.96, y: 0.87 },
  };
  return scales[position];
};

const toothGlyph = (toothNumber: number) => {
  const kind = toothGlyphKind(toothNumber);
  const position = Math.min(8, Math.max(1, toothNumber % 10));
  return { kind, path: TOOTH_POSITION_PATHS[position], ...toothGlyphScale(toothNumber) };
};

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
      stroke={isHighlight && state !== 'HEALTHY'
        ? 'var(--primary)'
        : hideSurfaces || state === 'HEALTHY'
          ? 'transparent'
          : SURFACE_COLORS[state]?.stroke || 'var(--border-hover)'}
      strokeWidth={isHighlight && state !== 'HEALTHY' ? 1.4 : hideSurfaces || state === 'HEALTHY' ? 0 : 0.8}
      className={`transition-colors duration-200 ${readOnly ? 'cursor-default' : 'cursor-pointer'}`}
      style={{ transform: `translate(${cx}px, ${cy}px)` }}
      onClick={onClick}
      onMouseEnter={() => onHover(face)}
      onMouseLeave={() => onHover(null)}
      whileHover={!readOnly ? { fillOpacity: Math.max(opacity, 0.12), fill: fill !== 'transparent' ? fill : 'color-mix(in srgb, var(--primary) 7%, transparent)' } : {}}
      animate={{ fillOpacity: isSelected ? Math.max(opacity, 0.10) : opacity, fill: isSelected && fill === 'transparent' ? 'color-mix(in srgb, var(--primary) 6%, transparent)' : fill }}
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
  showNumbers = true,
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

  const rows = useMemo(
    () => type === 'ADULT'
      ? { top: [...ADULT_TOP], bottom: [...ADULT_BOTTOM] }
      : { top: [...PEDIATRIC_TOP], bottom: [...PEDIATRIC_BOTTOM] },
    [type]
  );

  const teethList = useMemo(() => [...rows.top, ...rows.bottom], [rows]);
  const surfaces: ('M' | 'D' | 'O' | 'V' | 'P')[] = ['M', 'D', 'O', 'V', 'P'];

  const toothPx = useCallback(
    (toothNum: number) => {
      if (canvasSize.width === 0 || canvasSize.height === 0) return null;
      const { width: W, height: H } = canvasSize;
      const topIndex = rows.top.indexOf(toothNum as never);
      const bottomIndex = rows.bottom.indexOf(toothNum as never);
      const isUpper = topIndex >= 0;
      const index = isUpper ? topIndex : bottomIndex;
      const row = isUpper ? rows.top : rows.bottom;
      if (index < 0) return null;
      const compactViewport = W < 520;
      // Canonical mockup: broad, almost linear rows with a clean central FDI split.
      const edge = type === 'ADULT' ? (compactViewport ? 5.5 : 5.2) : (compactViewport ? 9 : 10);
      const xPct = row.length === 1 ? 50 : edge + (index * (100 - edge * 2)) / (row.length - 1);
      const yPct = isUpper ? (compactViewport ? 31 : 32) : (compactViewport ? 70 : 69);
      const radiusPct = type === 'ADULT' ? (compactViewport ? 4.65 : 4.70) : (compactViewport ? 5.10 : 5.00);
      return { cx: pctX(xPct, W), cy: pctY(yPct, H), r: pctR(radiusPct, W, H), isUpper };
    },
    [canvasSize, rows, type]
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

  const handleToothActivate = useCallback((toothNumber: number, event: React.SyntheticEvent) => {
    if (readOnly) return;
    event.stopPropagation();
    if (onToothDirectClick) {
      onToothDirectClick(toothNumber);
      return;
    }
    onSurfaceClick(toothNumber, 'O', event as unknown as React.MouseEvent);
  }, [readOnly, onToothDirectClick, onSurfaceClick]);

  const handleToothKeyDown = useCallback((toothNumber: number) => (event: React.KeyboardEvent<SVGGElement>) => {
    if (readOnly) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToothActivate(toothNumber, event);
    }
  }, [readOnly, handleToothActivate]);

  return (
    <div
      ref={containerRef}
      data-odontogram-renderer="compact-fdi"
      className={`relative w-full mx-auto aspect-[1.78/1] min-h-[310px] sm:min-h-[360px] ${className || 'max-w-[920px]'}`}
    >
      {canvasSize.width > 0 && canvasSize.height > 0 && (
        <svg
          className="absolute inset-0 z-10"
          width={canvasSize.width}
          height={canvasSize.height}
          viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`}
          style={{ overflow: 'hidden', display: 'block' }}
        >
          <defs>
            <radialGradient id="tooth-enamel" cx="42%" cy="34%" r="78%">
              <stop offset="0%" stopColor="color-mix(in srgb, var(--card-bg) 99%, var(--text-main) 1%)" />
              <stop offset="48%" stopColor="color-mix(in srgb, var(--card-bg) 96%, var(--text-main) 4%)" />
              <stop offset="72%" stopColor="color-mix(in srgb, var(--card-bg) 84%, var(--text-main) 16%)" />
              <stop offset="100%" stopColor="color-mix(in srgb, var(--card-bg) 48%, var(--text-main) 52%)" />
            </radialGradient>
            <linearGradient id="tooth-gloss" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="color-mix(in srgb, var(--card-bg) 100%, var(--text-main) 0%)" stopOpacity="0.9" />
              <stop offset="62%" stopColor="color-mix(in srgb, var(--card-bg) 92%, var(--text-main) 8%)" stopOpacity="0.22" />
              <stop offset="100%" stopColor="color-mix(in srgb, var(--card-bg) 78%, var(--text-main) 22%)" stopOpacity="0.06" />
            </linearGradient>
            <filter id="tooth-soft-shadow" x="-35%" y="-35%" width="170%" height="180%">
              <feDropShadow dx="0" dy="1.8" stdDeviation="1.8" floodColor="var(--text-main)" floodOpacity="0.26" />
            </filter>
            {/* Clips anatomiques pour les cinq surfaces interactives de chaque dent */}
            {teethList.map((toothNumber) => {
              const px = toothPx(toothNumber);
              if (!px) return null;
              const glyph = toothGlyph(toothNumber);
              return (
                <clipPath id={`clip-tooth-${toothNumber}`} key={`clip-${toothNumber}`}>
                  <path
                    d={glyph.path}
                    transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x} ${px.r * glyph.y * (px.isUpper ? -1 : 1)})`}
                  />
                </clipPath>
              );
            })}
          </defs>

          <rect
            x={1}
            y={1}
            width={Math.max(0, canvasSize.width - 2)}
            height={Math.max(0, canvasSize.height - 2)}
            rx={Math.min(28, canvasSize.width * 0.035)}
            fill="var(--card-bg)"
            stroke="var(--border-color)"
            className="pointer-events-none"
          />

          <text x={pctX(3.5, canvasSize.width)} y={pctY(9, canvasSize.height)} fill="var(--text-muted)" fontSize={Math.max(12, Math.min(17, canvasSize.width * 0.016))} fontWeight={800}>
            Maxillaire
          </text>
          <text x={pctX(3.5, canvasSize.width)} y={pctY(54, canvasSize.height)} fill="var(--text-muted)" fontSize={Math.max(12, Math.min(17, canvasSize.width * 0.016))} fontWeight={800}>
            Mandibulaire
          </text>
          <line
            x1={pctX(50, canvasSize.width)}
            y1={pctY(15, canvasSize.height)}
            x2={pctX(50, canvasSize.width)}
            y2={pctY(88, canvasSize.height)}
            stroke="var(--border-color)"
            strokeWidth={1.25}
            strokeDasharray="5 6"
            className="pointer-events-none"
          />
          {/* Rendu compact FDI des dents */}
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
            const glyph = toothGlyph(toothNumber);
            const position = Math.min(8, Math.max(1, toothNumber % 10));
            const useMockupSprite = type === 'ADULT';
            const spriteHeight = px.r * 2.55;
            const spriteWidth = px.r * (glyph.kind === 'MOLAR' ? 1.74 : 1.58);
            const spriteHref = `/assets/odontogram/mockup/${px.isUpper ? 'upper' : 'lower'}-${position}.png`;
            const verticalDirection = px.isUpper ? -1 : 1;

            return (
              <g
                key={`tooth-group-${toothNumber}`}
                tabIndex={!readOnly ? 0 : undefined}
                role={!readOnly ? 'button' : undefined}
                aria-label={!readOnly ? getToothAccessibleName(toothNumber) : undefined}
                aria-pressed={!readOnly ? (isMultiSelected || isToothSelected) : undefined}
                onClick={(event) => handleToothActivate(toothNumber, event)}
                onFocus={() => {
                  if (!readOnly) {
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
                <circle
                  cx={px.cx}
                  cy={px.cy}
                  r={px.r * 1.45}
                  fill="transparent"
                  className="cursor-pointer"
                />

                {showNumbers && (
                  <text
                    x={px.cx}
                    y={px.cy - px.r * 1.52}
                    textAnchor="middle"
                    fill="var(--text-main)"
                    fontSize={Math.max(10.5, Math.min(14, canvasSize.width * 0.014))}
                    fontWeight={800}
                    className="pointer-events-none select-none"
                  >
                    {toothNumber}
                  </text>
                )}

                {useMockupSprite && isToothSelected && (
                  <rect
                    x={px.cx - spriteWidth * 0.58}
                    y={px.cy - spriteHeight * 0.54}
                    width={spriteWidth * 1.16}
                    height={spriteHeight * 1.08}
                    rx={px.r * 0.34}
                    fill="color-mix(in srgb, var(--primary) 6%, transparent)"
                    stroke="var(--primary)"
                    strokeWidth={1.4}
                    className="pointer-events-none"
                  />
                )}

                {useMockupSprite && (
                  <image
                    data-selected-halo={isToothSelected ? 'true' : undefined}
                    href={spriteHref}
                    x={px.cx - spriteWidth / 2}
                    y={px.cy - spriteHeight / 2}
                    width={spriteWidth}
                    height={spriteHeight}
                    preserveAspectRatio="xMidYMid meet"
                    className="pointer-events-none"
                    style={{
                      filter: isToothSelected
                        ? 'drop-shadow(0 0 1px var(--primary)) drop-shadow(0 0 4px color-mix(in srgb, var(--primary) 45%, transparent))'
                        : undefined,
                    }}
                  />
                )}

                {isToothSelected && !useMockupSprite && (
                  <path
                    data-selected-halo="true"
                    d={glyph.path}
                    transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x * 1.13} ${px.r * glyph.y * 1.13 * (px.isUpper ? -1 : 1)})`}
                    fill="color-mix(in srgb, var(--primary) 5%, transparent)"
                    stroke="var(--primary)"
                    strokeWidth={2.35}
                    vectorEffect="non-scaling-stroke"
                    opacity={0.92}
                    className="pointer-events-none"
                  />
                )}

                <path
                  d={glyph.path}
                  transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x} ${px.r * glyph.y * (px.isUpper ? -1 : 1)})`}
                  fill={isToothSelected
                    ? 'color-mix(in srgb, var(--primary) 10%, var(--card-bg))'
                    : 'url(#tooth-enamel)'}
                  stroke={isToothSelected || isMultiSelected ? 'var(--primary)' : 'color-mix(in srgb, var(--border-hover) 75%, var(--text-main) 25%)'}
                  strokeWidth={isToothSelected || isMultiSelected ? 2.35 : 1.5}
                  vectorEffect="non-scaling-stroke"
                  filter="url(#tooth-soft-shadow)"
                  className={`pointer-events-none transition-colors duration-200 ${useMockupSprite ? 'hidden' : ''}`}
                />

                <path
                  d={glyph.path}
                  transform={`translate(${px.cx - px.r * 0.10} ${px.cy - (px.isUpper ? -1 : 1) * px.r * 0.08}) scale(${px.r * glyph.x * 0.72} ${px.r * glyph.y * 0.72 * (px.isUpper ? -1 : 1)})`}
                  fill="url(#tooth-gloss)"
                  stroke="none"
                  vectorEffect="non-scaling-stroke"
                  opacity={0.30}
                  className={`pointer-events-none ${useMockupSprite ? 'hidden' : ''}`}
                />

                {(glyph.kind === 'INCISOR' || glyph.kind === 'CANINE') && (
                  <path
                    d="M -0.42,-0.28 Q 0,-0.06 0.42,-0.28"
                    transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x} ${px.r * glyph.y * (px.isUpper ? -1 : 1)})`}
                    fill="none"
                    stroke="color-mix(in srgb, var(--border-hover) 64%, var(--text-main) 36%)"
                    strokeWidth={0.82}
                    vectorEffect="non-scaling-stroke"
                    className={`pointer-events-none ${useMockupSprite ? 'hidden' : ''}`}
                  />
                )}

                {(glyph.kind === 'MOLAR' || glyph.kind === 'PREMOLAR') && (
                  <path
                    d={glyph.kind === 'MOLAR'
                      ? 'M -0.48,-0.34 C -0.20,-0.10 0.20,-0.10 0.48,-0.34 M 0,-0.42 L 0,0.18'
                      : 'M -0.38,-0.34 Q 0,-0.08 0.38,-0.34'}
                    transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x} ${px.r * glyph.y * (px.isUpper ? -1 : 1)})`}
                    fill="none"
                    stroke="color-mix(in srgb, var(--border-hover) 64%, var(--text-main) 36%)"
                    strokeWidth={0.68}
                    vectorEffect="non-scaling-stroke"
                    opacity={0.46}
                    className={`pointer-events-none ${useMockupSprite ? 'hidden' : ''}`}
                  />
                )}

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
                    fill="color-mix(in srgb, var(--accent) 18%, transparent)"
                    stroke="var(--accent)" strokeWidth={2}
                    className="pointer-events-none"
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
                    <line x1={px.cx - px.r} y1={px.cy - px.r} x2={px.cx + px.r} y2={px.cy + px.r} stroke={SURFACE_COLORS.CARIES.stroke} strokeWidth={3} strokeLinecap="round" />
                    <line x1={px.cx - px.r} y1={px.cy + px.r} x2={px.cx + px.r} y2={px.cy - px.r} stroke={SURFACE_COLORS.CARIES.stroke} strokeWidth={3} strokeLinecap="round" />
                  </g>
                ) : (
                  <>
                    {/* Conteneur clippé sur la silhouette anatomique pour les faces */}
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
                      <path
                        d={glyph.path}
                        transform={`translate(${px.cx} ${px.cy}) scale(${px.r * glyph.x} ${px.r * glyph.y * (px.isUpper ? -1 : 1)})`}
                        fill={SURFACE_COLORS.CROWN.fill}
                        fillOpacity={0.34}
                        stroke={SURFACE_COLORS.CROWN.stroke}
                        strokeWidth={1.8}
                        vectorEffect="non-scaling-stroke"
                        className="pointer-events-none"
                      />
                    )}

                    {isRootCanal && (
                      <path
                        d={`M ${px.cx} ${px.cy - px.r * 0.08 * verticalDirection} Q ${px.cx - px.r * 0.10} ${px.cy + px.r * 0.34 * verticalDirection} ${px.cx} ${px.cy + px.r * 0.78 * verticalDirection}`}
                        fill="none"
                        stroke={SURFACE_COLORS.ROOT_CANAL.stroke}
                        strokeWidth={2.4}
                        strokeLinecap="round"
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
            className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-card/95 backdrop-blur-sm px-4 py-2 rounded-xl shadow-lg border border-border-main z-20 pointer-events-none"
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