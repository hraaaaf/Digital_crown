# FAC-03 D3E.15 — Faisabilité de la politique d'audit par utilisateur (lecture seule)

**Date :** 2026-10-10. **Périmètre :** expérimentation de lecture des réglages auditpol Windows, sans activation d'audit et sans accès à Facad/Ilexis. **FAC-03 D3 OPEN/RED**.

## Base factuelle

Sur le runner Windows jetable D3E.14a, la sous-politique **Audit File System Success** n'était pas configurée (\`success_not_configured\`). La règle SACL a pourtant été installée puis restaurée sur le fichier synthétique, et une écriture du processus enfant a été vérifiée, mais zéro événement Security 4663 correspondant n'a été trouvé : [run Windows #38082393080](https://github.com/hraaaaf/Digital_crown/actions/runs/38082393080), [CI 373/373](https://github.com/hraaaaf/Digital_crown/actions/runs/38082393098), HEAD \`f0799209516eecd690840574ae52f5fd4987926c\`.

Cette combinaison **ne prouve pas l'absence d'écrivain** ; elle est cohérente avec la désactivation de l'audit des accès réussis. Elle ne prouve pas l'état de la politique de tous les autres runners.

## Ce que Microsoft documente

- [auditpol /get](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/auditpol-get) accepte \`/user:<SID>\`, \`/subcategory:<GUID>\`, et \`/r\` pour demander la politique par utilisateur sous forme de CSV, **sans la modifier**.
- [auditpol /set](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/auditpol-set) permet \`/user:<SID>\`, \`/include\` et \`/success:enable\` ; une inclusion par utilisateur pourrait théoriquement générer des audits que la politique système ne demande pas. **Cette capacité n'est pas une autorisation de l'utiliser.** Les changements de politiques d'audit système ou par utilisateur peuvent élargir le volume d'événements Security.
- [Audit File System](https://learn.microsoft.com/en-us/windows/client-management/mdm/policy-csp-Audit#objectaccess_auditfilesystem) : une SACL correspondant au droit/au compte ne suffit pas si la configuration de l'audit nécessaire n'est pas active. Le mécanisme est conjoint : politique effective + audit SACL + droits + journal lisible.
- Un audit par utilisateur **n'est pas limité à un chemin**. Même si une règle SACL sur un fichier synthétique cible un fichier unique, l'inclusion d'une politique par utilisateur peut faire remonter des événements relatifs à d'autres objets compatibles avec leur SACL. L'option d'exclusion par utilisateur est ignorée pour certains administrateurs selon Microsoft.

## Contrat D3E.15 appliqué

Sur **un runner éphémère Windows vierge**, sans Facad, sans ouvrir ou écrire de fichiers applicatifs et sans créer de SACL :

1. Vérifier le HEAD exact, la syntaxe PowerShell et Python du dispositif.
2. Lire par \`auditpol /get /subcategory:{0cce921d-69ae-11d9-bed3-505054503030} /r\` la sous-politique système File System Success.
3. Lire par \`auditpol /get /user:{SID du runner} /subcategory:{GUID} /r\` la politique d'inclusion pour le seul utilisateur de la session ; le SID et la sortie CSV complète restent **uniquement en mémoire**.
4. Distinguer seulement \`success_configured\`, \`success_not_configured\`, \`undetermined\`, \`parse_error\`, \`unavailable\`. Une absence d'information ou un parsing dépendant de la langue Windows **ne devient jamais une affirmation d'audit désactivé**.
5. Émettre deux JSON anonymes strictement schématisés sous GitHub Actions, sans nom de compte, SID, données patient, PID, chemins ou liste d'événements. Enregistrer seulement un booléen d'appartenance au groupe Administrators du runner (contexte technique de la politique).
6. Aucun \`auditpol /set\`, \`auditpol /restore\`, \`auditpol /clear\`, aucune capture ETW, lecture du journal Security, SACL nouvelle, modification File System, lancement Facad, lecture licence ou écriture patient. En cas d'erreur, **inconclusif/fail-closed**.
7. Le validateur refuse absolument tout claim de politique modifiée, scope fichier garanti, auteur Ilexis connu, isolation ou édition clinique autorisée.

Ce lot **ne mesure pas** si l'activation par utilisateur produirait réellement 4663, n'implémente aucun mécanisme de rollback d'une activation, et ne sollicite pas l'autorisation d'une telle activation. Ce point est volontaire : une collecte nouvelle dans le Security log et un changement de politique de sécurité nécessiteraient une revue de confidentialité indépendante et un protocole réversible validé *avant* exécution.

## Deux revues adversariales internes (pas des reviewers indépendants)

**Perspective A — sécurité/confidentialité (8/10 pour le périmètre lecture seule).** Le code évite toute écriture de configuration et toute ouverture de journal Security ; la sortie est agrégée et le SID reste privé. Risques : sortie CSV dépendante de l'OS, identité de l'utilisateur du runner possiblement Administrators, revendications excessives sur une future politique per-user. **BLOCKER pour toute activation ultérieure** : champ de collecte et procédure de restauration indépendante non vérifiés.

**Perspective B — validité de la preuve (6/10 pour lecture de configuration ; 2/10 pour attribution Ilexis).** Un réglage d'inclusion présent ne signifie pas que le journal Security reçoit les événements 4663 à la fenêtre pertinente, que le bon processus est attribué ou qu'une écriture est terminée. L'état lu peut être indéterminé sur les runners localisés. Aucune expérience réelle de provenance Ilexis n'est exécutée. **CONVERGED=false**, deux revues internes seulement, aucune revue indépendante réelle.

## Sorties et prochaines conditions

Succès observable **pour D3E.15 seulement** : CI source-only verte, validation native Windows en lecture seule sur HEAD exact, sortie autorisée par schéma, et confirmation qu'aucune politique n'a été modifiée. Si la lecture échoue, documenter le blocage ; ne pas deviner le mode de la politique.

**Étape suivante potentielle, distincte :** revue du risque per-user + conception d'un éventuel essai isolé réversible, nécessitant un accord explicite avant modification de la politique. Aucune activation automatique par D3E.15.

**Verdict de sécurité : \`FAC-03 D3 OPEN/RED\` ; \`SHARED_APP_STORAGE_ISOLATION=UNVERIFIED\` ; \`CLINICAL_EDIT_ALLOWED=false\`. Aucun merge, aucun Vercel, aucun patient Load/Save.**
