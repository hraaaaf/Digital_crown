import { useLayoutEffect, useState, type RefObject } from 'react';

/** Presentation only: inverse SVG screen CTM, never an anatomical transform. */
export function useCephaloUnitsPerPixel(
  ref: RefObject<SVGSVGElement | null>, enabled: boolean, viewBox: string,
): number {
  const [units, setUnits] = useState(1);
  useLayoutEffect(() => {
    const svg = ref.current;
    if (!svg || !enabled) return;
    const measure = () => {
      const matrix = svg.getScreenCTM();
      if (!matrix) return;
      const pxPerUnit = Math.hypot(matrix.a, matrix.b);
      if (pxPerUnit > 0 && Number.isFinite(pxPerUnit)) {
        const next = 1 / pxPerUnit;
        setUnits(previous => Math.abs(previous - next) > .005 ? next : previous);
      }
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(svg);
    return () => observer.disconnect();
  }, [ref, enabled, viewBox]);
  return units;
}
