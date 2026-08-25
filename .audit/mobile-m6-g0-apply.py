from pathlib import Path

ROOT = Path('.')

main_path = ROOT / 'frontend/src/main.tsx'
main = main_path.read_text(encoding='utf-8')
anchor = "import './index.css' // <--- VERIFIE BIEN CETTE LIGNE\n"
replacement = anchor + "import './styles/mobileGlassSystem.css'\n"
if main.count(anchor) != 1:
    raise SystemExit('main.tsx glass import anchor mismatch')
main_path.write_text(main.replace(anchor, replacement), encoding='utf-8')

dashboard_path = ROOT / 'frontend/src/features/mobile/Dashboard/MobileDashboard.tsx'
dashboard = dashboard_path.read_text(encoding='utf-8')
anchor = '<div className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit pb-28 select-none relative" style={{ backgroundColor: \'var(--bg-medical-pearl)\' }}>'
replacement = '<div data-dc-mobile-shell className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit pb-28 select-none relative" style={{ backgroundColor: \'var(--bg-medical-pearl)\' }}>'
if dashboard.count(anchor) != 1:
    raise SystemExit('MobileDashboard root anchor mismatch')
dashboard_path.write_text(dashboard.replace(anchor, replacement), encoding='utf-8')

onboarding_path = ROOT / 'frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx'
onboarding = onboarding_path.read_text(encoding='utf-8')
anchor = '<div className="min-h-screen'
count = onboarding.count(anchor)
if count != 7:
    raise SystemExit(f'Onboarding root count mismatch: expected 7, got {count}')
onboarding_path.write_text(onboarding.replace(anchor, '<div data-dc-mobile-shell className="min-h-screen'), encoding='utf-8')

css_path = ROOT / 'frontend/src/styles/mobileGlassSystem.css'
css_path.parent.mkdir(parents=True, exist_ok=True)
css_path.write_text(r'''/*
 * Digital Crown — Mobile Glass System
 * Visual-only foundation. Existing theme glass tokens remain source of truth.
 */

:root {
  --dc-mobile-glass-surface: color-mix(in srgb, var(--glass-bg) 88%, transparent);
  --dc-mobile-glass-border: color-mix(in srgb, var(--glass-border) 82%, var(--primary) 18%);
  --dc-mobile-glass-shadow:
    0 18px 48px rgba(15, 23, 42, 0.10),
    0 4px 14px rgba(15, 23, 42, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.62);
}

:is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
) {
  background-image:
    radial-gradient(circle at 10% 8%, color-mix(in srgb, var(--accent) 14%, transparent) 0, transparent 34rem),
    radial-gradient(circle at 92% 18%, color-mix(in srgb, var(--primary) 9%, transparent) 0, transparent 30rem),
    linear-gradient(155deg, var(--bg-gradient-start), var(--bg-gradient-end));
  background-attachment: fixed;
}

:is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
) :is(.bg-card, .bg-card-bg, .bg-glass-bg, [style*="var(--glass-bg)"]) {
  background-color: var(--dc-mobile-glass-surface) !important;
  border-color: var(--dc-mobile-glass-border) !important;
  -webkit-backdrop-filter: blur(18px) saturate(142%);
  backdrop-filter: blur(18px) saturate(142%);
  box-shadow: var(--dc-mobile-glass-shadow);
}

/* Explicit glass surfaces are safe to enhance wherever the design system calls them glass. */
:is(.bg-glass-bg, [style*="var(--glass-bg)"]) {
  -webkit-backdrop-filter: blur(18px) saturate(142%);
  backdrop-filter: blur(18px) saturate(142%);
}

/* Clinical accessibility always wins over decorative translucency. */
[data-theme='high-contrast'] :is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
) :is(.bg-card, .bg-card-bg, .bg-glass-bg, [style*="var(--glass-bg)"]) {
  background-color: var(--card-bg) !important;
  border-color: var(--border-color) !important;
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
  box-shadow: none !important;
}

@media (prefers-reduced-transparency: reduce) {
  :is(
    [data-dc-mobile-shell],
    [data-mobile-context],
    [data-m4a-context],
    [data-m4b-context],
    [data-m4c-context],
    [data-m4d-context]
  ) :is(.bg-card, .bg-card-bg, .bg-glass-bg, [style*="var(--glass-bg)"]) {
    background-color: var(--card-bg) !important;
    -webkit-backdrop-filter: none !important;
    backdrop-filter: none !important;
  }
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  :is(
    [data-dc-mobile-shell],
    [data-mobile-context],
    [data-m4a-context],
    [data-m4b-context],
    [data-m4c-context],
    [data-m4d-context]
  ) :is(.bg-card, .bg-card-bg, .bg-glass-bg, [style*="var(--glass-bg)"]) {
    background-color: var(--card-bg) !important;
  }
}
''', encoding='utf-8')

print('M6-G0 glass product patch materialized')
