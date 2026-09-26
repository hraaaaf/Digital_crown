import React, { useMemo, useState } from 'react';
import { cn } from '../../utils/cn';
import type { OdontogramType, PediatricToothNumber } from './types';
import { ANATOMICAL_MAPPING } from './types';
import adultReference from '../../assets/odontogram/DigitalCrown_odontogram_adult_reference_v1.png';

interface PremiumOdontogramSVGProps {
  type?: OdontogramType;
  selectedTooth?: number | null;
  multiSelectedTeeth?: number[];
  onToothClick?: (toothNumber: number) => void;
  readOnly?: boolean;
  className?: string;
  showNumbers?: boolean;
}

type Row = 'upper' | 'lower';

interface ToothVisual {
  tooth: number;
  x: number;
  sourceX?: number;
  sourceWidth?: number;
}

const ADULT_UPPER = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
const ADULT_LOWER = [48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];

const ADULT_UPPER_SOURCE_X = [100,229,326,423,516,610,699,788,881,974,1066,1158,1250,1340,1435,1530];
const ADULT_LOWER_SOURCE_X = [101,208,319,430,527,621,707,795,886,980,1071,1162,1254,1348,1440,1532];

const CHILD_REFERENCE = '/assets/odontogram/pediatric-anatomical.jpg';
const CHILD_TEETH = Object.keys(ANATOMICAL_MAPPING.PEDIATRIC).map(Number) as PediatricToothNumber[];


const OUTER_WIDTH = 1000;
const OUTER_HEIGHT = 365;
const ADULT_LEFT = 24;
const ADULT_RENDER_WIDTH = 952;
const SOURCE_WIDTH = 1672;

const adultRow = (teeth:number[], sourceXs:number[]): ToothVisual[] =>
  teeth.map((tooth,index)=>({
    tooth,
    sourceX:sourceXs[index],
    x:ADULT_LEFT + (sourceXs[index] / SOURCE_WIDTH) * ADULT_RENDER_WIDTH,
  }));



