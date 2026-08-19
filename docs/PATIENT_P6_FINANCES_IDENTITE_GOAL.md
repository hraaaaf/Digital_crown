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

### Contrat backend identité
`backend/schemas/patient.py` impose à `PatientCreate` :
- `nom` ;
- `prenom` ;
- `date_naissance` ;
- `sexe`, normalisé uniquement à partir d’une valeur explicite M/F.

`numero_dossier`, téléphone(s), email, adresse, assurance, antécédents, motif et statut ortho sont optionnels. Le backend génère un numéro de dossier lorsqu’il est absent.

### AddPatientForm
Constats :
- `sexe` est initialisé à `F` avant interaction ;
- `assurance` est initialisée à `AUCUNE` ;
- le check numéro de dossier, en cas d’erreur réseau, force `status: available` ;
- `checkDuplicate()`, en cas d’erreur réseau, retourne `false` et poursuit donc la création ;
- le backend refait heureusement le contrôle doublon au POST, mais l’UI reste fail-open avant soumission ;
- téléphone/email/adresse sont correctement traités comme optionnels par la validation Add ;
- la page demande beaucoup d’enrichissement dès la première création alors que le backend ne l’exige pas.

### EditPatientForm
Constats :
- état initial `sexe: F`, puis `patient.sexe || F` ;
- même check de dossier fail-open (`catch => available`) ;
- en échec du GET Patient, l’erreur est seulement loggée puis `loading=false`, ce qui peut laisser un formulaire construit à partir de valeurs initiales ;
- téléphone principal est marqué `required` alors qu’il est optionnel dans le contrat backend et dans Add ;
- Add/Edit dupliquent structure, validation, assurance et téléphone avec des règles divergentes.

### Header Patient
P1 a déjà rendu le header compact. Identité, date/âge, dossier, assurance et alerte médicale sont visibles. P6 ne le redesign pas : il corrige seulement les ambiguïtés issues du formulaire et les permissions des actions financières.

### PatientFinances
`PatientFinances.tsx` :
- récupère `/patients/{id}/financial-snapshot` puis `/accounting/actes-billing/patient/{id}` ;
- ne gère pas explicitement `isError` sur le snapshot ;
- calcule le taux de recouvrement côté frontend ;
- affiche 4 KPI actuels : Facturé / Encaissé / Reste dû / Taux Recouvrement ;
- propose paiements par acte, échéancier et encaissement rapide.

Le snapshot backend calcule actuellement `total_billed` uniquement depuis `Acte` et `total_collected` depuis `Payment`, puis `remaining_due=max(facturé-encaissé,0)`. Contrairement au Journey P2, il n’expose pas `has_billing_data`. Un patient avec paiements mais sans lignes Acte peut donc visuellement ressembler à un dossier `0 facturé / 0 dû / aucun impayé`, alors que la base facturée est absente.

### Permissions financières
- `/patients/{id}/financial-snapshot` exige actuellement seulement `patients` ;
- `/accounting/actes-billing/patient/{id}` exige `accounting` ;
- `POST /accounting/payments` exige `accounting` ou `payments` ;
- la Page Patient affiche pourtant systématiquement l’onglet `Finances` et l’action rapide `Encaisser`.

Cette asymétrie doit être supprimée. L’UI ne doit pas inviter à une action interdite et le snapshot financier doit suivre une permission financière cohérente.

### Paiement canonique déjà correct à préserver
`QuickPayModal` exige :
- montant > 0 ;
- méthode explicite parmi ESPECES/CARTE/VIREMENT/CHEQUE ;
- appel `paymentApi.recordPayment()` vers `/accounting/payments`.

Le backend vérifie déjà qu’un `acte_id` / `installment_id` appartient au même patient et refuse un paiement ciblant les deux simultanément. P6 préserve cette frontière.

## Découpage P6

### P6-A — Contrat identité unique
- extraire un contrat/form model partagé Add/Edit sans créer une abstraction plus large que nécessaire ;
- aucun défaut de sexe ;
- aligner required/optional sur le backend ;
- état erreur de chargement Edit + Réessayer ;
- garder création rapide sur 4 champs obligatoires, enrichissement secondaire repliable.

### P6-B — Anti-doublon et dossier fail-closed
- état `unknown/error` distinct de `available` ;
- si précheck doublon échoue, ne pas interpréter cela comme « pas de doublon » ;
- permettre la soumission seulement via le backend canonique en affichant clairement que le précheck est indisponible, ou exiger un retry selon le flux retenu ;
- conserver le 409 backend comme autorité finale ;
- tests tenant/duplicate existants conservés.

### P6-C — Vérité financière
- exposer `has_billing_data` (ou équivalent explicite) dans le snapshot Patient ;
- `Facturé / Encaissé / Reste dû / Prochaine échéance` ;
- absence de base facturée => état indéterminé, jamais faux zéro ;
- supprimer/relocaliser le taux de recouvrement de la fiche Patient ;
- erreur snapshot => état erreur + Réessayer.

### P6-D — RBAC et cohérence encaissement
- aligner onglet Finances + action Encaisser sur `accounting/payments` ;
- aligner permission du snapshot avec la surface financière ;
- conserver `Payment` comme seule écriture d’encaissement ;
- tester QuickPay, paiement acte, échéance, patient A→B et sous-compte sans permission.

### P6-E — Certification
- BEFORE Add + Edit + Finances sur les 4 viewports ;
- tests frontend ciblés ;
- tests backend vérité financière/duplicate/RBAC ;
- AFTER mêmes 12 vues ;
- comparaison BEFORE / wireframe / AFTER ;
- CI + T2 exact-HEAD ;
- certificat P6 puis roadmap.

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

## Preuve requise
- baseline BEFORE 12 captures (Add/Edit/Finances × 4 viewports) ;
- tests d’erreurs réseau Add/Edit/Finances ;
- anti-doublon fail-closed ;
- test sexe non prérempli ;
- RBAC finance ;
- cohérence totals/payment/installment ;
- AFTER 12 captures mêmes viewports ;
- CI/T2 exact-HEAD ;
- score visuel argumenté.

## Règles
- pas de nouvelle donnée obligatoire non imposée par le backend ;
- pas de faux `disponible` après erreur réseau ;
- pas de sexe par défaut ;
- pas de `0 MAD` interprété comme absence de dette si la base facturée manque ;
- pas de finance visible/actionnable sans permission cohérente ;
- pas de rebuild du moteur de paiement déjà durci ;
- aucun déploiement Vercel.
