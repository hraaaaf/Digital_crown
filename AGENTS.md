# Digital Crown — Guide Codex

Digital Crown est une application de gestion de cabinet **on-premise / local-first**. Le runtime principal vit sur le poste du cabinet ou son LAN. Firebase sert à l'identité/licence et services associés ; les données métier restent sous l'autorité du backend local.

> **Ordre de lecture obligatoire**
>
> 1. `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md`
> 2. `STATE.md`
> 3. `AGENTS.md`
> 4. `.claude/rules/execution-scoring-verification.md`
> 5. règle de domaine sous `.claude/rules/`
> 6. `SKILL.md` correspondant au scope
> 7. code, tests, sources ou runbooks référencés
>
> L'ancienne version détaillée de ce guide reste disponible dans l'historique Git à `master@f6dd36e`.

## VERROU V1 — AUTORITÉ D'EXÉCUTION ABSOLUE

Jusqu'à ce que `V1_OPERATIONAL` soit explicitement enregistré dans `docs/clinic/DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` :

- ce fichier est **la seule roadmap autorisée** ;
- un chantier, lot, feature, refactor, cleanup, recherche implémentée, merge, release ou déploiement hors du lot V1 actuellement déverrouillé doit être **refusé** ;
- seules les corrections, tests, preuves et mises à jour documentaires strictement nécessaires pour faire passer les gates du lot courant sont autorisées ;
- les PR ouvertes appartenant à des lots ultérieurs restent parkées et ne peuvent ni autoriser du travail ni être mergées hors séquence ;
- aucun autre `ROADMAP`, `PLAN`, `HANDOVER`, `BACKLOG`, `OBJECTIVE` ou document historique ne peut modifier l'ordre, le scope ou déverrouiller un lot ;
- un lot N+1 ne démarre qu'après closeout documenté du lot N avec Goal atteint, Success observable, Proof capturée, CI/tests requis verts et merge/post-merge terminé si applicable ;
- aucune mutation cabinet/production n'est autorisée avant le lot final de mise à jour cabinet et validation humaine explicite ;
- aucun déploiement Vercel n'est autorisé par ce verrou.

En cas de conflit, `DIGITALCROWN_V1_CONSOLIDATED_ROADMAP.md` prévaut.

## Autopilot contrôlé — autonomie bornée par mission

**Portée prospective post-V1.** La roadmap consolidée V1 indique `V1_OPERATIONAL` ; elle conserve son rôle historique. Cette politique ne déverrouille aucune feature/lot V1.5+, n'autorise aucune opération cabinet et ne modifie pas rétroactivement les preuves.

1. **Cadrage unique PRE** : mission/lot/sous-lot/chantier courant, Goal, Success observable et oracle, scope/exclusions, HEAD, niveau de risque, actions autorisées et gates REQUIRED/EXPERIMENTAL/HORS SCOPE. Un GO de mission autorise les actions sûres et réversibles **dans ce scope uniquement**.
2. **Exécution continue** : explorer, coder sur branche isolée, tester, corriger et préparer PR DRAFT sans demander un accord à chaque micro-action ni élargir le périmètre. Arrêter et escalader en cas de risque clinique, d'accès patient, de modification de politique de sécurité ou d'opération irréversible.
3. **Risque A faible** : documentation, contrats et tests non productifs — FUE-0. **Risque B modéré** : UI/API/parcours limités — tests ciblés + FUE-I/G réellement exécutable + négatifs pertinents. **Risque C critique** : auth/RBAC, données patients, migration, sécurité, clinique, cabinet/release — contrôles spécialisés stricts, fail-closed, restore/rollback et approbations humaines lorsqu'ils s'appliquent. L'impact détermine le risque.
4. **Une seule chaîne de preuve** : FUE-0/I/G est le cadre de l'issue observable ; RPG-C/J/X/F/P ajoute les scénarios nécessaires selon le risque, sans campagne redondante. Tests ciblés pendant le développement ; réévaluation des seules preuves invalidées et confirmation sur HEAD final. Aucun rerun global systématique, ni polling CI. Sur lot significatif, une analyse adversariale transversale proportionnée au risque ; pas de double revue mécanique ni fausse indépendance.
5. **Un seul bilan de gate** : EXECUTION_SCORE + FUE_EVIDENCE_SCORE, Perfection Pass et validation finale sur candidat/HEAD de clôture (ou gate critique) plutôt qu'après chaque microcommit ; POST Notion compact, risques et Next ; les réserves sont ajoutées à `techdoubt.md`.
6. **Autorisation distincte toujours nécessaire** pour fusionner, déployer Vercel, installer/releaser cabinet, modifier irréversiblement les données réelles, activer une décision clinique ou changer un gate de sécurité, et pour toute validation clinique/réglementaire/visuelle/physique humaine requise. GO du scope != GO de merge ; ne pas contourner labels, règles et workflows trusted.
7. **UI** : BEFORE/Target/AFTER sur viewports pertinents ; vérifier l'existence de la feature sur mobile avant d'en certifier le rendu ; accord propriétaire sur rendu final si requis. Les lots purement documentaires FUE-0 ne doivent pas inventer d'écrans ou de preuves navigateur.
8. **Verdict** : tout BLOCKER/MAJOR, gate REQUIRED rouge, preuve critique absente ou GO humain manquant impose OPEN/BLOCKED. Un check expérimental n'est bloquant que s'il révèle un risque réel. Aucun score ne remplace la preuve.

