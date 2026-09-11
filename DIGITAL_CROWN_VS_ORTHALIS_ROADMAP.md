# DIGITAL CROWN VS ORTHALIS — ROADMAP CANONIQUE

**Statut : CANONIQUE — stratégie produit compétitive**  
**Création : 2026-09-11**  
**Repo : `hraaaaf/Digital_crown`**  
**Baseline vérifiée lors de la dernière revue : `master@9cbcf59bf85e124c4c2150c53e8d86029c923f07`**

> Ce fichier gouverne la stratégie « atteindre puis dépasser Orthalis ».
> Il ne remplace pas les roadmaps techniques spécialisées. Lorsqu'un lot touche un domaine possédant déjà un fichier canonique, ce fichier fixe **la priorité produit et le résultat attendu** ; le fichier spécialisé reste l'autorité d'implémentation et de certification.

---

## 0. RÈGLE DE LECTURE

Ce document distingue strictement quatre états :

- **VÉRIFIÉ** : preuve directe dans le repo, CI, runtime, documentation officielle ou source primaire.
- **NON PROUVÉ** : aucune preuve suffisante dans les sources inspectées ; ne signifie pas nécessairement « absent ».
- **CIBLE** : résultat futur souhaité ; ne doit jamais être présenté comme déjà disponible.
- **HYPOTHÈSE** : proposition stratégique à valider avant engagement lourd.

Aucun score, benchmark ou statut concurrentiel ne constitue une certification clinique, réglementaire, sécurité ou performance.

---

# 1. GOAL GLOBAL

## Goal

Faire de **Digital Crown** une plateforme de gestion dentaire et orthodontique capable de battre Orthalis **sur l'expérience clinique intégrée, la rigueur des données, l'adaptation au Maroc et le modèle local-first**, sans reproduire inutilement les couches historiques ou franco-spécifiques d'Orthalis.

## Succès observable

Le Goal n'est atteint que lorsque Digital Crown dispose, avec preuves exécutables et pilotes terrain, des capacités suivantes :

1. PMS cabinet robuste : patient, agenda, documents, finance, équipe, sécurité.
2. Workflow orthodontique longitudinal complet.
3. Imagerie patient unifiée avec timeline, protocoles photo et comparaisons temporelles.
4. Céphalométrie scientifiquement gouvernée, avec analyses validées et superpositions longitudinales.
5. Compagnon patient sécurisé : documents, questionnaires, rendez-vous, paiements et uploads contrôlés.
6. Framework d'intégrations auditable + connecteurs prioritaires réellement opérationnels.
7. Packaging, backup/restore, mise à jour/rollback, migration et support exploitables en cabinet réel.
8. Validation sur **au moins 3 cabinets pilotes distincts**, sans perte de données critique et avec scénario de restauration démontré.
9. Aucun lot clinique ne revendique une fonction autoritative sans preuve scientifique adaptée.
10. Aucun avantage concurrentiel déclaré sans benchmark reproductible ou preuve terrain.

## Preuve finale exigée

- code + tests + CI exacte du HEAD candidat ;
- runtime réel sur installation cabinet ;
- captures et validation responsive pour les surfaces UI ;
- tests d'isolation/permissions/sécurité proportionnels au risque ;
- restore drill complet ;
- dossier de preuve pilote ;
- re-benchmark Orthalis avec sources primaires datées ;
- mise à jour de ce fichier avec statut réellement démontré.

---

# 2. POSITIONNEMENT STRATÉGIQUE

## Digital Crown ne doit PAS devenir un clone d'Orthalis

La cible n'est pas : « recopier toutes les cases d'un logiciel historique français ».

La cible est :

**Orthalis breadth + Kitview workflow + Digital Crown safety/local-first + Maroc-first + UX moderne.**

### Avantages structurels à préserver

**VÉRIFIÉ dans Digital Crown :**

- architecture local-first / on-premise ;
- backend FastAPI + SQLAlchemy ;
- frontend React 19 / Vite / TypeScript / Zustand ;
- SQLite/SQLCipher autorisé pour cabinet solo ;
- PostgreSQL pour production serveur ;
- compagnon mobile appairé ;
- modèles d'imagerie locaux / moteurs déterministes ;
- absence de dépendance LLM requise dans le chemin clinique courant ;
- RBAC, isolation tenant, audit logs, protection média authentifiée ;
- doctrine « donnée absente = inconnue/non calculable » ;
- séparation assistance machine / validation praticien ;
- céphalométrie typée et provenance de calibration intégrées.