export const PremiumOdontogramSVG: React.FC<PremiumOdontogramSVGProps> = ({
  type='ADULT',
  selectedTooth=null,
  multiSelectedTeeth=[],
  onToothClick,
  readOnly=false,
  className,
  showNumbers=true,
}) => {
  const [focusedTooth,setFocusedTooth]=useState<number|null>(null);
  const [hoveredTooth,setHoveredTooth]=useState<number|null>(null);

  const rows=useMemo(()=>({
    upper:adultRow(ADULT_UPPER,ADULT_UPPER_SOURCE_X),
    lower:adultRow(ADULT_LOWER,ADULT_LOWER_SOURCE_X),
  }),[]);

  const renderInteraction = (visual:ToothVisual,row:Row) => {
    const selected=visual.tooth===selectedTooth || multiSelectedTeeth.includes(visual.tooth);
    const focused=focusedTooth===visual.tooth;
    const hovered=hoveredTooth===visual.tooth;
    const cy=row==='upper' ? 126 : 258;
    const rx=type==='PEDIATRIC' ? 40 : 27;
    const ry=type==='PEDIATRIC' ? 62 : 58;
    const labelY=row==='upper' ? 24 : 354;

    return (
      <g key={visual.tooth}>
        {showNumbers && (
          <text
            x={visual.x}
            y={labelY}
            textAnchor="middle"
            className={cn(
              'select-none fill-text-muted text-[17px] font-black transition-colors',
              selected && 'fill-primary',
            )}
            aria-hidden="true"
          >
            {visual.tooth}
          </text>
        )}

        {(selected || hovered) && (
          <ellipse
            cx={visual.x}
            cy={cy}
            rx={rx}
            ry={ry}
            className="fill-primary stroke-primary pointer-events-none"
            fillOpacity={selected ? 0.16 : 0.07}
            strokeOpacity={selected ? 0.95 : 0.35}
            strokeWidth={selected ? 3 : 1.5}
          />
        )}

        {selected && (
          <circle
            cx={visual.x}
            cy={row==='upper' ? 60 : 322}
            r={7}
            className="fill-primary stroke-card pointer-events-none"
            strokeWidth={3}
          />
        )}

        {focused && (
          <ellipse
            cx={visual.x}
            cy={cy}
            rx={rx+5}
            ry={ry+5}
            fill="none"
            className="stroke-primary pointer-events-none"
            strokeWidth={2.5}
            strokeDasharray="7 5"
          />
        )}

        <ellipse
          cx={visual.x}
          cy={cy}
          rx={rx+5}
          ry={ry+7}
          fill="transparent"
          tabIndex={readOnly ? undefined : 0}
          role={readOnly ? undefined : 'button'}
          aria-label={readOnly ? undefined : `Dent ${visual.tooth}`}
          aria-pressed={readOnly ? undefined : selected}
          onMouseEnter={()=>setHoveredTooth(visual.tooth)}
          onMouseLeave={()=>setHoveredTooth(null)}
          onFocus={()=>setFocusedTooth(visual.tooth)}
          onBlur={()=>setFocusedTooth(null)}
          onClick={()=>!readOnly && onToothClick?.(visual.tooth)}
          onKeyDown={(event)=>{
            if(readOnly) return;
            if(event.key==='Enter' || event.key===' '){
              event.preventDefault();
              onToothClick?.(visual.tooth);
            }
          }}
          className={cn('outline-none',!readOnly && 'cursor-pointer')}
        />
      </g>
    );
  };

  const renderAdultBase = () => (
    <>
      <svg x="24" y="42" width="952" height="128" viewBox="0 285 1672 205" preserveAspectRatio="none" overflow="hidden" aria-hidden="true">
        <image href={adultReference} x="0" y="0" width="1672" height="941" preserveAspectRatio="none" />
      </svg>
      <svg x="24" y="188" width="952" height="137" viewBox="0 485 1672 215" preserveAspectRatio="none" overflow="hidden" aria-hidden="true">
        <image href={adultReference} x="0" y="0" width="1672" height="941" preserveAspectRatio="none" />
      </svg>
    </>
  );

  const renderChild = () => (
    <div
      className={cn(
        'relative w-full overflow-hidden rounded-2xl border border-border-main bg-card/80 p-1.5 shadow-sm backdrop-blur-xl sm:p-3',
        className,
      )}
      data-premium-odontogram="pediatric"
      data-odontogram-asset="legacy-pediatric-anatomy"
    >
      <div className="relative w-full">
        <img
          src={CHILD_REFERENCE}
          alt=""
          aria-hidden="true"
          className="block h-auto w-full select-none opacity-0 pointer-events-none"
        />
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute inset-0 block h-full w-full"
          role="group"
          aria-label="Odontogramme enfant"
        >
          <defs>
            <filter id="premium-child-extract-lines">
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
            <mask id="premium-child-blueprint-mask">
              <image
                href={CHILD_REFERENCE}
                x="0"
                y="0"
                width="100"
                height="100"
                preserveAspectRatio="none"
                filter="url(#premium-child-extract-lines)"
              />
            </mask>
          </defs>

          <rect
            x="0"
            y="0"
            width="100"
            height="100"
            className="fill-text-main pointer-events-none"
            mask="url(#premium-child-blueprint-mask)"
          />

          {CHILD_TEETH.map(tooth => {
            const point=ANATOMICAL_MAPPING.PEDIATRIC[tooth];
            const selected=tooth===selectedTooth || multiSelectedTeeth.includes(tooth);
            const focused=focusedTooth===tooth;
            const hovered=hoveredTooth===tooth;
            const upper=tooth>=51 && tooth<=65;
            const radius=point.r || 3;
            const labelY=upper
              ? Math.max(4,point.y-radius-4.5)
              : Math.min(97,point.y+radius+6);

            return (
              <g key={tooth}>
                {showNumbers && (
                  <text
                    x={point.x}
                    y={labelY}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    className={cn(
                      'select-none fill-text-main text-[2.8px] font-black pointer-events-none',
                      selected && 'fill-primary',
                    )}
                  >
                    {tooth}
                  </text>
                )}

                {(selected || hovered) && (
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r={radius*(selected ? 1.3 : 1.18)}
                    className="fill-primary stroke-primary pointer-events-none"
                    fillOpacity={selected ? 0.17 : 0.07}
                    strokeOpacity={selected ? 0.95 : 0.38}
                    strokeWidth={selected ? 0.5 : 0.28}
                    vectorEffect="non-scaling-stroke"
                  />
                )}

                {selected && (
                  <circle
                    cx={point.x+radius*0.9}
                    cy={point.y-radius*0.9}
                    r="0.8"
                    className="fill-primary stroke-card pointer-events-none"
                    strokeWidth="0.3"
                    vectorEffect="non-scaling-stroke"
                  />
                )}

                {focused && (
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r={radius*1.48}
                    fill="none"
                    className="stroke-primary pointer-events-none"
                    strokeWidth="0.38"
                    strokeDasharray="1.1 0.75"
                    vectorEffect="non-scaling-stroke"
                  />
                )}

                <circle
                  cx={point.x}
                  cy={point.y}
                  r={radius*1.55}
                  fill="transparent"
                  tabIndex={readOnly ? undefined : 0}
                  role={readOnly ? undefined : 'button'}
                  aria-label={readOnly ? undefined : `Dent ${tooth}`}
                  aria-pressed={readOnly ? undefined : selected}
                  onMouseEnter={()=>setHoveredTooth(tooth)}
                  onMouseLeave={()=>setHoveredTooth(null)}
                  onFocus={()=>setFocusedTooth(tooth)}
                  onBlur={()=>setFocusedTooth(null)}
                  onClick={()=>!readOnly && onToothClick?.(tooth)}
                  onKeyDown={(event)=>{
                    if(readOnly) return;
                    if(event.key==='Enter' || event.key===' '){
                      event.preventDefault();
                      onToothClick?.(tooth);
                    }
                  }}
                  className={cn('outline-none',!readOnly && 'cursor-pointer')}
                />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );


  if(type==='PEDIATRIC') return renderChild();

  return (
    <div
      className={cn(
        'w-full rounded-2xl border border-border-main bg-card/80 p-1.5 shadow-sm backdrop-blur-xl sm:p-3',
        className,
      )}
      data-premium-odontogram="adult"
      data-odontogram-asset="approved-raster-reference-v1"
    >
      <svg
        viewBox={`0 0 ${OUTER_WIDTH} ${OUTER_HEIGHT}`}
        className="block h-auto w-full overflow-visible"
        role="group"
        aria-label="Odontogramme adulte"
        preserveAspectRatio="xMidYMid meet"
      >
        {renderAdultBase()}

        <line
          x1="36"
          x2="964"
          y1="181"
          y2="181"
          className="stroke-border-main pointer-events-none"
          strokeWidth="1.5"
        />

        {rows.upper.map(item=>renderInteraction(item,'upper'))}
        {rows.lower.map(item=>renderInteraction(item,'lower'))}
      </svg>
    </div>
  );
};

export default PremiumOdontogramSVG;
