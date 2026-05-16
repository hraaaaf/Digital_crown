import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
BUILD_DIR = PROJECT_ROOT / "build_output"

def run_command(command, cwd=None):
    print(f"Executing: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        sys.exit(1)

def build_frontend():
    print("--- BUILDING FRONTEND ---")
    run_command("npm install", cwd=str(FRONTEND_DIR))
    run_command("npm run build", cwd=str(FRONTEND_DIR))

def build_executable():
    print("--- BUILDING EXECUTABLE (PyInstaller) ---")
    
    # Nettoyage des anciens builds
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    
    # Commande PyInstaller
    # --noconsole : Masque le terminal uvicorn
    # --add-data : Inclut les fichiers statiques et modèles
    
    separator = ";" if os.name == 'nt' else ":"
    
    # Ressources à inclure
    datas = [
        (str(FRONTEND_DIR / "dist"), "frontend/dist"),
        (str(BACKEND_DIR / "templates"), "backend/templates"),
        (str(BACKEND_DIR / "ai_models"), "backend/ai_models"),
    ]
    
    # Ajout optionnel des credentials Firebase
    creds_path = BACKEND_DIR / "core" / "firebase_creds.json"
    if creds_path.exists():
        datas.append((str(creds_path), "backend/core"))
    
    data_args = " ".join([f'--add-data "{src}{separator}{dest}"' for src, dest in datas])
    
    pyinstaller_cmd = (
        f'pyinstaller --noconfirm --onedir --windowed --name "DigitalCrown" '
        f'{data_args} '
        f'--hidden-import uvicorn.logging '
        f'--hidden-import uvicorn.loops '
        f'--hidden-import uvicorn.loops.auto '
        f'--hidden-import uvicorn.protocols '
        f'--hidden-import uvicorn.protocols.http '
        f'--hidden-import uvicorn.protocols.http.auto '
        f'--hidden-import uvicorn.protocols.websockets '
        f'--hidden-import uvicorn.protocols.websockets.auto '
        f'--hidden-import uvicorn.lifespan '
        f'--hidden-import uvicorn.lifespan.on '
        f'--hidden-import fastapi.staticfiles '
        f'"{BACKEND_DIR / "main.py"}"'
    )
    
    run_command(pyinstaller_cmd, cwd=str(PROJECT_ROOT))

def main():
    # 1. Préparation du Frontend
    build_frontend()
    
    # 2. Obfuscation (Optionnel pour le premier test)
    # Note : Nécessite PyArmor installé. Commande type : pyarmor obfuscate ...
    print("--- SKIPPING OBFUSCATION FOR TEST BUILD ---")
    
    # 3. Création de l'EXE
    build_executable()
    
    print("\n✅ BUILD TERMINE !")
    print(f"L'exécutable se trouve dans : {PROJECT_ROOT / 'dist' / 'DigitalCrown'}")

if __name__ == "__main__":
    main()