**But : moins d'interruptions, garanties patient/sécurité/clinique inchangées.**

## Doctrine générale unique — commune à tous les assistants

**AGENTS.md est la seule source de consignes générales Digital Crown.** `CLAUDE.md` doit renvoyer ici sans recopier de doctrine. Les documents de roadmap, `STATE.md` et Notion apportent des faits, décisions et preuves ; les règles `.claude/rules/`, agents spécialisés et `SKILL.md` ajoutent uniquement des contrats propres à leur domaine. Ne jamais atténuer une exigence clinique, légale, de confidentialité, de sécurité ou de validation humaine applicable.

**Hiérarchie des faits :** repo/runtime/DB et HEAD vérifiés → documentation canonique GitHub → Notion canonique → sources Project → mémoire. Une ancienne instruction générale supprimée ne doit plus servir d'autorité concurrente.

### Discipline d'exécution et de communication

- **Périmètre verrouillé :** avant chaque action, vérifier qu'on reste dans le lot, sous-lot, chantier et mission autorisés. Fixer Goal, résultat observable, preuve et gates ; suspendre toute dérive et demander un GO distinct.
- **Notion : maximum deux notes par mission matérielle** lorsque la connexion le permet : PRE (objectif/état) puis POST (résultat/preuve/blocage/Next), avant le bilan final. Aucune prétention d'écriture lorsque l'outil échoue ; pas de micro-journal.
- **Autonomie :** contexte → agir dans le scope sûr/réversible → tester → corriger → preuve → POST → répondre. Ne pas annoncer du travail asynchrone fictif. Merge, Vercel, release cabinet, mutation irréversible et activation clinique ou changement d'un gate critique exigent une autorisation distincte.
- **GitHub Actions :** donner systématiquement **l'URL exacte de tout run effectivement lancé**. Contrôler HEAD/tests/skips une fois, travailler sur ce qui est indépendant, revérifier à la décision, jamais de polling. Échec REQUIRED = investigation/correction ; run encore en cours sans autre action possible = **BLOQUÉ ASYNCHRONE**, URL du run et Next, jamais PASS inventé.
- **Gates :** distinguer REQUIRED / EXPERIMENTAL / HORS SCOPE. Un gate expérimental n'est pas automatiquement bloquant, sauf risque réel sécurité, données, clinique ou production. Valider seulement ce que le diff ou les dépendances transversales peuvent invalider.
- **Closeout ordonné :** tests/FUE réels adaptés au risque → preuves exact HEAD → Perfection Pass → source canonique pertinente → cohérence roadmap → décision de merge distincte → contrôles post-merge → suite seulement si ses dépendances sont closes. Une CI verte et un merge ne valent ni certification ni GO de déploiement.
- **Mobile :** ne tester que les surfaces effectivement implémentées ; vérifier les routes avant d'imposer mobile. Fonction desktop-only = mobile non applicable motivé, sauf smoke ciblé pour un risque partagé.
- **Poste distant / Remote Desktop Commander : AUCUNE OBLIGATION.** Ne jamais imposer Remote Desktop Commander, la connexion à `DESKTOP-3MAJEEH` ou un autre ordinateur personnel pour lire/modifier le dépôt, produire une PR, exécuter la CI GitHub ou valider un laboratoire synthétique. **GitHub (dépôt, PR, Actions) est suffisant pour les missions exécutables dans GitHub** ; l'absence d'un appareil distant n'est pas un BLOCKER de ces missions. N'utiliser un poste physique ou un outil d'accès distant que si le lot l'exige réellement (gate matériel/cabinet) **et** après autorisation expresse visant cet appareil et ces opérations. Un essai matériel non réalisé demeure `NOT_RUN`/`OPEN`, mais ne bloque pas une preuve logicielle indépendante. Tout handover ancien qui exige cet outil est supplanté par cette règle.
- **Revue :** rechercher BLOCKER/MAJOR, fail-open, régression et fausses preuves par une analyse adversariale transversale proportionnée au risque. Deux reviewers indépendants ne sont pas une condition mécanique de CONVERGED ; toute revue/validation spécialisée explicitement exigée reste distincte.
- **Messages :** résultat → preuve → blocage → Next précis, avec effort recommandé (Instant/simple, Medium/standard, High/critique, Extra High si nécessaire et disponible ; en cas de doute choisir l'effort supérieur). Inscrire les réserves significatives dans `techdoubt.md` dès qu'une écriture sûre est possible. Terminer par le pied Lot · Sous-lot · Chantier · Roadmap défini ci-dessous.

## Pied de message obligatoire — contrat de communication Digital Crown

**À la fin de chaque message adressé à l'utilisateur dans le projet Digital Crown**, y compris une réponse courte, une question, un point de progression, un rapport de CI, une décision ou un blocage, ajouter **une dernière ligne unique**, sans aucun texte après, au format exact :

**Lot :** [lot réellement actif] · **Sous-lot :** [sous-lot réellement actif] · **Chantier :** [mission précise en cours] · **Roadmap :** [état courant vérifié, prochain lot gelé/différé si pertinent]

- **Identifier avant d'écrire** le lot, le sous-lot et le chantier à partir de la mission autorisée et des références courantes : repository/HEAD et canonique GitHub → roadmap/Notion → contexte conversationnel. Ne pas réutiliser mécaniquement le lot du message précédent si la mission a changé.
- La **roadmap** indique de façon brève ce qui est `OUVERT`, `EN COURS`, `GELÉ`, `DIFFÉRÉ` ou `CLOS`, seulement si le statut est prouvé. Ne jamais déverrouiller un lot, déduire un `PASS`, une fusion ou un déploiement de cette ligne. Si un fait manque, écrire explicitement `à confirmer` plutôt que l'inventer.
- Lorsque le travail concerne seulement la gouvernance documentaire, **nommer ce chantier réel** et son sous-lot documentaire, sans le faire passer artificiellement pour une fonctionnalité Crown Bot, clinique ou physique.
- Placer le résultat, la preuve, le blocage et le **Next avec effort conseillé** avant cette signature. **La signature reste le dernier élément visible** ; pas de liste, note, citation ou question après.
- **Exemple de forme uniquement, non à recopier comme état permanent :** Lot : Crown Bot 2.0 · Sous-lot : CB-01 FIRST_VALUE_UI · Chantier : alignement de gouvernance et requalification FUE · Roadmap : CB-01 ouvert, CB-02 gelé, Lot 10 physique différé.

## Contrat transversal des thèmes — tokens obligatoires, aucune palette figée

**Portée : toute l'application Digital Crown**, sur toutes les surfaces effectivement livrées (frontend React/TSX/CSS, MainLayout, Crown Bot, cabinets/patients/agenda/facturation/administration, modales, portails, PWA/mobile et composants réutilisés). Ce contrat vaut pour tout nouvel écran, correction, refactor et code de test qui vérifie des styles. La responsabilité est **celle du composant**, pas une rustine CSS globale par thème.

1. **Source unique** : consommer les tokens CSS sémantiques exposés par `frontend/src/index.css` (`@theme` + définitions `:root` et `[data-theme]`). Utiliser notamment `bg-background`, `bg-card`, `bg-sidebar`, `bg-input-field`, `text-text-main`, `text-text-muted`, `border-border-main`, `border-border-hover`, `bg-primary`, `text-on-primary`, `bg-secondary`, `bg-accent`, et les ensembles `success` / `warning` / `danger` / `info` avec `*-surface` / `*-border`. Les nouvelles couleurs de rôle doivent être définies dans la source canonique pour **tous** les thèmes avant consommation ; ne pas multiplier les valeurs de palette dans les composants.
2. **Interdiction de palette UI figée** : pas de `bg-white`, `text-white` sur un fond de marque, `bg-slate-*`, `text-slate-*`, `border-gray-*`, `bg-indigo-*`, `bg-emerald-*`, `bg-amber-*`, de `#hex`, `rgb()/hsl()` ou `style={{ color/backgroundColor: ... }}` figés pour les surfaces, textes, bordures, badges, hover, focus, ombres colorées et états de l'application. Les valeurs de teinte n'appartiennent qu'aux définitions de tokens du design system. Il en va de même pour les composants internes du bot, les panneaux flottants, les badges et les boutons de confirmation. Les exceptions **non-thématiques** (visuels cliniques, couleurs de marques tierces, graphiques à légende, imprimés réglementaires, masques/overlays translucides, fichiers médias) exigent une justification locale et un test vérifiant qu'elles ne rendent pas une interface inutilisable ; elles ne servent jamais d'échappatoire à un état UI.
3. **Contraste et accessibilité** : le texte sur `bg-primary` est **`text-on-primary`**, jamais `text-white` supposé universel. Vérifier lisibilité/contraste et états `hover`, `focus-visible`, `disabled`, `error`, `success`, sélection et indicateur de chargement. Préserver focus clavier, annonces NVDA/lecteurs d'écran et reflow à zoom 100 % et 200 % ; ne pas cacher un défaut de contraste avec des overrides `!important` ou un patch global `[data-theme]`.
4. **Matrice et preuves proportionnées** : couvrir le thème par défaut et **Emerald, Rose, Ocean, Graphite, Prestige, Dark et High Contrast** ; vérifier le changement de thème à chaud et la persistance lorsqu'ils sont concernés. **Dérogation expresse du propriétaire (25/10/2026) pour une migration strictement cosmétique vers les tokens sémantiques existants** : si le diff ne change ni structure, ni comportement, ni parcours, ni permissions, ni données cliniques, **de nouvelles captures et une approbation visuelle humaine ne sont pas exigées pour le seul remplacement des couleurs**. À la place : analyse du diff, preuve automatisée d'héritage des tokens (sans palette UI figée), contrôle des rôles/contrastes des huit thèmes, tests ciblés d'interaction/accessibilité, TypeScript et build. Ne jamais assimiler un garde « pas de nouvelle dette » à la preuve que tout le composant hérite effectivement des tokens. Si la correction modifie layout, typographie, interactions, lisibilité, logique clinique ou contraste non couvert par les tests, demander des preuves visuelles complémentaires adaptées ; l'exception ne couvre pas ces changements.
5. **Garde CI** : analyser les fichiers UI effectivement modifiés et refuser les nouvelles couleurs codées en dur, sauf exception explicitement consignée et revue. Un inventaire de dette historique doit être distinct d'un PASS : ne jamais annoncer « thème conforme partout » à partir du seul contrôle des lignes nouvelles, d'une compilation ou d'un test visuel unique. Corriger la dette par composants sans recherche/remplacement aveugle qui modifierait les marques, images, visualisations ou sémantique clinique.
6. **Gates et périmètre** : la dérogation de preuve visuelle ci-dessus vaut **uniquement pour les remplacements de couleurs par des tokens existants dont l'héritage et le contraste sont démontrés automatiquement**. Elle ne constitue **ni GO de merge, ni GO de déploiement, ni autorisation d'action clinique** et ne désactive pas d'autre gate de sécurité ou d'approbation applicable à un lot fonctionnel. Sur une branche de certification, tout nouveau SHA exige de réévaluer les preuves techniques exact-HEAD ; les validations visuelles humaines antérieures ne sont pas réutilisées pour des modifications fonctionnelles. Si un workflow CI général impose toujours une approbation humaine, constater distinctement son statut et adapter ce gate uniquement après classification fiable du périmètre ; **ne pas le contourner par un faux label ou un faux PASS**. Garder les PR cliniques en DRAFT et les flags OFF jusqu'aux autorisations distinctes.

## Architecture courante

- Backend : FastAPI + SQLAlchemy.
- Frontend : React 19 + Vite + TypeScript + Zustand.
- Mobile : PWA/Capacitor appairée au cabinet, réseau local, cache/offline.
- Automatisation : modèles locaux et moteurs déterministes.
- LLM : aucune dépendance LLM requise dans l'architecture courante.
- Packaging : PyInstaller + Inno Setup.

### Environnements

- `development` / `local` / `test` : développement/test.
- `cabinet` : production-like local ; `DEBUG` interdit, CORS wildcard interdit, SQLite/SQLCipher autorisé.
- `production` : mêmes exigences, PostgreSQL obligatoire.

Source : `backend/main.py::validate_environment_invariants()`.

## Reality Proof Gate (RPG) — preuve observable obligatoire

Lire `docs/quality/REALITY_PROOF_GATE.md` pour chaque lot/sous-lot V1.5. Choisir le niveau selon le risque (contrat, parcours, multi-acteurs, défaillance/privacy, matériel). Le FUE-0/I/G et les contrôles spécialisés déclenchés par le risque restent requis selon leur scope ; ils ne remplacent pas une simulation réelle de l'issue métier. Exiger SHA exact, tests réellement exécutés, preuves émetteur/récepteur et affichage si applicable, tests négatifs et artefacts inspectables. Une CI verte sans scénario exécuté ou un TestClient partagé présenté comme deux postes ne certifie pas le RPG. Un gate matériel/physique non exécuté reste OPEN. Ne jamais utiliser de données patient réelles en CI.

## Règles absolues

### Scoring d'exécution et vérification

### FUE — protocole principal de validation

La First User Experience (FUE) est le protocole principal de validation observable, proportionné au risque et à la maturité du lot. Aucune double revue adversariale A/B, aucun nombre de reviewers, aucun agent externe n'est requis par défaut pour VERIFIED ou CONVERGED.

FUE-0 : contrat/code/tests sans inventer de parcours utilisateur. FUE-I : parcours intermédiaire réellement utilisable. FUE-G : parcours complet jusqu'au résultat métier lorsque les dépendances sont disponibles. La PR #783 est un laboratoire expérimental, non une certification universelle.

Boucle : Goal et succès observable → scope/HEAD/gates → scénarios/oracles → tests ciblés, négatifs et sécurité applicable → FUE exécutée → preuves BEFORE/ACTION/AFTER, logs, artefacts → BLOCKER/MAJOR → correction → retests impactés → confirmation sur HEAD final. Les personas fictifs sont facultatifs ; ils ne prouvent ni utilisateurs indépendants ni vrai login/backend.

Les analyses sécurité, confidentialité, intégrité, migration, RBAC, clinique ou architecture sont déclenchées par les risques, sans obligation mécanique de deux revues A/B. Une FUE visuelle ne remplace pas un test de sécurité. Les approbations humaines explicitement requises, validations cliniques/réglementaires, essais physiques LOT10 et politique de release restent distincts.

Lire .claude/rules/execution-scoring-verification.md. Produire EXECUTION_SCORE /10 et FUE_EVIDENCE_SCORE /10, retenir le minimum ; l'ancien ADVERSARIAL_SCORE n'est qu'un champ de compatibilité lorsqu'un outil l'exige. Gate requis rouge/manquant : maximum 7.9/10 ; régression : 6.9/10 ; BLOCKER sécurité/privacy/data/clinique : 5.9/10 et BLOCKED ; UI sans comparaison Target ↔ Render : fidélité maximum 7.5/10. VERIFIED exige score retenu >=9.0/10, preuves inspectables, gates requis verts et Perfection Pass. CONVERGED exige en plus zéro BLOCKER/MAJOR et confirmation sur HEAD final. Aucun score ne remplace un gate.

### Données et isolation

- Ne jamais perdre, réinitialiser ou reseeder une vraie donnée utilisateur.
- Jamais de seed/demo sur une DB cabinet.
- Backup avant restore/migration à risque.
- Jamais de restore sur DB principale sans confirmation explicite.
- Toute opération de test qui écrit doit prouver qu'elle cible l'environnement isolé prévu.
- Toujours dériver le cabinet via `current_user.get_employer_id()` ; jamais depuis une valeur client non fiable.
- Toute route patient-scopée doit appliquer le guard d'accès backend approprié.
- Médias sensibles : routes authentifiées et tenant-aware, jamais accès statique public.
- Ne jamais logger secrets, tokens, mots de passe ou master key.

### Installation / release cabinet — INVARIANT ABSOLU

Lire `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` avant toute opération de build, packaging, installation, activation ou mise à jour cabinet.

- **Interdit d'installer ou démarrer `master`, `HEAD`, une branche, un tag ou un working tree.**
- `CODE_CERTIFIED` = code exact-SHA attesté par GitHub/Sigstore. **Ce niveau n'est PAS installable.**
- `INSTALLABLE_CERTIFIED` = `CODE_CERTIFIED` + bundle d'assets runtime certifié pour le même SHA + composition finale revalidée.
- **Seul `INSTALLABLE_CERTIFIED` est autorisé à atteindre un cabinet réel, PyInstaller ou Inno Setup.**
- Le CODE SHA nouvellement certifiable doit être le HEAD courant exact de `master`, 40 caractères.
- Toute release universelle couvre simultanément `BASIC`, `GOLD`, `ELITE` ; jamais trois forks/binaires divergents.
- Les noms release `BASIC/GOLD/ELITE` ne renomment pas implicitement les enums de licence historiques ; toute migration commerciale reste un lot séparé.
- `create_release.ps1` ne doit jamais recopier/reconstruire le working tree. Il doit vérifier hashes + provenance GitHub/Sigstore puis composer avec les assets runtime.
- La sélection des assets de `DigitalCrown.spec` doit rester dérivée de `backend/runtime_asset_certification.py`, jamais dupliquée à la main.
- `run_real_backend.ps1` doit rester fail-closed sur code + provenance + assets **avant** lecture de la config cabinet.
- `run.py` doit vérifier `INSTALLABLE_CERTIFIED` avant le first boot.
- Un merge sur `master` **ne signifie jamais installable**.
- Toute évolution pouvant toucher DB, migrations, patients, documents, médias, startup, seeds, paths, restore/backup, tenant filtering ou installer exige un rehearsal sur copie fraîche des données réelles avant certification destinée à un cabinet existant.
- Il est interdit de supprimer, neutraliser, path-filter ou contourner ces gates pour « débloquer » une release.

### Domaines scientifiques / cliniques

Pour tout scope clinique ou scientifique :

- lire `.claude/rules/scientific-engineering.md` ;
- lire le `SKILL.md` correspondant ;
- respecter strictement son mode read-only ou implementation ;
- ne pas inventer de donnée manquante ;
- ne pas introduire de constante non sourcée ;
- conserver provenance, versions et états explicites ;
- tests verts ne valent pas validation scientifique ;
- validation humaine ou scientifique spécialisée avant merge lorsque le skill applicable l'exige explicitement ; pas de double revue A/B systématique.

## Skills à router explicitement

- Prescription : `.claude/skills/audit-prescription-flow/SKILL.md`
- Diagnostic : `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- Panoramique : `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- Céphalométrie : `.claude/skills/validate-cephalo-pipeline/SKILL.md`

Les skills d'audit sont **read-only**. Un finding se corrige dans un lot séparé.

## Pièges opérationnels

### Runtime réel

- Le dépôt de travail n'est pas le runtime cabinet.
- Ne jamais lancer un process auto-reload contre le runtime réel.
- Utiliser uniquement une release `INSTALLABLE_CERTIFIED` composée via les scripts sous `backend/scripts/`.
- Un build de test ne doit jamais écraser un frontend réellement servi.

### Environnement de test

- Exporter seulement `DATABASE_URL` dans le shell ne garantit pas l'isolation si un fichier d'environnement local est rechargé.
- Pour un test d'écriture isolé, utiliser `DIGITALCROWN_ENV_FILE` vers un fichier dédié puis vérifier explicitement le `DATABASE_URL` réellement résolu.

### Database / migrations

- Ne pas supposer qu'Alembic s'exécute automatiquement.
- Lire le chemin runtime courant avant toute migration.
- Ne jamais ouvrir une DB SQLCipher avec `sqlite3` standard.
- Backup PostgreSQL via `pg_dump`, jamais par heuristique de chemin fichier.

### Backup

- Backup DB seul ne vaut pas forcément backup complet.
- Les backups planifiés utilisent une release immuable dédiée ; ne pas dupliquer la logique dans un script ad hoc.
- Une réussite n'est prouvée qu'après vérification de l'artefact et du restore attendu selon le runbook.

### Packaging

- Conserver les hidden imports runtime nécessaires dans `DigitalCrown.spec`.
- Ne jamais embarquer un `.env` contenant des secrets.
- `console=False` exige une journalisation fichier fiable.
- Le bootstrap first-run doit précéder les imports qui figent les settings, mais **la vérification `INSTALLABLE_CERTIFIED` doit précéder le bootstrap first-run**.

### Modèles

- `backend/ai_models/` contient aussi des dépôts de recherche historiques.
- Ne pas embarquer un dépôt complet si seuls certains artefacts runtime sont nécessaires.
- La certification d'intégrité des assets ne vaut pas validation scientifique.
- Un asset scientifiquement épinglé dans `backend/scientific_assets.json` doit matcher path + taille + SHA-256 ; sinon release refusée.
- Les assets non encore épinglés restent explicitement déclarés comme tels ; ne jamais prétendre qu'ils sont scientifiquement certifiés.

## Documents / PDF

- Réutiliser les helpers typographiques et de layout existants.
- Éviter les règles de présentation ad hoc.
- Une preview doit être read-only sur l'état métier.
- Après modification d'une route ou d'un générateur, faire un smoke réel/rehearsal adapté au risque.

## Tests et CI

### Backend

```bash
python -m pytest backend/tests -q
python scripts/prod_safety_check.py
```

### Frontend

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

### CI actuelle

`.github/workflows/ci.yml` contient backend install + prod safety check + pytest, frontend `npm ci` + tests + build, et garde production négatif.

`.github/workflows/cabinet-upgrade-postgres-cert.yml` est un gate PR global sans filtre de chemin et verrouille PostgreSQL 18 + préservation + politique de release.

Ne déclarer aucun SHA `CODE_CERTIFIED` sans preuve du run + attestation correspondants. Ne déclarer aucune version installable sans certificat final `INSTALLABLE_CERTIFIED` vérifié.

### Validation CI chirurgicale — INVARIANT OPÉRATIONNEL

**RÈGLE ABSOLUE — NE JAMAIS RELANCER TOUTE LA CI PAR DÉFAUT.** Relancer uniquement les tests, builds, jobs et workflows directement touchés par le code modifié. **En particulier, ne jamais relancer tout le frontend lorsqu'une modification n'affecte qu'une sous-partie du frontend ou n'affecte pas le frontend du tout.** Un élargissement de la validation n'est autorisé que si le diff touche une dépendance transverse, un harness partagé, un invariant sécurité/données/release, ou si une preuve concrète montre qu'une surface plus large peut régresser. Les gates déjà verts et non impactés restent acquis.

Pendant une phase de correction ou de stabilisation :

- un micro-correctif doit être validé d'abord par le **test, job ou workflow directement impacté** ;
- si aucun code n'a changé et qu'un rerun suffit, relancer **uniquement le job échoué** ou les seuls jobs échoués ; ne pas relancer volontairement la matrice complète ;
- si un commit déclenche automatiquement d'autres workflows GitHub, **ne pas attendre ni réinterpréter toute la matrice** : suivre uniquement le gate corrigé et ses dépendances directes ;
- un gate déjà prouvé vert reste acquis tant que ni son code, ni son harness, ni une dépendance pertinente n'ont changé ;
- après correction d'un rouge, passer au **prochain rouge réel terminé**, sans recommencer les preuves déjà acquises ;
- au closeout final, **ne pas rejouer aveuglément toute la matrice** : vérifier la cohérence `HEAD ↔ preuves acquises` et ne rejouer que les tests/jobs/gates dont le code, le harness ou une dépendance pertinente a changé ; un changement transverse ou un invariant sécurité/données/release invalide et élargit automatiquement les preuves concernées ;
- une CI encore queued/in_progress n'autorise pas l'attente passive : traiter le travail indépendant disponible ; sinon déclarer le blocage asynchrone exact ;
- ne jamais masquer un changement produit derrière une validation ciblée : si le diff touche une dépendance transverse ou un invariant de sécurité/données/release, élargir les tests proportionnellement au risque.

Objectif : réduire les reruns inutiles sans diminuer le niveau de preuve final.


## Runbooks utiles

- `docs/CABINET_CERTIFIED_RELEASE_POLICY.md`
- `docs/CABINET_ONPREM_GUIDE.md`
- `docs/PREPROD_RUNBOOK.md`
- `docs/PATIENT_DATA_ROLLBACK.md`
- `STATE.md`

## Workflow par lot — Post-V1 Autopilot

1. Vérifier lot V1.5 réellement déverrouillé, `STATE.md`, règles de domaine et skills. La V1 consolidée est historique après `V1_OPERATIONAL`.
2. PRE Notion unique : Goal, preuve, scope/risque, HEAD et gates ; aucune dérive de chantier autorisée.
3. Modifier sur branche isolée ; tests ciblés, corrections et cas négatifs autonomes, sans micro-approbations.
4. Choisir FUE-0/I/G et scénarios RPG proportionnés, exécuter toutes protections spécialisées pertinentes.
5. Sur HEAD final, vérifier preuves réellement impactées, CI une fois à la décision ; revue adversariale transversale proportionnée au risque si significatif.
6. Noter les deux scores et faire une Perfection Pass consolidée au verdict ; aucune fausse validation par une CI simplement verte.
7. POST Notion compact ; réserve dans `techdoubt.md` ; PR DRAFT, liens des runs, Next. Solliciter GO distinct avant merge/déploiement/release ou mutation sensible.
8. Toute installation reste soumise à `docs/CABINET_CERTIFIED_RELEASE_POLICY.md` et aux gates exact-artifact.

**Révision prospective 20 octobre 2026 ; V1 historique intacte.**

## V1.5 — FUE rétroactif par sous-lot (PR #783 = laboratoire)

- Pour chaque sous-lot V1.5 déjà CLOSED, réconcilier les preuves existantes avec le plan Notion « V1.5 — Plan FUE canonique par lot / sous-lot » **avant d'ouvrir V1.5-04**.
- La PR [#783](https://github.com/hraaaaf/Digital_crown/pull/783) est le **laboratoire FUE réutilisable**, pas un lot produit ni un certificat universel. Lire son prompt `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md` et adapter persona, première valeur, contexte, viewports, scénarios, métriques, seuils et risques au lot/sous-lot concerné. Les catégories FUE-A…G du laboratoire sont un référentiel de contexte, distinct de cette campagne V1.5.
- Appliquer la classification propre au plan V1.5 : **FUE-0** = contrat/code/tests seulement, sans inventer de parcours utilisateur ; **FUE-I** = parcours intermédiaire utilisable ; **FUE-G** = gate complet une fois le workflow de bout en bout disponible.
- Matrice par sous-lot : CLOSED réel + niveau exigible + preuves exact-HEAD préexistantes + statut **PROUVÉ / PARTIEL / À FAIRE**. Réutiliser les preuves pertinentes ; ne pas convertir un CI vert en FUE prouvé.
- Si FUE-I/G exigible : **Exécuter la FUE avec des preuves observables ; les personas simulés sont facultatifs et ne valent pas utilisateurs indépendants.** Le parcours de l'application exige en plus un vrai login UI (ou entrée publique pertinente), session/persona de test vierge, frontend/backend isolés et réellement exécutés, captures BEFORE/AFTER pertinentes, premier résultat utile, échecs/récupération, mesures, P0/P1/P2, score sévère, puis correction/test et confirmation même HEAD. Ne pas inventer une preuve navigateur non acquise. Les corrections produit restent dans des PR produit distinctes de #783.
- Commencer dans l'ordre V1.5-00.1 → 03.6, puis décider l'ouverture de 04. Aucun merge/déploiement Vercel implicite.

### Définition opérationnelle FUE — parcours de nouvel utilisateur dans le produit réel, couverture complète, preuve avant verdict

**FUE = First User Experience : parcours de première utilisation observable, depuis le login UI jusqu'au résultat dans un produit et backend de test réellement exécutés (ou depuis une entrée publique appropriée).** ChatGPT peut jouer **dans cette même conversation** deux personas « blind users » spécialisés A/B pour critiquer le parcours de manière complémentaire ; ceci constitue deux **perspectives internes**, pas deux acteurs techniques indépendants ni deux humains. Les étapes navigateur, captures et persistance ne sont certifiées qu'avec preuves réellement produites. Le LOT10 physique avec personnes/appareils réels et toute approbation clinique humaine explicitement requise demeurent séparés.

- Définir d'abord le contrat concret du sous-lot (écrans, liens, boutons, états, permissions, cas limites, risques, intégrations, chemins heureux et négatifs, reprise), la persona, l'état initial et le First Value attendu. Adapter le scénario au sous-lot; distinguer strictement FUE-0, FUE-I et FUE-G, et consigner N/A avec justification. Ne pas exiger un parcours inexistant dans FUE-0.
- **Parcourir la totalité des éléments applicables**, comme un nouvel utilisateur, en explorant les sorties possibles et pas seulement un chemin heureux. Observer clarté des libellés, compréhension, cohérence, guidage, charge cognitive, feedback, visibilité des permissions, navigation, accessibilité, robustesse et sécurité; ne pas confondre les assertions techniques avec l'expérience.
- Capturer chaque étape importante (BEFORE/action/AFTER, écran complet pertinent, screenshot d'échec, état de départ, destination, erreur, temps et viewport). Joindre à l'artefact Actions la matrice nominative de couverture: PASS, FAIL ou NON TESTÉ, preuve exacte et HEAD. Une preuve manquante sur un invariant critique empêche une revendication de certification exhaustive.
- Un **rouge** est un défaut démontré et matériel : parcours impossible, situation incompréhensible, incohérence significative, information trompeuse, barrière de sécurité défaillante, impasse de navigation, violation d'un contrat critique, ou gate requis réellement échoué. Une longueur d'onboarding justifiée, une préférence esthétique ou un détail cosmétique ne rendent pas le lot rouge à eux seuls. Classer sévérité P0/P1/P2 et expliquer l'impact.
- Distinguer rouge **produit**, rouge **harness/environnement** et **preuve insuffisante**; investiguer avant correction. Les problèmes mineurs/non bloquants sont consignés sans immobiliser toute la progression. Ne jamais transformer un timeout en diagnostic produit sans preuve, ni un CI vert en FUE concluant.
- Les contrôles doivent être **fail-closed sur la preuve** : pas de verdict PASS si l'assertion valide seulement « pas arrivé sur une mauvaise URL » sans état positif observé; pas de suite silencieuse sur exceptions. Continuer les scénarios indépendants pour recueillir le maximum de preuves, puis produire le verdict agrégé et toutes les captures, même si un parcours échoue.
- Après corrections, exécuter les validations impactées et la confirmation FUE sur le même HEAD ; ajouter les contrôles de sécurité/contrat adaptés au risque. La clôture exige zéro BLOCKER/MAJOR, score retenu conforme au protocole, couverture et preuves explicites. Le workflow se bloque sur **du rouge réel** ou une preuve critique impossible à obtenir, pas sur une suggestion mineure.

### Gates par sous-lot puis intégration de fin de lot 1

- **Gate sous-lot maintenant** : valider uniquement le périmètre applicable et déjà réalisable du sous-lot, avec captures, matrice, tests UX/techniques et absence de rouge significatif sur ce scope. Publier explicitement les exclusions qui dépendent d'autres sous-lots; elles ne sont pas des échecs de ce gate à moins qu'un invariant déjà exigible soit violé.
- **Gate transversal différé à la fin du lot V1.5-01 (« lot 1 »)** : tester le parcours inter-sous-lots complet avec véritable authentification backend, poste enrôlé/Station appairée, vérification serveur du PIN, reprise et navigation autorisée. Cette campagne n'autorise pas à dire que ces propriétés ont été testées plus tôt.
- Tenir deux statuts indépendants : `SOUS-LOT VALIDÉ (scope)` et `GATE INTÉGRÉ EN ATTENTE`. N'affirmer `FUE-G / fin de lot CONVERGED` qu'après exécution et preuves du gate transversal, jamais par héritage des sous-lots verts.
