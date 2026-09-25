import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

describe('OdontogramSVG theme inheritance contract', () => {
  it('uses Digital Crown semantic tokens instead of local palette literals', () => {
    const source = fs.readFileSync(path.resolve(__dirname, 'OdontogramSVG.tsx'), 'utf8');
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
    expect(source).not.toMatch(/rgba?\s*\(/i);
    expect(source).toContain('var(--primary)');
    expect(source).toContain('var(--card-bg)');
    expect(source).toContain('var(--text-main)');
    expect(source).toContain('var(--border-color)');
  });
});
