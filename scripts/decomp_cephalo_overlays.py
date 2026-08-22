from pathlib import Path
import textwrap

PAGE = Path("frontend/src/features/ortho/CephaloTracingLayer.tsx")
CAL_OUT = Path("frontend/src/features/ortho/components/CephaloCalibrationOverlay.tsx")
MAG_OUT = Path("frontend/src/features/ortho/components/CephaloMagnifierOverlay.tsx")

CAL_START = "        {/* ══ CALIBRATION"
MAG_START = "        {/* ══ LOUPE SVG PIXEL-PERFECT"
SVG_END = "      </svg>\n"
IMPORT_ANCHOR = "import { WedgeZone } from './components/WedgeZone';\n"

text = PAGE.read_text(encoding="utf-8")
if text.count(CAL_START) != 1 or text.count(MAG_START) != 1 or text.count(SVG_END) != 1:
    raise SystemExit("Cephalo overlay sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("Cephalo import anchor changed; refusing automated refactor")
if "CephaloCalibrationOverlay" in text or "CephaloMagnifierOverlay" in text:
    raise SystemExit("Cephalo overlays already extracted; refusing duplicate refactor")

cal_start = text.index(CAL_START)
mag_start = text.index(MAG_START, cal_start)
svg_end = text.index(SVG_END, mag_start)
cal_block = textwrap.dedent(text[cal_start:mag_start]).rstrip()
mag_block = textwrap.dedent(text[mag_start:svg_end]).rstrip()

for token in ["isCalibrating", "calibrationPoints", "magnifier.show", "activeDragId"]:
    if token not in cal_block:
        raise SystemExit(f"Calibration baseline changed; missing {token}")
for token in ["magnifierEnabled", "MAG_ZOOM", "P.magnifierRing", "imageSrc"]:
    if token not in mag_block:
        raise SystemExit(f"Magnifier baseline changed; missing {token}")

cal_component = """interface CephaloCalibrationOverlayProps {
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
""" + textwrap.indent(cal_block, "    ") + "\n  </>\n);\n"

mag_component = """import type { ImageFilters } from '../cephaloShared';

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
""" + textwrap.indent(mag_block, "      ") + "\n    </>\n  );\n};\n"

CAL_OUT.parent.mkdir(parents=True, exist_ok=True)
CAL_OUT.write_text(cal_component, encoding="utf-8")
MAG_OUT.write_text(mag_component, encoding="utf-8")

replacement = """        <CephaloCalibrationOverlay
          isCalibrating={isCalibrating}
          activeDragId={activeDragId}
          magnifier={magnifier}
          calibrationPoints={calibrationPoints}
        />

        <CephaloMagnifierOverlay
          magnifierEnabled={magnifierEnabled}
          magnifier={magnifier}
          imageSrc={imageSrc}
          imageWidth={imageWidth}
          imageHeight={imageHeight}
          imgFilters={imgFilters}
          magX={magX}
          magY={magY}
          MAG_R={MAG_R}
          MAG_ZOOM={MAG_ZOOM}
          palette={P}
        />
"""

updated = text[:cal_start] + replacement + text[svg_end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { CephaloCalibrationOverlay } from './components/CephaloCalibrationOverlay';\nimport { CephaloMagnifierOverlay } from './components/CephaloMagnifierOverlay';\n",
    1,
)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<CephaloCalibrationOverlay") != 1 or final.count("<CephaloMagnifierOverlay") != 1:
    raise SystemExit("Cephalo overlay replacement missing")
if CAL_START in final or MAG_START in final:
    raise SystemExit("Original cephalo overlay blocks unexpectedly remain")

print("P0-B1 prepared: calibration and magnifier overlays extracted mechanically")
