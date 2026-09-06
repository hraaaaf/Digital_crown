# DIGITAL CROWN MOBILE — MOB-5H SUPERADMIN GOAL UI

Status: GOAL UI LOCKED — BEFORE PENDING
Baseline exact: `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
Branch: `ux/mobile-superadmin-mob5h`
Audit: `docs/ux/DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_AUDIT.md`

## Goal

Transformer la surface mobile SuperAdmin en **console complète de pilotage**, donnant accès à **100 % des prérogatives SuperAdmin existantes** déjà autorisées par le backend Digital Crown, sans dupliquer ni affaiblir la logique métier/RBAC serveur.

Le mobile doit rester un cockpit opérationnel : accès rapide, hiérarchie claire, mutations sensibles explicites, pas une copie responsive du desktop.

## Success

1. Toutes les prérogatives inventoriées dans l'audit sont accessibles depuis la console mobile.
2. Toute nouvelle route active `verify_superadmin` / `require_superadmin` découverte avant certification entre automatiquement dans le scope.
3. Les mutations utilisent les endpoints canoniques et gardent leurs règles serveur : validation, transition, version, idempotence, confirmation, audit.
4. Les actions sensibles ne partent jamais sur un simple tap accidentel.
5. Le rôle reste fail-closed : aucun utilisateur non SuperAdmin ne voit ni n'utilise la console.
6. La nav mobile canonique reste exactement `Aujourd’hui / Patients / + / Assistant / Plus`, hauteur 76 px.
7. Preview entièrement fictive et sans réseau réel.
8. 390×844, 430×932 et 768×1024 : 0 overflow horizontal, 0 erreur runtime, actions principales accessibles au pouce.
9. Test dédié `MobileSuperAdminView.test.tsx` + build production + gates backend pertinents verts.
10. Score visuel cible >= 9,2/10, sans forcer la note : seul le BEFORE/AFTER inspecté décide.

## Proof

- BEFORE sur le baseline exact `6eb93c75...` aux mêmes viewports que l'AFTER ;
- matrice endpoint → surface mobile → test ;
- tests frontend dédiés ;
- build production ;
- tests backend SuperAdmin/Marketplace réellement présents et pertinents ;
- AFTER 390/430/768 + états secondaires critiques ;
- report runtime : 0 page error, 0 console error, 0 overflow ;
- preview : 0 appel API réel ;
- aucune modification des guards backend nécessaire pour la parité ;
- diff final sans changement Vercel.

---

# 1. Architecture UI cible

La console garde l'entrée mobile SuperAdmin existante et devient un shell dédié à cinq sections internes. **Ce ne sont pas cinq entrées de la bottom nav canonique.**

## Sections internes

1. **Vue globale**
2. **Clients**
3. **Codes d’essai**
4. **Marketplace**
5. **Opérations**

Navigation recommandée : segmented tabs/chips horizontaux sous un header compact `SuperAdmin`, avec conservation de la position et du filtre par section.

### Pourquoi cette structure

- `Clients` regroupe identité, licence et CRM interne.
- `Codes d’essai` est une tâche autonome, fréquente et courte.
- `Marketplace` regroupe gouvernance catalogue/fournisseurs.
- `Opérations` regroupe commandes, dispatch, procurement, finance et réceptions, où les mutations ont un risque supérieur.
- `Vue globale` permet de diagnostiquer avant d'agir.

---

# 2. Header cible

```text
┌──────────────────────────────────────┐
│ ←   SuperAdmin                  ↻    │
│ Console Digital Crown                │
│ [Vue globale] [Clients] [Essais] →   │
└──────────────────────────────────────┘
```

Contraintes :
- retour vers le dashboard mobile ;
- refresh explicite ;
- pas de hero vertical ;
- statut réseau/erreur visible sans masquer toute la console ;
- aucun bouton destructif dans le header.

---

# 3. Vue globale

Objectif : comprendre l'état du parc et de Marketplace avant mutation.

```text
┌─ Vue globale ────────────────────────┐
│ Clients       42     À renouveler  5 │
│ Suspendus      2     Archivés       1 │
│                                      │
│ Marketplace                           │
│ Commandes      18    Incidents sync 2 │
│ Fournisseurs   7     À traiter       4 │
│                                      │
│ [Voir clients critiques]             │
│ [Voir opérations]                    │
└──────────────────────────────────────┘
```

Les KPI Marketplace proviennent des endpoints SuperAdmin globaux existants. Pas de métrique inventée si le backend ne la fournit pas.

---

# 4. Clients

## Liste

Recherche dominante : nom / cabinet / email.
Filtres secondaires : Actif / À renouveler / Suspendu / Archivé.
Carte compacte, aucune mutation destructive directement sur la liste.

```text
┌─ Clients ────────────────────────────┐
│ 🔎 Nom, cabinet ou email             │
│ [Actifs] [Renouveler] [Suspendus] →  │
│                                      │
│ Cabinet Atlas                  Actif │
│ Dr Baseline · GOLD                   │
│ Expire dans 24 j                ›    │
└──────────────────────────────────────┘
```

## Détail client

Ouverture en page/sheet plein écran mobile. Toutes les prérogatives core doivent être accessibles :

- valider/activer le client + essai 30j ;
- changer GOLD/PREMIUM/ELITE ;
- prolonger 1m/3m/6m/1y ;
- révoquer la licence ;
- suspendre/réactiver ;
- archiver/désarchiver ;
- consulter/modifier notes internes ;
- consulter historique licence ;
- envoyer email de renouvellement.

```text
┌─ Cabinet Atlas ──────────────────────┐
│ Dr Baseline                          │
│ baseline@example.test                │
│ Actif · GOLD · expire 30/09/2026     │
│                                      │
│ Licence                              │
│ [ +1M ] [ +3M ] [ +6M ] [ +1AN ]   │
│ Pack          [ GOLD ▾ ]             │
│ [Envoyer relance]                    │
│                                      │
│ Notes internes                       │
│ [.................................]  │
│ [Enregistrer]                        │
│                                      │
│ Historique                      ›    │
│                                      │
│ Zone sensible                        │
│ [Suspendre] [Archiver]               │
│ [Révoquer licence]                   │
└──────────────────────────────────────┘
```

### Garde-fous

- extension de licence : confirmation légère ou action réversible explicitement annoncée ;
- pack : confirmation si changement ;
- relance email : confirmation simple ;
- suspension / archivage : confirmation modale explicite avec nom du client ;
- révocation licence : confirmation renforcée avec libellé de conséquence, jamais un tap unique.

---

# 5. Codes d'essai

Fonctions : liste, création, copie du lien/code, révocation si non consommé.

```text
┌─ Codes d’essai ──────────────────────┐
│ [+ Nouveau code]                     │
│                                      │
│ DC-AB12-CD34-EF56             Actif  │
│ Cabinet Démo · 30 jours              │
│ expire 15/09/2026                    │
│ [Copier] [Révoquer]                  │
└──────────────────────────────────────┘
```

Création via bottom sheet/formulaire avec les champs réellement supportés par le backend : email, nom, cabinet, jours d'essai, durée de validité du code, notes.

Révocation : confirmation explicite.

---

# 6. Marketplace — gouvernance

Surface dédiée aux pouvoirs globaux SuperAdmin :

- overview Marketplace ;
- fournisseurs globaux ;
- activer/désactiver fournisseur ;
- créer/modifier fournisseur ;
- créer/modifier produit ;
- audit Marketplace ;
- incidents de synchronisation ;
- statut sync fournisseur ;
- synchronisation et force sync.

```text
┌─ Marketplace ────────────────────────┐
│ [Fournisseurs] [Catalogue] [Audit] → │
│                                      │
│ MedSupply Maroc                Actif │
│ API · Sync FRESH                      │
│ 423 produits                         │
│ [Détails] [Synchroniser]             │
│                                      │
│ ⚠ 2 incidents sync                   │
└──────────────────────────────────────┘
```

### Mutations sensibles Marketplace

- désactivation fournisseur : confirmation explicite ;
- force sync : confirmation avec impact possible sur catalogue ;
- création/modification fournisseur/produit : formulaire validé, pas d'édition inline fragile ;
- conserver les tokens/confirmations imposés par les endpoints.

---

# 7. Opérations Marketplace

Cette section réunit ce qui agit sur de vraies commandes et flux financiers.

## Liste commandes

Filtres : statut / cabinet / fournisseur / besoin d'action selon ce que les endpoints existants supportent réellement.

```text
┌─ Opérations ─────────────────────────┐
│ 🔎 Commande, cabinet, fournisseur     │
│ [DRAFT] [Envoyées] [Confirmées] →    │
│                                      │
│ CMD-PART-...                   DRAFT │
│ Cabinet Atlas · MedSupply            │
│ 1 240 MAD                       ›    │
└──────────────────────────────────────┘
```

## Détail opération

Doit donner accès aux capacités canoniques réellement autorisées :

- transitions commande et note/référence/montant selon moteur serveur ;
- consultation du dispatch ;
- dispatch fournisseur réel ;
- procurement : facture fournisseur, coût, payé, statut, notes ;
- finance : paiement, ajustements/frais, règlement, charge cabinet, payout fournisseur, références ;
- réceptions : historique, partielle/complète, quantité, lot, expiration, note ;
- audit/événements associés disponibles dans les réponses existantes.

### Dispatch réel

Le bouton doit afficher avant envoi : fournisseur, commande, montant/destination utile disponible, et rappeler que l'action déclenche un appel externe réel. Confirmation obligatoire.

### Finance / procurement

Formulaire dédié, jamais mutation inline accidentelle. Les champs `version` / idempotency existants doivent être transmis exactement selon contrat backend.

### Réception

Le mobile doit afficher commandé / déjà reçu / restant. Impossible de proposer une quantité supérieure au restant, même si le backend la refuserait ensuite.

---

# 8. États et feedback

Chaque mutation suit le même contrat UX :

1. état initial lisible ;
2. confirmation si nécessaire ;
3. bouton désactivé pendant requête ;
4. succès/erreur explicite ;
5. refresh de la ressource canonique ;
6. aucune simulation locale d'un succès serveur.

Pas d'optimistic update sur : licence, suspension, archive, dispatch, finance, procurement, réception, sync forcée.

---

# 9. Preview / certification visuelle

Preview fictive obligatoire avec au minimum :

- 3 clients : actif, à renouveler, suspendu ;
- 2 codes d'essai : actif, révoqué/consommé ;
- 2 fournisseurs : FRESH et DEGRADED ;
- 3 commandes : DRAFT, CONFIRMED partiellement reçue, FULFILLED ;
- données financières fictives ;
- aucun nom/email/cabinet réel ;
- aucune requête réseau réelle.

Captures AFTER minimales :

- 390×844 : Vue globale ;
- 390×844 : détail client + zone sensible ;
- 390×844 : Codes d'essai ;
- 390×844 : Marketplace fournisseurs ;
- 390×844 : détail opération ;
- 430×932 : mêmes familles d'états ;
- 768×1024 : Vue globale + détail opération.

Le BEFORE doit capturer les mêmes viewports disponibles sur le baseline exact. Lorsque certaines surfaces n'existent pas au BEFORE, la preuve doit l'indiquer comme absence fonctionnelle plutôt que fabriquer une capture équivalente.

---

# 10. Non-objectifs

- aucune nouvelle prérogative backend inventée ;
- aucun assouplissement `verify_superadmin` / `require_superadmin` ;
- aucune écriture directe DB/Supabase ;
- aucune duplication desktop/mobile de logique métier ;
- aucune modification de la bottom nav canonique ;
- aucun déploiement Vercel sans autorisation explicite.

---

# 11. Critère de fermeture

MOB-5H n'est CERTIFIED que si :

- audit final des guards = aucune prérogative active oubliée ;
- matrice parité = 100 % couverte ou impossibilité documentée comme vrai blocage externe ;
- tests/build/runtime verts ;
- BEFORE/AFTER inspectés ;
- score visuel mesuré >= 9,2/10 ou, s'il est inférieur, correction poursuivie ;
- proof + canonique mis à jour ;
- PR mergée puis post-merge vérifié.
