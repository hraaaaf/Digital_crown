import React, { useMemo, useState } from 'react';
import { cn } from '../../utils/cn';
import type { OdontogramType } from './types';
import { ANATOMICAL_MAPPING } from './types';

interface PremiumOdontogramSVGProps {
  type?: OdontogramType;
  selectedTooth?: number | null;
  multiSelectedTeeth?: number[];
  onToothClick?: (toothNumber: number) => void;
  readOnly?: boolean;
  className?: string;
  showNumbers?: boolean;
}

const ADULT_REFERENCE = '/assets/odontogram/digital-crown-adult-reference-v2.png';
const CHILD_REFERENCE = '/assets/odontogram/digital-crown-child-reference-v2.png';

const ADULT_UPPER = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
const ADULT_LOWER = [48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
const CHILD_UPPER = [55,54,53,52,51,61,62,63,64,65];
const CHILD_LOWER = [85,84,83,82,81,71,72,73,74,75];

const VIEWBOX_WIDTH = 1000;
const VIEWBOX_HEIGHT = 750;

export const PremiumOdontogramSVG: React.FC<PremiumOdontogramSVGProps> = ({
  type='ADULT',
  selectedTooth=null,
  multiSelectedTeeth=[],
  onToothClick,
  readOnly=false,
  className,
}) => {
  const [focusedTooth,setFocusedTooth]=useState<number|null>(null);
  const [hoveredTooth,setHoveredTooth]=useState<number|null>(null);

  const teeth = useMemo(
    () => type === 'ADULT'
      ? [...ADULT_UPPER, ...ADULT_LOWER]
      : [...CHILD_UPPER, ...CHILD_LOWER],
    [type],
  );

  const reference = type === 'ADULT' ? ADULT_REFERENCE : CHILD_REFERENCE;
  const mapping = type === 'ADULT' ? ANATOMICAL_MAPPING.ADULT : ANATOMICAL_MAPPING.PEDIATRIC;
  const asset = type === 'ADULT' ? 'user-reference-adult-v2' : 'user-reference-child-v2';

  return (
    <div
      className={cn(
        'w-full rounded-2xl border border-border-main bg-card/80 p-1.5 shadow-sm backdrop-blur-xl sm:p-3',
        className,
      )}
      data-premium-odontogram={type === 'ADULT' ? 'adult' : 'pediatric'}
      data-odontogram-asset={asset}
    >
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        className="block h-auto w-full overflow-visible"
        role="group"
        aria-label={type === 'ADULT' ? 'Odontogramme adulte' : 'Odontogramme enfant'}
        preserveAspectRatio="xMidYMid meet"
      >
        <image
          href={reference}
          x="0"
          y="0"
          width={VIEWBOX_WIDTH}
          height={VIEWBOX_HEIGHT}
          preserveAspectRatio="xMidYMid meet"
          aria-hidden="true"
          className="pointer-events-none"
        />

        {teeth.map((tooth) => {
          const point = mapping[tooth as keyof typeof mapping] as { x:number; y:number; r?:number } | undefined;
          if (!point) return null;

          const cx = point.x * 10;
          const cy = point.y * 7.5;
          const baseRadius = point.r ?? (type === 'ADULT' ? 3.4 : 4.2);
          const rx = baseRadius * 10;
          const ry = type === 'ADULT' ? 66 : 72;
          const selected = selectedTooth === tooth || multiSelectedTeeth.includes(tooth);
          const focused = focusedTooth === tooth;
          const hovered = hoveredTooth === tooth;

          return (
            <g key={tooth}>
              {(selected || hovered) && (
                <ellipse
                  cx={cx}
                  cy={cy}
                  rx={rx}
                  ry={ry}
                  className="fill-primary stroke-primary pointer-events-none"
                  fillOpacity={selected ? 0.13 : 0.05}
                  strokeOpacity={selected ? 0.95 : 0.35}
                  strokeWidth={selected ? 3 : 1.5}
                />
              )}

              {focused && (
                <ellipse
                  cx={cx}
                  cy={cy}
                  rx={rx + 6}
                  ry={ry + 6}
                  fill="none"
                  className="stroke-primary pointer-events-none"
                  strokeWidth={2.5}
                  strokeDasharray="7 5"
                />
              )}

              <ellipse
                cx={cx}
                cy={cy}
                rx={rx + 6}
                ry={ry + 7}
                fill="transparent"
                tabIndex={readOnly ? undefined : 0}
                role={readOnly ? undefined : 'button'}
                aria-label={readOnly ? undefined : `Dent ${tooth}`}
                aria-pressed={readOnly ? undefined : selected}
                onMouseEnter={() => setHoveredTooth(tooth)}
                onMouseLeave={() => setHoveredTooth(null)}
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
                className={cn('outline-none', !readOnly && 'cursor-pointer')}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};

export default PremiumOdontogramSVG;
