from pathlib import Path

path = Path('frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx')
text = path.read_text(encoding='utf-8')
old = """  return INTERNAL_STATUS_LABELS[raw.toUpperCase()]
    ?? raw.replace(/[_-]+/g, ' ').toLowerCase().replace(/^./, letter => letter.toUpperCase());"""
new = """  return INTERNAL_STATUS_LABELS[raw.toUpperCase()] ?? 'À vérifier';"""
if text.count(old) != 1:
    raise SystemExit(f'Unknown-status fallback mismatch: {text.count(old)}')
path.write_text(text.replace(old, new), encoding='utf-8')
