import React from 'react';
import { toDeg } from '../cephaloMath';

interface ToothProps {
  incisalPoint: { x: number; y: number };
  apexPoint: { x: number; y: number };
  color: string;
  isHovered: boolean;
  opacity?: number;
  isGhost?: boolean;
  isBeingDragged?: boolean;
  glowFilter?: string;
  performanceMode?: boolean;
}

export const AnatomicalTooth: React.FC<ToothProps> = React.memo(({
  incisalPoint, apexPoint, color,
  isHovered, opacity = 1,
  isGhost = false, isBeingDragged = false,
  glowFilter, performanceMode = false,
}) => {
  const cx = (incisalPoint.x + apexPoint.x) / 2;
  const cy = (incisalPoint.y + apexPoint.y) / 2;
  const dx = incisalPoint.x - apexPoint.x;
  const dy = incisalPoint.y - apexPoint.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const s = dist > 1 ? dist / 100 : 0.01;
  const angle = toDeg(Math.atan2(dy, dx)) - 90;

  const dash = isGhost ? '7,4' : undefined;
  const fillAlpha = isGhost ? 0.04 : isBeingDragged ? 0.28 : 0.14;
  const swC = isHovered && !isGhost ? 2.5 : 1.5;
  const swA = isHovered && !isGhost ? 2.2 : 1.2;

  return (
    <g
      transform={`translate(${cx},${cy}) rotate(${angle}) scale(${s})`}
      opacity={opacity}
      style={{ pointerEvents: 'none', filter: !performanceMode && isBeingDragged && !isGhost ? glowFilter : undefined }}
    >
      <path
        d="M 0,-52 C 15,-52 22,-28 22,-4 C 22,20 11,44 0,52 C -11,44 -22,20 -22,-4 C -22,-28 -15,-52 0,-52 Z"
        fill={color} fillOpacity={fillAlpha}
        stroke={color} strokeWidth={swC} strokeDasharray={dash}
        vectorEffect="non-scaling-stroke"
      />
      <line x1="-22" y1="0" x2="22" y2="0"
        stroke={color} strokeWidth="1"
        strokeDasharray={isGhost ? '5,3' : '3,3'}
        opacity="0.45" vectorEffect="non-scaling-stroke"
      />
      <line x1="0" y1="-2000" x2="0" y2="2000"
        stroke={color} strokeWidth={swA}
        strokeDasharray={isGhost ? '6,5' : undefined}
        opacity="0.80" vectorEffect="non-scaling-stroke"
      />
      {!isGhost && (
        <>
          <polygon points="0,-62 -7,-50 7,-50" fill={color} fillOpacity="0.95" vectorEffect="non-scaling-stroke" />
          <circle cx="0" cy="-52" r="3" fill={color} opacity="0.9" vectorEffect="non-scaling-stroke" />
          <circle cx="0" cy="52" r="2.8" fill={color} opacity="0.72" vectorEffect="non-scaling-stroke" />
        </>
      )}
    </g>
  );
});
AnatomicalTooth.displayName = 'AnatomicalTooth';
