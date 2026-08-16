# Document Studio — P6 Document Libre — audit de recertification

Date : 2026-08-16
Branche : `agent/p6-document-libre-recertification`
Base : P5 Suivi Paiement

## Verdict

**Engineering local convergé. Certification full-app/browser/PDF cabinet non revendiquée.**

P6 disposait déjà d'un socle historique durci. La recertification du code courant a identifié une régression de lifecycle sur la protection des brouillons : le Document Libre pouvait rester marqué sale après un archivage pourtant réussi. Le correctif P6 remet l'état propre uniquement après une réponse backend d'archive Libre réussie contenant un `pdf_url`; preview, échec, doublon/409 ou autre type de document ne nettoient pas le brouillon.

## Contrat courant vérifié

### Frontend
- titre et contenu obligatoires avant génération non-preview ;
- toolbar `button` non-submit ;
- A4/A5 et alignement sont transmis explicitement ;
- modifications de titre, contenu, destinataire, date/lieu, en-tête, format, alignement et toolbar marquent le brouillon sale ;
- `beforeunload` protège un brouillon Libre sale ;
- changement d'onglet depuis Libre exige confirmation avant abandon ;
- entrée/réouverture Libre établit une baseline propre ;
- archivage réussi nettoie le dirty-state uniquement si la réponse correspond à `POST /documents/generate?...archive=true`, payload `type=libre`, avec `pdf_url` non vide.

### Backend / PDF
- `/documents/generate` exige la permission `clinical` pour `libre`/`lettre` et vérifie l'accès patient ;
- `LibreGenerator._normalize_and_validate_libre_data()` refuse titre/contenu implicites ou vides ;
- limites : titre <= 200 caractères, contenu <= 100 000 caractères, destinataire <= 500, date/lieu <= 120 ;
- formats autorisés : A4/A5 ; alignements autorisés : left/center/right/justify ;
- markup inline limité aux balises de toolbar, autres contenus échappés ;
- nom de fichier nettoyé ;
- tables texte supportées avec wrapping et `repeatRows=1` ;
- archive documentaire seulement si `archive=true` et `preview=false` après génération PDF réussie.

## Régression P6 corrigée

### P6-R1 — dirty-state après archivage

**Avant** : `LibreForm` marquait bien les mutations et protégeait navigation/fermeture, mais aucun chemin observé ne remettait le flag Libre à propre après archive réussie.

**Après** :
- `LibreDirtyState.isSuccessfulLibreArchiveResponse()` centralise le contrat de succès ;
- `LibreForm` installe un interceptor de réponse Axios pendant son montage ;
- seul un vrai succès d'archive Libre avec nouveau `pdf_url` appelle `setLibreDirty(false)` ;
- interceptor et listener `beforeunload` sont retirés au démontage.

## Preuves locales exécutées

Policy P6 dirty/archive :
- `tsc --strict` : **PASS** ;
- assertions : **11/11 PASS** :
  - archive Libre payload objet ;
  - archive Libre payload JSON sérialisé ;
  - preview/non-archive rejeté ;
  - Devis rejeté ;
  - `pdf_url` absent rejeté ;
  - `pdf_url` vide rejeté ;
  - JSON invalide rejeté ;
  - mauvaise méthode HTTP rejetée ;
  - état initial propre ;
  - mutation sale ;
  - reset propre.

## Preuves statiques actuelles

Code courant relu :
- `frontend/src/features/admin/DocumentStudio/Forms/LibreForm.tsx` ;
- `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx` ;
- `frontend/src/features/admin/DocumentStudio/LibreDirtyState.ts` ;
- `frontend/src/features/admin/DocumentStudio/useDocumentGenerator.ts` ;
- `backend/routers/documents.py` ;
- `backend/schemas/documents.py` ;
- `backend/services/document_factory.py` ;
- `backend/services/generators/libre_gen.py`.

## Gates différés

Non exécutés dans cette session et donc non revendiqués :
- vrai `npm test` / `npm run build` full-project ;
- runtime authentifié : création, toolbar, tableau, A4/A5, alignements ;
- archive réelle puis réouverture ;
- échec doublon/409 et vérification du dirty-state ;
- impression fraîche ;
- PDF cabinet court/long/multipage avec branding/signature ;
- browser 390 / 768 / desktop, clavier/touch/focus ;
- ready review / merge / post-merge recertification.

## Conclusion

Aucun P0/P1 engineering connu ne reste après P6-R1 dans le périmètre statique/local disponible. Le chantier P6 peut être considéré **engineering local convergé**, avec certification applicative différée.