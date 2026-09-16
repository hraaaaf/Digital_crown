import { CEPHALO_SCIENTIFIC_COLORS } from '../cephaloVisualSemantics';

interface CephaloSvgDefsProps {
  magX: number;
  magY: number;
  MAG_R: number;
  isPro: boolean;
}

export const CephaloSvgDefs = ({ magX, magY, MAG_R, isPro }: CephaloSvgDefsProps) => (
  <>
    <defs>
      <clipPath id="cephalo-mag-clip">
        <circle cx={magX} cy={magY} r={MAG_R} />
      </clipPath>
      {isPro && (
        <filter id="dc-glow-pro" x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      )}
      <linearGradient id="ghostFaceGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor={CEPHALO_SCIENTIFIC_COLORS.soft_tissue} stopOpacity="0.22" />
        <stop offset="60%" stopColor={CEPHALO_SCIENTIFIC_COLORS.soft_tissue} stopOpacity="0.08" />
        <stop offset="100%" stopColor={CEPHALO_SCIENTIFIC_COLORS.soft_tissue} stopOpacity="0" />
      </linearGradient>
      <filter id="skinGlow">
        <feGaussianBlur stdDeviation="15" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
      </filter>
    </defs>
  </>
);
