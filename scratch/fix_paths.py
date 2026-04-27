import os
import re

files = [
    "backend/services/generators/ordonnance_gen.py",
    "backend/services/generators/certificat_gen.py",
    "backend/services/generators/libre_gen.py",
    "backend/services/generators/accounting_gen.py"
]

for f in files:
    if not os.path.exists(f): continue
    
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remplacer tout le bloc de chemin relatif par un retour simple du filepath
    pattern = r'relative_path\s*=\s*filepath\[filepath\.find\("static"\):\]\s*if\s*"static"\s*in\s*filepath\s*else\s*filepath\s*return\s*relative_path\.replace\("\\\\",\s*"/"\)'
    content = re.sub(pattern, 'return filepath.replace("\\\\", "/")', content)
    
    # DeuxiÃ¨me pattern possible (Accounting)
    pattern2 = r'return\s*filepath\[filepath\.find\("static"\):\]\.replace\("\\\\",\s*"/"\)'
    content = re.sub(pattern2, 'return filepath.replace("\\\\", "/")', content)
    
    with open(f, 'w', encoding='utf-8', newline='\n') as file:
        file.write(content)
    print(f"Fixed {f}")
