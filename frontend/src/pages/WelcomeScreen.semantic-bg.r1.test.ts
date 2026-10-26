import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const welcomeSource = readFileSync(resolve(process.cwd(), 'src/pages/WelcomeScreen.tsx'), 'utf8');

describe('WelcomeScreen theme-aware background contract', () => {
  it('uses the semantic page background instead of a hard-coded light background', () => {
    expect(welcomeSource).toMatch(/className="min-h-screen bg-background\b/);
    expect(welcomeSource).not.toContain('bg-[#f8fafc]');
    expect(welcomeSource).toContain('dark:brightness-0 dark:invert');
  });
});
