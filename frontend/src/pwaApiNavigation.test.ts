import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

describe('PWA navigation fallback', () => {
  it('never intercepts /api navigations', () => {
    const config = fs.readFileSync(path.resolve(__dirname, '../vite.config.ts'), 'utf8')
    expect(config).toContain('navigateFallbackDenylist: [/^\\/api\\//]')
  })
})
