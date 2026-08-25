from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
path = root / 'frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx'
text = path.read_text()
old = "        return { route: BRIDGE_ROUTES.context, label: BRIDGE_LABELS.context, context };"
new = """        const resourceLabel = typeof payload.label === 'string' && payload.label.trim()\n          ? payload.label.trim()\n          : (context.label || BRIDGE_LABELS.context);\n        return { route: BRIDGE_ROUTES.context, label: resourceLabel, context };"""
count = text.count(old)
if count != 1:
    raise SystemExit(f'Onboarding resource-label anchor expected once, found {count}')
path.write_text(text.replace(old, new, 1))
print('M4-D onboarding resource label patched.')
