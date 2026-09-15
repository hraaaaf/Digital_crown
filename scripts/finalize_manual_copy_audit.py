from pathlib import Path


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'{path}: expected {expected} occurrence(s), found {count}: {old[:140]}')
    file.write_text(text.replace(old, new), encoding='utf-8')


# Panoramic mobile access: no bridge/server/secret implementation vocabulary may surface.
path = 'frontend/src/features/panoramic/PanoramicMobileBridge.tsx'
replace_exact(path, 'Réponse de pont panoramique non sûre.', 'Réponse de connexion mobile non valide.', expected=2)
replace_exact(path, 'Impossible de préparer le pont mobile.', 'Impossible de préparer l’accès mobile.')
replace_exact(path, 'alt="QR de pont mobile panoramique"', 'alt="QR de connexion pour la radiographie panoramique"')
replace_exact(
    path,
    'Le QR contient seulement un secret temporaire. La radio exacte est résolue côté serveur après l’appairage.',
    'Le QR ne contient aucune donnée clinique. La radiographie s’ouvre uniquement après vérification de la connexion.',
)

# Mobile header: localized, user-facing connectivity states and demo wording.
path = 'frontend/src/features/mobile/Dashboard/components/MobileHeader.tsx'
replace_exact(path, 'aria-label="Notifications désactivées dans la Preview"', 'aria-label="Notifications désactivées dans la démonstration"')
replace_exact(
    path,
    "{syncStatus === 'loading' ? 'Mise à jour…' : syncStatus === 'error' ? 'Offline' : 'Live'}",
    "{syncStatus === 'loading' ? 'Mise à jour…' : syncStatus === 'error' ? 'Hors ligne' : 'À jour'}",
)

# Desktop mobile-security messages can also surface in errors/confirmation flows.
path = 'frontend/src/features/admin/Security/MobileSecurity.tsx'
replace_exact(path, "throw new Error('Réponse de pont mobile non conforme.');", "throw new Error('Réponse de connexion mobile non valide.');")
replace_exact(
    path,
    'if (!window.confirm("Révoquer immédiatement toutes les sessions mobiles existantes de ce cabinet ? Les téléphones devront être appairés à nouveau.")) return;',
    'if (!window.confirm("Déconnecter immédiatement tous les téléphones de ce cabinet ? Ils devront être connectés à nouveau avec un QR.")) return;',
)
replace_exact(path, 'setStatus({ type: \'success\', msg: "Sessions mobiles révoquées. Un nouvel appairage est nécessaire." });', 'setStatus({ type: \'success\', msg: "Tous les téléphones ont été déconnectés. Un nouveau QR de connexion est nécessaire." });')
replace_exact(path, 'setStatus({ type: \'error\', msg: typeof detail === \'string\' ? detail : "Impossible de confirmer la révocation mobile." });', 'setStatus({ type: \'error\', msg: typeof detail === \'string\' ? detail : "Impossible de déconnecter les téléphones." });')

# Assistant/settings copy.
replace_exact(
    'frontend/src/components/CrownBot/CrownBotChat.tsx',
    "suggestions: ['Configurer la facturation', 'Branding du cabinet', 'Paramètres IA'],",
    "suggestions: ['Configurer la facturation', 'Branding du cabinet', 'Paramètres de l’assistant'],",
)

# Team permission names: describe the clinical capability, not its implementation.
replace_exact(
    'frontend/src/features/admin/TeamManager.tsx',
    "{ key: 'panoramic', label: 'Imagerie OPG IA', desc: 'Analyses radio panoramiques' },",
    "{ key: 'panoramic', label: 'Imagerie panoramique', desc: 'Analyses radio panoramiques' },",
    expected=2,
)

# Partner catalog admin: preserve API values, translate every displayed status/value.
path = 'frontend/src/pages/PartnerCatalogAdminPage.tsx'
replace_exact(path, 'Impossible de charger le dashboard catalogue partenaire.', 'Impossible de charger le catalogue fournisseur.')
replace_exact(path, 'Base pour futur import API fournisseur', 'Configuration du fournisseur')
replace_exact(path, '<Input label="API base URL" value={supplierForm.apiBaseUrl} onChange={(value) => setSupplierForm((current) => ({ ...current, apiBaseUrl: value }))} />', '<Input label="Adresse de connexion" value={supplierForm.apiBaseUrl} onChange={(value) => setSupplierForm((current) => ({ ...current, apiBaseUrl: value }))} />')
replace_exact(path, '<Input label="Mode de mise à jour" value={supplierForm.syncMode} onChange={(value) => setSupplierForm((current) => ({ ...current, syncMode: value }))} />', '<Select label="Mode de mise à jour" value={supplierForm.syncMode} onChange={(value) => setSupplierForm((current) => ({ ...current, syncMode: value }))} options={[{ value: \'manual\', label: \'Manuelle\' }, { value: \'api\', label: \'Automatique\' }]} />')
replace_exact(path, "setSuccessMessage('Fournisseur partenaire ajoute.');", "setSuccessMessage('Fournisseur partenaire ajouté.');")
replace_exact(path, "setSuccessMessage('Produit partenaire ajoute.');", "setSuccessMessage('Produit partenaire ajouté.');")
replace_exact(path, 'Les commandes passées depuis la marketplace apparaîtront ici pour réconciliation.', 'Les commandes passées depuis l’approvisionnement apparaîtront ici pour suivi.')
replace_exact(path, "{state.saving ? 'Mise à jour...' : 'Appliquer le recalcul'}", "{state.saving ? 'Mise à jour…' : 'Enregistrer les modifications'}")
replace_exact(path, '<option value="">Selectionner</option>', '<option value="">Sélectionner</option>')

