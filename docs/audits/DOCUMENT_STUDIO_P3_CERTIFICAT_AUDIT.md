# Document Studio — P3 Certificat — audit

Date de l'audit : 2026-08-15

## Statut

P3 Certificat n'est **pas certifié final** à ce stade.

Le décorticage pratique, technique et médico-légal a produit des correctifs dédiés, mais GitHub Actions reste bloqué par `Billing & plans`. Les runs concernés échouent avant toute étape (`steps=[]`, `runner_id=0`).

Aucun pourcentage d'avancement global n'est déclaré tant que la CI réellement exécutée, les merges, la régression finale et la validation runtime/visuelle ne sont pas clos.

## Baseline déjà mergée

- PR #48 — Nature du document : mergée.
- PR #49 — Dates + durée : mergée.
- Baseline `master` vérifiée : `a7fc4417e39120ff844c119fd2f4cfe42239bb8b`.

## Lots P3 ouverts

| PR | Scope | Base | Head audité | État GitHub | Certification |
|---|---|---|---|---|---|
| #52 | signature manuscrite + signataire DENTISTE uniquement | master | `31e7943fab0b3d1e7a38bc7f091c545fb3fbdf24` | open / mergeable | non certifiée |
| #53 | validation UX praticien | master | `00f85c37639dc5537a2e19387a273e9e91cda1bb` | open / mergeable | non certifiée |
| #54 | signal contextuel non prescriptif | master | `7371793eaa4857dbbd03e461e38bccb422c23f5e` | open / mergeable | CI bloquée avant steps |
| #55 | identité datée + intégrité PDF | #52 | `b122d92dc15d38dec37542b66ad133f161143636` | open / mergeable | non certifiée |
| #56 | contrat backend fail-closed | master | `9976a7a5a4a06665dc5601e8af101414d45b9aa7` | open / mergeable | non certifiée |
| #57 | suppression assertions PDF non vérifiées | #55 | `e1a538c9f1890a20f5c90fe5297b78475a4973f7` | open / mergeable | non certifiée |
| #58 | QR validation fail-closed | #57 | `963915c7d4ff2326a863fee9ce59451d169e821d` | open / mergeable | non certifiée |
| #59 | identité réelle dans zone de signature | #58 | `ee316763f25d0eab9d509d5e18d370147fff63ef` | open / mergeable | non certifiée |
| #60 | état neuf sans choix clinique + preview/UX | #53 | `f800925a2b0e72af6816feda1277459a0dca7804` | open / mergeable | CI à recertifier |
| #63 | impression sûre Certificat uniquement | #60 | `84ad80b14c82a4eb7b297b16526afe55f82af161` | open / mergeable | run 31908774717 : failure avant toute étape, Billing & plans |
| #61 | routage PDF, noms de fichiers, texte libre long | #59 | `85bba649947f8d912777fa9ea8cb1e665f62a76c` | open / mergeable | non certifiée |

## Audit pratique synthétique

### Nature / durée
- nouveau certificat : `type=''`, `days=0` ; aucun choix clinique automatique ; auto-preview silencieux tant qu'invalide ; backend refuse les defaults implicites ; durée d'arrêt entière 1..365 uniquement après saisie explicite.

### Signal contextuel
- aucun signal sans élément du jour ; seuls `EN_S_ATTENTE`, `EN_FAUTEUIL`, `TERMINÉ` peuvent soutenir une présence ; aucun type/durée appliqué automatiquement ; aucune aptitude/sport synthétisée.

### Certificat libre / PDF
- contenu praticien obligatoire ; pas de complétion clinique ; échappement ReportLab ; texte long multi-page ; aucune inférence mineur→éviction scolaire, ortho→soins ortho, ou remise en main propre ; raison inconnue refusée ; nom de fichier assaini.

### Signature
- seul le rôle `DENTISTE` est autorisé à signer ; `ADMIN` et `SECRETAIRE` sont refusés fail-closed ; identité du signataire obligatoire ; zone blanche 2,4 cm ; signature manuscrite uniquement ; aucun fac-similé/griffe/substitution.

### QR / preview / impression / archive
- QR `VALIDATION` neutralisé tant qu'aucune route `/verify/{id}` valide n'existe ; preview n'archive pas ; preview invalide n'appelle pas le backend ; #63 prépare un PDF final frais avant impression sans modifier les autres documents ; doublon géré par version forcée ; snapshot `req.data` archivé et réhydraté.

## Audit médico-légal

Source officielle : SGG, décret n° 2-96-989 du 5 janvier 1999. Points retenus : art. 9 certificat de complaisance interdit ; art. 23 certificat conforme aux constatations du médecin-dentiste, signature manuscrite obligatoire et substitution interdite ; art. 24 données acquises de la science.

Conséquence de conception : le logiciel ne doit pas inventer un fait clinique/documentaire, décider automatiquement d'une durée, ni remplacer la signature du praticien.

## Blocages réels avant certification finale

1. **CI GitHub Actions** : blocage `Billing & plans`; notamment #63 run `31908774717`, `steps=[]`, `runner_id=0`.
2. **Merges** : toutes les PR P3 ouvertes restent non certifiées tant qu'une CI exacte-head n'a pas réellement exécuté les tests.
3. **Régression finale** : backend + frontend + PDF après convergence.
4. **Runtime/visuel** : génération réelle des trois parcours et inspection PDF finale.
5. **Closeout canonique** : roadmap/statut/changelog après preuves finales uniquement.

## Ordre de convergence

- indépendants : #54, #56.
- UX : #53 → #60 → #63.
- PDF : #52 → #55 → #57 → #58 → #59 → #61.

La pile PDF est désormais réalignée sur le head courant #52. Après chaque merge parent : CI exacte-head réellement exécutée, puis merge de l'enfant. Après convergence : régression P3 complète + runtime/visuel + closeout.

## Amélioration non bloquante

Pas de garde SPA générique `useBlocker/usePrompt` pour formulaires non archivés ; à traiter transversalement, pas uniquement sur Certificat.