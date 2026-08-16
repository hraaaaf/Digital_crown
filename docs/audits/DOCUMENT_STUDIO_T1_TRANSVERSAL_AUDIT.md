# Document Studio — T1 Audit transversal premium

Date : 2026-08-16
Branche : `agent/t1-document-studio-transversal-audit`
Base : P7 Compagnon Diagnostique

## Verdict

**Engineering transversal local convergé sur les défauts critiques identifiés. Full build/runtime/browser non revendiqués.**

T1 a audité les mécanismes partagés entre P1→P7 : navigation, dirty-state, preview/archive/print, permissions/contrats backend, branches mortes et accessibilité commune.

## T1-A — navigation et dirty-state centralisés

### Findings

- `documentTab` dans l'URL pouvait appeler `setActiveTab()` directement et contourner les gardes de brouillon de `StudioTabs`.
- Certificat n'avait plus de dirty-state courant malgré son ancien closeout.
- la date commune du Header pouvait modifier Ordonnance/Certificat/Libre sans marquer leur brouillon sale.
- les gardes étaient fragmentées entre Hub, Tabs et formulaires.

### Corrections

- nouveau `DocumentNavigationPolicy.ts` ;
- `DocumentHub` devient l'autorité de navigation pour clics, changements query-param et transitions programmatiques ;
- URL `documentTab` synchronisée uniquement après navigation validée ;
- annulation d'une navigation restaure l'URL sur l'onglet courant ;
- nouveau `CertificateDirtyState.ts` ;
- dirty sources communes : accounting / prescription / certificate / libre / diagnostic ;
- garde `beforeunload` commune au Hub ;
- date commune marque Ordonnance/Certificat/Libre dirty ; accounting reste couvert par son fingerprint ;
- `StudioTabs` est réduit à un déclencheur de navigation.

### Preuve locale

`DocumentNavigationPolicy` : **`tsc --strict` PASS + 10/10 assertions PASS**.

## T1-B — contrat impression + suppression ghost AI

### P5 Suivi Paiement

Finding : la modale d'impression promettait un archivage alors que le flux P5 utilise seulement `/installments/generate-preview`.

Correction :
- texte explicite : impression = PDF du brouillon, **sans enregistrement du plan** ;
- sauvegarde réelle reste exclusivement `POST /installments/` via le bouton P5 dédié ;
- le footer P5 n'affiche pas de faux bouton global d'archive.

### Ghost AI Document Studio

Finding : une branche cachée `ai` restait accessible via query param, avec UI `Lancer Analyse IA` et appel `/patients/{id}/ai-diagnostic` dans le hook.

Correction :
- `ai` supprimé de `HubDocumentType` et des valeurs `documentTab` admises ;
- UI AI retirée du footer ;
- `aiReport`, `loadingAi`, `handleGenerateAI` et événements `ai-generation-*` retirés ;
- appel `/ai-diagnostic` retiré ;
- les vérifications restantes dans `useDocumentGenerator` sont explicitement déterministes.

Aucune certification full-repo ZERO LLM n'est déduite de ce lot ; seule la branche Document Studio inspectée est couverte.

## T1-C — archive-success explicite

### Finding

Le Hub pouvait déduire qu'une archive avait réussi à partir d'un simple changement de `pdfUrl`. Après un 409 annulé, une preview ultérieure pouvait donc théoriquement nettoyer à tort un brouillon.

### Correction

`useDocumentGenerator` émet désormais `ArchiveSuccessSignal` seulement si :
- la requête backend réussit ;
- `pdf_url` est présent ;
- `archive=true` ;
- `preview=false`.

`DocumentHub` nettoie les dirty-state uniquement depuis ce signal :
- Devis/Honoraires : nouvelle baseline accounting ;
- Ordonnance : dirty false ;
- Certificat : dirty false ;
- Document Libre : dirty false.

Preview, erreur, 409 annulé ou P5 preview-only n'émettent aucun signal d'archive.

## T1-D — suppression du second moteur Échéancier

### Finding

Le backend `/documents/generate` possédait encore un chemin historique `echeancier` capable de construire/persister un plan à partir d'un dictionnaire brut, contournant le contrat P5 strict. Le générateur legacy référençait en outre une architecture obsolète et constituait une seconde autorité financière inutile.

### Correction

Le `DocumentRequest` réellement exporté par `backend.schemas` bloque désormais **tout** `type=echeancier` sous `/documents/generate`.

Les trois chemins P5 autoritaires sont :
- `POST /installments/` : création persistante ;
- `POST /installments/generate-preview` : PDF brouillon ;
- `/installments/...` : suivi et encaissement.

### Preuves

- helper `assert_document_installment_path_is_disabled` : **4/4 PASS** sous Linux ;
- test d'intégration du `backend.schemas.DocumentRequest` versionné pour vérifier le rejet du chemin legacy, y compris avec `plan_id`.

## T1-E — UI partagée

`StudioHeader` :
- branche morte `activeTab !== 'ai'` retirée ;
- boutons communs explicitement `type="button"` ;
- label de date lié à son input ;
- odonto toggle explicitement button.

`StudioFooter` :
- modale impression porte une sémantique `dialog` ;
- message P5 transactionnel corrigé.

`LivePreview` :
- layout déjà responsive en drawer mobile/tablette et panneau desktop ;
- iframe titrée ;
- boutons refresh/close explicites.

## T1-F — stale print P5

### Finding

Le flux P5 armait `pendingPrint` avant le retour du nouveau PDF. Avec un aperçu précédent déjà présent, l'effet d'impression pouvait imprimer le PDF précédent.

### Correction

- `pendingPrint` est neutralisé avant génération P5 ;
- il n'est armé qu'après réception du **nouveau `pdf_url`** ;
- une erreur remet explicitement le flag à false ;
- absence de `pdf_url` = aucune impression.

Le comportement suit désormais la même règle de fraîcheur que les autres documents.

## Permissions backend vérifiées

Le routeur partagé mappe actuellement :
- Ordonnance → `prescriptions` ;
- Certificat → `patients` ;
- Devis/Honoraires/Échéancier → `accounting` ;
- Libre/Lettre → `clinical` ;
- autres documents patient → `patients`.

`generate_document` applique aussi `assert_patient_access()`.

Aucun autre trou de permission partagé n'a été démontré dans le périmètre inspecté.

## Anomalies non bloquantes consignées pour T2

- code legacy interne `DocumentFactory.create_installment_plan()` devenu inatteignable par le `DocumentRequest` public : suppression physique à considérer ;
- listeners `beforeunload` locaux historiques dans certains formulaires encore redondants avec le Hub ;
- quelques props historiques du footer restent inutilisées ;
- la modale doublon du Hub pourrait recevoir une sémantique ARIA aussi explicite que la modale de navigation ;
- full responsive/browser n'a pas été réexécuté après les refactors T1.

## Gates différés

Non exécutés et non revendiqués :
- vrai `npm test` / `npm run build` full-project ;
- suite backend full-repo ;
- navigation réelle clic + query-param avec brouillons P1/P2/P3/P4/P6/P7 ;
- archive/preview/409/print sur l'application authentifiée ;
- browser 390 / 768 / desktop ;
- PDF cabinet réels ;
- merge / post-merge.

## Conclusion

Aucun P0/P1 transversal **connu et immédiatement exécutable dans cet environnement** ne reste après T1-F. Les restes identifiés sont reportés à T2 comme nettoyage/refonte finale ou gates runtime.