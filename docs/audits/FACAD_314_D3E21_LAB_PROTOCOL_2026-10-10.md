# FAC-03 D3E.21 — Protocole offline de comparaison (DESIGN UNIQUEMENT)

Date : 2026-10-10. Baseline GitHub : `565d3767c2218c8820424e88ab6e936cfae4241d`. **Aucune VM, ISO, capture, transfert, exécution FACAD ou nouvelle preuve clinique.**

## Référence déjà observée

Le dépôt contient `docs/audits/FACAD_314_ROBERT_DIRECT_PARITY_BASELINE_2026-10-08.md` et sa preuve de run [#37841266986](https://github.com/hraaaaf/Digital_crown/actions/runs/37841266986) : exemple non clinique Robert chargé, fenêtre d'analyse **Bergen short**, 12 valeurs **affichées par UIA**. Corrigeons donc l'affirmation « aucune démo Robert observée ». La preuve existante n'est **pas** un export FACAD complet, pas une trace numérique DC de la même géométrie et pas une comparaison de parité ou d'isolation native Hyper-V.

Un fichier versionné, `docs/audits/FACAD_314_D3E21_ROBERT_DISPLAY_MATRIX.json`, fige ces 12 libellés/valeurs/unités, leurs identités DC seulement **candidates** et les statuts `NOT_COMPARABLE` ; aucune norme démographique n'est importée. Le simple contrôle 67,7 - 78,4 = -10,7 relève uniquement de l'arithmétique sur trois valeurs affichées.

## Plan d'expérience future — toutes les phases NON AUTORISÉES ici

| Phase | Condition de passage | Arrêt obligatoire |
|---|---|---|
| P0 — Distribution | Droits éditeur/échantillon officiel non clinique documentés, vérification intégrité/licence et activation offline | STOP sans autorisation ou provenance |
| P1 — Hôte | Matériel/compte isolé non clinique, secrets absents, propriétaire des règles documenté | STOP si machine clinique ou contrôles non auditables |
| P2 — Ingress | ISO en lecture seule vérifié, allowlist + SHA privés, aucune donnée patient ou secrets | STOP si besoin d'accès réseau/dossiers hôte/presse-papiers |
| P3 — VM | Hyper-V Gen2 éventuel, aucune NIC/vSwitch, inventaire hôte/invité, Enhanced Session désactivée ; inspecter PowerShell Direct et Guest Service Interface, privilèges, périphériques et contrôles négatifs | STOP si frontière hôte-invité invérifiable ; pas de lancement dans ce lot |
| P4 — Même tracé | Exemple Robert, image, landmarks, version, mm/pixel, orientation, analyse et constructions identiques ; bras froid/chaud et contrôles préenregistrés | STOP si calibration ou définition anatomique non identique |
| P5 — Preuves | Proposer à reviewer confidentialité un protocole d'agrégation *dans invité* et une voie d'extraction minimale approuvée et vérifiée | **BLOCKER actuel : aucune sortie approuvée.** Interdiction d'activer discrètement réseau/Copy-VMFile/USB/clipboard, ou d'exporter ETL/EVTX/paths/PID dans GitHub |
| P6 — Clôture | Revue indépendante sécurité + science même SHA, effacement VHD/checkpoints/ISO/traces et rétention prouvés | STOP si permission, reviewer ou destruction manquants |

Sources techniques : [Hyper-V integration services](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/integration-services), [PowerShell Direct](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/powershell-direct), [Set-VMDvdDrive](https://learn.microsoft.com/en-us/powershell/module/hyper-v/set-vmdvddrive). Ce sont des descriptions de mécanismes, **pas une preuve de confinement**.

## Matrice de comparaison (préparation scientifique)

Les noms SNA/SNB/ANB sont des identités candidates DC, pas des constructions garanties égales. **ML/NSL ≠ automatiquement GoGn–SN ; ILi/ML ≠ automatiquement IMPA ; ILs/NSL ≠ U1/NA**. Aucun statut de parité ne doit basculer par correspondance de libellé.

Scénarios à préenregistrer : identité de cas/version, calibration et orientation, landmarks/constructions, unités et signes, écarts quantitatifs au même tracé, reproductibilité et arrondis, témoins négatifs (mauvaise unité, tracé différent, fichier absent). Les tolérances seront justifiées et fixées *avant* de consulter des écarts réels. Valeurs et normes Facad visibles ≠ normes ni preuves de validité clinique.

Le petit validateur source-only D3E.21 vérifie exclusivement un dossier historique et une matrice figée ; ses éventuels exemples arithmétiques sont marqués **SYNTHETIC_ONLY**. Aucun fichier nouveau de patient, aucune donnée clinique et aucun binaire installé par ce lot.

## Deux perspectives adversariales internes — non indépendantes

**Sécurité :** provenance de licence, isolation native, host privilege et egress non prouvés. **BLOCKER → NO-GO native.**
**Scientifique :** même tracé DC et export numérique indépendant absents, identités anatomiques et métriques non qualifiées. **BLOCKER → NO-GO parité**.

Les 6 BLOCKER et 4 MAJOR D3E.20 demeurent ouverts. `FAC03_D3=OPEN_RED` ; `SHARED_APP_STORAGE_ISOLATION=UNVERIFIED` ; `CLINICAL_EDIT_ALLOWED=false` ; `CONVERGED=false`. Hypothèse de permission utilisateur = outil de planification, pas autorisation Ilexis vérifiée ni autorisation nouvelle de faire une expérience native.