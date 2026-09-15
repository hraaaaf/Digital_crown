from pathlib import Path

VIEW = Path('frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.tsx')
AUDIT = Path('frontend/src/ClientFacingCopyCandidateAudit.test.ts')
TEST = Path('frontend/src/features/mobile/Dashboard/views/MobileSuperAdminView.test.tsx')


def replace_exact(text: str, old: str, new: str, expected: int = 1) -> str:
    count = text.count(old)
    if count != expected:
        raise SystemExit(f'Expected {expected} occurrence(s), found {count}: {old[:160]}')
    return text.replace(old, new)


def patch_view() -> None:
    text = VIEW.read_text(encoding='utf-8')

    anchor = "const PLAN_OPTIONS = ['GOLD', 'PREMIUM', 'ELITE'] as const;\n"
    helper = """const PLAN_OPTIONS = ['GOLD', 'PREMIUM', 'ELITE'] as const;

const INTERNAL_STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Brouillon',
  SENT_TO_PARTNER: 'Envoyée au fournisseur',
  MODIFIED_AFTER_SEND: 'Modifiée après envoi',
  CONFIRMED: 'Confirmée',
  FULFILLED: 'Livrée',
  CANCELLED: 'Annulée',
  WAITING_INVOICE: 'En attente de facture',
  AMOUNT_MISMATCH: 'Écart de montant',
  MATCHED: 'Rapprochée',
  SUCCEEDED: 'Réussi',
  FAILED: 'Échec',
  DEGRADED: 'À vérifier',
  STALE: 'À actualiser',
  APPLIED: 'Appliqué',
  AVAILABLE: 'Disponible',
  ON_REQUEST: 'Sur demande',
  DISCONTINUED: 'Arrêté',
  NONE: 'Aucun',
  ACTIVE: 'Actif',
  SUSPENDED: 'Suspendu',
  TERMINATED: 'Terminé',
  SUPPLIER: 'Fournisseur',
  PRODUCT: 'Produit',
  SUPPLIER_GOVERNANCE_UPDATED: 'Gouvernance fournisseur mise à jour',
  PRODUCT_UPDATED: 'Produit mis à jour',
};

const SYNC_MODE_LABELS: Record<string, string> = {
  manual: 'Manuelle',
  api: 'Automatique',
};

const AGREEMENT_STATUS_LABELS: Record<string, string> = {
  NONE: 'Aucun accord',
  DRAFT: 'Brouillon',
  ACTIVE: 'Actif',
  SUSPENDED: 'Suspendu',
  TERMINATED: 'Terminé',
};

const AVAILABILITY_LABELS: Record<string, string> = {
  AVAILABLE: 'Disponible',
  ON_REQUEST: 'Sur demande',
  DISCONTINUED: 'Arrêté',
};

function statusLabel(value: unknown): string {
  const raw = String(value ?? '').trim();
  if (!raw) return '—';
  return INTERNAL_STATUS_LABELS[raw.toUpperCase()]
    ?? raw.replace(/[_-]+/g, ' ').toLowerCase().replace(/^./, letter => letter.toUpperCase());
}

function syncModeLabel(value: unknown): string {
  const raw = String(value ?? 'manual').trim().toLowerCase();
  return SYNC_MODE_LABELS[raw] ?? 'Manuelle';
}
"""
    text = replace_exact(text, anchor, helper)

    replacements = [
        ("body: `${supplier.name} sera synchronisé via le moteur canonique serveur.${force ? ' Le backoff normal sera contourné.' : ''}`", "body: `${supplier.name} sera synchronisé avec les données centrales.${force ? ' Les délais d’attente habituels seront ignorés.' : ''}`", 1),
        ('<h3 className="mt-1 text-base font-black">Control-plane</h3>', '<h3 className="mt-1 text-base font-black">Administration</h3>', 1),
        ('Le JWT mobile ordinaire reste refusé. Une session WebAuthn UV courte ouvre le control-plane.', 'Une vérification biométrique est requise pour accéder temporairement à l’administration de l’approvisionnement.', 1),
        ('Aucune donnée Marketplace chargée.', 'Aucune donnée d’approvisionnement chargée.', 1),
        ('Le backend utilisera le canal canonique disponible, actuellement WhatsApp si un téléphone est renseigné.', 'La relance sera envoyée via le canal disponible, actuellement WhatsApp si un téléphone est renseigné.', 1),
        ('<SectionTitle eyebrow="Control-plane" title="Administration approvisionnement" />', '<SectionTitle eyebrow="Approvisionnement" title="Administration approvisionnement" />', 1),
        ('Step-up WebAuthn requis', 'Vérification biométrique requise', 1),
        ('Le control-plane global refuse le JWT mobile durable. Déverrouille une session UV de 5 minutes pour continuer.', 'Une vérification biométrique ouvre l’accès à l’administration de l’approvisionnement pendant 5 minutes.', 1),
        ('<SectionTitle eyebrow="Control-plane" title="Administration approvisionnement" action=', '<SectionTitle eyebrow="Approvisionnement" title="Administration approvisionnement" action=', 1),
        ("{supplier.syncMode || 'manual'}", '{syncModeLabel(supplier.syncMode)}', 1),
        ('>Force sync</button>', '>Forcer la synchronisation</button>', 1),
        ('{String(incident.freshness.status)} · {incident.consecutiveFailures} échec(s)', '{statusLabel(incident.freshness.status)} · {incident.consecutiveFailures} échec(s)', 1),
        ("{incident.lastErrorDetail || incident.lastErrorCode || 'Incident de fraîcheur'}", "{'Synchronisation à vérifier.'}", 1),
        ('Aucun incident sync global.', 'Aucun incident de synchronisation.', 1),
        ('>{event.action}</span>', '>{statusLabel(event.action)}</span>', 1),
        ('>{event.entityType} #{event.entityId} · Cabinet #{event.employerId}</p>', '>{statusLabel(event.entityType)} #{event.entityId} · Cabinet #{event.employerId}</p>', 1),
        ('label="URL API"', 'label="Adresse de connexion"', 2),
        ('<SelectField label="Mode sync" value={syncMode} options={[\'manual\', \'api\']} onChange={setSyncMode} />', '<SelectField label="Mode de synchronisation" value={syncMode} options={[\'manual\', \'api\']} optionLabels={SYNC_MODE_LABELS} onChange={setSyncMode} />', 1),
        ('<SelectField label="Statut accord" value={agreementStatus} options={[\'NONE\', \'DRAFT\', \'ACTIVE\', \'SUSPENDED\', \'TERMINATED\']} onChange={setAgreementStatus} />', '<SelectField label="Statut accord" value={agreementStatus} options={[\'NONE\', \'DRAFT\', \'ACTIVE\', \'SUSPENDED\', \'TERMINATED\']} optionLabels={AGREEMENT_STATUS_LABELS} onChange={setAgreementStatus} />', 1),
        ('body: `Accord ${agreementStatus} pour ${props.supplier.name}. Le backend exigera confirm=true et journalisera la mutation.`', 'body: `Accord ${statusLabel(agreementStatus)} pour ${props.supplier.name}. Le statut sera mis à jour et enregistré dans l’historique.`', 1),
        ('subtitle="Création globale SuperAdmin"', 'subtitle="Création fournisseur"', 1),
        ('label="ID cabinet cible"', 'label="Cabinet cible (ID)"', 2),
        ('label="Clé fournisseur"', 'label="Identifiant fournisseur"', 1),
        ('<SelectField label="Mode sync" value={form.syncMode || \'manual\'} options={[\'manual\', \'api\']} onChange={value => setForm({ ...form, syncMode: value })} />', '<SelectField label="Mode de synchronisation" value={form.syncMode || \'manual\'} options={[\'manual\', \'api\']} optionLabels={SYNC_MODE_LABELS} onChange={value => setForm({ ...form, syncMode: value })} />', 1),
        ("{busy ? 'Création…' : 'Créer avec confirmation globale'}", "{busy ? 'Création…' : 'Créer'}", 2),
        ('subtitle="Catalogue global SuperAdmin"', 'subtitle="Nouveau produit du catalogue"', 1),
        ('<SelectField label="Disponibilité" value={f.availability} options={[\'AVAILABLE\', \'ON_REQUEST\', \'DISCONTINUED\']} onChange={value => props.setForm({ ...f, availability: value })} />', '<SelectField label="Disponibilité" value={f.availability} options={[\'AVAILABLE\', \'ON_REQUEST\', \'DISCONTINUED\']} optionLabels={AVAILABILITY_LABELS} onChange={value => props.setForm({ ...f, availability: value })} />', 1),
        ('Tenant courant · actions réelles', 'Cabinet sélectionné', 1),
        ('{order.partnerName} · {order.status}', '{order.partnerName} · {statusLabel(order.status)}', 1),
        ('Aucune commande opérationnelle pour le tenant courant.', 'Aucune commande pour ce cabinet.', 1),
        ('Vue globale P10', 'Vue multi-cabinets', 1),
        ('>Déverrouiller WebAuthn</button>', '>Vérifier l’identité</button>', 1),
        ('>{order.status}</p>', '>{statusLabel(order.status)}</p>', 1),
        ('subtitle={`${props.order.partnerName} · ${props.order.status}`}', 'subtitle={`${props.order.partnerName} · ${statusLabel(props.order.status)}`}', 1),
        ("title: 'Envoyer réellement au fournisseur ?'", "title: 'Envoyer la commande au fournisseur ?'", 1),
        ('body: `Commande ${props.order.orderNumber} → ${props.order.partnerName}. Le backend effectuera l’appel HTTPS avec preuve de transport et idempotence.`', 'body: `Commande ${props.order.orderNumber} → ${props.order.partnerName}. L’envoi sera confirmé après réponse du fournisseur.`', 1),
        ('>Dispatch fournisseur</button>', '>Envoyer au fournisseur</button>', 1),
        ('title: `Passer en ${state} ?`', 'title: `Passer en ${statusLabel(state)} ?`', 1),
        ("body: 'La transition sera validée par le moteur canonique serveur. Aucun succès local ne sera simulé.'", "body: 'Le statut de la commande sera mis à jour après validation.'", 1),
        ('confirmLabel: state', 'confirmLabel: statusLabel(state)', 1),
        ('>{state}</button>', '>{statusLabel(state)}</button>', 1),
        ('>Preuve dispatch</p>', '>Envoi fournisseur</p>', 1),
        (">Outcome: {String(detail.dispatch.outcome ?? '—')}</p>", '>Résultat : {statusLabel(detail.dispatch.outcome)}</p>', 1),
        ("<p>HTTP: {String(detail.dispatch.responseStatus ?? '—')} · Réf: {String(detail.dispatch.supplierReference ?? '—')}</p>", "<p>Référence fournisseur : {String(detail.dispatch.supplierReference ?? '—')}</p>", 1),
        ('>Procurement</p>', '>Suivi fournisseur</p>', 1),
        ('label={`Backorder ${line.sku} · max ${line.quantity}`}', 'label={`Reliquat ${line.sku} · max ${line.quantity}`}', 1),
        ("body: 'Le serveur vérifiera CONFIRMED, reliquats et backorders avant toute écriture.'", "body: 'Les quantités confirmées et les reliquats seront vérifiés avant l’enregistrement.'", 1),
        ("body: `${invoiceReference} · ${formatMoney(invoiceAmount)}. Une clé d’idempotence sera générée côté mobile et validée par le serveur.`", "body: `${invoiceReference} · ${formatMoney(invoiceAmount)}. La facture sera enregistrée après validation des informations.`", 1),
        ("value={String(detail.reconciliation.reconciliationStatus ?? '—')}", 'value={statusLabel(detail.reconciliation.reconciliationStatus)}', 1),
    ]

    for old, new, expected in replacements:
        text = replace_exact(text, old, new, expected)

    select_old = "function SelectField(props: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {\n  return <label className=\"mt-3 block\"><span className=\"text-[9px] font-black uppercase tracking-wider text-text-muted\">{props.label}</span><select value={props.value} onChange={event => props.onChange(event.target.value)} className=\"mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary\">{props.options.map(option => <option key={option} value={option}>{option}</option>)}</select></label>;\n}"
    select_new = "function SelectField(props: { label: string; value: string; options: string[]; optionLabels?: Record<string, string>; onChange: (value: string) => void }) {\n  return <label className=\"mt-3 block\"><span className=\"text-[9px] font-black uppercase tracking-wider text-text-muted\">{props.label}</span><select value={props.value} onChange={event => props.onChange(event.target.value)} className=\"mt-1 min-h-12 w-full rounded-[14px] border border-glass-border bg-background px-3 text-sm font-semibold outline-none focus:border-primary\">{props.options.map(option => <option key={option} value={option}>{props.optionLabels?.[option] ?? option}</option>)}</select></label>;\n}"
    text = replace_exact(text, select_old, select_new)
    VIEW.write_text(text, encoding='utf-8')


