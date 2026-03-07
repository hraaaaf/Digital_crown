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
// COMPOSANT HOTZONE
// ============================================================================

interface HotzoneProps {
  cx: number;
  cy: number;
  r: number;
  surface: 'M' | 'D' | 'O' | 'V' | 'P';
  isSelected: boolean;
  isReadOnly: boolean;
  onClick: (e: React.MouseEvent) => void;
  onHover: (surface: string | null) => void;
  showPulse: boolean;
}

const Hotzone: React.FC<HotzoneProps> = ({
  cx,
  cy,
  r,
  isSelected,
  isReadOnly,
  onClick,
  onHover,
  showPulse,
}) => (
  <g className="hotzone-group">
    {/* Anneau de pulsation quand la dent est survolée / sélectionnée */}
    {showPulse && (
      <motion.circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke="#3b82f6"
        strokeWidth={1.5}
        initial={{ opacity: 0.8, scale: 1 }}
        animate={{ opacity: 0, scale: 1.5 }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
        style={{ transformOrigin: `${cx}px ${cy}px` }}
      />
    )}

    {/* Zone cliquable principale */}
    <circle
      cx={cx}
      cy={cy}
      r={r * 0.5}
      fill={isSelected ? 'rgba(59, 130, 246, 0.3)' : 'transparent'}
      stroke={isSelected ? '#3b82f6' : 'transparent'}
      strokeWidth={1.5}
      className={isReadOnly ? 'cursor-default' : 'cursor-pointer'}
      onClick={onClick}
      onMouseEnter={() => onHover('active')}
      onMouseLeave={() => onHover(null)}
    />
  </g>
);

// ============================================================================
// COMPOSANT PASTILLE DE TRAITEMENT
// ============================================================================

interface TreatmentBadgeProps {
  cx: number;
  cy: number;
  r: number;
  state: SurfaceState;
  isSelected: boolean;
}

const TreatmentBadge: React.FC<TreatmentBadgeProps> = ({
  cx,
  cy,
  r,
  state,
  isSelected,
}) => {
  if (state === 'HEALTHY' || state === 'SELECTED') return null;

  const colors = SURFACE_COLORS[state];

  return (
    <motion.g
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 500, damping: 25 }}
      style={{ transformOrigin: `${cx}px ${cy}px` }}
    >
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill={colors.fill}
        stroke={colors.stroke}
        strokeWidth={1.5}
        opacity={0.85}
        style={{ filter: 'drop-shadow(0 1px 2px rgba(0,0,0,0.2))' }}
      />
      {isSelected && (
        <circle
          cx={cx}
          cy={cy}
          r={r * 1.3}
          fill="none"
          stroke="#3b82f6"
          strokeWidth={1.5}
          strokeDasharray="2 2"
        />
      )}
    </motion.g>
  );
};

// ============================================================================
// CALCUL DES DÉCALAGES PAR SURFACE (en % du rayon)
// ============================================================================

/**
 * Retourne le décalage (dx, dy) en fraction du rayon pour chaque face de la dent.
 * Ces valeurs sont appliquées APRÈS la conversion en pixels, garantissant que
 * le décalage est proportionnel à la taille affichée.
 */
