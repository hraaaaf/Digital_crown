import uvicorn
import multiprocessing
import threading
import time
import webbrowser
import sys
import os
from backend.main import app


def _resolve_host_port():
    """Résout l'adresse d'écoute selon l'environnement.

    - CABINET_HOST / CABINET_PORT explicites : toujours prioritaires.
    - ENVIRONMENT=cabinet : 0.0.0.0 par défaut (la PWA mobile du cabinet doit
      pouvoir joindre le backend depuis le LAN — appairage QR, snapshot).
      Restreindre l'accès au sous-réseau du cabinet via le pare-feu Windows
      (cf. docs/CABINET_ONPREM_GUIDE.md §2).
    - Tout autre environnement (dev/local/test/production) : 127.0.0.1,
      défaut sûr — jamais d'exposition réseau implicite.
    """
    env = os.environ.get("ENVIRONMENT", "development").lower()
    default_host = "0.0.0.0" if env == "cabinet" else "127.0.0.1"
    host = os.environ.get("CABINET_HOST", default_host)
    port = int(os.environ.get("CABINET_PORT", "8005"))
    return host, port


def open_browser(port: int):
    time.sleep(2)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == '__main__':
    multiprocessing.freeze_support()

    host, port = _resolve_host_port()

    if getattr(sys, 'frozen', False):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")
