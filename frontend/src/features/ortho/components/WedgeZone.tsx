import React from 'react';
import { toDeg, buildWedgePath, polarPoint } from '../cephaloMath';

interface WedgeZoneProps {
  apexPt: { x: number; y: number };
  incisalPt: { x: number; y: number };
  po: { x: number; y: number };
  or_: { x: number; y: number };
  label: string;
  normMean: number;
  normHalf: number;
  compHalf: number;
  colors: { norm: string; comp: string; severe: string; normLine: string };
}

export const WedgeZone: React.FC<WedgeZoneProps> = React.memo(({
  apexPt, incisalPt, po, or_,
  label, normMean, normHalf, compHalf, colors,
}) => {
  const toothVec = { x: incisalPt.x - apexPt.x, y: incisalPt.y - apexPt.y };
  const frkVec = { x: or_.x - po.x, y: or_.y - po.y };
  const toothMag = Math.sqrt(toothVec.x ** 2 + toothVec.y ** 2);
  const frkMag = Math.sqrt(frkVec.x ** 2 + frkVec.y ** 2);
  if (toothMag < 2 || frkMag < 2) return null;

  const cosA = Math.max(-1, Math.min(1,
    (toothVec.x * frkVec.x + toothVec.y * frkVec.y) / (toothMag * frkMag)
  ));
  const angle = 180 - (toDeg(Math.acos(cosA)) % 180);
  const delta = angle - normMean;

  const isNorm = Math.abs(delta) <= normHalf;
  const isComp = !isNorm && Math.abs(delta) <= compHalf;
  const fillColor = isNorm ? colors.norm : isComp ? colors.comp : colors.severe;

  const R = Math.min(Math.max(toothMag * 0.85, 50), 130);
  const Rinner = R * 0.34;
  const frkAngle = toDeg(Math.atan2(frkVec.y, frkVec.x));
  const toothAngle = toDeg(Math.atan2(toothVec.y, toothVec.x));

  let sweep = toothAngle - frkAngle;
  while (sweep > 180) sweep -= 360;
  while (sweep < -180) sweep += 360;

  const normAxis = frkAngle + (normMean - 90);
  const dCurrent = buildWedgePath(apexPt.x, apexPt.y, R, Rinner, frkAngle, sweep);
  const dNorm = buildWedgePath(apexPt.x, apexPt.y, R * 0.92, Rinner * 1.08, normAxis - normHalf, normHalf * 2);
  const dComp = buildWedgePath(apexPt.x, apexPt.y, R, Rinner, normAxis - compHalf, compHalf * 2);
  const normEnd = polarPoint(apexPt.x, apexPt.y, R * 1.12, normAxis);
  const labelPos = polarPoint(apexPt.x, apexPt.y, R + 20, toothAngle);

  return (
    <g className="pointer-events-none">
      <path d={dComp} fill={colors.comp} fillOpacity="0.09"
        stroke={colors.comp} strokeWidth="0.8" strokeDasharray="3,2" vectorEffect="non-scaling-stroke" />
      <path d={dNorm} fill={colors.norm} fillOpacity="0.14"
        stroke={colors.norm} strokeWidth="0.9" vectorEffect="non-scaling-stroke" />
      <path d={dCurrent} fill={fillColor} fillOpacity="0.22"
        stroke={fillColor} strokeWidth="1.4" vectorEffect="non-scaling-stroke" />
      <line x1={apexPt.x} y1={apexPt.y} x2={normEnd.x} y2={normEnd.y}
        stroke={colors.normLine} strokeWidth="1.3" strokeDasharray="5,3"
        opacity="0.9" vectorEffect="non-scaling-stroke" />
      <circle cx={apexPt.x} cy={apexPt.y} r="4"
        fill={fillColor} fillOpacity="0.5" stroke={fillColor}
        strokeWidth="1" vectorEffect="non-scaling-stroke" />
      <text x={labelPos.x} y={labelPos.y} fontSize="11"
        fontFamily="'IBM Plex Mono','JetBrains Mono',monospace" fontWeight="800"
        fill={fillColor} textAnchor="middle" dominantBaseline="middle"
        style={{ userSelect: 'none', pointerEvents: 'none' }}>
        {label} {angle.toFixed(1)}°
      </text>
    </g>
  );
});
WedgeZone.displayName = 'WedgeZone';
