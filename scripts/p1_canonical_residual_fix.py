from pathlib import Path

replacements = {
    Path('DOCUMENT_STUDIO_ROADMAP.md'): [
        ('CI push post-merge : run `31898590067` — à vérifier avant fermeture documentaire complète.', 'CI push post-merge : run `31898590067` — **SUCCESS**.'),
    ],
    Path('docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md'): [
        ('CI push exacte du merge `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8` : run `31898590067` — à vérifier avant closeout documentaire final.', 'CI push exacte du merge `91a2c2efd781fd736ebdc96e9de4f5e3c73c82c8` : run `31898590067` — **SUCCESS**.'),
    ],
}

for path, reps in replacements.items():
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in reps:
        if old not in text:
            raise SystemExit(f'missing expected marker in {path}: {old}')
        text = text.replace(old, new)
    if text == original:
        raise SystemExit(f'no change produced for {path}')
    path.write_text(text, encoding='utf-8')
