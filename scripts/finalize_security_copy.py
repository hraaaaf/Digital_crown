from pathlib import Path


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'{path}: expected {expected} occurrence(s), found {count}: {old[:140]}')
    file.write_text(text.replace(old, new), encoding='utf-8')


def replace_or_verify(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == 1:
        file.write_text(text.replace(old, new), encoding='utf-8')
        return
    if old_count == 0 and new_count == 1:
        return
    raise SystemExit(f'{path}: expected old once or verified new once; old={old_count}, new={new_count}')


# Mobile production security: keep guarantees, remove implementation vocabulary.
path = 'frontend/src/features/mobile/Dashboard/views/SecuriteView.tsx'
for old, new in [
    ('Terminal Appairé', 'Téléphone connecté'),
    ('Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.', 'Connexion directe et sécurisée au cabinet.'),
    ('Zero-Knowledge · AES-256', 'Connexion chiffrée'),
    ("{isOnline ? 'Temps réel' : 'Cache local'}", "{isOnline ? 'Temps réel' : 'Accès hors connexion'}"),
    ('>Sync</span>', '>Mise à jour</span>'),
    ('>Status Système</p>', '>État de la connexion</p>'),
    ('>Serveur local opérationnel</p>', '>Cabinet accessible</p>'),
    ('La passkey est créée mais le coffre local doit encore être scellé avant activation.', 'La biométrie est enregistrée mais son activation doit encore être terminée.'),
    ('Ajoute un second verrou local sans remplacer le QR d’appairage ni la révocation du cabinet.', 'Ajoute une protection biométrique supplémentaire sans modifier votre accès actuel.'),
    ('Après vérification biométrique, le coffre local sera restauré puis la passkey sera déliée de cet appareil.', 'Après vérification biométrique, l’accès biométrique sera retiré de cet appareil.'),
    ('Origine passkey stable : <span className="font-black">digitalcrown.local</span>. Aucune empreinte ni donnée Face ID n’est reçue par Digital Crown.', 'La biométrie reste gérée par votre téléphone. Digital Crown ne reçoit ni empreinte ni donnée Face ID.'),
    ('Cela supprimera les clés de ce téléphone. Il faudra re-scanner le QR Code pour se reconnecter.', 'Cela supprimera l’accès enregistré sur ce téléphone. Il faudra scanner à nouveau le QR de connexion.'),
]:
    replace_exact(path, old, new)

# Desktop settings security.
path = 'frontend/src/features/admin/Security/MobileSecurity.tsx'
for old, new in [
    ('Créez un pont sécurisé vers une surface mobile précise.', 'Connectez un téléphone à l’espace mobile de votre choix.'),
    ('Pont mobile sécurisé', 'Connexion mobile sécurisée'),
    ("Choisissez l'utilisateur et la destination. Le QR contient uniquement un secret éphémère ; aucune donnée patient n'y est encodée.", "Choisissez l’utilisateur et l’espace à ouvrir. Le QR ne contient aucune donnée patient et expire automatiquement."),
    ('Générer le pont mobile', 'Générer le QR de connexion'),
    ('Impossible de générer le pont mobile.', 'Impossible de générer le QR de connexion.'),
    ('alt="Pont QR Digital Crown Mobile"', 'alt="QR de connexion Digital Crown Mobile"'),
    ("Aucune donnée patient dans le QR. La destination est validée côté serveur après l'appairage.", 'Aucune donnée patient dans le QR. L’accès s’ouvre uniquement vers l’espace choisi.'),
    ('Zone de Danger', 'Révoquer les accès'),
    ("En cas de perte ou de vol, révoquez les sessions mobiles existantes. Les anciens jetons seront refusés immédiatement et les codes d'appairage en attente seront invalidés pour ce cabinet.", 'En cas de perte ou de vol, révoquez les accès mobiles existants. Les accès actifs seront immédiatement désactivés et les QR en attente ne fonctionneront plus.'),
    ("Les données cliniques restent sur le réseau local du cabinet. L'appairage mobile utilise une connexion chiffrée et respecte les droits de l'utilisateur.", 'Les données cliniques restent au cabinet. La connexion mobile est chiffrée et respecte les droits de l’utilisateur.'),
]:
    replace_exact(path, old, new)

# Demo security.
path = 'frontend/src/features/mobile/Dashboard/MobilePreviewSecurityView.tsx'
for old, new in [
    ('Aucun appel réseau vers Digital Crown local.', 'Aucune connexion au cabinet réel.'),
    ('Face ID / empreinte restent un gate terrain sur appareil physique.', 'La biométrie doit être vérifiée sur un appareil physique.'),
    ('Preview isolée', 'Démonstration isolée'),
    ('Aucun appareil appairé. Aucune clé, session ou donnée cabinet n’est créée dans cette Preview.', 'Aucun appareil connecté. Aucun accès ni aucune donnée du cabinet n’est créé dans cette démonstration.'),
    ('Isolation active', 'Mode démonstration actif'),
]:
    replace_exact(path, old, new)

# Additional rendered wording surfaced by the strengthened scanner.
for path, old, new in [
    ('frontend/src/features/agenda/AppointmentMobileBridge.tsx', 'aria-label="Pont mobile rendez-vous"', 'aria-label="Rendez-vous sur mobile"'),
    ('frontend/src/features/agenda/AppointmentMobileBridge.tsx', '>Pont mobile<', '>Accès mobile<'),
    ('frontend/src/features/agenda/AppointmentMobileBridge.tsx', 'aria-label="Fermer le pont mobile rendez-vous"', 'aria-label="Fermer l’accès mobile rendez-vous"'),
    ('frontend/src/features/mobile/Context/MobileContext.tsx', 'Contexte résolu côté serveur · aucun identifiant rendez-vous dans l’URL', 'Rendez-vous vérifié de manière sécurisée'),
    ('frontend/src/features/mobile/Dashboard/components/MobileHeader.tsx', "'Sync…'", "'Mise à jour…'"),
    ('frontend/src/features/mobile/Dashboard/MobilePreviewBotView.tsx', 'Preview locale · données fictives', 'Démonstration locale · données fictives'),
    ('frontend/src/features/mobile/Dashboard/MobilePreviewBotView.tsx', 'Assistant désactivé dans la Preview', 'Assistant désactivé dans cette démonstration'),
    ('frontend/src/features/mobile/Dashboard/MobilePreviewDashboard.tsx', 'MODE DÉMO — PREVIEW LOCALE', 'MODE DÉMO — DONNÉES FICTIVES'),
    ('frontend/src/features/mobile/Onboarding/MobilePreviewOnboarding.tsx', 'MODE DÉMO — PREVIEW VERCEL', 'MODE DÉMO — PARCOURS FICTIF'),
    ('frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx', '>Zero-Knowledge<', '>Données protégées<'),
    ('frontend/src/features/mobile/Onboarding/OnboardingScanner.tsx', 'La clé AES-256 reste sur ce téléphone. Aucune donnée lisible ne quitte votre réseau local.', 'Les informations de connexion restent protégées sur ce téléphone. Aucune donnée lisible ne quitte le cabinet.'),
    ('frontend/src/features/mobile/Security/MobileBiometricGate.tsx', 'Le QR d’appairage et la révocation du cabinet restent obligatoires. La passkey ne remplace jamais l’identité serveur.', 'Le QR de connexion et la révocation du cabinet restent obligatoires. La biométrie ne remplace jamais l’identification du compte.'),
    ('frontend/src/features/ortho/components/SyncBadge.tsx', "label: 'Erreur sync'", "label: 'Échec de mise à jour'"),
    ('frontend/src/features/panoramic/PanoramicMobileBridge.tsx', 'aria-label="Pont mobile radio panoramique"', 'aria-label="Radiographie panoramique sur mobile"'),
    ('frontend/src/features/panoramic/PanoramicMobileBridge.tsx', '>Pont mobile<', '>Accès mobile<'),
    ('frontend/src/features/panoramic/PanoramicMobileBridge.tsx', 'aria-label="Fermer le pont mobile"', 'aria-label="Fermer l’accès mobile"'),
    ('frontend/src/features/patients/DocumentMobileBridge.tsx', 'aria-label="Pont mobile document"', 'aria-label="Document sur mobile"'),
    ('frontend/src/features/patients/DocumentMobileBridge.tsx', '>Pont mobile<', '>Accès mobile<'),
    ('frontend/src/features/patients/DocumentMobileBridge.tsx', 'aria-label="Fermer le pont mobile document"', 'aria-label="Fermer l’accès mobile document"'),
    ('frontend/src/pages/PartnerCatalogAdminPage.tsx', 'label="Sync mode"', 'label="Mode de mise à jour"'),
]:
    replace_exact(path, old, new)

# Permanent scanner.
path = 'frontend/src/ClientFacingCopyCandidateAudit.test.ts'
anchor = "  { label: 'integration field jargon', re: /\\b(?:URL\\s+API|Mode\\s+sync)\\b/i },\n"
block = anchor + """  { label: 'security implementation vocabulary', re: /Zero-Knowledge|AES-256|\\bpasskey\\b|\\bcoffre\\s+local\\b/i },
  { label: 'system status implementation vocabulary', re: /\\bCache\\s+local\\b|\\bSync\\b|Status\\s+Syst[eè]me|Serveur\\s+local\\s+op[eé]rationnel/i },
  { label: 'mobile bridge implementation vocabulary', re: /pont\\s+mobile|secret\\s+[ée]ph[ée]m[eè]re|c[oô]t[ée]\\s+serveur|\\bjetons?\\b/i },
  { label: 'preview developer vocabulary', re: /\\bPreview\\b|\\bgate\\b|appel\\s+r[eé]seau|Digital\\s+Crown\\s+local/i },
"""
replace_exact(path, anchor, block)

# Existing harnesses must follow user-facing labels.
replace_or_verify(
    'frontend/scripts/capture-mobile-superadmin-mob5h-after.mjs',
    "dispatch: await page.getByRole('button', { name: /Dispatch fournisseur/i }).isVisible(),",
    "dispatch: await page.getByRole('button', { name: /Envoyer au fournisseur/i }).isVisible(),",
)
replace_or_verify(
    'frontend/scripts/capture-mobile-marketplace-mob5g.mjs',
    "await page.getByRole('button', { name: 'Préparer le DRAFT' }).click();",
    "await page.getByRole('button', { name: 'Préparer le brouillon' }).click();",
)
replace_or_verify(
    '.github/workflows/settings-security-visual-cert.yml',
    "const generateTarget = page.getByRole('button', { name: 'Générer le pont mobile', exact: true });",
    "const generateTarget = page.getByRole('button', { name: 'Générer le QR de connexion', exact: true });",
)
