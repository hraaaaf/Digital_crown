# DIGITAL CROWN — AUDIT GLOBAL (produit + technique + opérationnel)

> Date : 2026-07-11
> Portée : synthèse de l'audit concurrent du 09/07 (`DIGITAL_CROWN_FEATURE_AUDIT_VS_COMPETITOR.md`),
> du refresh roadmap du 10/07 (`STATE.md`), ET des découvertes opérationnelles des sessions
> 10-11/07 (runtime immuable, backups, incidents réels) — que les audits précédents ne
> couvraient pas. Contrairement à l'audit du 09/07 (produit vu de l'extérieur), celui-ci
> intègre ce que l'exploitation réelle a révélé.

---

## SCORE GLOBAL RÉVISÉ

| Dimension | 09/07 | 10/07 | **11/07 (cet audit)** | Tendance |
|---|---|---|---|---|
| Produit / fonctionnalités | 7,2 | 8,0 | **8,0** | stable (Journey construit mais non activé) |
| **Exploitation / fiabilité** | non audité | non audité | **7,5** (était ~3/10 avant le 10/07) | ⬆⬆ transformé cette session |
| Sécurité données | 9,5 | 9,5 | **9,0** (nuances découvertes, voir §3) | ⬇ léger |
| Qualité / dette technique | non audité | non audité | **6,5** | nouveau |

---

## 1. CE QUI EST BIEN FAIT (les vrais atouts, confirmés par l'exploitation réelle)

### Produit — différenciateurs difficiles à répliquer
- **IA locale ONNX** (panoramique YOLO11x 4 classes, céphalométrie automatique) — confirmé
  fonctionnel en production réelle (logs de boot vérifiés pendant RRIG-1). Aucun concurrent
  local-first n'a ça.
- **Céphalométrie** : studio 4 étapes, mesures auto, consistency validator — référence marché.
- **14 générateurs PDF** bilingues Fr/Ar avec registre typographique unifié, QR stratégique,
  protection médico-légale.
- **Ordonnance intelligente** : pharmacovigilance temps réel, learning loop par praticien,
  scraping medicament.ma.
- **Crown Bot** : LLM 100% local (Ollama), schéma strict, PII masking avant LLM,
  permission-gating par intent.
- **Multi-tenant rigoureux** : `employer_id` partout, `assert_patient_access`, médias derrière
  routes authentifiées, audit log.
- **Treatment Journey** (nouveau, 10/07) : construit, testé (13 tests backend + 10 frontend +
  concurrence PostgreSQL + sécurité), validé en rehearsal + smoke CTO — **prêt, non activé**.
  C'est LE différenciateur workflow qui manquait face au concurrent.

### Exploitation — transformée pendant les sessions 10-11/07 (nouveau depuis l'audit produit)
- **Runtime réel immuable** : le cabinet tourne depuis une release figée hors dépôt
  (`create_release.ps1` + `run_real_backend.ps1`), plus jamais `--reload` sur le port réel.
  Incident d'origine (activation accidentelle de code non validé) structurellement fermé.