Sources internes primaires : `README.md`, PR #406, `master@9cbcf59...`.

### Non-objectifs stratégiques

Ne pas prioriser :

- Carte Vitale / FSE / DEP / CCAM comme axe produit principal ;
- réplication des écrans historiques Orthalis pour « faire pareil » ;
- migration vers un SaaS patient-data-hosted uniquement pour imiter Orthalis Cloud ;
- catalogue de 25 méthodes céphalométriques non validées pour un chiffre marketing ;
- diagnostic ou plan thérapeutique autonome ;
- réintroduction d'un LLM dans le runtime clinique ;
- déploiement Vercel sans autorisation explicite.

---

# 3. BASELINE CONCURRENTIELLE VÉRIFIÉE — ORTHALIS / ORQUAL

Sources officielles consultées le **2026-09-11** :

- Orthalis : https://www.orthalis.com/orthalis/
- Ceph : https://www.orthalis.com/ceph/
- Kitview : https://www.orthalis.com/kitview/
- Options / Dentapoche / Borne / Orqual Sign / Save : https://www.orthalis.com/options/
- Passerelles : https://www.orthalis.com/les-passerelles/
- Orthalis Cloud : https://www.orthalis.com/orthalis-connect-2/
- Dentalis : https://www.orthalis.com/dentalis/

## Capacités Orthalis officiellement annoncées

### PMS orthodontique

**VÉRIFIÉ via source officielle :**

- planning / rendez-vous / correspondance ;
- facturation / relance / encaissement ;
- fiche patient / questionnaires médicaux ;
- statuts automatiques ;
- stocks ;
- profils utilisateurs et droits ;
- devis / factures / actes / plans ;
- automatisations cabinet.

### Ceph

**VÉRIFIÉ via source officielle :**

- plus de 25 méthodes annoncées ;
- exemples explicitement listés : Delaire, Ricketts, Steiner, Tweed, TTD-Plance, Genève, Root, Sassouni ;
- tracés automatiques annoncés ;
- superposition tracés / radios / photos ;
- modification manuelle possible.

> La documentation marketing officielle établit la présence revendiquée de ces fonctions. Elle ne constitue pas une validation indépendante de précision scientifique, sensibilité, reproductibilité ou sécurité clinique.

### Kitview

**VÉRIFIÉ via source officielle :**

- bibliothèque numérique clinique ;
- photos, vidéos, sons, PDF et documents ;
- acquisition smartphone ;
- reconnaissance automatique des types de photos ;
- recadrage / anonymisation ;
- comparateur ;
- cas similaires ;
- scénarios de présentation ;
- interfaçage imagerie dentaire.

### Patient / cabinet connecté

**VÉRIFIÉ via source officielle :**

Dentapoche annonce :

- alertes ;
- rappels et prise de rendez-vous ;
- signature électronique ;
- questionnaires médicaux ;
- paiement en ligne ;
- documents ;
- photos d'urgence ;
- visioconférence.

Autres briques annoncées : borne d'accueil, Orqual Sign, Orqual Save, SMS.

### Passerelles

**VÉRIFIÉ via source officielle :**

- DentalMonitoring ;
- Spark ;
- Doctolib ;
- 3Shape ;
- Invisalign ;
- OnyxCeph.

### Cloud

**VÉRIFIÉ via source officielle :**

Orthalis Cloud 2025 / Orthalis Connect annonce un accès depuis différents appareils et lieux.

---

# 4. SCORECARD STRATÉGIQUE DE DÉPART

## Méthode

Score sur 100, pondéré par valeur clinique/opérationnelle. Ce score sert uniquement à prioriser la roadmap.

Formule : `Σ(poids_domaine × note_domaine/10)`.

