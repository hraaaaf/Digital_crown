interface CephaloCalibrationOverlayProps {
  isCalibrating: boolean;
  activeDragId: string | null;
  magnifier: { x: number; y: number; show: boolean };
  calibrationPoints?: { x: number; y: number }[];
}

export const CephaloCalibrationOverlay = ({
  isCalibrating,
  activeDragId,
  magnifier,
  calibrationPoints,
}: CephaloCalibrationOverlayProps) => (
  <>
    {/* ══ CALIBRATION ══════════════════════════════════════════════ */}
    {isCalibrating && (
      <g className="pointer-events-none">
        {/* Règle dynamique qui suit le curseur */}
        {!activeDragId && magnifier.show && (
          <g opacity="0.6">
            <line 
              x1={magnifier.x - 40} y1={magnifier.y} 
              x2={magnifier.x + 40} y2={magnifier.y} 
              stroke="#eab308" strokeWidth="0.5" strokeDasharray="2,2" 
            />
            <line 
              x1={magnifier.x} y1={magnifier.y - 40} 
              x2={magnifier.x} y2={magnifier.y + 40} 
              stroke="#eab308" strokeWidth="0.5" strokeDasharray="2,2" 
            />
            <circle cx={magnifier.x} cy={magnifier.y} r="15" fill="none" stroke="#eab308" strokeWidth="0.5" strokeDasharray="1,2" />
          </g>
        )}

        {calibrationPoints && calibrationPoints.map((cpt, i) => (
          <g key={`calib-group-${i}`}>
            <path
              d={[
                `M ${cpt.x - 16} ${cpt.y} L ${cpt.x + 16} ${cpt.y}`,
                `M ${cpt.x} ${cpt.y - 16} L ${cpt.x} ${cpt.y + 16}`,
              ].join(' ')}
              stroke="#eab308" strokeWidth="2" vectorEffect="non-scaling-stroke" 
            />
            <circle cx={cpt.x} cy={cpt.y} r="4" fill="#eab308" />
          </g>
        ))}
        {calibrationPoints && calibrationPoints.length === 2 && (
          <g>
            <line
              x1={calibrationPoints[0].x} y1={calibrationPoints[0].y}
              x2={calibrationPoints[1].x} y2={calibrationPoints[1].y}
              stroke="#eab308" strokeWidth="2" strokeDasharray="6,4"
              vectorEffect="non-scaling-stroke" 
            />
            <rect 
              x={Math.min(calibrationPoints[0].x, calibrationPoints[1].x) + Math.abs(calibrationPoints[0].x - calibrationPoints[1].x)/2 - 20}
              y={Math.min(calibrationPoints[0].y, calibrationPoints[1].y) + Math.abs(calibrationPoints[0].y - calibrationPoints[1].y)/2 - 10}
              width="40" height="20" rx="4" fill="#eab308" 
            />
            <text 
               x={Math.min(calibrationPoints[0].x, calibrationPoints[1].x) + Math.abs(calibrationPoints[0].x - calibrationPoints[1].x)/2}
               y={Math.min(calibrationPoints[0].y, calibrationPoints[1].y) + Math.abs(calibrationPoints[0].y - calibrationPoints[1].y)/2 + 4}
               fontSize="10" fontWeight="bold" fill="#000" textAnchor="middle"
            >
              REF
            </text>
          </g>
        )}
      </g>
    )}
  </>
);
