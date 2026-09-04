import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const ROOT = join(process.cwd(), 'src', 'features', 'mobile');
const FORBIDDEN_FONT_CLASS = /\bfont-(?:outfit|sans|serif|mono)\b/;

function sourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    if (!/\.(?:ts|tsx)$/.test(name) || name.endsWith('.test.ts') || name.endsWith('.test.tsx')) return [];
    return [path];
  });
}

describe('mobile theme hardcoding guard', () => {
  it('does not force a font family inside mobile product components', () => {
    const offenders = sourceFiles(ROOT)
      .filter((path) => FORBIDDEN_FONT_CLASS.test(readFileSync(path, 'utf8')))
      .map((path) => relative(process.cwd(), path));

    expect(offenders, `Hardcoded mobile font utilities: ${offenders.join(', ')}`).toEqual([]);
  });
});
