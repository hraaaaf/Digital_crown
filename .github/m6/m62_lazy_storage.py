from pathlib import Path

p = Path('frontend/src/services/zka/MobileStorage.ts')
s = p.read_text()

old = """import localforage from 'localforage';

/** Mobile ZKA persistence: credentials, last snapshot and the single offline queue. */
localforage.config({
  driver: localforage.INDEXEDDB,
  name: 'digital-crown-zka',
  version: 1.0,
  storeName: 'secure_keys',
});
"""
new = """import localforage from 'localforage';

/** Mobile ZKA persistence: credentials, last snapshot and the single offline queue. */
let storageConfigured = false;

function mobileStore() {
  if (!storageConfigured) {
    // IndexedDB reste obligatoire pour les secrets mobiles. La configuration est
    // volontairement lazy : importer api.ts ne doit pas initialiser un driver de
    // stockage dans les contextes qui n'utilisent pas l'app mobile (SSR/tests).
    localforage.config({
      driver: localforage.INDEXEDDB,
      name: 'digital-crown-zka',
      version: 1.0,
      storeName: 'secure_keys',
    });
    storageConfigured = true;
  }
  return localforage;
}
"""
if s.count(old) != 1:
    raise SystemExit(f'MobileStorage top-level config anchor count={s.count(old)}')
s = s.replace(old, new)

for old_call, new_call in (
    ('localforage.getItem', 'mobileStore().getItem'),
    ('localforage.setItem', 'mobileStore().setItem'),
    ('localforage.removeItem', 'mobileStore().removeItem'),
):
    if old_call not in s:
        raise SystemExit(f'MobileStorage expected call missing: {old_call}')
    s = s.replace(old_call, new_call)

# The driver must never initialize at module import, and no localStorage fallback
# is permitted for the mobile master key / durable credentials.
prefix_before_helper = s.split('function mobileStore()', 1)[0]
assert 'localforage.config(' not in prefix_before_helper
assert 'driver: localforage.INDEXEDDB' in s
assert 'localforage.LOCALSTORAGE' not in s
assert 'mobileStore().getItem' in s
assert 'mobileStore().setItem' in s
assert 'mobileStore().removeItem' in s
p.write_text(s)

# Lock the regression in the source-truth test as well. The full Vitest suite is
# still required by the materializer and the PR CI.
t = Path('frontend/src/test/mobileM62OfflineTruth.test.ts')
ts = t.read_text()
needle = """    expect(storage).toContain('LEGACY_ACTION_QUEUE_ID');
  });
"""
replacement = """    expect(storage).toContain('LEGACY_ACTION_QUEUE_ID');
    expect(storage).toContain('function mobileStore()');
    expect(storage).toContain('driver: localforage.INDEXEDDB');
    expect(storage).not.toContain('localforage.LOCALSTORAGE');
    const helperIndex = storage.indexOf('function mobileStore()');
    expect(storage.slice(0, helperIndex)).not.toContain('localforage.config(');
  });
"""
if ts.count(needle) != 1:
    raise SystemExit(f'offline truth storage anchor count={ts.count(needle)}')
t.write_text(ts.replace(needle, replacement))
