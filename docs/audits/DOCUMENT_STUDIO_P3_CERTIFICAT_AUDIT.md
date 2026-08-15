# Document Studio — P3 Certificat — audit

Date de l'audit : 2026-08-15

## Statut

P3 Certificat n'est **pas certifié final** à ce stade.

Le décorticage pratique, technique et médico-légal a produit des correctifs dédiés, mais les PR ouvertes ne peuvent pas être certifiées par GitHub Actions tant que le blocage compte `Billing & plans` empêche les jobs de démarrer. Les runs observés échouent avant toute étape (`steps=[]`, `runner_id=0`).

Aucun pourcentage d'avancement global n'est déclaré tant que l'audit complet, la CI réellement exécutée, les merges et la validation runtime/visuelle ne sont pas clos.

## Baseline déjà mergée

### PR #48 — Nature du document
- mergée ; trois parcours explicites : `Arrêt de travail`, `Certificat de Présence`, `Certificat médical` ; contenu libre praticien ; aucune suggestion clinique injectée ; migration legacy ; durée uniquement pour arrêt de travail.

### PR #49 — Dates + durée
- mergée ; date d'émission distincte du début du repos ; présence et certificat libre sans durée/date de repos inutile ; réouverture historique compatible.

Baseline `master` auditée : `a7fc4417e39120ff844c119fd2f4cfe42239bb8b`.

## Lots P3 ouverts

| PR | Scope | Base | Head audité | État GitHub | Certification |
|---|---|---|---|---|---|
| #52 | signature manuscrite + signataire DENTISTE uniquement | master | `31e7943fab0b3d1e7a38bc7f091c545fb3fbdf24` | open / mergeable | non certifiée |
| #53 | validation UX praticien | master | `00f85c37639dc5537a2e19387a273e9e91cda1bb` | open / mergeable | non certifiée |
| #54 | signal contextuel non prescriptif | master | `7371793eaa4857dbbd03e461e38bccb422c23f5e` | open / mergeable | CI exact-head bloquée avant steps |
| #55 | identité datée + intégrité PDF | #52 | `f859e9ba652a36bfc4553318d56716ede19fe0d2` | open | doit être réaligné sur le nouveau head #52 |
| #56 | contrat backend fail-closed | master | `9976a7a5a4a06665dc5601e8af101414d45b9aa7` | open / mergeable | non certifiée |
| #57 | suppression assertions PDF non vérifiées | #55 | `954ae116b174778d9d60056b36ae242ef52f0e3f` | open | dépend du réalignement #55 |
| #58 | QR validation fail-closed | #57 | `407c0d8a1814246fe7b8aa4df99648d399dcb34f` | open | dépend du réalignement amont |
| #59 | identité réelle dans zone de signature | #58 | `cee04dbf08c792795fe10046b4ea763b781384ac` | open | dépend du réalignement amont |
| #60 | état neuf sans choix clinique + preview/UX | #53 | `f800925a2b0e72af6816feda1277459a0dca7804` | open / mergeable | CI exact-head à recertifier |
| #63 | impression sûre Certificat uniquement | #60 | `84ad80b14c82a4eb7b297b16526afe55f82af161` | open / mergeable | run 31908774717 : 3 jobs failure avant toute étape, Billing & plans |
| #61 | routage PDF, noms de fichiers, texte libre long | #59 | `f59fb121904b9bf61f67ee3e8d73fdbecf46a2f2` | open | dépend du réalignement amont |

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
2. **Pile PDF** : #52 a changé de head après durcissement `DENTISTE`-only ; #55→#57→#58→#59→#61 doivent être réalignées avant toute certification/merge.
3. **Régression finale** : backend + frontend + PDF après convergence.
4. **Runtime/visuel** : génération réelle des trois parcours et inspection PDF finale.
5. **Closeout canonique** : roadmap/statut/changelog après preuves finales uniquement.

## Ordre de convergence

- indépendants : #54, #56.
- UX : #53 → #60 → #63.
- PDF : #52 → réaligner #55 → #57 → #58 → #59 → #61.

Après chaque merge parent : réaligner le lot enfant, CI exacte-head réellement exécutée, puis merge. Après convergence : régression P3 complète + runtime/visuel + closeout.

## Amélioration non bloquante

Pas de garde SPA générique `useBlocker/usePrompt` pour formulaires non archivés ; à traiter transversalement, pas uniquement sur Certificat.