import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const sidebarSource = readFileSync(
  resolve(process.cwd(), 'src/components/Sidebar.tsx'),
  'utf8',
);

describe('Sidebar voluntary help policy', () => {
  it('does not contain the unsolicited Clinical Tip launcher', () => {
    expect(sidebarSource).not.toContain('ClinicalTipBubble');
    expect(sidebarSource).not.toContain('triggerTip');
    expect(sidebarSource).not.toContain('animate-tooth-slingshot');
  });
});
