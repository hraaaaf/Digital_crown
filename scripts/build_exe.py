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

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    separator = ";" if os.name == "nt" else ":"

    # Cabinet package boundary: only runtime assets belong in the client.
    # Control-plane credentials, signing keys and .env files are forbidden.
    datas = [
        (str(FRONTEND_DIR / "dist"), "frontend/dist"),
        (str(BACKEND_DIR / "templates"), "backend/templates"),
        (str(BACKEND_DIR / "ai_models"), "backend/ai_models"),
        (str(BACKEND_DIR / "static"), "backend/static"),
    ]

    data_args = " ".join([f'--add-data "{src}{separator}{dest}"' for src, dest in datas])

    pyinstaller_cmd = (
        f'"{sys.executable}" -m PyInstaller --noconfirm --onedir --windowed '
        f'--name "DigitalCrown" {data_args} --hidden-import passlib.handlers.bcrypt '
        f'--collect-all fastapi --collect-all uvicorn "{BACKEND_DIR / "main.py"}"'
    )

    run_command(pyinstaller_cmd, cwd=str(PROJECT_ROOT))


def main():
    build_frontend()
    print("--- SKIPPING OBFUSCATION FOR TEST BUILD ---")
    build_executable()

    print("\n[BUILD SUCCESS]")
    print(f"L'exécutable se trouve dans : {PROJECT_ROOT / 'dist' / 'DigitalCrown'}")


if __name__ == "__main__":
    main()