| Domaine | Poids | Digital Crown | Orthalis | Confiance |
|---|---:|---:|---:|---|
| PMS patient + agenda | 12 | 9.0/10 | 9.5/10 | moyenne-haute |
| Workflow orthodontique | 15 | 7.0/10 | 9.5/10 | moyenne |
| Céphalométrie | 15 | 7.5/10 | 9.5/10 | moyenne |
| Imagerie / media patient | 12 | 6.0/10 | 9.5/10 | moyenne |
| Documents + finance | 8 | 8.5/10 | 9.0/10 | moyenne-haute |
| Patient-facing | 10 | 7.0/10 | 9.0/10 | moyenne |
| Intégrations externes | 10 | 3.0/10 | 10.0/10 | moyenne-haute |
| Architecture / sécurité / provenance | 8 | 9.0/10 | 7.5/10 | faible côté Orthalis |
| Maroc-first | 5 | 9.5/10 | 4.0/10 | moyenne |
| Industrialisation / support terrain | 5 | 3.0/10 | 10.0/10 | moyenne |

**Calcul vérifié : Digital Crown = 70,0/100 ; Orthalis = 90,5/100.**

### Interdiction d'interprétation abusive

- Le 70,0/100 n'est pas un audit qualité global de Digital Crown.
- Le 90,5/100 n'est pas une validation indépendante d'Orthalis.
- Les notes doivent être recalculées après chaque grand jalon avec preuves actualisées.
- Une fonction non testée de manière comparable ne peut pas faire gagner artificiellement un point.

---

# 5. GAP REGISTER CANONIQUE

## G0 — Industrialisation terrain

**Priorité : CRITIQUE**

Digital Crown possède packaging, installer et règles de sécurité, mais ne dispose pas encore d'une preuve équivalente à un produit installé/supporté massivement en cabinets.

**Cible :** installation, migration, mise à jour, rollback, backup/restore, support bundle et procédure de reprise démontrés sur matériel cabinet réel.

**Preuve de fermeture :**

- installation propre Windows ;
- migration depuis release N-1 ;
- upgrade N → N+1 ;
- rollback contrôlé ;
- backup chiffré ;
- restauration sur machine distincte ;
- aucun secret/PHI dans support bundle ;
- pilote réel documenté.

---

## G1 — Media Hub / « Kitview-class »

**Priorité : CRITIQUE — plus gros gap fonctionnel produit**

Digital Crown possède des fonctions d'imagerie clinique ciblées, mais aucune preuve actuelle n'établit une bibliothèque patient unifiée de niveau Kitview couvrant l'ensemble du workflow média.

**Cible :** Media Hub transverse, pas simple galerie.

Minimum produit :

- ingestion photos / radios / scans / PDF / vidéos ;
- métadonnées et provenance ;
- patient + cas + date + protocole ;
- timeline T0/T1/T2/... ;
- thumbnails dérivés, jamais source clinique unique ;
- recherche et filtres ;
- comparaison côte à côte ;
- mode séance / présentation ;
- capture smartphone contrôlée ;
- déduplication par hash ;
- permissions et audit ;
- aucune URL média anonyme.

**Gate de fermeture :** scénario synthétique reproductible avec plusieurs patients et centaines de médias, isolation cross-tenant testée, comparaison temporelle fonctionnelle, responsive 390/768/1280.

---

## G2 — Ortho Journey longitudinal

**Priorité : CRITIQUE**

Le Patient Journey existe, mais Digital Crown doit prouver un parcours spécifiquement orthodontique où les étapes cliniques, appareils et contrôles sont structurés et longitudinalement exploitables.

**Cible minimum :**

`consultation → diagnostic structuré → objectifs → choix appareil/aligneur → pose/remise → contrôles → incidents → progression → dépose → contention → suivi`

Le système peut assister l'organisation et exposer des signaux. Il ne choisit jamais automatiquement le traitement.

**Preuve :** scénario E2E d'un cas orthodontique synthétique complet, modifications auditables, reprise après interruption, données longitudinales stables.

---

## G3 — Céphalométrie compétitive R2+

**Priorité : HAUTE**

R1 calibration assistée/provenance a été mergé via PR #406 ; closeout canonique ajouté sur `master@9cbcf59...`.

**Cible compétitive :** ne pas viser « 25 méthodes » avant validation. Viser **5 à 8 analyses majeures réellement gouvernées et certifiées**.

Priorité suggérée :

1. Steiner ;
2. Tweed ;
3. Ricketts ;
4. Delaire ;
5. Wits / analyses associées déjà présentes ;
6. méthodes supplémentaires uniquement avec sources primaires et validation.

Capacités requises :

