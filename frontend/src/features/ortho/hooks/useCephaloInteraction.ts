import { useCallback, useEffect, useRef, useState, type MouseEvent } from 'react';
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
