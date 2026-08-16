# Document Studio — roadmap canonique page par page

Date de référence : 2026-08-16

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page, dans l’ordre visuel réel de l’interface**, sans confondre engineering, runtime, validation clinique/financière et production.

Ordre canonique (`StudioTabs.tsx`) :

1. **P1 — Ordonnance**
2. **P2 — Certificat**
3. **P3 — Devis**
4. **P4 — Note Honoraires**
5. **P5 — Suivi Paiement**
6. **P6 — Document Libre**
7. **P7 — Compagnon Diagnostique**
8. **T1 — Audit transversal premium**
9. **T2 — Refonte intelligente finale / recertification globale**

## Règle de preuve

- **CODE VÉRIFIÉ** : comportement démontré par le code courant.
- **TEST EXÉCUTÉ** : résultat réellement observé.
- **INTERACTION EXÉCUTÉE** : parcours réellement observé dans l’application.
- **CERTIFICATION** : séparée et jamais déduite automatiquement d’un test local ou d’une CI.

Aucun pourcentage global n’est déduit de cette roadmap : aucune pondération officielle des pages/gates n’a été définie. **Avancement global chiffré : indéterminé.**

---

## P1 — Ordonnance

**État : ✅ engineering fermé + recertification visuelle réalisée ; gates clinique/runtime séparés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`.

Acquis principaux : contrats/safety, persistance habitudes/protocoles, dirty-state, fast prescription, contexte patient, preview responsive, recertification 1440/768/390.

Gates séparés : interaction authentifiée finale et validation clinique/pharmacologique humaine.

---

## P2 — Certificat

**État : ✅ engineering convergé ; ⏳ runtime/PDF final différé.**

Rapport historique : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md` (ancien identifiant conservé pour traçabilité).

Acquis : nature/date/durée explicites, certificat libre praticien, contrat backend fail-closed, signature dentiste, impression fraîche, PDF/identité/QR sécurisés.

Gates différés : checkout complet, runtime authentifié, inspection PDF finale, validation réglementaire/clinique si requise.

---

## P3 — Devis

**État : ⏸ CLOSED / PAUSED UNTIL FURTHER NOTICE — décision produit du 16 août 2026.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_AUDIT.md`
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md`

PR d’intégration : **#77**, conservée **open + draft**.

Preuves locales P3-H conservées : backend **26/26 PASS**, frontend policies `tsc --strict` PASS, frontend ciblé **39/39 PASS**, PDF long lisible avec floor >=7 pt.

Gates différés uniquement si P3 est rouvert : full build/tests, smoke authentifié adulte/pédiatrique, archive/reopen réel, PDF cabinet, responsive/browser, merge/post-merge.

---

## P4 — Note Honoraires

**État : ✅ engineering local convergé ; ⏳ full-app/browser/PDF cabinet différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P4_NOTE_HONORAIRES_AUDIT.md`.
PR : **#90**, draft.

Acquis : contrat financier fail-closed, isolation échéanciers, séparation impayé/encaissement, round-trip odontogramme, PDF multipage sûr, sémantique financière et accessibilité renforcées.

Preuves locales : backend **13/13 PASS**, policy échéancier **4/4 PASS**, archive hydration **1/1 PASS**, PDF long **36/36 lignes / 6 pages / header 6/6 / floor 7 pt**.

Gates différés : React/Vite full-project, smoke authentifié, PDF cabinet, responsive/browser, merge/post-merge.

---

## P5 — Suivi Paiement

**État : ✅ engineering local convergé ; ⏳ certification financière/full-app différée.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md`.
Handover : `docs/audits/DOCUMENT_STUDIO_P5_HANDOVER_2026-08-16.md`.
PR : **#95**, draft.

Acquis :
- création de plan fail-closed et somme exacte ;
- édition conciliée avec le total contractuel ;
- échéance payée immuable sans contrepassation ;
- suppression d’un plan avec historique de paiement interdite ;
- suivi backend-authoritative : payé / restant / prochaine échéance / retard ;
- règlement réel explicite avec mode de paiement ;
- alias TPE→CARTE ;
- brouillon nouveau plan séparé du suivi réel ;
- faux toggle local `Réglé` supprimé ;
- sauvegarde explicite `POST /installments/` ;
- faux bouton global `Enregistrer` supprimé pour P5 ;
- rappel WhatsApp manuel depuis données backend.

Preuves locales : backend **15/15 PASS**, summary policy **4/4 PASS**, create-payload policy `tsc --strict` + **8/8 PASS**.

Gates différés : build/tests full-project, création/reload/paiement authentifiés, vérification vraie ligne `Payment`, suppression réelle avec historique, responsive/browser, WhatsApp réel.

Amélioration produit séparée : restructuration atomique d’un plan impayé existant.

---

## P6 — Document Libre

**État : ✅ engineering local convergé ; ⏳ runtime/PDF cabinet différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md`.
PR : **#96**, draft.

Socle vérifié :
- titre/contenu obligatoires ;
- toolbar non-submit ;
- permission backend `clinical` + accès patient ;
- validation fail-closed avant PDF : titre/contenu explicites, tailles maximales, A4/A5, alignements autorisés ;
- markup toolbar limité et contenu non autorisé échappé ;
- filename nettoyé ;
- tableaux/wrapping/multipage ;
- preview non archivée ;
- archive documentaire uniquement après génération réussie ;
- protection brouillon sur changement d’onglet et `beforeunload`.

Correction P6-R1 :
- l’ouverture/réouverture établit une baseline Libre propre ;
- un archivage Libre ne nettoie le dirty-state qu’après réponse backend réussie avec `pdf_url` ;
- preview, échec, 409/doublon, autre type ou PDF absent conservent l’état sale.

Preuve locale P6-R1 : `tsc --strict` PASS + **11/11 assertions PASS**.

Gates différés : vrai build/tests React/Vite, runtime saisie/toolbar/tableau/A4-A5/alignements, archive/reopen/409, impression, PDF cabinet multipage, responsive/browser, merge/post-merge.

---

## P7 — Compagnon Diagnostique

**État : 🟡 PAGE ACTIVE — audit complet à exécuter maintenant.**

Acquis historique : frontière pharmacovigilance/substitution durcie, notamment PR #38 ; les signaux d’allergie avertissent sans substitution thérapeutique automatique.

### Chemin critique P7

- [ ] cartographier l’arbre réel des états/questions ;
- [ ] vérifier les données patient réellement consommées ;
- [ ] qualifier les sorties : diagnostic, hypothèse, acte proposé, orientation ;
- [ ] vérifier la validation praticien avant toute action clinique ;
- [ ] auditer P7→P3 Devis et les filtres déjà durcis ;
- [ ] auditer P7→P1 Ordonnance / autres documents ;
- [ ] vérifier conservation/perte d’état inter-pages ;
- [ ] supprimer callbacks/branches orphelins ;
- [ ] auditer UX/accessibilité/responsive ;
- [ ] séparer explicitement validation scientifique humaine de la certification engineering.

---

## T1 — Audit transversal premium

**État : ⬜ après P7.**

Couvre notamment : cohérence navigation, dirty-state multi-pages, preview/impression/archive, permissions, responsive, accessibilité, duplication de logique, contrats backend partagés et nomenclature.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ⬜ après T1.**

Objectif : corriger les points transversaux retenus, exécuter la régression globale Document Studio, fermer les gates runtime/PDF/browser disponibles et produire le closeout final sans sur-certification.