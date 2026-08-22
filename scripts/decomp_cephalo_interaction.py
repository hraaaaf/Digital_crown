from pathlib import Path

PAGE = Path("frontend/src/features/ortho/CephaloTracingLayer.tsx")
OUT = Path("frontend/src/features/ortho/hooks/useCephaloInteraction.ts")

text = PAGE.read_text(encoding="utf-8")

if "useCephaloInteraction" in text:
    raise SystemExit("Cephalo interaction hook already extracted; refusing duplicate refactor")
if "const svgRef = useRef<SVGSVGElement>(null);" not in text:
    raise SystemExit("svgRef baseline changed; refusing automated refactor")
if "const clientToSVG = useCallback" not in text or "getScreenCTM()" not in text or "ctm.inverse()" not in text:
    raise SystemExit("canonical clientToSVG baseline changed; refusing automated refactor")
if "const handleSvgClick = useCallback" not in text:
    raise SystemExit("SVG click handler baseline changed; refusing automated refactor")

start1 = text.index("  // ── Refs")
hover_marker = "  // HOVER METRIC"
end1 = text.index(hover_marker, start1)

click_marker = "  // CLICK HANDLER (calibration / empty area)"
click_start = text.index(click_marker, end1)
loupe_marker = "  // LOUPE — positionnement adaptatif (évite les bords)"
click_end = text.index(loupe_marker, click_start)

hook = '''import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react';
import type { Landmark } from '../cephaloShared';

interface UseCephaloInteractionParams {
  landmarks: Landmark[];
  imageWidth: number;
  imageHeight: number;
  magnifierEnabled: boolean;
  isCalibrating: boolean;
  onAddCalibrationPoint?: (p: { x: number; y: number }) => void;
  onEmptyAreaClick?: (p: { x: number; y: number }) => void;
}

export const useCephaloInteraction = ({
  landmarks,
  imageWidth,
  imageHeight,
  magnifierEnabled,
  isCalibrating,
  onAddCalibrationPoint,
  onEmptyAreaClick,
}: UseCephaloInteractionParams) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [activeDragId, setActiveDragId] = useState<string | null>(null);
  const [activeDragPos, setActiveDragPos] = useState<{ id: string; x: number; y: number } | null>(null);
  const [magnifier, setMagnifier] = useState<{ x: number; y: number; show: boolean }>(
    { x: 0, y: 0, show: false }
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!magnifierEnabled && magnifier.show) setMagnifier(m => ({ ...m, show: false }));
  }, [magnifierEnabled]); // eslint-disable-line

  // Canonical v4.2 coordinate conversion. Do not replace with bounding-rect scaling.
  const clientToSVG = useCallback((clientX: number, clientY: number): { x: number; y: number } | null => {
    const svg = svgRef.current;
    if (!svg) return null;
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const svgPt = pt.matrixTransform(ctm.inverse());
    return {
      x: Math.max(0, Math.min(imageWidth, svgPt.x)),
      y: Math.max(0, Math.min(imageHeight, svgPt.y)),
    };
  }, [imageWidth, imageHeight]);

  // Resolve activeDragPos for the live landmark so skeletal lines/wedges follow the cursor.
  const getPoint = useCallback((pts: Landmark[], id: string): Landmark | undefined => {
    const pt = pts.find(l => l.id === id || l.id.toLowerCase() === id.toLowerCase());
    const adp = activeDragPos;
    if (pts === landmarks && pt && adp?.id === pt.id) {
      return { ...pt, x: adp.x, y: adp.y };
    }
    return pt;
  }, [landmarks, activeDragPos]);

  const handleSvgClick = useCallback((e: MouseEvent<SVGSVGElement>) => {
    if (activeDragId) return;
    const coords = clientToSVG(e.clientX, e.clientY);
    if (!coords) return;
    if (isCalibrating && onAddCalibrationPoint) {
      onAddCalibrationPoint(coords);
      return;
    }
    if (e.target === e.currentTarget && onEmptyAreaClick) {
      onEmptyAreaClick(coords);
    }
  }, [clientToSVG, activeDragId, isCalibrating, onAddCalibrationPoint, onEmptyAreaClick]);

  return {
    svgRef,
    activeDragId,
    setActiveDragId,
    activeDragPos,
    setActiveDragPos,
    magnifier,
    setMagnifier,
    clientToSVG,
    getPoint,
    handleSvgClick,
  };
};
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(hook, encoding="utf-8")

interaction_call = '''  const {
    svgRef,
    activeDragId,
    setActiveDragId,
    activeDragPos,
    setActiveDragPos,
    magnifier,
    setMagnifier,
    clientToSVG,
    getPoint,
    handleSvgClick,
  } = useCephaloInteraction({
    landmarks,
    imageWidth,
    imageHeight,
    magnifierEnabled,
    isCalibrating,
    onAddCalibrationPoint,
    onEmptyAreaClick,
  });

'''

updated = text[:start1] + interaction_call + text[end1:click_start] + text[click_end:]
updated = updated.replace(
    "import React, { useState, useRef, useCallback, useEffect } from 'react';",
    "import React from 'react';",
    1,
)
anchor = "import { CephaloMagnifierOverlay } from './components/CephaloMagnifierOverlay';\n"
if anchor not in updated:
    raise SystemExit("cephalo overlay import anchor missing")
updated = updated.replace(
    anchor,
    anchor + "import { useCephaloInteraction } from './hooks/useCephaloInteraction';\n",
    1,
)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
hook_final = OUT.read_text(encoding="utf-8")

# Structural safety gates for the v4.2 drag fix.
for token in ["getScreenCTM()", "ctm.inverse()", "createSVGPoint()"]:
    if token not in hook_final:
        raise SystemExit(f"canonical coordinate token missing from hook: {token}")
if "getBoundingClientRect" in hook_final:
    raise SystemExit("forbidden manual coordinate conversion introduced")
for token in [
    "setPointerCapture(e.pointerId)",
    "setActiveDragPos({ id: pt.id, ...coords })",
    "onUpdateLandmarks(",
    "const dispX = isDragged && activeDragPos ? activeDragPos.x : pt.x;",
    "const dispY = isDragged && activeDragPos ? activeDragPos.y : pt.y;",
]:
    if token not in final:
        raise SystemExit(f"pointer/drag contract moved or changed unexpectedly: {token}")
if final.count("useCephaloInteraction({") != 1:
    raise SystemExit("interaction hook replacement missing or duplicated")

print("P0-B2 prepared: cephalo interaction foundation extracted with v4.2 drag contract preserved")
