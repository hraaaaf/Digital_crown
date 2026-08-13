import { describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

describe('service worker registration', () => {
  it('keeps Workbox as the only root-scope worker', () => {
    const source = fs.readFileSync(path.resolve(__dirname, 'main.tsx'), 'utf8')

    expect(source).toContain('registerSW({ immediate: true })')
    expect(source).not.toMatch(/serviceWorker\.register\(['"]\/sw\.js['"]\)/)
  })
})
