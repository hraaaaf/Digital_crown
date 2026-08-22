import type { ImageFilters } from '../cephaloShared';

interface CephaloMagnifierOverlayProps {
  magnifierEnabled: boolean;
  magnifier: { x: number; y: number; show: boolean };
  imageSrc?: string;
  imageWidth: number;
  imageHeight: number;
  imgFilters?: ImageFilters;
  magX: number;
  magY: number;
  MAG_R: number;
  MAG_ZOOM: number;
  palette: {
    magnifierBg: string;
    magnifierRing: string;
    crosshairCol: string;
  };
}

export const CephaloMagnifierOverlay = ({
  magnifierEnabled,
  magnifier,
  imageSrc,
  imageWidth,
  imageHeight,
  imgFilters,
  magX,
  magY,
  MAG_R,
  MAG_ZOOM,
  palette,
}: CephaloMagnifierOverlayProps) => {
  const P = palette;
  return (
    <>
      {/* ══ LOUPE SVG PIXEL-PERFECT ═══════════════════════════════════
          Image repositionnée : x = magX - cursor.x × zoom
          Croix de visée au centre exact.
          ══════════════════════════════════════════════════════════ */}
      {magnifierEnabled && magnifier.show && imageSrc && (
        <g className="pointer-events-none">
          <circle cx={magX} cy={magY} r={MAG_R}
            fill={P.magnifierBg} stroke={P.magnifierRing}
            strokeWidth="2" vectorEffect="non-scaling-stroke" />
          <image
            href={imageSrc}
            x={magX - magnifier.x * MAG_ZOOM}
            y={magY - magnifier.y * MAG_ZOOM}
            width={imageWidth * MAG_ZOOM}
            height={imageHeight * MAG_ZOOM}
            clipPath="url(#cephalo-mag-clip)"
            preserveAspectRatio="none"
            style={{
              filter: [
                `brightness(${imgFilters?.brightness ?? 100}%)`,
                `contrast(${imgFilters?.contrast ?? 100}%)`,
                `invert(${imgFilters?.invert ? 100 : 0}%)`,
              ].join(' '),
            }}
          />
          <circle cx={magX} cy={magY} r={MAG_R - 1}
            fill="none" stroke={P.magnifierRing}
            strokeWidth="1" opacity="0.35" vectorEffect="non-scaling-stroke" />
          <line x1={magX - 14} y1={magY} x2={magX + 14} y2={magY}
            stroke={P.crosshairCol} strokeWidth="1.2" opacity="0.95" vectorEffect="non-scaling-stroke" />
          <line x1={magX} y1={magY - 14} x2={magX} y2={magY + 14}
            stroke={P.crosshairCol} strokeWidth="1.2" opacity="0.95" vectorEffect="non-scaling-stroke" />
          <circle cx={magX} cy={magY} r={2.2}
            fill={P.crosshairCol} opacity="1" vectorEffect="non-scaling-stroke" />
        </g>
      )}
    </>
  );
};
