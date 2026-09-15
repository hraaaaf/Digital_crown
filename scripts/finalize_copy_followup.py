from pathlib import Path


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'{path}: expected {expected} occurrence(s), found {count}: {old[:120]}')
    file.write_text(text.replace(old, new), encoding='utf-8')


# The first-stage scanner is intentionally strict, but an HTTPS URL example is not
# implementation jargon. Keep standalone HTTP/HTTPS detection while allowing URLs.
replace_exact(
    'frontend/src/ClientFacingCopyCandidateAudit.test.ts',
    "  { label: 'transport implementation jargon', re: /\\b(?:HTTP(?:S)?|idempotence)\\b/i },",
    "  { label: 'transport implementation jargon', re: /\\b(?:HTTP|HTTPS)\\b(?!:\\/\\/)|\\bidempotence\\b/i },",
)

# SuperAdmin renders this status in both the list and the open order sheet.
replace_exact(
    'frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.test.tsx',
    "    expect(screen.getByText(/Dental Supply Demo · Brouillon/i)).toBeTruthy();",
    "    expect(screen.getAllByText(/Dental Supply Demo · Brouillon/i).length).toBeGreaterThan(0);",
)

# Mobile marketplace: preserve the internal DRAFT contract, translate only the UI.
replace_exact(
    'frontend/src/features/mobile/Dashboard/views/MarketplaceView.tsx',
    'Préparer le DRAFT',
    'Préparer le brouillon',
)
replace_exact(
    'frontend/src/features/mobile/Dashboard/views/MarketplaceView.tsx',
    'Crée un DRAFT Digital Crown. Rien n’est transmis au fournisseur.',
    'Crée un brouillon de commande Digital Crown. Rien n’est transmis au fournisseur.',
)

# Mobile security: describe the user-visible guarantee, not the UV implementation.
replace_exact(
    'frontend/src/features/mobile/Dashboard/views/SecuriteView.tsx',
    'Face ID, empreinte ou verrou sécurisé requis. La session UV reste courte et liée à ce téléphone.',
    'Face ID, empreinte ou verrou sécurisé requis. L’accès reste temporaire et lié à ce téléphone.',
)

# Onboarding: keep the security meaning without exposing the transport protocol name.
replace_exact(
    'frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx',
    'Activez HTTPS pour chiffrer vos données sur le réseau local.',
    'Activez la connexion sécurisée pour chiffrer vos données sur le réseau local.',
)
replace_exact(
    'frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx',
    'sans HTTPS',
    'sans connexion sécurisée',
)

# Landing page: tenant isolation is a product benefit; “multi-tenant” is architecture jargon.
replace_exact(
    'frontend/src/pages/LandingPage.tsx',
    'title="Sécurité & Multi-tenant"',
    'title="Sécurité & isolation des cabinets"',
)

# Desktop marketplace: preserve raw order status internally, translate the rendered copy.
replace_exact(
    'frontend/src/pages/PartnerMarketplacePage.tsx',
    'Préparer le DRAFT',
    'Préparer le brouillon',
    expected=2,
)
replace_exact(
    'frontend/src/pages/PartnerMarketplacePage.tsx',
    'Cette action crée une commande DRAFT dans Digital Crown. Rien n’est encore transmis au fournisseur.',
    'Cette action crée un brouillon de commande dans Digital Crown. Rien n’est encore transmis au fournisseur.',
)

# Notification capability: client-facing explanation, same secure-context requirement.
replace_exact(
    'frontend/src/services/zka/mobilePush.ts',
    "title: 'HTTPS requis',",
    "title: 'Connexion sécurisée requise',",
)
