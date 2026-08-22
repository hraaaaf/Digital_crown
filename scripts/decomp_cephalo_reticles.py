from pathlib import Path
import textwrap

PAGE = Path("frontend/src/features/ortho/CephaloTracingLayer.tsx")
OUT = Path("frontend/src/features/ortho/components/CephaloLandmarkReticles.tsx")

text = PAGE.read_text(encoding="utf-8")

START = "        {/* ══ RÉTICULES — Pointer Events natifs (v4.2)"
END = "        <CephaloCalibrationOverlay"
if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("reticles sentinels changed; refusing automated refactor")
if "CephaloLandmarkReticles" in text:
    raise SystemExit("reticles already extracted; refusing duplicate refactor")

start = text.index(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

required = [
    "setPointerCapture(e.pointerId)",
    "const dispX = isDragged && activeDragPos ? activeDragPos.x : pt.x;",
    "const dispY = isDragged && activeDragPos ? activeDragPos.y : pt.y;",
    "setActiveDragPos({ id: pt.id, ...coords })",
    "onUpdateLandmarks(",
    "clientToSVG(e.clientX, e.clientY)",
]
for token in required:
    if token not in body:
        raise SystemExit(f"reticles drag contract changed; missing: {token}")

component = '''import type { Dispatch, SetStateAction } from 'react';
import { motion } from 'framer-motion';
import type { Landmark } from '../cephaloShared';

const SOFT_TISSUE_IDS = new Set([
  'ul', 'll', 'sn', 'stpog', 'ls', 'li', 'prn', 'cm', 'g_soft', 'n_soft', 'a_soft', 'st', 'b_soft', 'pog_soft', 'me_soft', 'g-soft', 'n-soft'
]);

interface CephaloLandmarkReticlesProps {
  landmarks: Landmark[];
  isCalibrating: boolean;
  baseOpacity: number;
  activeDragId: string | null;
  activeDragPos: { id: string; x: number; y: number } | null;
  activePointId?: string | null;
  focusedPointId?: string | null;
  hoveredMetric?: { key: string; points: string[]; lines: string[] } | null;
  palette: { ptU: string; ptL: string; ptDefault: string; isolationDim: number };
  isPro: boolean;
  setActiveDragId: Dispatch<SetStateAction<string | null>>;
  setActiveDragPos: Dispatch<SetStateAction<{ id: string; x: number; y: number } | null>>;
  magnifierEnabled: boolean;
  setMagnifier: Dispatch<SetStateAction<{ x: number; y: number; show: boolean }>>;
  clientToSVG: (clientX: number, clientY: number) => { x: number; y: number } | null;
  onPointMouseDown?: (id: string) => void;
  onUpdateLandmarks: (newLandmarks: Landmark[]) => void;
}

export const CephaloLandmarkReticles = ({
  landmarks,
  isCalibrating,
  baseOpacity,
  activeDragId,
  activeDragPos,
  activePointId,
  focusedPointId,
  hoveredMetric,
  palette,
  isPro,
  setActiveDragId,
  setActiveDragPos,
  magnifierEnabled,
  setMagnifier,
  clientToSVG,
  onPointMouseDown,
  onUpdateLandmarks,
}: CephaloLandmarkReticlesProps) => {
  const P = palette;
  const isHoverActive = !!hoveredMetric;
  const isPointHovered = (ptId: string) =>
    !isHoverActive ||
    hoveredMetric!.points.map(p => p.toLowerCase()).includes(ptId.toLowerCase());

  return (
    <>
''' + textwrap.indent(body, "      ") + '''
    </>
  );
};
'''

OUT.write_text(component, encoding="utf-8")

replacement = '''        <CephaloLandmarkReticles
          landmarks={landmarks}
          isCalibrating={isCalibrating}
          baseOpacity={baseOpacity}
          activeDragId={activeDragId}
          activeDragPos={activeDragPos}
          activePointId={activePointId}
          focusedPointId={focusedPointId}
          hoveredMetric={hoveredMetric}
          palette={P}
          isPro={isPro}
          setActiveDragId={setActiveDragId}
          setActiveDragPos={setActiveDragPos}
          magnifierEnabled={magnifierEnabled}
          setMagnifier={setMagnifier}
          clientToSVG={clientToSVG}
          onPointMouseDown={onPointMouseDown}
          onUpdateLandmarks={onUpdateLandmarks}
        />

'''
updated = text[:start] + replacement + text[end:]

anchor = "import { CephaloMagnifierOverlay } from './components/CephaloMagnifierOverlay';\n"
if anchor not in updated:
    raise SystemExit("magnifier import anchor missing")
updated = updated.replace(
    anchor,
    anchor + "import { CephaloLandmarkReticles } from './components/CephaloLandmarkReticles';\n",
    1,
)

# SOFT_TISSUE_IDS is now owned by the reticles component.
soft_start = updated.index("const SOFT_TISSUE_IDS = new Set([")
soft_end = updated.index("]);", soft_start) + len("]);")
updated = updated[:soft_start] + updated[soft_end:]

# isPointHovered is now local to the reticles component; line-hover logic stays in parent.
point_hover = '''  const isPointHovered = (ptId: string) =>
    !isHoverActive ||
    hoveredMetric!.points.map(p => p.toLowerCase()).includes(ptId.toLowerCase());
'''
if point_hover not in updated:
    raise SystemExit("point hover baseline changed")
updated = updated.replace(point_hover, "", 1)

PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
child = OUT.read_text(encoding="utf-8")
if final.count("<CephaloLandmarkReticles") != 1:
    raise SystemExit("reticles replacement missing or duplicated")
for token in required:
    if token not in child:
        raise SystemExit(f"drag contract missing from extracted reticles: {token}")
if "getBoundingClientRect" in child:
    raise SystemExit("forbidden manual coordinate conversion introduced")

print("P0-B3 prepared: landmark reticles extracted mechanically with pointer contract preserved")