def patch_audit() -> None:
    text = AUDIT.read_text(encoding='utf-8')
    anchor = "  { label: 'security implementation jargon', re: /\\b(?:ECDH|LAN)\\b/ },\n"
    block = anchor + """  { label: 'internal control-plane terminology', re: /\\bcontrol[- ]plane\\b/i },
  { label: 'authentication implementation jargon', re: /\\b(?:WebAuthn|JWT|session\\s+UV)\\b/i },
  { label: 'synchronization implementation jargon', re: /\\b(?:backoff|Force\\s+sync|Mode\\s+sync|incident\\s+sync)\\b/i },
  { label: 'transport implementation jargon', re: /\\b(?:HTTP(?:S)?|idempotence)\\b/i },
  { label: 'supply implementation jargon', re: /\\b(?:Procurement|Backorder|Dispatch|Outcome)\\b/i },
  { label: 'internal tenancy/version jargon', re: /\\bTenant\\b|\\bP10\\b/i },
  { label: 'raw internal workflow status', re: /\\b(?:DRAFT|SENT_TO_PARTNER|MODIFIED_AFTER_SEND|CONFIRMED|FULFILLED|CANCELLED|WAITING_INVOICE|AMOUNT_MISMATCH|SUCCEEDED|DEGRADED|APPLIED)\\b/ },
  { label: 'integration field jargon', re: /\\b(?:URL\\s+API|Mode\\s+sync)\\b/i },
"""
    text = replace_exact(text, anchor, block)
    text = replace_exact(
        text,
        "const USER_COPY_ATTRIBUTES = new Set(['alt', 'aria-label', 'aria-description', 'placeholder', 'title', 'engineName']);",
        "const USER_COPY_ATTRIBUTES = new Set(['alt', 'aria-label', 'aria-description', 'placeholder', 'title', 'engineName', 'label', 'eyebrow', 'subtitle', 'description', 'message', 'caption', 'helperText', 'emptyText']);",
    )
    text = replace_exact(
        text,
        "const USER_COPY_PROPERTIES = new Set(['label', 'title', 'subtitle', 'description', 'message', 'caption', 'helperText', 'emptyText', 'placeholder']);",
        "const USER_COPY_PROPERTIES = new Set(['label', 'title', 'subtitle', 'description', 'message', 'body', 'caption', 'helperText', 'emptyText', 'placeholder']);",
    )
    AUDIT.write_text(text, encoding='utf-8')


def patch_test() -> None:
    text = TEST.read_text(encoding='utf-8')
    text = replace_exact(
        text,
        "expect(screen.getByRole('button', { name: /Dispatch fournisseur/i })).toBeTruthy();",
        "expect(screen.getByRole('button', { name: /Envoyer au fournisseur/i })).toBeTruthy();",
    )
    text = replace_exact(
        text,
        "    expect(screen.getByRole('button', { name: /Enregistrer réception/i })).toBeTruthy();\n",
        "    expect(screen.getByRole('button', { name: /Enregistrer réception/i })).toBeTruthy();\n    expect(screen.getByText(/Dental Supply Demo · Brouillon/i)).toBeTruthy();\n    expect(screen.queryByText(/DRAFT|CONFIRMED|FULFILLED|Control-plane|WebAuthn|JWT|Procurement|Backorder|Outcome|HTTP/i)).toBeNull();\n",
    )
    TEST.write_text(text, encoding='utf-8')


patch_view()
patch_audit()
patch_test()