- **Backups automatiques réels, enfin** : avant le 10/07, **aucun backup automatique n'avait
  jamais fonctionné** (scheduler in-app visait un fichier SQLCipher illisible depuis +1 mois ;
  tâche Windows cassée depuis sa création, 5 semaines d'échec silencieux). Aujourd'hui :
  `DigitalCrown_DailyBackup_v2` (03h00, DB via pg_dump + médias, chiffré, checksums, manifeste,
  verrou, rétention plafonnée, code exécuté depuis une release dédiée vérifiée par hash) —
  validé 2× en conditions réelles, restore et extraction testés en environnement isolé.
- **Provenance Git verrouillée** : l'état exact servi en production correspond à des commits
  locaux identifiés (6de00db → d7a8e7a → 0bd18fc), fichiers vérifiés octet par octet.
- **31 documents patients récupérés** (11/07) : seuls exemplaires physiques dans le dépôt,
  jamais sauvegardés, remis au bon emplacement avec triple vérification de hash, désormais
  couverts par les backups.
- **~2200 tests backend** avec fixtures réelles, CI backend fonctionnelle.

---

## 2. CE QUI N'EST PAS BIEN FAIT (constats factuels, hiérarchisés)

### Critique — à traiter avant/avec la Phase D
1. **`UNIFY-ACT-PERSISTENCE-1` (bombe silencieuse du module financier)** : la table `actes`
   (176 lignes) est de la donnée de seed, ne couvre que 13,6% des patients réels. Or
   `get_patient_financial_snapshot` (onglet Finances, déclaré "terminé") calcule les impayés
   depuis `Acte` → **le reste dû est très probablement sous-déclaré pour ~86% des patients
   réels**. Un cabinet qui fait confiance à cet écran perd de l'argent sans le savoir.
2. **`ENVIRONMENT=development` dans le `.env.local` du cabinet réel** : les invariants
   bloquants (`validate_environment_invariants` : DEBUG interdit, CORS wildcard interdit) ne
   s'appliquent PAS au vrai cabinet. `/api/health` répond littéralement
   `"environment":"development"` en production. Découvert pendant RRIG-1, jamais corrigé
   (hors scope des missions backup).
3. **Tous les backups vivent sur le même disque physique que les données** — et ce disque
   est à **3,2 Go libres** (10 Go recommandés). Une panne disque unique détruit données ET
   sauvegardes. La copie hebdo USB est documentée (`CABINET_ONPREM_GUIDE.md` §6) mais
   entièrement manuelle et non vérifiée.
4. **Aucune alerte quand un backup échoue** : les deux mécanismes précédents ont échoué en
   silence pendant des semaines sans que personne ne le voie. Le nouveau produit des
   manifestes exploitables (`last_backup_status.json`, `overall_status`) mais **rien ne les
   lit** : pas de widget dashboard, pas de ProactiveAlert, pas de notification. La même panne
   silencieuse peut se reproduire.

### Important — dette structurelle
5. **`version: "unknown"` dans `/api/health`** : aucun versionnage applicatif. Impossible de
   savoir quelle version tourne sans inspecter les manifestes de release à la main.
6. **Frontend sous-testé** : 39 tests frontend vs ~2200 backend ; **aucun job frontend en CI**
   (`ci.yml` = backend uniquement). Un `tsc` cassé peut atteindre master sans être détecté.
7. **Hygiène Git** : `node_modules/` racine (5215 fichiers), `e2e/node_modules/` et
   `e2e/test-results/*.zip` (traces Playwright) **trackés dans Git** — ~530 Mo dans
   l'historique. `.gitignore` incomplet.
8. **Module Labo** : route réactivée mais 8/10 items du backlog UI ouverts (pas de delete,
   deadline hardcodée, pas de picker patient, pas d'annuaire labos...). Visible comme
   inachevé par un utilisateur.
9. **Dépendance résiduelle au dépôt de travail** : l'interpréteur Python du runtime réel ET de
   la tâche de backup reste `venv/` du dépôt (`RUNTIME-PYTHON-INDEPENDENCE-1`). Le code est
   immuable, l'interpréteur ne l'est pas encore.
10. **Pas de 2FA, HTTPS non intégré** (reverse proxy non documenté), mot de passe unique par
    compte — acceptable en LAN cabinet fermé, insuffisant si un jour multi-site/remote.

### Mineur mais réel
11. `backend/backups/` (backups manuels) : aucune rétention automatique — a déjà atteint 1,3 Go.
12. `SQLCIPHER-AUTO-BACKUP-FIX-1` : mode solo-cabinet SQLCipher sans backup automatique
    fonctionnel (sans impact pour CE cabinet, PostgreSQL).
13. Smoke UI humain jamais réalisé formellement (tâche #35) — les validations techniques sont
    solides mais aucun humain n'a déroulé le parcours complet depuis le nouveau runtime.

---

## 3. POUR DÉPASSER LA CONCURRENCE (ordre de valeur commerciale)

Le concurrent gagne sur : workflow commercial visuel unifié, stock avec déduction auto,
avances nommées, UX guidée. Digital Crown gagne sur : IA, sécurité, imagerie, ortho, documents.
La bascule se joue sur 5 chantiers :

1. **Activer le Treatment Journey (Phase D)** — déjà construit et validé. C'est LA réponse au
   "pipeline commercial visuel" du concurrent, en mieux (chronologie clinique + administrative
   complète, pas juste facturation). Chemin : smoke humain → GO/NO-GO → activation contrôlée.
2. **Fiabiliser le financier (`UNIFY-ACT-PERSISTENCE-1`)** — le concurrent a un financier
   *fiable* ; DC a un financier *joli mais partiellement faux* (cf. §2.1). Un impayé raté vaut
   plus qu'un module manquant.
3. **Stock : passer du MVP à la déduction automatique** (lien acte → mouvement de stock) —
   c'est la feature démo qui fait mouche chez le concurrent. Le MVP CRUD existe déjà,
   l'infrastructure ProactiveAlert aussi.
4. **Avances patients nommées** (table dédiée + solde visible) — petit chantier, gros effet
   perçu par les praticiens.
5. **Finir le module Labo** (8 items restants) — un module visible à moitié fini coûte plus
   cher en crédibilité qu'un module absent.

Atouts structurels à capitaliser (déjà identifiés le 09/07, toujours valides) :
IA certifiée médicalement (sensibilité/spécificité publiées), Crown Bot étendu
(QUERY_STOCK, QUERY_PAYMENTS_LATE, génération PDF en une phrase, vocal Whisper local),
conformité RGPD/HDS documentée + intégration CNOPS/CNSS (décisif au Maroc).
**Nouvel argument commercial depuis cette session** : « backups automatiques chiffrés
vérifiés par restauration » — les concurrents cloud ne peuvent pas le prouver, DC peut
maintenant le démontrer manifeste à l'appui.

---

## 4. CE QUI DEVRAIT ÊTRE AJOUTÉ (au-delà des roadmaps existantes)

### Opérationnel (nouveau — issu des leçons de cette session)
- **Widget "Santé cabinet" sur le Dashboard** : dernier backup (date + statut lu depuis
  `last_backup_status.json`), espace disque libre, version applicative. Infrastructure
  ProactiveAlert déjà en place — une alerte `BACKUP_FAILED`/`DISK_LOW` est un petit chantier.
- **Copie de backup hors machine automatisée** : cible réseau/disque externe/cloud chiffré
  E2E — le 3-2-1 minimal. Aujourd'hui une seule panne disque est fatale.
- **Versionnage applicatif** : injecter le commit/release dans `/api/health` (le manifeste de
  release contient déjà tout).
- **CI frontend** : job `npm test` + `tsc` dans `ci.yml`.
- **`ENVIRONMENT=cabinet` en production réelle** + test de non-régression sur les invariants.

### Produit (nouvelles idées, non listées dans les roadmaps précédentes)
- **Relances impayés semi-automatiques** : la vue impayés existe ; ajouter « générer la lettre
  de relance PDF » (14 générateurs déjà en place) puis WhatsApp/SMS (infra Twilio présente).
- **Récapitulatif de fin de journée** (auto, 19h) : CA du jour, actes réalisés, impayés créés,
  RDV demain — par notification ou écran. Différenciateur quotidien fort pour le praticien.
- **Mode « fin de traitement »** dans le Journey : générer automatiquement le dossier de
  sortie (récapitulatif soins + documents + solde) — prolonge naturellement la Phase D.
- **Consentements éclairés signés** (SignaturePad mobile déjà présent) — traçabilité
  médico-légale, très vendeur.

---

## 5. ORDRE D'EXÉCUTION RECOMMANDÉ

```
1. Smoke UI humain (tâche #35 — 10 minutes, débloque tout)
2. GO/NO-GO Phase D → activation Treatment Journey (déjà prêt)
3. UNIFY-ACT-PERSISTENCE-1 (fiabilité financière — le CTO l'avait déjà séquencé après Journey)
4. Widget santé cabinet + alerte backup + copie hors machine (1-2 jours, ferme le risque ops restant)
5. ENVIRONMENT=cabinet + versionnage /api/health (½ journée)
6. Stock déduction auto + avances nommées (différenciation commerciale)
7. Module Labo finalisation (8 items)
8. CI frontend + hygiène Git (dette, en tâche de fond)
9. P2 existants : WhatsApp/SMS, multi-site, BI, HDS/CNOPS (dans l'ordre du roadmap 09/07)
```

---

## VERDICT

L'application est **commercialement au niveau du concurrent (8,0 vs 7,0)** et
**structurellement au-dessus** sur l'IA, la sécurité et l'imagerie. Les sessions 10-11/07 ont
transformé le vrai maillon faible — l'exploitation (backups inexistants de fait, runtime
mutable) — en atout démontrable. Les deux dangers restants ne sont pas là où on les cherche :
**un module financier qui sous-déclare les impayés** (§2.1) et **des sauvegardes qui vivent
sur le même disque presque plein que les données** (§2.3). Le Journey activé + le financier
fiabilisé + le widget santé cabinet = une position réellement inattaquable sur ce segment.