- registre de méthodes versionné ;
- définitions exactes landmarks/constructions/mesures ;
- valeurs normatives sourcées et contextualisées ;
- superposition T0/T1/T2 ;
- recalage explicite avec méthode/provenance ;
- comparaison radio / tracé / photo ;
- export/reporting ;
- impossibilité d'utiliser silencieusement une norme `LEGACY_UNVALIDATED` comme vérité clinique.

**Preuve :** jeux de référence documentés, validation géométrique, sources scientifiques, tests de non-régression et revue praticien.

---

## G4 — Patient Companion

**Priorité : HAUTE**

**Cible :** équivalent fonctionnel moderne de Dentapoche, adapté au modèle local-first.

Lot minimum :

- prochains rendez-vous ;
- confirmations/rappels ;
- documents attribués ;
- questionnaires médicaux ;
- consentements/signatures ;
- échéancier / historique financier autorisé ;
- paiement si provider validé ;
- photo d'urgence contrôlée ;
- notifications ;
- révocation immédiate.

### Gates sécurité

- identité patient séparée de l'identité cabinet ;
- token court / révocable ;
- aucun accès à un autre patient ;
- aucune exposition du LAN par défaut ;
- upload MIME + magic bytes + taille + sandboxing adaptée ;
- audit complet ;
- politique offline minimale.

### Gate juridique

La valeur légale des signatures, consentements, conservation et paiement au Maroc doit être validée juridiquement avant revendication de conformité. Ne jamais copier une affirmation française HADS/eIDAS et l'appliquer par analogie au Maroc.

---

## G5 — Connect Hub

**Priorité : HAUTE**

Les intégrations Orthalis sont un moat majeur. Digital Crown doit construire **d'abord le framework**, puis les connecteurs.

### Architecture cible

- `ConnectorAdapter` versionné ;
- secrets chiffrés localement ;
- OAuth/API tokens jamais dans logs ;
- journal de synchronisation ;
- idempotence ;
- retry borné ;
- mapping patient explicite ;
- conflit visible ;
- dry-run quand possible ;
- désactivation/révocation ;
- métriques sans PHI.

### Priorités connecteurs

**P1 :** 3Shape, sous réserve d'accès API/partenariat réel.  
**P1 Maroc :** WhatsApp Business/Meta pour communication administrative, sous réserve d'un design consentement/confidentialité propre.  
**P2 :** Invisalign / Spark selon accès partenaires.  
**P2 :** DentalMonitoring si API/accord disponible.  
**P3 :** autres passerelles selon adoption réelle des pilotes.

**Interdiction :** aucun connecteur fictif ou écran « connecté » sans échange réel vérifié.

---

## G6 — Imagerie intelligente locale

**Priorité : MOYENNE-HAUTE**

Après le Media Hub, ajouter uniquement les automatismes apportant un gain réel :

- classification protocole photo ;
- recadrage standardisé ;
- rotation / orientation ;
- anonymisation pour présentation ;
- contrôle qualité image ;
- association suggérée au bon protocole.

**Règle :** assistance ≠ vérité clinique. Toute classification incertaine reste modifiable et conserve sa provenance.

---

## G7 — Cabinet operations / stock / communication

**Priorité : MOYENNE**

Orthalis revendique stocks, SMS, relances, borne et automatisations cabinet. Digital Crown ne doit fermer ce gap qu'après G1-G5 sauf besoin pilote démontré.

Cibles possibles :

- stock réellement relié aux actes/consommations ;
- communications administratives ;
- relance impayé ;
- check-in patient par QR ;
- borne uniquement si ROI cabinet prouvé.

Reconnaissance faciale de borne : **non prioritaire** en l'absence d'un besoin fort et d'un dossier biométrique/juridique adapté.

---

# 6. ROADMAP D'EXÉCUTION

## LOT A — Fermer les chantiers actifs avant nouvelle verticale majeure

### A1 — P6 Document Libre

À la dernière vérification :

- PR #405 ouverte ;
- draft ;
- HEAD observé `218e7ef1580e69958f02d9e8319750772f273376` ;
- objectif : certification runtime/visuelle sans changement produit.

**Gate A :** fermer proprement #405 ou documenter un blocage réel avant d'ouvrir un chantier concurrentiel UI massif partageant la même surface/CI.

### A2 — Céphalo R1

