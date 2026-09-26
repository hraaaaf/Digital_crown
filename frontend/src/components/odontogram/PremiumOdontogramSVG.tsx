import React, { useMemo, useState } from 'react';
import { cn } from '../../utils/cn';
import type { OdontogramType } from './types';

type ToothKind = 'molar' | 'premolar' | 'canine' | 'incisor';

interface PremiumOdontogramSVGProps {
  type?: OdontogramType;
  selectedTooth?: number | null;
  multiSelectedTeeth?: number[];
  onToothClick?: (toothNumber: number) => void;
  readOnly?: boolean;
  className?: string;
  showNumbers?: boolean;
}

const ADULT_UPPER = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
const ADULT_LOWER = [48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
const CHILD_UPPER = [55,54,53,52,51,61,62,63,64,65];
const CHILD_LOWER = [85,84,83,82,81,71,72,73,74,75];

const kindFor = (tooth: number, type: OdontogramType): ToothKind => {
  const n = tooth % 10;
  if (type === 'PEDIATRIC') {
    if (n >= 4) return 'molar';
    if (n === 3) return 'canine';
    return 'incisor';
  }
  if (n >= 6) return 'molar';
  if (n >= 4) return 'premolar';
  if (n === 3) return 'canine';
  return 'incisor';
};

const metrics: Record<ToothKind, { w: number; h: number }> = {
  molar: { w: 46, h: 76 },
  premolar: { w: 36, h: 74 },
  canine: { w: 32, h: 86 },
  incisor: { w: 31, h: 72 },
};

const toothPath = (kind: ToothKind, w: number, h: number) => {
  const cw = w / 2;
  const root = -h * 0.5;
  if (kind === 'molar') {
    return [
      `M ${-cw} 8`,
      `C ${-cw} 24 ${-w*0.36} 34 0 35`,
      `C ${w*0.36} 34 ${cw} 24 ${cw} 8`,
      `C ${w*0.42} -2 ${w*0.33} -11 ${w*0.28} -18`,
      `L ${w*0.2} ${root}`,
      `C ${w*0.1} ${root+8} ${w*0.07} ${-h*0.18} 0 ${-h*0.08}`,
      `C ${-w*0.07} ${-h*0.18} ${-w*0.1} ${root+8} ${-w*0.2} ${root}`,
      `L ${-w*0.28} -18`,
      `C ${-w*0.33} -11 ${-w*0.42} -2 ${-cw} 8 Z`,
    ].join(' ');
  }
  const rootScale = kind === 'canine' ? 0.62 : kind === 'incisor' ? 0.54 : 0.5;
  return [
    `M ${-cw} 8`,
    `C ${-cw} 24 ${-w*0.32} 33 0 34`,
    `C ${w*0.32} 33 ${cw} 24 ${cw} 8`,
    `C ${w*0.36} -3 ${w*0.18} -10 0 ${-h*rootScale}`,
    `C ${-w*0.18} -10 ${-w*0.36} -3 ${-cw} 8 Z`,
  ].join(' ');
};

const fissurePath = (kind: ToothKind, w: number) => {
  if (kind === 'molar') return `M ${-w*0.24} 18 Q ${-w*0.08} 10 0 20 Q ${w*0.08} 10 ${w*0.24} 18 M 0 20 L 0 30`;
  if (kind === 'premolar') return `M ${-w*0.16} 19 Q 0 12 ${w*0.16} 19`;
  return '';
};

const layoutFor = (type: OdontogramType) => {
  const upper = type === 'ADULT' ? ADULT_UPPER : CHILD_UPPER;
  const lower = type === 'ADULT' ? ADULT_LOWER : CHILD_LOWER;
  return { upper, lower };
};

export const PremiumOdontogramSVG: React.FC<PremiumOdontogramSVGProps> = ({
  type = 'ADULT',
  selectedTooth = null,
  multiSelectedTeeth = [],
  onToothClick,
  readOnly = false,
  className,
  showNumbers = true,
}) => {
  const [focusedTooth, setFocusedTooth] = useState<number | null>(null);
  const { upper, lower } = useMemo(() => layoutFor(type), [type]);
  const viewWidth = 960;
  const rowWidth = type === 'ADULT' ? 840 : 620;
  const upperY = 118;
  const lowerY = 236;

  const rowX = (index: number, count: number) => {
    if (count <= 1) return viewWidth / 2;
    const left = (viewWidth - rowWidth) / 2;
    return left + (rowWidth / (count - 1)) * index;
  };

  const renderTooth = (tooth: number, index: number, count: number, row: 'upper'|'lower') => {
    const kind = kindFor(tooth, type);
    const { w, h } = metrics[kind];
    const x = rowX(index, count);
    const y = row === 'upper' ? upperY : lowerY;
    const selected = tooth === selectedTooth || multiSelectedTeeth.includes(tooth);
    const transform = row === 'upper'
      ? `translate(${x} ${y})`
      : `translate(${x} ${y}) scale(1 -1)`;
    const numberY = row === 'upper' ? 34 : 322;

    return (
      <g key={tooth}>
        {showNumbers && (
          <text
            x={x}
            y={numberY}
            textAnchor="middle"
            className={cn(
              'select-none fill-text-muted text-[18px] font-black tracking-tight transition-colors',
              selected && 'fill-primary',
            )}
            aria-hidden="true"
          >
            {tooth}
          </text>
        )}

        <g
          transform={transform}
          tabIndex={readOnly ? undefined : 0}
          role={readOnly ? undefined : 'button'}
          aria-label={readOnly ? undefined : `Dent ${tooth}`}
          aria-pressed={readOnly ? undefined : selected}
          onFocus={() => setFocusedTooth(tooth)}
          onBlur={() => setFocusedTooth(null)}
          onClick={() => !readOnly && onToothClick?.(tooth)}
          onKeyDown={(event) => {
            if (readOnly) return;
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              onToothClick?.(tooth);
            }
          }}
          className={cn('group outline-none', !readOnly && 'cursor-pointer')}
        >
          {focusedTooth === tooth && (
            <ellipse
              cx={0}
              cy={0}
              rx={w * 0.72}
              ry={h * 0.64}
              fill="none"
              strokeWidth={2}
              strokeDasharray="5 4"
              className="stroke-primary"
            />
          )}

          <path
            d={toothPath(kind, w, h)}
            className={cn(
              'fill-card stroke-text-main transition-all duration-200',
              selected ? 'stroke-primary' : 'group-hover:stroke-primary',
            )}
            fillOpacity={selected ? 0.96 : 1}
            strokeOpacity={selected ? 1 : 0.72}
            strokeWidth={selected ? 2.6 : 1.9}
          />

          {selected && (
            <path
              d={toothPath(kind, w, h)}
              className="fill-primary stroke-primary pointer-events-none"
              fillOpacity={0.14}
              strokeOpacity={1}
              strokeWidth={2.8}
            />
          )}

          {!!fissurePath(kind, w) && (
            <path
              d={fissurePath(kind, w)}
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              className={cn('stroke-text-muted pointer-events-none', selected && 'stroke-primary')}
              opacity={0.78}
            />
          )}
        </g>
      </g>
    );
  };

  return (
    <div
      className={cn(
        'w-full rounded-2xl border border-border-main bg-card/80 p-2 sm:p-4 shadow-sm backdrop-blur-xl',
        className,
      )}
      data-premium-odontogram={type.toLowerCase()}
    >
      <svg
        viewBox="0 0 960 350"
        className="block h-auto w-full overflow-visible"
        role="group"
        aria-label={type === 'ADULT' ? 'Odontogramme adulte' : 'Odontogramme enfant'}
        preserveAspectRatio="xMidYMid meet"
      >
        <line
          x1="72"
          x2="888"
          y1="176"
          y2="176"
          className="stroke-border-main"
          strokeWidth="1"
          strokeOpacity="0.9"
        />

        {upper.map((tooth, index) => renderTooth(tooth, index, upper.length, 'upper'))}
        {lower.map((tooth, index) => renderTooth(tooth, index, lower.length, 'lower'))}
      </svg>
    </div>
  );
};

export default PremiumOdontogramSVG;
