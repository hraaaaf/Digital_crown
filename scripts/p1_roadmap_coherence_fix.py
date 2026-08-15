from pathlib import Path

p = Path('ROADMAP_ORDONNANCE_P1.md')
text = p.read_text(encoding='utf-8')

text = text.replace('- [ ] CI exacte post-merge sur `master` verte', '- [x] CI exacte post-merge sur `master` verte')
text = text.replace('- [ ] `DOCUMENT_STUDIO_ROADMAP.md` mis à jour', '- [x] `DOCUMENT_STUDIO_ROADMAP.md` mis à jour')
text = text.replace('- [ ] `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` mis à jour', '- [x] `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md` mis à jour')
text = text.replace('- [ ] cohérence documentaire finale vérifiée', '- [x] cohérence documentaire finale vérifiée')

start = text.index('## 10. État de reprise')
end = text.index('## 12. Règles critiques de reprise')
replacement = '''## 10. État de reprise\n\n### Terminé côté engineering / UX visuelle\n- R1→R7 engineering ;\n- responsive 1440 / 768 / 390 recertifié ;\n- fidélité glass historique vérifiée puis hiérarchie premium restaurée ;\n- PR #43 mergée ;\n- CI post-merge `31898590067` — **SUCCESS** ;\n- documentation canonique P1 réalignée via PR #44 ;\n- cohérence documentaire finale vérifiée.\n\n### Gates explicitement séparés et toujours ouverts\n- interaction authentifiée dans l’application locale réelle du cabinet ;\n- certification clinique/pharmacologique humaine.\n\nCes gates ne remettent pas en cause la fermeture engineering / UX visuelle de P1, mais interdisent toute formulation du type « production ready » ou « cliniquement certifié ».\n\n---\n\n## 11. Prochaine action exacte\n\n**Aucune action engineering / UX visuelle P1 restante.**\n\nLa prochaine action P1 ne peut être que l’un des gates séparés ci-dessus : exécution authentifiée dans l’application locale réelle, ou revue clinique/pharmacologique qualifiée.\n\n---\n\n'''
text = text[:start] + replacement + text[end:]

text = text.replace('CI push exacte du merge sur `master` : run `31898590067` — **à vérifier avant fermeture complète**.', 'CI push exacte du merge sur `master` : run `31898590067` — **SUCCESS**.')

p.write_text(text, encoding='utf-8')
