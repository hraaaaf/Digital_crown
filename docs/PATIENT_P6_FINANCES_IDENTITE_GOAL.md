# Patient P6 — Finances & identité Patient

## Goal
Rendre la création, l’édition et la lecture financière d’un patient plus courtes et sans ambiguïté : un seul contrat d’identité, contrôles fail-closed, permissions financières cohérentes et quatre informations financières factuelles au maximum.

## Succès observable
1. Add/Edit reposent sur le même contrat de champs, validation et états réseau.
2. Aucun sexe n’est préselectionné ou reconstruit si l’utilisateur/backend ne l’a pas fourni explicitement.
3. Une erreur du précheck doublon ou numéro de dossier n’est jamais présentée comme « aucun doublon » / « disponible ».
4. Création initiale requiert uniquement le contrat backend réel : nom, prénom, date de naissance, sexe explicite. Le reste est optionnel/enrichissable après création.
5. Une erreur de chargement Edit affiche une erreur + Réessayer ; elle ne rend jamais un formulaire vide comme s’il s’agissait du patient.
6. Finances affiche en priorité : Facturé, Encaissé, Reste dû, Prochaine échéance.
7. En absence de base facturée fiable, l’UI affiche `Solde indéterminé` et ne conclut ni `0 MAD` ni `Aucun impayé`.
8. Le taux de recouvrement quitte la ligne KPI principale Patient ; il peut rester dans une vue comptable dédiée si utile.
9. Onglet Finances et action Encaisser suivent la permission réelle `accounting/payments`; le backend reste autoritaire.
10. Encaissement rapide, paiement lié à un acte et paiement d’échéance utilisent le même contrat `Payment` canonique et exigent une méthode explicite.
11. Zéro overflow horizontal, erreur runtime ou HTTP 5xx sur 390x844, 430x932, 768x1024 et 1280x900.

## Audit initial
L’audit a établi que `PatientCreate` n’exige réellement que nom, prénom, date de naissance et sexe explicite. Add/Edit divergeaient, préremplissaient `F`, transformaient certains échecs réseau en faux états positifs, et Edit pouvait afficher un formulaire à partir de valeurs initiales après échec GET. Côté finances, le snapshot ne distinguait pas absence de base facturée et zéro réel ; la fiche exposait un taux de recouvrement et des surfaces Finances/Encaisser sans RBAC cohérent.

## Wireframe cible

```text
NOUVEAU PATIENT
┌─────────────────────────────────────────────────────────────┐
│ IDENTITÉ ESSENTIELLE                                        │
│ Nom*              Prénom*                                   │
│ Date naissance*   Sexe* [Choisir…]                          │
│ N° dossier [généré automatiquement]                         │
│ Etat du contrôle : disponible / pris / vérification HS      │
└─────────────────────────────────────────────────────────────┘

[ + Coordonnées, assurance et informations complémentaires ]

                                      [Créer le patient]

EDIT PATIENT
Même contrat de champs et validations.
Erreur GET => « Impossible de charger le patient » [Réessayer]

FINANCES
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ FACTURÉ      │ │ ENCAISSÉ     │ │ RESTE DÛ     │ │ PROCH. ÉCH.  │
│ 3 000 MAD    │ │ 1 500 MAD    │ │ 1 500 MAD    │ │ 24 août     │
│ Source Actes │ │ Paiements    │ │ Calcul sourcé│ │ Échéancier   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

Sans base Acte fiable :
Facturé : Indéterminé | Reste dû : Indéterminé
Encaissé reste affichable si des Payments existent réellement.
```

## Implémentation actuelle — à certifier

### P6-A/B — Identité partagée et fail-closed
- `PatientIdentityContract.ts` centralise initialisation, mapping API, validation et payload Add/Edit.
- sexe initial vide et option `Choisir…`; aucune substitution `F`.
- téléphone cohérent et optionnel.
- erreur check-dossier => `Disponibilité non vérifiée`.
- erreur précheck doublon => création interrompue ; 409 backend reste l’autorité finale.
- erreur GET Edit => état erreur + Réessayer, aucun formulaire fantôme.

### P6-C — Vérité financière
- `patient_financial_p6.py` remplace explicitement l’ancien snapshot sous la même URL publique.
- `has_billing_data` signifie au moins une ligne `Acte` ; `remaining_due=null` si aucune base facturée n’existe.
- paiements restent factuels même sans base Acte.
- prochaine échéance réelle exposée via `next_installment`.
- UI : Facturé / Encaissé / Reste dû / Prochaine échéance ; taux de recouvrement retiré.
- base facturée absente => Facturé/Reste dû indéterminés et situation d’impayé indéterminée.
- erreur snapshot => erreur + Réessayer.

### P6-D — RBAC / encaissement
- snapshot : permission `accounting OR payments` + isolation patient.
- Page Patient masque Finances + Encaisser + QuickPay sans permission adéquate et redirige `?tab=finances` vers Vue d’ensemble.
- QuickPay et paiements ciblés continuent d’utiliser `/accounting/payments`, avec méthode explicite.

## Preuves préparées
- backend : absence de base vs zéro réel, prochaine échéance, RBAC accounting/payments.
- frontend : identité partagée, fail-closed, finance visible/RBAC, KPI factuels, paiement canonique.
- AFTER : Add/Edit/Finances × 390/430/768/1280 = 12 captures.

## Reste avant CLOSED
1. resynchroniser P6 sur P5 final ;
2. CI + T2 + AFTER exact-HEAD ;
3. inspecter les 12 captures et scorer ;
4. certificat + roadmap ;
5. recertification closeout exact-HEAD.

## Règles
- pas de nouvelle donnée obligatoire non imposée par le backend ;
- pas de faux `disponible` après erreur réseau ;
- pas de sexe par défaut ;
- pas de `0 MAD` interprété comme absence de dette si la base facturée manque ;
- pas de finance visible/actionnable sans permission cohérente ;
- pas de rebuild du moteur de paiement déjà durci ;
- aucun déploiement Vercel.
