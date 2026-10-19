# LOT05.7-J phase 3 — SCM Windows réel et contrôle Service SID/NTFS sur fixtures FAKE

**Scope immuable** : LOT05 / SQL Migration Wizard, sous-lot 05.7-J phase 3 uniquement, sur PR Draft empilée sur [#977](https://github.com/hraaaaf/Digital_crown/pull/977) @ `db23aeda69f95892d690f293007472bee7b9c3cb`. AUCUNE modification du runtime clinique, aucune activation de restauration, pas de patient réel, pas de service Digital Crown installé. Ce test, à la différence de J2, doit créer de vrais services Windows **à noms éphémères**, puis les supprimer dans le même job CI.

## Preuves recherchées / conditions STRICTES

- Windows runner GitHub Actions administrateur, `GITHUB_ACTIONS=true`, `RUNNER_OS=Windows` et drapeau `LOT05J3_WINDOWS_SCM_FAKE_ONLY=1` obligatoires ; ne rien installer sur un poste clinique.
- Compilateur C# de .NET Framework Windows, `ServiceBase.Run`, deux services uniques `DCJ3A_<nonce>` et `DCJ3B_<nonce>` enregistrés via `sc.exe create`, compte `NT AUTHORITY\LocalService`, démarrage `demand` ; configuration de Service SID `UNRESTRICTED` pour A et `NONE` pour B ; preuves `sc.exe qsidtype`, `sc.exe showsid` et résolution LSA `NT SERVICE\DCJ3A_<nonce>`.
- Le vrai processus SCM A exécute `WindowsIdentity.GetCurrent()` et recherche le SID A dans ses groupes du **token Windows**, non seulement dans le fichier de configuration. La racine de fixture `%ProgramData%\lot05j3_fake_<nonce>` contient uniquement un fichier `challenge.fake` avec DACL explicite permettant SYSTEM, Administrators et SID A (PAS `LocalService`).
- Les deux services exécutent le **même exécutable** sous le **même compte LocalService** ; A doit confirmer SID dans son token et lecture du fichier ; B, service avec `sidtype NONE`, doit prouver l'absence du SID de A et un `access_denied` réel, tout en écrivant un retour dans un répertoire télémétrie distinct explicitement accessible à LocalService. L'exécutable lancé en direct par le runner doit aussi reconnaître l'absence du SID A dans son token.
- `finally` : `sc.exe stop`, `sc.exe delete`, suppression de la fixture et `sc.exe query` obligatoire pour prouver l'absence des deux services. Si création/attestation/configuration, ACL ou nettoyage échouent, **CI ROUGE** : aucun silent skip ni faux PASS.

## CI et gouvernance

Le workflow REQUIRED J3 (Windows **service réel** et matrix Linux/Windows pour les suites héritées) atteste 18 tests J2 SQLCipher, 16 tests J1 SQLite, 21 tests I vrai JWT/SQLCipher et 16 tests guided_restore par OS, soit 142 exécutions héritées, en plus de la preuve SCM Windows. Le workflow parent J2 est HORS SCOPE/SKIPPED pour une PR J3 empilée, sa contrainte 6 fichiers restant effective pour #977. Le différentiel J3 est limité aux six fichiers : source C# fixture, script PowerShell fixture, workflow J3, restriction du workflow J2, ce contrat, `techdoubt.md`. Deux revues adversariales internes perspectives A/B, confirmation même HEAD, PRE/POST Notion, CI Scope obligatoire.

## Ce que le laboratoire ne prouve PAS

Même une preuve A=autorisé / B=interdit sur un runner administrateur **ne suffit pas** pour Digital Crown en clinique. L'utilisateur du runner administrateur peut en théorie modifier les DACL et les binaires ; aucune résistance aux attaques administrateur/SYSTEM n'est revendiquée. Il faut encore prouver l'installation du véritable service du cabinet, identité SCM/Service SID et binaire signé, protection des ACL sur les répertoires réels, absence de reparse/jonctions/hardlinks, courses TOCTOU et rôles cross-tenant, JWT→job signé/anti-rejeu→worker, durabilité SQLCipher WAL+SHM/coffre/médias sans exposition clinique. Aucune restauration réelle n'est connectée ou permise. Les points d'entrée de restauration actifs restent **DENY inconditionnel** depuis #976.

**Verdict maximum autorisé** : preuve LAB d'une isolation Windows SID sur fixtures et non une certification Windows production. **Certification clinique NO-GO** ; réserves `techdoubt.md`.

**Sources officielles** : Microsoft Learn, <https://learn.microsoft.com/en-us/windows/win32/services/configuring-a-service-using-sc> et <https://learn.microsoft.com/en-us/windows/win32/services/localservice-account>.

**Roadmap** : LOT05 → 05.7-J phases 1/2 CONVERGED LAB → phase3 SCM synthétique à vérifier → intégration/attestation réelle du service cabinet et récupération multicomposants toujours NO-GO → LOT10 terrain séparé.
