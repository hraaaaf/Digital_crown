from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    src = p.read_text()
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, got {count}")
    p.write_text(src.replace(old, new))


main_path = "frontend/src/main.tsx"
replace_once(
    main_path,
    """import { registerSW } from 'virtual:pwa-register'\n\nif ('serviceWorker' in navigator) {\n  // Un seul Service Worker Workbox pour le shell statique. Les données métier\n  // et mutations offline restent exclusivement dans MobileStorage.\n  registerSW({ immediate: true })\n}\n""",
    """import { registerSW } from 'virtual:pwa-register'\n\nconst LEGACY_SW_RELOAD_KEY = 'dc_m62_legacy_sw_reload'\n\nfunction isLegacyMobileWorker(worker: ServiceWorker | null): boolean {\n  if (!worker) return false\n  try {\n    return new URL(worker.scriptURL).pathname === '/sw.js'\n  } catch {\n    return worker.scriptURL.endsWith('/sw.js')\n  }\n}\n\nasync function deleteLegacySyncDb(): Promise<void> {\n  if (!('indexedDB' in window)) return\n  await new Promise<void>((resolve) => {\n    const request = indexedDB.deleteDatabase('sync-db')\n    request.onsuccess = () => resolve()\n    request.onerror = () => resolve()\n    // Un ancien worker encore vivant peut garder une connexion ouverte pendant\n    // quelques instants. La suppression reste demandée et se terminera à sa fermeture.\n    request.onblocked = () => resolve()\n  })\n}\n\nasync function migrateLegacyMobileOfflineState(): Promise<boolean> {\n  const legacyController = isLegacyMobileWorker(navigator.serviceWorker.controller)\n\n  try {\n    const registrations = await navigator.serviceWorker.getRegistrations()\n    const legacyRegistrations = registrations.filter((registration) =>\n      [registration.installing, registration.waiting, registration.active].some(isLegacyMobileWorker)\n    )\n    await Promise.all(legacyRegistrations.map((registration) => registration.unregister()))\n  } catch { /* best effort: le nouveau Workbox remplacera le scope */ }\n\n  try {\n    if ('caches' in window) await caches.delete('dc-mobile-v10')\n  } catch { /* cache legacy non accessible */ }\n  await deleteLegacySyncDb().catch(() => undefined)\n\n  if (legacyController) {\n    try {\n      if (sessionStorage.getItem(LEGACY_SW_RELOAD_KEY) !== '1') {\n        sessionStorage.setItem(LEGACY_SW_RELOAD_KEY, '1')\n        window.location.reload()\n        return false\n      }\n    } catch { /* sessionStorage indisponible: ne jamais bloquer le nouveau SW */ }\n  }\n\n  try { sessionStorage.removeItem(LEGACY_SW_RELOAD_KEY) } catch { /* ignore */ }\n  return true\n}\n\nif ('serviceWorker' in navigator) {\n  void migrateLegacyMobileOfflineState().then((ready) => {\n    if (!ready) return\n    // Un seul Service Worker Workbox pour le shell statique. Les données métier\n    // et mutations offline restent exclusivement dans MobileStorage.\n    registerSW({ immediate: true })\n  })\n}\n""",
)

truth_path = "frontend/src/test/mobileM62OfflineTruth.test.ts"
replace_once(
    truth_path,
    """    expect(vite).not.toContain('api-snapshot-cache');\n    expect(fs.existsSync(path.join(root, 'public/sw.js'))).toBe(false);\n""",
    """    expect(vite).not.toContain('api-snapshot-cache');\n    expect(fs.existsSync(path.join(root, 'public/sw.js'))).toBe(false);\n    expect(main).toContain("indexedDB.deleteDatabase('sync-db')");\n    expect(main).toContain("caches.delete('dc-mobile-v10')");\n    expect(main).toContain('registration.unregister()');\n    expect(main).toContain("new URL(worker.scriptURL).pathname === '/sw.js'");\n    expect(main).toContain('window.location.reload()');\n""",
)