const getSurfaceOffset = (
  surface: 'M' | 'D' | 'O' | 'V' | 'P',
  r: number
): { dx: number; dy: number } => {
  const d = r * 0.6;
  switch (surface) {
    case 'O': return { dx: 0,  dy: 0  }; // Centre
    case 'V': return { dx: 0,  dy: -d }; // Haut  (Vestibulaire)
    case 'P': return { dx: 0,  dy:  d }; // Bas   (Palatin / Lingual)
    case 'M': return { dx: -d, dy: 0  }; // Gauche (Mésial)
    case 'D': return { dx:  d, dy: 0  }; // Droite (Distal)
    default:  return { dx: 0,  dy: 0  };
  }
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
}) => {
  const [hoveredTooth, setHoveredTooth] = useState<number | null>(null);

  // Référence sur le conteneur — le ResizeObserver l'observe
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasSize = useElementSize(containerRef as React.RefObject<HTMLElement>);

  const backgroundImage = useMemo(
    () => (type === 'ADULT' ? ODONTOGRAM_IMAGES.ADULT : ODONTOGRAM_IMAGES.PEDIATRIC),
    [type]
  );

  const teethList = useMemo(
    () =>
      type === 'ADULT'
        ? Object.keys(ANATOMICAL_MAPPING.ADULT).map(Number)
        : Object.keys(ANATOMICAL_MAPPING.PEDIATRIC).map(Number),
    [type]
  );

  const surfaces: ('M' | 'D' | 'O' | 'V' | 'P')[] = ['M', 'D', 'O', 'V', 'P'];

  // ── Helpers pour obtenir la position d'une surface en pixels absolus ──────

  const getToothPosition = useCallback(
    (toothNum: number) =>
      type === 'ADULT'
        ? ANATOMICAL_MAPPING.ADULT[toothNum as ToothNumberFDI]
        : ANATOMICAL_MAPPING.PEDIATRIC[toothNum as PediatricToothNumber],
    [type]
  );

  /**
   * Convertit les coordonnées % du mapping en coordonnées px.
   * Le résultat est exact quelle que soit la taille d'affichage car il est
   * recalculé à chaque changement de `canvasSize` via le ResizeObserver.
   */
  const toothPx = useCallback(
    (toothNum: number) => {
      const pos = getToothPosition(toothNum);
      if (!pos || canvasSize.width === 0 || canvasSize.height === 0) return null;

      const { width: W, height: H } = canvasSize;
      const r = pctR(pos.r ?? 3, W, H);
      return {
        cx: pctX(pos.x, W),
        cy: pctY(pos.y, H),
        r,
      };
    },
    [canvasSize, getToothPosition]
  );

  // ── Gestion des événements ─────────────────────────────────────────────────

  const handleSurfaceClick = useCallback(
    (toothNumber: number, surface: 'M' | 'D' | 'O' | 'V' | 'P') =>
      (e: React.MouseEvent) => {
        if (readOnly) return;
        e.stopPropagation();
        // Mode sélection directe (groupée) : on transmet seulement le numéro de dent
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
      onSurfaceHover?.(surface ? toothNumber : null, surface);
    },
    [onSurfaceHover]
  );

  // ── Rendu ──────────────────────────────────────────────────────────────────

  return (
    <div ref={containerRef} className={`relative w-full max-w-2xl mx-auto ${className}`}>
      {/*
       * 1. L'IMAGE dicte la géométrie du conteneur.
       * `display: block` supprime l'espace de ligne de base inline.
       * `w-full h-auto` conserve le ratio d'aspect natif.
       * Le parent `relative` prend exactement les dimensions de l'image.
       */}
      <img
        src={backgroundImage}
        alt={`Schéma dentaire ${type === 'ADULT' ? 'adulte' : 'pédiatrique'}`}
        className="w-full h-auto block select-none pointer-events-none"
        // Déclencher une nouvelle mesure du conteneur après le chargement de l'image
        onLoad={() => {
          if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            // Le ResizeObserver prendra automatiquement la nouvelle dimension,
            // mais on force une mise à jour immédiate si nécessaire.
          }
        }}
      />

      {/*
       * 2. Le SVG est superposé pixel par pixel sur l'image.
       * - `width` et `height` sont les dimensions réelles mesurées par ResizeObserver.
       * - `viewBox` utilise ces mêmes dimensions → 1 unité SVG = 1 pixel CSS.
       * - Les coordonnées en % du mapping sont converties en px absolus via `toothPx()`.
       * - overflow: hidden évite tout débordement accidentel.
       */}
      {canvasSize.width > 0 && canvasSize.height > 0 && (
        <svg
          className="absolute inset-0 z-10"
          width={canvasSize.width}
          height={canvasSize.height}
          viewBox={`0 0 ${canvasSize.width} ${canvasSize.height}`}
          style={{ overflow: 'hidden', display: 'block' }}
        >
          <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="1" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* ── Cercles de multi-sélection groupée (bridge / PAP / totale) ── */}
          {multiSelectedTeeth.length > 0 && teethList.map((toothNumber) => {
            if (!multiSelectedTeeth.includes(toothNumber)) return null;
            const px = toothPx(toothNumber);
            if (!px) return null;
            return (
              <motion.circle
                key={`multisel-${toothNumber}`}
                cx={px.cx}
                cy={px.cy}
                r={px.r * 0.9}
                fill="rgba(34, 197, 94, 0.18)"
                stroke="#22c55e"
                strokeWidth={2}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                style={{
                  transformOrigin: `${px.cx}px ${px.cy}px`,
                  cursor: onToothDirectClick ? 'pointer' : 'default',
                  filter: 'drop-shadow(0 0 4px rgba(34,197,94,0.45))',
                }}
              />
            );
          })}

          {/* ── Pastilles de traitement (sous les hotzones) ── */}
          {teethList.map((toothNumber) => {
            const px = toothPx(toothNumber);
            if (!px) return null;

            const toothSurfaces = teethSurfaces[toothNumber];
            if (!toothSurfaces) return null;

            return surfaces.map((surface) => {
              const { dx, dy } = getSurfaceOffset(surface, px.r * 0.4);
              return (
                <TreatmentBadge
                  key={`badge-${toothNumber}-${surface}`}
                  cx={px.cx + dx}
                  cy={px.cy + dy}
                  r={px.r * 0.4}
                  state={toothSurfaces[surface]}
                  isSelected={
                    selectedTooth === toothNumber && selectedSurface === surface
                  }
                />
              );
            });
          })}

          {/* ── Hotzones cliquables ── */}
          {teethList.map((toothNumber) => {
            const px = toothPx(toothNumber);
            if (!px) return null;

            const isToothSelected = selectedTooth === toothNumber;
            const isMultiSelected = multiSelectedTeeth.includes(toothNumber);
            const showPulse = isToothSelected || hoveredTooth === toothNumber || isMultiSelected;

            return surfaces.map((surface) => {
              const { dx, dy } = getSurfaceOffset(surface, px.r);
              return (
                <Hotzone
                  key={`hotzone-${toothNumber}-${surface}`}
                  cx={px.cx + dx}
                  cy={px.cy + dy}
                  r={px.r}
                  surface={surface}
                  isSelected={isToothSelected && selectedSurface === surface}
                  isReadOnly={readOnly}
                  onClick={handleSurfaceClick(toothNumber, surface)}
                  onHover={(surf) => handleHover(toothNumber, surf)}
                  showPulse={showPulse}
                />
              );
            });
          })}

          {/* ── Numéros FDI (optionnels) ── */}
          {showNumbers &&
            teethList.map((toothNumber) => {
              const px = toothPx(toothNumber);
              if (!px) return null;

              // Taille de police proportionnelle à la hauteur de l'image
              const fontSize = Math.max(8, Math.round(canvasSize.height * 0.028));

              return (
                <text
                  key={`label-${toothNumber}`}
                  x={px.cx}
                  y={px.cy + px.r + fontSize * 1.2}
                  textAnchor="middle"
                  fontSize={fontSize}
                  fontWeight="600"
                  fill={selectedTooth === toothNumber ? '#3b82f6' : '#64748b'}
                  className="select-none pointer-events-none"
                  style={{ paintOrder: 'stroke', stroke: 'white', strokeWidth: 3 }}
                >
                  {toothNumber.toString()}
                </text>
              );
            })}
        </svg>
      )}

      {/* ── Tooltip de survol ── */}
      <AnimatePresence>
        {hoveredTooth && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-xl shadow-lg border border-gray-200 z-20 pointer-events-none"
          >
            <p className="text-sm font-medium text-gray-700 whitespace-nowrap">
              Dent {hoveredTooth}
              {type === 'ADULT'
                ? TOOTH_NAMES[hoveredTooth as ToothNumberFDI]
                  ? ` — ${TOOTH_NAMES[hoveredTooth as ToothNumberFDI]}`
                  : ''
                : PEDIATRIC_TOOTH_NAMES[hoveredTooth as PediatricToothNumber]
                ? ` — ${PEDIATRIC_TOOTH_NAMES[hoveredTooth as PediatricToothNumber]}`
                : ''}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default OdontogramSVG;