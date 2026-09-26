import React, { useMemo, useState } from 'react';
import { cn } from '../../utils/cn';
import type { OdontogramType } from './types';
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

const CHILD_UPPER: Array<{ tooth:number; sourceX:number; sourceWidth:number }> = [
  { tooth:55, sourceX:229, sourceWidth:112 },
  { tooth:54, sourceX:326, sourceWidth:108 },
  { tooth:53, sourceX:610, sourceWidth:86 },
  { tooth:52, sourceX:699, sourceWidth:82 },
  { tooth:51, sourceX:788, sourceWidth:92 },
  { tooth:61, sourceX:881, sourceWidth:94 },
  { tooth:62, sourceX:974, sourceWidth:84 },
  { tooth:63, sourceX:1066, sourceWidth:86 },
  { tooth:64, sourceX:1340, sourceWidth:100 },
  { tooth:65, sourceX:1435, sourceWidth:106 },
];

const CHILD_LOWER: Array<{ tooth:number; sourceX:number; sourceWidth:number }> = [
  { tooth:85, sourceX:101, sourceWidth:94 },
  { tooth:84, sourceX:208, sourceWidth:94 },
  { tooth:83, sourceX:621, sourceWidth:80 },
  { tooth:82, sourceX:707, sourceWidth:78 },
  { tooth:81, sourceX:795, sourceWidth:78 },
  { tooth:71, sourceX:886, sourceWidth:78 },
  { tooth:72, sourceX:980, sourceWidth:78 },
  { tooth:73, sourceX:1071, sourceWidth:78 },
  { tooth:74, sourceX:1440, sourceWidth:100 },
  { tooth:75, sourceX:1532, sourceWidth:108 },
];

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

const childRow = (
  entries:Array<{tooth:number;sourceX:number;sourceWidth:number}>,
): ToothVisual[] => {
  const left = 105;
  const right = 895;
  return entries.map((entry,index)=>({
    ...entry,
    x:left + ((right-left) / (entries.length-1)) * index,
  }));
};

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

  const rows=useMemo(()=>{
    if(type==='PEDIATRIC'){
      return {upper:childRow(CHILD_UPPER),lower:childRow(CHILD_LOWER)};
    }
    return {
      upper:adultRow(ADULT_UPPER,ADULT_UPPER_SOURCE_X),
      lower:adultRow(ADULT_LOWER,ADULT_LOWER_SOURCE_X),
    };
  },[type]);

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

  const renderChildImage = (visual:ToothVisual,row:Row) => {
    const sourceWidth=visual.sourceWidth || 90;
    const sourceX=(visual.sourceX || 0) - sourceWidth/2;
    const sourceY=row==='upper' ? 285 : 485;
    const sourceHeight=row==='upper' ? 205 : 215;
    const targetWidth=row==='upper' ? 72 : 74;
    const targetHeight=row==='upper' ? 126 : 132;
    const targetY=row==='upper' ? 42 : 190;
    return (
      <svg
        key={`img-${visual.tooth}`}
        x={visual.x-targetWidth/2}
        y={targetY}
        width={targetWidth}
        height={targetHeight}
        viewBox={`${sourceX} ${sourceY} ${sourceWidth} ${sourceHeight}`}
        preserveAspectRatio="xMidYMid meet"
        overflow="hidden"
        aria-hidden="true"
      >
        <image href={adultReference} x="0" y="0" width="1672" height="941" />
      </svg>
    );
  };

  return (
    <div
      className={cn(
        'w-full rounded-2xl border border-border-main bg-card/80 p-1.5 shadow-sm backdrop-blur-xl sm:p-3',
        className,
      )}
      data-premium-odontogram={type.toLowerCase()}
      data-odontogram-asset="approved-raster-reference-v1"
    >
      <svg
        viewBox={`0 0 ${OUTER_WIDTH} ${OUTER_HEIGHT}`}
        className="block h-auto w-full overflow-visible"
        role="group"
        aria-label={type==='ADULT' ? 'Odontogramme adulte' : 'Odontogramme enfant'}
        preserveAspectRatio="xMidYMid meet"
      >
        {type==='ADULT'
          ? renderAdultBase()
          : <>
              {rows.upper.map(item=>renderChildImage(item,'upper'))}
              {rows.lower.map(item=>renderChildImage(item,'lower'))}
            </>
        }

        <line
          x1={type==='ADULT' ? 36 : 78}
          x2={type==='ADULT' ? 964 : 922}
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