**FERMÉ / MERGÉ** : PR #406, merge `ac858696a734cf04fcf2797ebd0bf53b0caaac25`.  
**CLOSEOUT master** : `9cbcf59bf85e124c4c2150c53e8d86029c923f07`.

Ne pas rouvrir R1 pour ajouter des fonctions concurrentielles. Les évolutions suivantes passent par un lot R2 distinct.

---

## LOT B — Competitive Evidence Harness

**Goal :** disposer d'une baseline produit reproductible avant implémentation lourde.

Livrables :

- inventaire fonctionnel exact Digital Crown par route/module ;
- matrice Orthalis avec source, date, type de preuve ;
- screenshots/vidéos uniquement si accessibles légalement ;
- dataset synthétique de benchmark ;
- scénarios utilisateurs communs ;
- temps/erreurs/clics observables pour les workflows clés.

**Succès :** plus aucun « on pense que X existe » dans le benchmark principal.

**Preuve :** `docs/competitive/` avec sources datées + scénario reproductible.

---

## LOT C — MEDIA CORE

**Goal :** construire le socle média transverse sur lequel céphalo, panoramique, photo ortho et patient reposent.

Ordre :

1. modèle `ClinicalAsset` / équivalent ;
2. stockage + hash + metadata + tenant guard ;
3. import sécurisé ;
4. thumbnails/derivatives ;
5. timeline patient ;
6. viewer ;
7. comparaison ;
8. recherche/filtres ;
9. capture mobile ;
10. certification runtime + sécurité + UX.

**Ne pas ajouter d'IA au début.** Le stockage/provenance doivent être fiables avant classification automatique.

---

## LOT D — ORTHO JOURNEY

**Goal :** rendre l'évolution du traitement orthodontique lisible et exploitable en un seul parcours.

Dépend de Media Core pour les preuves visuelles T0/T1/T2.

Minimum :

- case orthodontique distinct ;
- phases ;
- appareil/aligneur ;
- contrôles ;
- événements/incidents ;
- objectifs praticien ;
- médias liés ;
- documents liés ;
- finance liée sans mélanger vérité clinique et comptable ;
- clôture/contention/suivi.

---

## LOT E — CEPHALO R2 COMPETITIVE

**Goal :** dépasser la logique « tracé automatique » par un système longitudinal traçable.

Priorités :

1. superposition T0/T1 ;
2. extension T2/Tn ;
3. analyses validées prioritaires ;
4. profils/normes sourcés ;
5. comparaison tracé/radio/photo ;
6. rapport longitudinal ;
7. review clinique indépendante.

**Gate scientifique :** aucun nombre normatif nouveau n'entre sans source explicite et statut de validation.

---

## LOT F — PATIENT COMPANION

Construire après stabilisation des contrats identité/mobile/sécurité.

Commencer read-mostly :

1. RDV ;
2. documents ;
3. questionnaires ;
4. notifications ;
5. finance consultative ;
6. upload urgence ;
7. signature ;
8. paiement.

Écriture clinique directe par le patient : interdite sauf contrat explicite, validation et provenance.

---

## LOT G — CONNECT HUB

1. architecture connecteur ;
2. sandbox/provider mock contractuel ;
3. premier provider réel ;
4. journal + retry + idempotence ;
5. second provider réel ;
6. certification de révocation et perte réseau.

**Go/no-go par provider :** documentation officielle + droit d'accès + environnement de test + mapping données + politique sécurité. Sans ces éléments, le connecteur reste `BLOCKED_EXTERNAL`, pas « presque terminé ».

---

## LOT H — INDUSTRIALISATION ET PILOTES

**Goal :** transformer un excellent repo en produit cabinet exploitable.

### H1 Installation

- machine Windows propre ;
- prérequis documentés ;
- installation non interactive autant que possible ;
- diagnostic démarrage ;
- échec fail-closed si chiffrement attendu absent.

### H2 Update / rollback

- version immuable ;
- migration DB versionnée ;
- backup pré-migration ;
- rollback testé ;
- compatibilité des données démontrée.

### H3 Backup / restore

- backup chiffré ;
- intégrité ;
- restore sur machine distincte ;
- procédure documentée ;
- RPO/RTO mesurés sur matériel de référence, pas inventés.

### H4 Supportability

