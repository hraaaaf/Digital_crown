# Digital Crown — SANINOVA Edition

## Plateforme de gestion dentaire & orthodontique — local-first

Digital Crown est une application de gestion de cabinet dentaire et orthodontique conçue pour fonctionner **sur le poste du cabinet ou sur son LAN**, et non comme un SaaS hébergeant les données patients à distance.

- **Backend** : FastAPI + SQLAlchemy
- **Frontend** : React 19 + Vite + TypeScript + Zustand
- **Mode cabinet solo** : SQLite/SQLCipher local autorisé
- **Mode production serveur** : PostgreSQL requis
- **Mobile** : compagnon PWA/Capacitor appairé au cabinet
- **Imagerie** : modèles locaux ONNX / moteurs déterministes
- **LLM** : aucune dépendance LLM requise dans l'architecture clinique courante
- **Firebase** : identité/licence et services associés, jamais source de vérité des dossiers patients

> La source de vérité opérationnelle et les risques ouverts vivent dans `STATE.md`.
> `AGENTS.md` et `CLAUDE.md` décrivent les règles de développement à respecter avant toute modification.

---

## Architecture d'exécution

### Environnements

- `development` / `local` / `test` : environnements de développement et de test.
- `cabinet` : environnement production-like pour installation locale ; `DEBUG` et CORS wildcard sont interdits, SQLite/SQLCipher reste autorisé.
- `production` : mêmes exigences de durcissement, avec PostgreSQL obligatoire.

Les invariants de démarrage sont appliqués par `backend/main.py::validate_environment_invariants()`.

### Données patients

- Backend = autorité métier.
- Frontend = client non fiable.
- Isolation cabinet par `employer_id`.
- Toute route patient doit faire respecter l'accès via les guards backend appropriés, notamment `assert_patient_access(...)` lorsque le flux est patient-scopé.
- Les médias patients sont servis via des routes authentifiées, pas via un répertoire statique public.
- Les données cliniques ne doivent pas être envoyées dans un service LLM externe.

---

## Modules principaux

### Agenda & patients

- Agenda multi-praticien et statuts de rendez-vous
- Dossier patient longitudinal
- Patient Journey
- Actes, paiements et échéanciers
- Documents et archives
- Scoring et signaux administratifs

### Céphalométrie

- Import / landmarks / correction manuelle
- Calculs géométriques locaux
- SNA, SNB, ANB, IMPA, I-Francfort, Tweed/FMA, Wits et mesures associées
- Registre normatif versionné : définitions, profils, règles de classification et bornes de plausibilité
- Refus des classifications normatives ambiguës, quarantined ou non autoritatives

**État scientifique important :** une partie du registre historique reste explicitement marquée `LEGACY_UNVALIDATED`. L'existence d'une valeur historique dans le registre ne constitue donc pas une validation scientifique.

### Panoramique

- Studio panoramique local
- Détection/localisation assistée
- Annotation et validation praticien
- Rapport déterministe et archivage
- Protection d'accès aux médias patients

Le chemin clinique courant doit conserver la séparation suivante : **assistance machine ≠ diagnostic autonome**.

### Documents

- Ordonnances
- Certificats
- Devis
- Notes d'honoraires
- Documents libres / lettres
- Échéanciers
- Rapports céphalométriques et panoramiques
- Archivage, versioning et génération PDF

#### Document Studio — état de chantier

Roadmap canonique : `DOCUMENT_STUDIO_ROADMAP.md`.

Au 16 août 2026 :
- **P3 Devis** : chantier **clos/pausé jusqu'à nouvel ordre** après durcissement P3-A→P3-G et recertification locale Linux P3-H ; full-app/authenticated/browser gates différés et non revendiqués ; PR #77 conservée open + draft ;
- preuves locales P3 principales : backend **26/26 PASS**, frontend policies **`tsc --strict` PASS**, tests frontend P3 **39/39 PASS**, PDF multipage ciblé **PASS** ;
- **P4 Note Honoraires** : **page active suivante**.

Le statut détaillé P3 est conservé dans `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md`.

### Comptabilité

- Actes
- Paiements
- Échéanciers
- Impayés
- Forecasts et analytics
- Export et reporting

### Proactivité

- Alertes quotidiennes
- Snooze / lecture / expiration
- Risque de no-show
- Traitement non commencé
- Suivi post-soin
- Gaps orthodontiques
- Signaux de pression agenda / matériaux

