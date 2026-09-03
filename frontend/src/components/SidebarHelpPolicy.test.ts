import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const sidebarSource = readFileSync(
  fileURLToPath(new URL('./Sidebar.tsx', import.meta.url)),
  'utf8',
);

describe('Sidebar voluntary help policy', () => {
  it('does not contain the unsolicited Clinical Tip launcher', () => {
    expect(sidebarSource).not.toContain('ClinicalTipBubble');
    expect(sidebarSource).not.toContain('triggerTip');
    expect(sidebarSource).not.toContain('animate-tooth-slingshot');
  });
});
