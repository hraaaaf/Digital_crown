import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');

describe('T2 mobile sidebar interaction boundary', () => {
  it('disables hit testing while the off-canvas sidebar is closed and restores it on desktop', () => {
    const css = read('src/sidebar-interaction.css');
    const main = read('src/main.tsx');

    expect(main).toContain("import './sidebar-interaction.css'");
    expect(css).toContain('aside.bg-sidebar.-translate-x-full');
    expect(css).toContain('pointer-events: none');
    expect(css).toContain('@media (min-width: 1024px)');
    expect(css).toContain('pointer-events: auto');
  });
});
