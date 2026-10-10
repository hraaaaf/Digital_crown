# FUE-G 00 — Certification Hub / Cabinet / Centre de contrôle / Station (LAB T2 isolé)

Date : **2026-10-10**  
Statut de référence : **LAB logiciel CONVERGED / PASS — 9,0/10** sur le commit exact `36ff7da479ae1a1996e6bb4bbd02f428032f5a02`.  
**FUE-G 00 canonique global : PARTIEL / OUVERT** — premier démarrage, installation et redémarrage sur PC physique vierge et usage réel non prouvés.  
**Attention à la validité du HEAD :** cette mise à jour documentaire modifie elle-même le commit. Le résultat ci-dessous appartient exclusivement au SHA de référence tant que la CI sur le nouveau HEAD documentaire n'est pas terminée et vérifiée. Aucun merge ni Vercel implicitement autorisé.

Sources canoniques : [plan FUE](https://app.notion.com/p/3f177c66336281c49a48d1361307f458), [roadmap / POST](https://app.notion.com/p/3e677c66336281d88c82d2fbe43835fb), [matrice rétrospective des 18 sous-lots](./V1_5_FUE_00_TO_03_RETROSPECTIVE_MATRIX.md).  
Compte-rendu des deux perspectives de revue **internes** (non reviewers externes) : [PR #821 — certification exacte](https://github.com/hraaaaf/Digital_crown/pull/821#issuecomment-6096130969).

## Résultat observable et preuves exactes

| Contrôle | Preuve sur le commit `36ff7da4…` | Verdict |
| --- | --- | --- |
| FUE-G 00 — trois parcours Chromium | [GitHub Actions #38040827000](https://github.com/hraaaaf/Digital_crown/actions/runs/38040827000) | **COMPLETED / SUCCESS** |
| CI Scope Gate | [GitHub Actions #38040826992](https://github.com/hraaaaf/Digital_crown/actions/runs/38040826992) | **COMPLETED / SUCCESS** |
| Contrats backend de topologie | Logs du run FUE-G 00 | **35/35 PASS** |
| Contrats frontend Hub | Logs du run FUE-G 00 | **8/8 PASS** |
| Précondition premier poste | Requête en lecture seule, SQLite/SQLCipher T2 chiffrée | **0 poste au départ** |
| Preuve BEFORE / ACTION / AFTER | [Artefact GitHub #11666330618](https://github.com/hraaaaf/Digital_crown/actions/runs/38040827000/artifacts/11666330618) | **42 PNG + 3 rapports JSON** |
| Total de scénarios instrumentés | 16 + 34 + 40 | **90/90 vérifications vraies** |
| M6-I — biométrie / passkey | [Run #38040827044](https://github.com/hraaaaf/Digital_crown/actions/runs/38040827044) | **SKIPPED — EXPERIMENTAL / HORS SCOPE** |

Archive ZIP : SHA-256 `79156abaff2f0c917c255a0c44650b6e9c88e519dd5ed81fbe0c0a851445296d`. Les **45 fichiers** ont été comptés ; les **42 PNG** ont été décodés et contrôlés aux largeurs attendues (768 ou 1280 px), regroupés en **5 planches visuelles effectivement examinées** ; les **3 JSON** portent le même `head=36ff7da479ae1a1996e6bb4bbd02f428032f5a02`, `success=true`, `isolated=true`, `failures=[]`. Pas de `pageerror`, HTTP 5xx ni débordement horizontal signalé par les scripts.

## Les trois parcours réellement couverts

### A — Tout premier poste d'un cabinet logiciel vierge (16/16, 6 PNG)

Script : [`frontend/scripts/audit-v15-fue-g00-first-ever-t2.mjs`](../../frontend/scripts/audit-v15-fue-g00-first-ever-t2.mjs), **tablette 768 × 1024 seulement**. Le workflow nettoie la base T2 puis exige **zéro ligne** `WorkstationMode` avant le test. Navigateur neuf sans cookies, sans JWT ou `storageState` injectés. Hub avec ses trois choix → clic **Cabinet** → authentification propriétaire par vrai formulaire UI. Selon le routage réel de première connexion, l'écran de destination entièrement rendu peut être le Hub ou le Dashboard ; le harness enregistre ce résultat, n'accepte aucune simple URL transitoire et revient au Hub explicite pour vérifier la propriété du poste.

Le **produit** crée automatiquement la première identité via son vrai `GET /workstation/state`, et non via un `POST /workstation/enroll` lancé par le test. Les lectures serveur `GET /workstation/bootstrap` et `GET /workstation/registry` exigent **exactement un poste**, identifiant cohérent avec le cookie `dc_workstation` émis par le serveur. Clic UI Cabinet → Dashboard clinique → Centre de contrôle → retour au Hub par son bouton affiché. Les contrôles négatifs d'injection et de stabilité sont conservés.

### B — Parcours Hub, Cabinet, PIN, Station et sortie (34/34, 20 PNG)

Script : [`frontend/scripts/audit-v15-fue-g00-integrated-t2.mjs`](../../frontend/scripts/audit-v15-fue-g00-integrated-t2.mjs), **tablette 768 × 1024 et desktop 1280 × 900**, 17 assertions et 10 captures par profil. Pour ce scénario seulement, le banc T2 prépare en amont une **identité de poste légitime par API serveur** et transmet uniquement le cookie `dc_workstation`, sans injecter d'authentification utilisateur dans le navigateur.

Hub anonyme à trois destinations → Cabinet exige login réel → Dashboard authentifié → Control via Hub et retour par son bouton. Configuration du PIN propriétaire au serveur (HTTP 200), mode Station par UI et serveur (200). URLs directes Hub et Control interdites tant que Station verrouillée, verrou conservé après rechargement ; mauvais PIN refusé par serveur (**403**, reste en Station), bon PIN accepté (**200**, retour Hub via UI réelle).

### C — Nouveau navigateur dans un cabinet possédant déjà des postes (40/40, 16 PNG)

Script : [`frontend/scripts/audit-v15-fue-g00-fresh-enrollment-t2.mjs`](../../frontend/scripts/audit-v15-fue-g00-fresh-enrollment-t2.mjs), **tablette et desktop**, 20 assertions et 8 captures par profil. Chaque navigateur est neuf, **aucun cookie de poste ni token utilisateur injecté**. Hub → Cabinet → vrai login propriétaire → écran d'enrôlement au lieu d'un accès clinique. Le serveur refuse l'identité inconnue (**423**), et le mauvais mot de passe propriétaire est refusé (**403**) sans attribuer de cookie de poste.

Le formulaire UI propriétaire permet ensuite l'enrôlement légitime (**HTTP 200**), qui produit **seulement alors** le cookie `dc_workstation`. Le Dashboard clinique et le Centre de contrôle deviennent accessibles et le retour Hub s'effectue par le bouton réel. L'assertion visuelle est renforcée : attendre `[data-tour="quick-action-new-patient"]` **visible** et le titre **« Nouveau Patient »** effectivement affiché avant de photographier le Dashboard. La capture desktop finale a été ouverte en pleine résolution ; « Nouveau Patient », « Dossiers Patients » et « Agenda Clinique » sont réellement rendus, contrairement à un ancien faux positif de transition.

## Revues adversariales (même HEAD, perspectives internes)

**A — UX, capture et navigation : 9,1/10 — CLEAN sur ce périmètre LAB.** Les cinq planches BEFORE/ACTION/AFTER et la capture Dashboard desktop finale ont été inspectées ; chemin premier poste, refus d'accès, vrai enrôlement, panneau propriétaire, contrôle, Station/reload et sortie PIN lisibles. Pas de CTAs principaux coupés ni d'écran final blanc observés aux résolutions couvertes. **Dette P2** : panneau Hub propriétaire long et dense sur tablette ; zoom texte 200 %, largeur mobile 390 px, clavier seul et observation humaine **non certifiés**.

**B — Sécurité, isolation, autorité et preuves : 9,0/10 — CLEAN sur ce périmètre LAB.** La base T2 est jetable et isolée ; cookie de poste opaque délivré par le serveur ; premier poste issu de l'application et identité contrôlée par lectures `bootstrap/registry` ; refus backend 423/403 et autorisations 200 ; verrou Station, mauvais PIN et rechargement réellement vérifiés. Secrets temporaires masqués dans les logs, aucun credential authentifiant dans les rapports inspectés. Les changements de la PR ne touchent **aucun runtime produit, routeur auth, backend de production ni migration DB** : uniquement trois scripts LAB, workflow et présent audit.

**Convergence LAB :** deux perspectives internes sur le même SHA, **aucun BLOCKER/MAJOR démontré dans les trois parcours ciblés**, CI REQUIRED verte, 90 vérifications et preuves visuelles inspectées. Score sévère retenu **min(9,1 ; 9,0) = 9,0/10**. Ne jamais qualifier ces revues de **revues externes indépendantes**.

## Limites, gates et décision

- **FUE-G 00 logiciel T2 = CONVERGED / PASS sur `36ff7da4…`** ; le nouveau commit du rapport documentaire reste conditionné à son **propre run exact-HEAD**.
- **FUE-G 00 canonique terrain = PARTIEL / OUVERT** : vraie installation sur PC matériel vierge, premier démarrage OS, relance après reboot, identité/continuité sur le réseau LAN/TLS réel, interaction d'un opérateur et reprise hors banc isolé ne sont pas démontrés.
- **G01/G02/G03** (LAN multi-postes, webcam réelle et patients Station) restent des gates distincts. Les contrôles biométriques expérimentaux ou autres workflows **hors scope** ne sont pas promus en blockers sans défaut de sécurité réel ; les tests **REQUIRED** ne sont pas réduits.
- La logique d'enrôlement initial par d'autres rôles, abus/rate-limit répétés, tenants réels, appareils mobiles/zoom et essais cliniques sur dossiers réels n'ont **pas** été validés par cette preuve ciblée.
- **PR #821 reste DRAFT / NON MERGED**, master inchangé à la preuve de référence ; ni Vercel, ni release, ni déploiement, ni test sur PC client autorisés par ce résultat.

## Closeout documentaire et prochaine décision

1. Après le commit **document + déclencheur CI sur le chemin de cet audit**, revérifier les checks requis et les archives sur le nouveau HEAD ; **aucun « PASS sur nouveau HEAD » par héritage**. Si rouge, diagnostiquer et corriger sans affaiblir les assertions ni prétendre à une validation asynchrone.
2. Confirmer que les cinq fichiers de PR sont exclusivement du matériel de test/documentation, que les deux perspectives adversariales restent propres sur le même nouveau HEAD, et que GitHub/Notion sont cohérents.
3. Proposer la fusion **uniquement après ces preuves**, et **demander une autorisation explicite distincte** pour merge ; Vercel exige un autre accord. La certification terrain exige son protocole/état propre.

Historique : postmerge indépendant de [#820 / run #38014691497](https://github.com/hraaaaf/Digital_crown/actions/runs/38014691497) PASS sur `master@4edd5975…` ; ancienne preuve intégrée [#38034317309](https://github.com/hraaaaf/Digital_crown/actions/runs/38034317309) 34/34 ; deux parcours [#38036303489](https://github.com/hraaaaf/Digital_crown/actions/runs/38036303489) 74/74 ; premier run vert 90/90 [#38038917578](https://github.com/hraaaaf/Digital_crown/actions/runs/38038917578), dont l'inspection a permis de renforcer la capture desktop AFTER. **Seule la certification exacte #38040827000 établit le présent score LAB sur le SHA 36ff.**
