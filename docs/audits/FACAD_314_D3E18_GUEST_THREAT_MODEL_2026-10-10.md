# FAC-03 D3E.18 — Préflight statique d'un invité Windows à exposition réduite

**État (2026-10-10) : DESIGN ONLY / STATIC VALIDATION. Aucun Windows Sandbox lancé, aucun fichier Facad/Ilexis lu, aucune capture ETW, aucune opération clinique autorisée.**

## 1. Décision de méthode et état des preuves

D3E.17 a comparé huit alternatives d'attribution des écritures. Aucune ne démontre un confinement au fichier pour un écrivain Ilexis réel. Le seul résultat positif d'attribution processus correspond à un enfant **synthétique** sous ETW Kernel-File ; le fournisseur ETW collecte à l'échelle de la machine. La méthode proposée n'est donc **pas « ETW par fichier »**. Il s'agit d'une **revue de la réduction des données étrangères grâce à un invité entièrement jetable** : ETW y resterait global *dans l'invité*, mais pourrait ne pas exposer les données du Windows hôte si les frontières d'isolation étaient effectivement prouvées. **Aucune de ces frontières n'est aujourd'hui prouvée par une exécution.**

Baseline exact D3E.17 : `2b9985c78dececde8e697b4d923022592b2927ea`, [CI 507/507](https://github.com/hraaaaf/Digital_crown/actions/runs/38087790508), `SOURCE_REVIEW_COMPLETE_NATIVE_CAPTURE_BLOCKED`.

## 2. Configuration proposée, PAS EXECUTABLE par double clic

Fichier : `docs/audits/FACAD_314_D3E18_ISOLATED_GUEST_DESIGN.wsb.template`. L'extension **`.wsb.template`** est intentionnelle : c'est une pièce de revue statique, **pas une instruction d'ouverture de Windows Sandbox**. Le gate CI parse le contenu XML et rejette les champs additionnels, duplications, DTD, entités, attributes, text hors schéma et toute modification dangereuse.

La configuration demande explicitement :
- `Networking=Disable` et `VGpu=Disable` : réduction du partage réseau et du GPU de l'hôte ;
- `ClipboardRedirection=Disable`, `PrinterRedirection=Disable`, `AudioInput=Disable`, `VideoInput=Disable` : réduction des passerelles hôte → invité ;
- `ProtectedClient=Enable` : renforcement de la session RDP de Sandbox ;
- **ABSENCE totale** de `MappedFolders` (même readonly), `LogonCommand` (pas de lancement automatique), de toute référence hôte, de chemin, d'identité ou de binaire Facad.

**Documentation officielle Microsoft consultée le 10 octobre 2026** :
[Windows Sandbox — configuration WSB](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file),
[Windows Sandbox — architecture et prérequis](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/),
[Windows Sandbox — restrictions GPO/CSP](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-windowssandbox).

**Attention :** Microsoft indique que le réseau et le presse-papiers peuvent être activés par défaut ; une configuration WSB **demande** leur désactivation sans apporter de preuve que l'OS, l'édition Windows, l'hyperviseur, les politiques de l'entreprise ou la runtime Sandbox appliquent ces demandes. Un contrôle de politique hôte et des vérifications de fonctionnement seront nécessaires avant tout lancement expérimental.

## 3. Chaîne d'approvisionnement : BLOCKER explicite

Avec `Networking=Disable`, `ClipboardRedirection=Disable`, aucun `MappedFolders`, et aucun `LogonCommand`, il n'existe **dans ce lot aucune méthode approuvée** pour placer l'installeur officiel Quick-demo et son exemple Robert dans l'invité. Il serait dangereux de supposer qu'un dossier partagé readonly, le presse-papiers ou Internet sont acceptables « juste pour installer ».

Un futur lot doit proposer **une procédure de staging sûre, réversible et autorisée**, soumise à deux revues réellement indépendantes et à un accord distinct. La sécurité du transfert doit être vérifiée sans recopier de données patient, configuration, licence, traces ou secrets de l'hôte. Faute de ce chemin : **NO NATIVE TEST**. Ne pas contourner un verrou pour obtenir plus vite une trace.

## 4. Matrice des preuves manquantes (toutes = FALSE)

Le contrat `docs/audits/FACAD_314_D3E18_GUEST_PREFLIGHT_CONTRACT.json` a **24 indicateurs non vérifiés**, notamment :
1. disponibilité effective du Sandbox/Hyper-V, absence de stratégie hôte contraire, frontières réseau/clipboard/devices testées ;
2. absence de mounts hôte, secrets, connexions compte, données patient et licence clinique ;
3. origine et empreintes d'un Quick-demo officiel + méthode de transfert non risquée ;
4. aucune trace brute exportable, cleanup et destruction de guest observables ;
5. visibilité des pertes ETW, causalité FileObject/PID/événement/écriture complétée analysable, indépendance des bras ;
6. **deux revues indépendantes externes réelles** sur SHA commun, autorisation explicite d'une future expérience distincte ;
7. aucun claim `CLINICAL_EDIT_ALLOWED`, `SHARED_APP_STORAGE_ISOLATION=VERIFIED`, merge ou déploiement.

Une preuve doit inclure la **mesure native sur la configuration exacte**, des négatifs et un contrôle de la séparation hôte-invité ; le simple fichier WSB ne certifie **aucun** de ces points.

## 5. Revue adversariale interne (pas une revue indépendante réelle)

**Perspective A — confidentialité / hôte : 7/10 pour le document, BLOCKER execution.**
Les sept paramètres WSB sécurisés sont définis explicitement et testés par whitelist. Cependant, les options WSB n'attestent pas l'absence d'accès hôte au runtime ; la source officielle ne fournit aucune garantie suffisante de politique, staging ni effacement. Si une interface d'import est ajoutée sans preuve : BLOCKER.

**Perspective B — science / qualité de la preuve : 6/10 design, 2/10 attribution clinique réelle.**
Une guest isolée ne rend pas l'ETW par fichier, et une liaison Write-FileObject-PID synthétique ne démontre pas une écriture achevée ou l'origine du drift observé sur l'application. Des scénarios contrôle/counterfactual et métriques de loss seraient nécessaires avant interprétation. Pas de revues indépendantes réelles, aucun nouveau test Windows Ilexis, pas de capture.

**`CONVERGED=false`**. Toute future modification du SHA annule une revue antérieure. Gate CI `D3E18_STATIC_CONFIGURATION_VALID_NATIVE_GATES_BLOCKED` signifie uniquement que le template et le contrat respectent le modèle de sécurité **statique**.

## 6. Next exact : D3E.19 éventuel (ne pas démarrer implicitement)

Élaborer une procédure de transfert d'échantillon *sans franchir le périmètre clinique* ainsi qu'une preuve de confinement runtime dans une VM jetable ; obtenir des revues indépendantes réelles et une autorisation propriétaire explicite **avant** toute capture native. Cette étape peut être impossible dans Windows Sandbox avec tous les ports désactivés : documenter le blocage et considérer une VM offline préconstruite depuis sources publiques autorisées, sans diminuer les protections.

**FAC-03 D3 OPEN/RED · SHARED_APP_STORAGE_ISOLATION=UNVERIFIED · CLINICAL_EDIT_ALLOWED=false. Aucun merge, déploiement ni Live Capture.**