Les automatismes administratifs peuvent proposer une action. Les automatismes cliniques doivent rester des **signaux à vérifier par le praticien**, pas devenir une décision thérapeutique autonome.

### Mobile

- Appairage LAN
- ECDH P-256 / HKDF / AES-GCM pour l'échange de secrets
- Dashboard mobile
- Agenda, finance, labo et sécurité
- Cache/offline queue
- Révocation des accès mobiles

Le stockage local des credentials mobiles doit être traité comme une surface de sécurité séparée du chiffrement réseau.

---

## Paramètres cabinet

Le centre de paramètres couvre actuellement :

1. Profil cabinet
2. Branding / design
3. Catalogue des actes
4. Horaires & agenda
5. Intelligence & performance
6. Sécurité & backup
7. Équipe

---

## Sécurité

Mesures présentes dans le code :

- JWT et contrôle d'accès backend
- RBAC
- isolation tenant
- audit logs
- CORS borné
- headers de sécurité
- protection anti-path-traversal des médias
- health checks
- garde de configuration production
- tokens d'appairage mobiles temporaires
- rotation/révocation d'accès mobile

### Doctrine

- Ne jamais exposer un média patient anonymement.
- Ne jamais accepter un `employer_id` client comme autorité d'isolation.
- Ne jamais inventer une donnée patient manquante.
- Ne jamais transformer une approximation en écriture financière réelle.
- Une base locale attendue chiffrée ne doit pas être considérée sûre uniquement parce qu'une tentative de chiffrement a été effectuée.
- Un test vert ne constitue pas à lui seul une validation scientifique ou clinique.

---

## Gouvernance scientifique

Les changements touchant prescription, diagnostic, céphalométrie, panoramique, radiologie ou logique clinique sont régis par :

- `.claude/rules/scientific-engineering.md`
- `.claude/skills/audit-prescription-flow/SKILL.md`
- `.claude/skills/audit-clinical-diagnosis-flow/SKILL.md`
- `.claude/skills/audit-panoramic-report-pipeline/SKILL.md`
- `.claude/skills/validate-cephalo-pipeline/SKILL.md`
- les skills d'implémentation/review scientifiques correspondant au domaine

Les audits sont **read-only**. Un finding d'audit doit être corrigé dans une mission distincte, testée puis revue indépendamment.

---

## Tests & CI

Workflow : `.github/workflows/ci.yml`.

Le pipeline versionné comprend actuellement :

- backend : installation, `prod_safety_check.py`, `pytest backend/tests`
- frontend : `npm ci`, tests, build
- garde production négatif : une configuration faible doit être refusée

Commandes usuelles :

```bash
# Backend
python -m pytest backend/tests -q
python scripts/prod_safety_check.py

# Frontend
npm --prefix frontend test
npm --prefix frontend run build
```

Pour un changement sur un chemin API ou un générateur PDF, une validation live/rehearsal adaptée au risque est requise en plus des tests unitaires.

---

## Packaging cabinet

Le packaging Windows s'appuie sur :

- `DigitalCrown.spec` / PyInstaller
- `installer/DigitalCrown.iss` / Inno Setup
- les scripts de runtime et release immuable sous `backend/scripts/`

Voir `docs/CABINET_ONPREM_GUIDE.md` et les runbooks associés avant toute opération sur une installation réelle.

---

## Contraintes non négociables

- Jamais de perte de données patients.
- Jamais de seed/demo sur une base cabinet réelle.
- Jamais de secret, token, mot de passe ou master key dans les logs.
- Jamais de test d'écriture supposé isolé sans vérifier explicitement le fichier d'environnement et la DB réellement ciblée.
- Jamais de diagnostic automatique confirmé sans état clinique explicite et validation praticien.
- Jamais de constante clinique non sourcée introduite silencieusement.

---

## État courant

Ce README décrit l'architecture et les invariants, pas le statut de certification d'une release.

Pour reprendre le projet ou décider du prochain lot, lire dans cet ordre :

1. `STATE.md`
2. `DOCUMENT_STUDIO_ROADMAP.md` si le chantier concerne le Studio documentaire
3. `AGENTS.md` ou `CLAUDE.md` selon l'agent utilisé
4. la règle/`SKILL.md` correspondant au domaine modifié
5. les fichiers scientifiques ou runbooks référencés par ce skill

**Dernière révision canonique : 16 août 2026.**
