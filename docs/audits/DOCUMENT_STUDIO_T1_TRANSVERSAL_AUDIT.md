# Document Studio — T1 Audit transversal premium

Date : 2026-08-16
Branche : `agent/t1-document-studio-transversal-audit`
Base : P7 Compagnon Diagnostique

## Verdict

**Engineering transversal local convergé sur les défauts critiques identifiés. Full build/runtime/browser non revendiqués.**

T1 couvre les mécanismes partagés P1→P7 : navigation, dirty-state, preview/archive/print, contrats financiers partagés, branches mortes et UI commune.

## T1-A — navigation et dirty-state centralisés

### Findings corrigés

- `documentTab` URL pouvait appeler `setActiveTab()` directement et contourner les gardes ;
- Certificat n'avait pas de dirty-state partagé ;
- la date commune pouvait changer Ordonnance/Certificat/Libre sans dirty-state ;
- les gardes étaient fragmentées entre Hub, Tabs et formulaires.

### Corrections

- `DocumentNavigationPolicy.ts` devient la décision commune clic/query-param ;
- `StudioTabs` devient un déclencheur pur ;
- dirty sources : accounting / prescription / certificate / libre / diagnostic ;
- Devis→Honoraires conserve sa confirmation explicite ;
- query param synchronisé après navigation validée et restauré après annulation ;
- `CertificateDirtyState.ts` ajouté ;
- date d'émission marque Ordonnance/Certificat/Libre dirty ;
- `beforeunload` commun au Hub.

### Preuve locale rejouée

- `tsc --strict` : PASS ;
- navigation policy : **9/9 PASS**.

## T1-B — archive-success explicite

### Finding corrigé

Un simple changement de `pdfUrl` n'est pas une preuve d'archive et pouvait théoriquement nettoyer un brouillon après un 409 puis une preview.

### Correction

`useDocumentGenerator` émet `ArchiveSuccessSignal` uniquement après :
- réponse backend réussie ;
- `pdf_url` présent ;
- `archive=true` ;
- `preview=false`.

`DocumentHub` nettoie alors uniquement la source concernée :
- Devis/Honoraires : nouvelle baseline accounting ;
- Ordonnance : dirty false ;
- Certificat : dirty false ;
- Document Libre : dirty false.

Preview, erreur, 409 annulé et P5 preview-only n'émettent aucun signal d'archive.

## T1-C — P5 impression / stale print

### Findings corrigés

- la modale P5 promettait un archivage alors que le flux utilise `/installments/generate-preview` ;
- `pendingPrint` pouvait être armé avant le nouveau PDF et imprimer un aperçu précédent.

### Corrections

- texte explicite : impression P5 = PDF du brouillon, sans enregistrement du plan ;
- sauvegarde réelle uniquement via `POST /installments/` ;
- confirmation P5 appelle `archive=false` ;
- `pendingPrint` est remis à false avant génération puis armé seulement après réception du nouveau `pdf_url` ;
- erreur ou absence de PDF = aucune impression.

## T1-D — second moteur Échéancier désactivé

### Finding corrigé

`/documents/generate` gardait un chemin historique `echeancier` capable de construire/persister un plan depuis un dictionnaire brut, en parallèle du contrat P5.

### Correction

Le `DocumentRequest` réellement exporté par `backend.schemas` hérite du contrat P4 durci et appelle `assert_document_installment_path_is_disabled()` avant validation. `type=echeancier` est donc refusé sur `/documents/generate`.

Chemins P5 autoritaires :
- `POST /installments/` : persistance ;
- `POST /installments/generate-preview` : PDF brouillon ;
- `/installments/...` : suivi / encaissement.

### Preuve locale rejouée

Helper de désactivation : **4/4 PASS**.

## T1-E — suppression ghost AI Document Studio

### Finding corrigé

Le Studio conservait une branche cachée `ai`, une UI `Lancer Analyse IA` et l'appel `/patients/{id}/ai-diagnostic`.

### Correction

- `ai` retiré de `HubDocumentType` et des valeurs URL admises ;
- états/callbacks AI retirés du footer/hook ;
- appel `ai-diagnostic` et événements `ai-generation-*` retirés du Document Studio.

Cette correction aligne ce périmètre avec la doctrine ZERO LLM. Elle ne constitue pas à elle seule une recertification full-repo ZERO LLM.

## T1-F — bypass Header supprimés

### Finding corrigé

Les boutons `Actualiser` et `Quitter` appelaient directement `window.location.reload()` / `window.history.back()` et contournaient le Hub.

### Correction

- suppression des deux raccourcis internes ;
- le navigateur reste disponible et passe par le `beforeunload` commun en présence d'un brouillon ;
- toggle odontogramme : `type="button"` + `aria-pressed`.

## Permissions backend vérifiées

Le routeur partagé applique une permission par type puis `assert_patient_access()` avant génération. Aucun contournement backend partagé n'a été démontré dans le périmètre T1.

## Dette non bloquante pour T2

- listeners/interceptors locaux Ordonnance/Libre encore redondants avec la frontière centrale ; ils restent fail-closed actuellement ;
- `DocumentFactory.create_installment_plan()` legacy est devenu inatteignable par le `DocumentRequest` public et peut être supprimé physiquement ;
- quelques props historiques du footer restent inutilisées ;
- LivePreview peut recevoir une sémantique modal/focus encore plus explicite ;
- full responsive/browser non rejoué après T1.

## Gates différés

Non exécutés et non revendiqués :
- vrai `npm test` / `npm run build` full-project ;
- suite backend full-repo ;
- navigation réelle multi-pages avec brouillons ;
- archive/preview/409/print authentifiés ;
- browser 390 / 768 / desktop ;
- PDF cabinet réels ;
- merge / post-merge des PR stackées.

## Conclusion

Aucun P0/P1 transversal **connu et immédiatement exécutable dans l'environnement actuel** ne reste après T1. T2 peut commencer sur ce head pour nettoyage final et recertification globale disponible.