anchor = "type ReconcileState = Record<number, { status: string; currentTotal: string; note: string; partnerReference: string; saving: boolean }>;\n"
status_block = anchor + """

const PRODUCT_AVAILABILITY_LABELS: Record<string, string> = {
  AVAILABLE: 'Disponible',
  ON_REQUEST: 'Sur demande',
  DISCONTINUED: 'Arrêté',
};

const ORDER_STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Brouillon',
  SENT_TO_PARTNER: 'Envoyée au fournisseur',
  MODIFIED_AFTER_SEND: 'Modifiée après envoi',
  CONFIRMED: 'Confirmée',
  FULFILLED: 'Livrée',
  CANCELLED: 'Annulée',
};

const orderStatusLabel = (value: string | null | undefined) =>
  ORDER_STATUS_LABELS[String(value || '').toUpperCase()] ?? 'À vérifier';
"""
replace_exact(path, anchor, status_block)
replace_exact(path, 'setSuccessMessage(`Commande ${order.orderNumber} réconciliée avec le statut ${state.status}.`);', 'setSuccessMessage(`Commande ${order.orderNumber} mise à jour : ${orderStatusLabel(state.status)}.`);')
replace_exact(path, '{product.availability}', "{PRODUCT_AVAILABILITY_LABELS[product.availability] ?? 'À vérifier'}")
replace_exact(path, "options={(meta?.availability || []).map((item) => ({ value: item, label: item }))}", "options={(meta?.availability || []).map((item) => ({ value: item, label: PRODUCT_AVAILABILITY_LABELS[item] ?? 'À vérifier' }))}")
replace_exact(path, '{order.status}', '{orderStatusLabel(order.status)}')
replace_exact(path, "options={(ordersMeta?.supportedStatuses || []).map((statusValue) => ({ value: statusValue, label: statusValue }))}", "options={(ordersMeta?.supportedStatuses || []).map((statusValue) => ({ value: statusValue, label: orderStatusLabel(statusValue) }))}")

# Permanent regression gate: cover the exact scanner gaps found by manual review.
path = 'frontend/src/ClientFacingCopyCandidateAudit.test.ts'
replace_exact(
    path,
    "  { label: 'integration field jargon', re: /\\b(?:URL\\s+API|Mode\\s+sync)\\b/i },",
    "  { label: 'integration field jargon', re: /\\b(?:URL\\s+API|API\\s+base\\s+URL|Mode\\s+sync)\\b/i },",
)
anchor = "  { label: 'preview developer vocabulary', re: /\\bPreview\\b|\\bgate\\b|appel\\s+r[eé]seau|Digital\\s+Crown\\s+local/i },\n"
extra = anchor + """  { label: 'raw connectivity status', re: /^(?:Offline|Live)$/i },
  { label: 'assistant implementation label', re: /\\bParam[eè]tres\\s+IA\\b/i },
  { label: 'imaging implementation label', re: /\\bImagerie\\s+OPG\\s+IA\\b/i },
"""
replace_exact(path, anchor, extra)

# Align the old contextual bridge contract with the current client-facing label.
replace_exact(
    'frontend/src/test/mobileM64ContextualBridge.test.ts',
    "expect(securitySource).toContain('Générer le pont mobile');",
    "expect(securitySource).toContain('Générer le QR de connexion');",
)

# Fail closed on all manually identified remnants in client-facing product copy.
checks = {
    'frontend/src/features/panoramic/PanoramicMobileBridge.tsx': ['pont mobile', 'côté serveur', 'secret temporaire'],
    'frontend/src/features/mobile/Dashboard/components/MobileHeader.tsx': ["'Offline'", "'Live'", 'dans la Preview'],
    'frontend/src/features/admin/Security/MobileSecurity.tsx': ['Réponse de pont mobile non conforme', 'sessions mobiles existantes', 'appairés à nouveau', 'Sessions mobiles révoquées', 'nouvel appairage'],
    'frontend/src/components/CrownBot/CrownBotChat.tsx': ['Paramètres IA'],
    'frontend/src/features/admin/TeamManager.tsx': ['Imagerie OPG IA'],
    'frontend/src/pages/PartnerCatalogAdminPage.tsx': ['API base URL', 'futur import API fournisseur', 'depuis la marketplace', '{order.status}', 'label: statusValue', '{product.availability}'],
}
for file_name, forbidden in checks.items():
    text = Path(file_name).read_text(encoding='utf-8')
    remaining = [token for token in forbidden if token in text]
    if remaining:
        raise SystemExit(f'{file_name}: remaining client-facing technical wording: {remaining}')

print('FINAL_MANUAL_COPY_AUDIT_PATCH_READY')
