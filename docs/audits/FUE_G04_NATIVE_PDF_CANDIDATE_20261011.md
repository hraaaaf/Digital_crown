# FUE-G04 — Candidat d'intégration PDF natif Windows (2026-10-11)

**Statut : DRAFT / NO-GO installation réelle.** Cette PR part exclusivement du `master@fa377f1ee05534cafbc26971f70f2e8ba8b792fd`. Elle n'emploie jamais l'ancienne PR de recherche #825 comme base de code produit.

## Goal et preuve disponible

Préparer l'assemblage vérifiable des DLL WeasyPrint 68.1 / Pango / GLib / Fontconfig et des polices DejaVu dans le **vrai** `DigitalCrown.spec`, sans insérer de binaire expérimental dans une release attestée.

Recherche amont prouvée uniquement en laboratoire : [run #38105734471](https://github.com/hraaaaf/Digital_crown/actions/runs/38105734471), SHA `2905c55fc5973e3ac7bbbb5a96b27f74fd971909`, ZIP artifact `11689756884` SHA256 `789f51dc023f70c5f7383594765f69cfe22d270bffbd44e8dbf8a057b38fac1d`. Manifest JSON des 40 packages MSYS2, 64 DLLs, 21 wheels : SHA256 `3e4389f86361c223e115c4a209e97f59a501798c64fce87e383fda1155beb82e`. EXE PyInstaller synthétique : PDF 5595 octets, police DejaVu locale, zéro erreur de configuration Fontconfig au démarrage, cinq DLL natives chargées dans le bundle. Ce PDF synthétique **n'est pas** un PDF métier produit par Digital Crown.

## Implémentation de la PR

- `backend/windows_native_pdf_bundle.py` rejette tout manifeste non épinglé, les archives du cache pacman incohérentes, les 64 DLLs absentes/altérées, les 40 packages source différents, les TTF/licence différents. Elle distingue explicitement le test `lab_only=True` d'une approbation release.
- `DigitalCrown.spec` conserve en tout premier le `verify_installable_release_directory` canonique, puis requiert les fichiers natifs vérifiés avant `Analysis`. Elle ajoute les DLL sous `pdf_native/bin`, les polices et Fontconfig sous `pdf_native/`, et le runtime hook fail-closed sous Windows.
- `backend/scripts/pyi_rth_windows_native_pdf.py` n'importe pas le backend SQLAlchemy à l'initialisation. Il contrôle le manifest approuvé, chaque DLL, les duplications éventuelles dans `_internal`, les TTF, et fixe `FONTCONFIG_FILE` et `WEASYPRINT_DLL_DIRECTORIES` avant le chargement des moteurs PDF.
- `backend/tests/test_windows_native_pdf_bundle.py` inclut des cas négatifs de manifeste malveillant, fichier altéré, collision de noms, respect du garde `INSTALLABLE_CERTIFIED`, et un test optionnel réel des 40 packages/64 DLLs sous GitHub Windows.
- `.github/workflows/fue-g04-native-pdf-candidate.yml` ne construit ni n'exécute l'application certifiée ; elle teste cette PR sur Linux et utilise un runner Windows jetable + le manifest officiel du labo, sans données patient.

## BLOCKER de release volontaire, à ne pas contourner

Les constantes `RELEASE_APPROVED_PROVENANCE_SHA256` dans le vérificateur de build et le hook runtime sont **`None`**. Une compilation Windows de cette PR est donc intentionnellement refusée, même avec une variable d'environnement mensongère. Le manifest déjà observé a le statut `EXPERIMENTAL_NOT_RELEASE_APPROVED` ; il ne doit jamais être rebaptisé « certifié » par un contrôle local.

La future étape requiert une provenance signée/revue pour les archives et DLL natives et une décision d'approbation explicite **dans le code re-certifié**, après une revue de licence et de fermeture PE ; pas une option en ligne de commande. Ensuite seulement : nouveaux tests Windows exact SHA de l'application entière, PDF métier BASIC/GOLD/ELITE, rapport PDF police/arabe/mise en page, certification `CODE_CERTIFIED` issue du nouveau `master`, composition `INSTALLABLE_CERTIFIED` avec assets scientifiques au même SHA, création d'installateur Inno depuis cette release, installation/lecture sur runner jetable, puis autorisation distincte avant installation Lenovo. L'ancien EXE signé `fa377f...` est **immuable** et ne prouve pas la nouvelle fonctionnalité.

## Revue adversariale — deux perspectives requises

**Perspective A — supply chain / fail-closed :** « Sur le HEAD exact, pourrais-je introduire une DLL différente via pacman, un chemin traversant, un doublon, une archive expirée, une variable d'environnement ou un manifest de laboratoire, et obtenir malgré tout un build approuvé ? Relever BLOCKER, MAJOR, faux positifs de CI et cas négatifs manquants. »

**Perspective B — packaging / clinique :** « Le même HEAD prouve-t-il réellement le chargement de la bonne police et des DLL dans le vrai DigitalCrown.exe, l'identité de la release et la génération des documents cliniques BASIC/GOLD/ELITE en isolement complet ? Distinguer synthétique et production, Fontconfig/PyInstaller hooks, préservation patient, régression Windows/mobile, et faux `VERIFIED`. »

**Gates :** invariant de branche/code immuable : requis ; tests négatifs du contrat : requis ; test d'inputs Windows : expérimental ; test réel DigitalCrown.exe et chaîne `CODE_CERTIFIED → INSTALLABLE_CERTIFIED` : REQUIS mais NON EXÉCUTÉ ; revue humaine et vérification sur machine cible : REQUIS plus tard. **Pas de merge, pas de Vercel, pas de Lenovo.**