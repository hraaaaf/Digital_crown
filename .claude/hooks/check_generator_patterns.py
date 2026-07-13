#!/usr/bin/env python3
"""PostToolUse hook — après édition d'un générateur PDF
(backend/services/generators/*.py), vérifie que les patterns déjà connus
comme bugués dans ce projet n'existent pas ailleurs dans le même dossier.

Purement informatif : n'affecte jamais le code retour (exit 0 toujours),
n'écrit rien, ne bloque rien. Sert seulement à rappeler qu'un même bug a
déjà été trouvé et corrigé dans plusieurs générateurs quasi-identiques
(ex: doc_date=None -> NoneType.strftime, commit a41b54f, présent
initialement dans 4 fichiers sur 14).
"""
import json
import re
import sys
from pathlib import Path

GENERATORS_DIR = Path(__file__).resolve().parents[2] / "backend" / "services" / "generators"

# (description, regex du pattern buggé) — une réapparition indique une
# régression ou un copier-coller de l'ancien code dans un nouveau générateur.
KNOWN_BAD_PATTERNS = [
    (
        "doc_date via getattr(data, 'doc_date', date.today()) sans gérer le "
        "cas où l'attribut existe mais vaut None -> crash NoneType.strftime "
        "(cf. commit a41b54f). Utiliser : "
        "getattr(data, 'doc_date', None) or date.today()",
        re.compile(r"getattr\(\s*data\s*,\s*['\"]doc_date['\"]\s*,\s*date\.today\(\)\s*\)"),
    ),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    edited_path = str(
        payload.get("tool_response", {}).get("filePath")
        or payload.get("tool_input", {}).get("file_path")
        or ""
    ).replace("\\", "/")

    if "generators" not in edited_path or not GENERATORS_DIR.is_dir():
        return 0

    warnings = []
    for py_file in sorted(GENERATORS_DIR.glob("*.py")):
        try:
            text = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for description, pattern in KNOWN_BAD_PATTERNS:
            if pattern.search(text):
                warnings.append(f"  - {py_file.name}: {description}")

    if warnings:
        print("[check_generator_patterns] Pattern(s) déjà bugué(s) ailleurs détecté(s) :")
        for w in warnings:
            print(w)
        print("(Avertissement informatif seulement — rien n'est bloqué.)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
