#!/usr/bin/env python3
"""
Script de nettoyage des caractères encodés dans CephaloWorkspace.tsx
"""
import sys
import codecs

def fix_file(filepath):
    # Lecture avec remplacement d'erreurs
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # Décodage avec gestion des erreurs
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        content = raw.decode('utf-8', errors='replace')
    
    # Table de remplacement des caractères corrompus
    replacements = {
        '\u00e2\u201d\u00e2': '─',  # â"€
        '\u00e2\u20ac': '→',        # â†
        '\u00e2\u2013': '▲',        # â–²
        '\u00e2\u2013': '▼',        # â–¼
        '\u00c3\u00a9': 'é',       # Ã©
        '\u00c3\u00a8': 'è',       # Ã¨
        '\u00c3\u00a7': 'ç',       # Ã§
        '\u00c3 ': 'à',            # Ã 
        '\u00c3\u00b4': 'ô',       # Ã´
        '\u00c3\u00aa': 'ê',       # Ãª
        '\u00c3\u00a2': 'â',       # Ã¢
        '\u00c3\u00ae': 'î',       # Ã®
        '\u00c3\u00af': 'ï',       # Ã¯
        '\u00c3\u00bc': 'ü',       # Ã¼
        '\u00c3\u2030': 'É',       # Ã‰
        '\u00c3\u02c6': 'È',       # Ãˆ
        '\u00c3\u20ac': 'À',       # Ã€
        '\u00c3\u201d': 'Ô',       # Ã"
        '\u00e2\u201d': '',        # â"
        '\u00e2\u201c': '',        # âœ
        '\u00e2\u20ac': '→',       # â†
        '\u00c2\u00b0': '°',       # Â°
        '\u00c2': '',              # Â
    }
    
    # Application des remplacements
    count = 0
    for old, new in replacements.items():
        if old in content:
            count += content.count(old)
            content = content.replace(old, new)
    
    # Écriture
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier nettoyé : {count} remplacements effectués")
    return True

if __name__ == "__main__":
    filepath = "frontend/src/features/ortho/CephaloWorkspace.tsx"
    if fix_file(filepath):
        print(f"✅ {filepath} corrigé avec succès")
        sys.exit(0)
    else:
        print(f"❌ Erreur lors de la correction")
        sys.exit(1)
