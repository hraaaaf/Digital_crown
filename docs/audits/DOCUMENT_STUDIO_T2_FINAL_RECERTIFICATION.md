# Document Studio — T2 Refonte intelligente finale / recertification globale

Date : 2026-08-16
Branche : `agent/t2-document-studio-final-recertification`
Base : T1 Audit transversal premium

## Verdict

**Engineering local Document Studio convergé sur P1→P7 + T1/T2. Certification full-app / production NON revendiquée.**

Source de statut détaillée : `docs/audits/DOCUMENT_STUDIO_T2_FINAL_STATUS.md`.

## T2-A — harness final fail-closed

`scripts/certify_document_studio.sh` est le certificateur automatisé unique du chantier Document Studio.

Il couvre :
1. Python >=3.12, Node >=20, git/npm présents, worktree propre ;
2. prod-safety positive en environnement de développement ;
3. régression backend ciblée P1→P7 ;
4. suite backend complète ;
5. tests frontend ciblés `src/features/admin/DocumentStudio` ;
6. suite frontend complète ;
7. build frontend production ;
8. invariants source anti-ghost AI / diagnostic autonome ;
9. prod-safety négative.

Preuve réellement exécutée dans le Linux de cette session :
- `bash -n` : **PASS** ;
- Python 3.13.5 ; Node 22.16.0 ; npm 10.9.2.

Le dépôt complet et ses dépendances ne sont pas montés dans ce Linux : le harness complet n'est **pas** revendiqué PASS.

## T2-B — tests critiques versionnés

Tests ajoutés/conservés dans le futur `npm test` full-project :
- `DocumentNavigationPolicy.test.ts` ;
- `DiagnosticCompanionPolicy.test.ts` ;
- `LivePreview.r7.test.tsx` étendu pour dialog / focus initial / Escape.

Dernière preuve réellement exécutée pour la navigation T1 : `tsc --strict` + **9/9 scénarios PASS** dans le harness Linux isolé.

Les nouveaux tests Vitest T2 sont versionnés mais non exécutés dans un checkout frontend complet ici.

## T2-C — accessibilité LivePreview

La preview non-inline est désormais exposée comme une vraie modale :
- `role="dialog"` ;
- `aria-modal="true"` ;
- titre relié par `aria-labelledby` ;
- focus initial sur Fermer ;
- fermeture Escape ;
- label accessible du bouton Fermer ;
- statut de chargement annoncé via `aria-live`.

## T2-D — legacy cleanup fail-closed

Plusieurs gros fichiers historiques semblent potentiellement orphelins (`EliteAssistant`, `EliteDock`, `DiagnosticEngine`, etc.), mais l'API de recherche a retourné `incomplete_results=true`.

Décision : **aucune suppression sans preuve exhaustive d'absence de référence**.

Même doctrine pour `DocumentFactory.create_installment_plan()` : le chemin public `/documents/generate` avec `type=echeancier` est déjà refusé par le `DocumentRequest` réellement exporté, mais la méthode legacy n'est pas supprimée sans scan complet fiable.

## État final des pages

- P1 Ordonnance : engineering fermé ; gates clinique/runtime séparés.
- P2 Certificat : engineering convergé ; runtime/PDF final différé.
- P3 Devis : CLOSED / PAUSED par décision produit ; PR #77 draft.
- P4 Note Honoraires : engineering local convergé ; PR #90 draft.
- P5 Suivi Paiement : engineering local convergé ; PR #95 draft.
- P6 Document Libre : engineering local convergé ; PR #96 draft.
- P7 Compagnon Diagnostique : engineering safety local convergé ; PR #97 draft.
- T1 Transversal : engineering transversal local convergé ; PR #101 draft.
- T2 : engineering closeout local convergé ; PR #102 draft.

## Preuves locales consolidées

- P3 : backend 26/26 PASS ; frontend ciblé 39/39 PASS ; PDF multipage ciblé PASS.
- P4 : backend 13/13 PASS ; échéancier 4/4 ; hydration 1/1 ; PDF long 36/36 lignes / 6 pages.
- P5 : backend 15/15 PASS ; summary 4/4 ; create payload `tsc --strict` + 8/8.
- P6 : dirty/archive `tsc --strict` + 11/11.
- P7 : safety `tsc --strict` + 8/8 ; P7→P3 + dirty `tsc --strict` + 12/12.
- T1 : navigation dernier rerun `tsc --strict` + 9/9 ; contrat legacy échéancier helper 4/4.
- T2 : `bash -n scripts/certify_document_studio.sh` équivalent local PASS.

## Gates indispensables avant certification complète

Sur checkout propre du **head candidat exact**, dépendances installées :

```bash
bash scripts/certify_document_studio.sh
```

Puis :
1. runtime authentifié P1→P7 ;
2. navigation + abandon brouillon ;
3. preview/archive/reopen/duplicate cancel+force ;
4. impression fraîche ;
5. P5 création/reload/paiement ;
6. P7→P3 confirmé ;
7. PDF cabinet court/long/A4/A5/branding/signature ;
8. browser 390 / 768 / desktop + clavier/touch/focus ;
9. validations humaines clinique/scientifique/réglementaire/financière applicables ;
10. ready/merge ordonné puis post-merge recertification.

## Conclusion

T2 clôt l'engineering local connu du Document Studio. Le verrou restant est l'exécution des certifications full-app et humaines, pas un P0/P1 engineering actuellement identifié.

Aucune pondération officielle n'existe : **pourcentage global indéterminé**.