- health report ;
- logs structurés ;
- redaction PHI/secrets ;
- support bundle ;
- codes d'erreur exploitables.

### H5 Pilotes

Minimum avant revendication « production-ready » :

- 3 cabinets ;
- profils d'usage différents ;
- période suffisante pour couvrir agenda, documents, paiements, backup et mise à jour ;
- registre incidents ;
- aucun P0 ouvert ;
- restore drill validé.

---

# 7. PRIORITÉ PRODUIT — CE QUI FAIT RÉELLEMENT GAGNER

Ordre stratégique recommandé :

1. **fermer les lots actifs/certification** ;
2. **Media Core** ;
3. **Ortho Journey** ;
4. **Ceph R2 longitudinal + méthodes validées** ;
5. **Patient Companion** ;
6. **Connect Hub** ;
7. **industrialisation/pilotes** ;
8. seulement ensuite : borne, fonctions périphériques et breadth marketing.

Pourquoi : Media + Journey + Ceph créent un workflow intégré qu'Orthalis répartit entre plusieurs briques. C'est l'endroit où Digital Crown peut construire un avantage produit cohérent au lieu de jouer à la photocopieuse fonctionnelle.

---

# 8. RÈGLES D'EXÉCUTION POUR CHAQUE LOT

Chaque lot significatif doit commencer par :

**Goal → Succès observable → Preuve attendue → risques → dépendances.**

Chaque changement UI/UX :

**BEFORE → Goal visuel → référence/mockup → implémentation → AFTER mêmes viewports → comparaison/tests → score visuel.**

Viewports minimaux Digital Crown :

- 390 ;
- 768 ;
- 1280+.

Chaque changement clinique :

- source des constantes ;
- provenance ;
- gestion UNKNOWN/NOT_COMPUTABLE ;
- séparation mesure/interprétation/diagnostic ;
- validation praticien là où nécessaire ;
- test négatif/fail-closed.

Chaque intégration :

- droits d'accès/provider ;
- secrets ;
- idempotence ;
- retries ;
- mapping ;
- audit ;
- révocation ;
- test perte réseau.

Chaque lot data :

- migration ;
- rollback ;
- sauvegarde ;
- isolation tenant ;
- suppression/retention ;
- test volumétrique proportionnel au risque.

---

# 9. DEFINITION OF DONE — COMPÉTITIVE

Une fonction n'est pas « au niveau Orthalis » parce qu'un écran ressemble à leur brochure.

Elle doit avoir :

1. contrat fonctionnel ;
2. code ;
3. tests ;
4. permissions ;
5. erreurs explicites ;
6. migration si nécessaire ;
7. runtime réel ;
8. UX responsive si visuel ;
9. documentation ;
10. benchmark sur scénario équivalent ;
11. preuve archivée ;
12. aucune dette P0 ouverte.

Pour les fonctions cliniques : ajouter validation scientifique adaptée.

Pour les fonctions cabinet critiques : ajouter backup/restore/recovery.

---

# 10. STOP CONDITIONS

Arrêter ou reclasser un lot si :

- API partenaire indisponible ou accès non autorisé ;
- information clinique indispensable sans source fiable ;
- exigence réglementaire/juridique non tranchée ;
- changement met en danger migration ou données réelles ;
- dépendance critique non stable ;
- preuve impossible à produire honnêtement.

Dans ces cas, statut exact : `BLOCKED_EXTERNAL`, `BLOCKED_SCIENTIFIC`, `BLOCKED_LEGAL` ou `BLOCKED_DATA_SAFETY`.

Jamais « terminé » par fatigue administrative. Les humains ont déjà inventé assez de statuts verts décoratifs comme ça.

---

# 11. WATCHLIST ORTHALIS

À chaque grand closeout, re-vérifier au minimum :

- Orthalis core ;
- Ceph ;
- Kitview ;
- Dentapoche ;
- nouvelles passerelles ;
- Orthalis Cloud ;
- nouveaux usages IA ;
- changements de pricing/offres si publiquement vérifiables.

Une nouvelle annonce concurrente n'entre dans la roadmap que si elle change :

- valeur clinique ;
- adoption cabinet ;
- coût de switching ;
- différenciation Digital Crown ;
- ou dépendance stratégique.

---

# 12. KPI DE COMPÉTITIVITÉ

Ne pas suivre seulement « nombre de features ».

KPI à établir et mesurer sur pilotes :

- temps création patient → premier RDV ;
- temps ouverture dossier → information clinique recherchée ;
- temps import série photo → série classée ;
- temps comparaison T0/T1 ;
- temps création/validation document ;
- taux de tâches répétitives évitées ;
- taux d'erreurs utilisateur ;
- taux de rendez-vous confirmés ;
- récupération après incident ;
- temps restauration ;
- incidents sécurité ;
- satisfaction praticien/assistante/patient ;
- temps de formation nouvel utilisateur.

Les objectifs chiffrés ne seront inscrits qu'après création d'une baseline reproductible Digital Crown et, si possible, d'une mesure comparable concurrente. Aucun seuil arbitraire ne sera inventé pour donner au tableau l'air scientifique.

---

# 13. ÉTAT INITIAL AU 2026-09-11

## Terminé / prouvé

- cœur PMS Digital Crown présent ;
- local-first / on-premise ;
- sécurité et tenant guards structurés ;
- Document Studio avancé ;
- finance / échéanciers / paiements avancés ;
- panoramique ;
- céphalométrie typed read-path ;
- R1 calibration/provenance mergé dans master ;
- closeout R1 présent dans master ;
- mobile cabinet existant ;
- packaging Windows existant.

## En cours

- P6 Document Libre certification, PR #405.

## Gaps prioritaires non fermés

- Media Hub transverse de niveau Kitview ;
- Ortho Journey longitudinal compétitif ;
- Ceph longitudinal/superpositions + breadth scientifique certifiée ;
- Patient Companion ;
- Connect Hub + providers réels ;
- preuve d'industrialisation/pilotes multi-cabinets.

---

# 14. NEXT EXACT

**Fermer le lot actif P6 #405 sans mutation produit parasite, puis ouvrir LOT B — Competitive Evidence Harness à partir du master réellement courant.**

Ensuite :

`Evidence Harness → Media Core → Ortho Journey → Ceph R2 Competitive → Patient Companion → Connect Hub → Industrialisation/Pilotes → re-benchmark`.

Si une roadmap spécialisée déjà active impose une étape de sécurité/science préalable, cette étape prévaut sur l'ordre produit ci-dessus.

---

# 15. CRITÈRE « DIGITAL CROWN > ORTHALIS »

La revendication est interdite tant que les conditions suivantes ne sont pas toutes réunies :

- scorecard recalculée avec sources fraîches ;
- aucune catégorie critique < 8/10 ;
- Media / Ortho Journey / Ceph / Patient / Connectors prouvés en runtime ;
- restore drill réussi ;
- pilotes cabinet réussis ;
- aucun P0 sécurité/data ouvert ;
- fonctions cliniques majeures validées selon leur niveau de risque ;
- benchmark utilisateur démontre un avantage mesurable sur au moins **3 workflows structurants** ;
- avantage Maroc-first documenté sur besoins réels de cabinets marocains.

Avant cela, formulation autorisée :

> « Digital Crown vise à dépasser Orthalis sur certains workflows et possède des avantages architecturaux/local-first démontrés. »

Après preuve complète seulement :

> « Digital Crown dépasse Orthalis sur les dimensions X/Y/Z mesurées selon le protocole versionné N. »

---

# 16. GOUVERNANCE DU FICHIER

Mettre à jour ce fichier uniquement lorsque l'un des événements suivants survient :

- grand lot compétitif fermé ;
- changement majeur du benchmark Orthalis ;
- nouvelle preuve pilote ;
- changement de priorité stratégique ;
- gap déclaré fermé avec preuve ;
- nouveau blocage externe majeur.

Ne jamais convertir une intention en état terminé.

À chaque reprise de ce chantier :

1. lire ce fichier ;
2. vérifier `master` / HEAD ;
3. vérifier PRs actives et CI ;
4. vérifier le fichier canonique du lot courant ;
5. exécuter `Next exact` ;
6. mettre à jour ce document seulement avec état réellement prouvé.

---

## FICHIER CANONIQUE

`DIGITAL_CROWN_VS_ORTHALIS_ROADMAP.md` — Digital Crown vs Orthalis — **baseline stratégique initiale vérifiée : 70,0/100 vs 90,5/100, non certifiante**.
