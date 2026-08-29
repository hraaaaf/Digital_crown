from __future__ import annotations

import html
import json
import threading
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from backend.core.platform import PlatformAdapter, PlatformFileLock, get_platform_adapter


_RECOVERY_COPY = {
    "RUNTIME_NOT_READY": "Le service local n’est pas devenu disponible dans le délai attendu.",
    "RUNTIME_START_FAILED": "Le démarrage du service local s’est interrompu avant que Digital Crown soit prêt.",
    "INSTANCE_NOT_READY": "Une autre instance de Digital Crown est ouverte mais son service local ne répond pas.",
}


class RuntimeSupervisor:
    """Own single-instance, readiness and local recovery behavior for the packaged runtime."""

    def __init__(
        self,
        port: int,
        *,
        adapter: PlatformAdapter | None = None,
        runtime_dir: str | Path | None = None,
        request_timeout: float = 1.5,
    ) -> None:
        if not 1 <= int(port) <= 65535:
            raise ValueError("port must be between 1 and 65535")
        self.port = int(port)
        self.adapter = adapter or get_platform_adapter()
        self.runtime_dir = Path(runtime_dir) if runtime_dir is not None else self.adapter.runtime_dir()
        self.request_timeout = max(0.1, float(request_timeout))
        self._recovery_guard = threading.Lock()
        self._recovery_opened = False

    @property
    def ui_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.ui_url}/health"

    @property
    def lock_path(self) -> Path:
        return self.runtime_dir / "digitalcrown.instance.lock"

    @property
    def recovery_path(self) -> Path:
        return self.runtime_dir / "digitalcrown-recovery.html"

    @property
    def log_path(self) -> Path:
        return self.adapter.log_dir() / "digitalcrown.log"

    def try_acquire_instance(self) -> PlatformFileLock | None:
        return self.adapter.try_acquire_process_lock(self.lock_path)

    def is_ready(self) -> bool:
        request = Request(self.health_url, headers={"Cache-Control": "no-store"})
        try:
            with urlopen(request, timeout=self.request_timeout) as response:
                if getattr(response, "status", response.getcode()) != 200:
                    return False
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
            return False
        return payload.get("status") == "ok" and payload.get("db") == "ok"

    def wait_until_ready(self, *, timeout: float = 120.0, poll_interval: float = 0.25) -> bool:
        deadline = time.monotonic() + max(0.0, float(timeout))
        interval = max(0.01, float(poll_interval))
        while True:
            if self.is_ready():
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            time.sleep(min(interval, remaining))

    def _recovery_document(self, reason_code: str) -> str:
        reason = _RECOVERY_COPY.get(reason_code, _RECOVERY_COPY["RUNTIME_NOT_READY"])
        safe_code = html.escape(reason_code)
        safe_reason = html.escape(reason)
        safe_ui_url = html.escape(self.ui_url, quote=True)
        safe_log_path = html.escape(str(self.log_path))
        log_path_js = json.dumps(str(self.log_path))
        return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Digital Crown — Récupération</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f7f9fc;color:#0f172a}}
.page{{min-height:100vh;padding:28px 20px}} .brand{{max-width:1120px;margin:0 auto;font-size:14px;font-weight:900;color:#0b377f;letter-spacing:.02em}}
.wrap{{min-height:calc(100vh - 70px);display:grid;place-items:center}} .card{{width:min(720px,100%);background:#fff;border:1px solid #e2e8f0;border-radius:30px;box-shadow:0 24px 70px rgba(23,62,117,.08);padding:38px}}
.status{{display:inline-flex;align-items:center;gap:8px;background:#fff7ed;color:#9a3412;border:1px solid #fed7aa;border-radius:999px;padding:8px 12px;font-size:12px;font-weight:800}}
.dot{{width:8px;height:8px;border-radius:50%;background:#f59e0b}} h1{{font-size:34px;line-height:1.08;letter-spacing:-.035em;margin:18px 0 12px}} .lead{{font-size:17px;line-height:1.55;color:#475569;margin:0 0 24px}}
.safe{{display:flex;gap:12px;align-items:flex-start;border:1px solid #bbf7d0;background:#f0fdf4;border-radius:18px;padding:15px 16px;color:#166534;font-size:14px;font-weight:700}}
.check{{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;background:#dcfce7;flex:0 0 auto}} .diag{{margin-top:20px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:20px;padding:18px}}
.row{{display:flex;justify-content:space-between;gap:18px;padding:7px 0;font-size:13px}} .row span:first-child{{color:#64748b}} .row span:last-child{{font-weight:800;text-align:right;overflow-wrap:anywhere}}
.actions{{display:flex;gap:12px;margin-top:24px;flex-wrap:wrap}} .btn{{min-height:48px;border-radius:14px;padding:0 20px;border:0;font:inherit;font-size:14px;font-weight:800;display:inline-flex;align-items:center;justify-content:center;text-decoration:none;cursor:pointer}}
.primary{{background:#0f2b5b;color:#fff;box-shadow:0 10px 24px rgba(15,43,91,.14)}} .secondary{{background:#eef3f9;color:#334155}} .hint{{margin-top:18px;color:#64748b;font-size:12px;line-height:1.55}}
#copy-status{{margin-left:4px;color:#166534;font-weight:700}}
@media(max-width:600px){{.page{{padding:20px 14px}} .card{{padding:26px 20px;border-radius:24px}} h1{{font-size:27px}} .lead{{font-size:15px}} .row{{display:block}} .row span{{display:block;text-align:left!important}} .row span:last-child{{margin-top:4px}} .actions{{flex-direction:column}} .btn{{width:100%;min-height:50px}}}}
</style>
</head>
<body>
<main class="page">
<div class="brand">DIGITAL CROWN</div>
<div class="wrap">
<section class="card" aria-labelledby="recovery-title">
<div class="status"><span class="dot"></span>Démarrage interrompu</div>
<h1 id="recovery-title">Digital Crown n’a pas pu démarrer</h1>
<p class="lead">{safe_reason} Vous pouvez réessayer l’ouverture ou conserver le journal technique pour le diagnostic.</p>
<div class="safe"><span class="check">✓</span><span>Cet écran de récupération ne lance aucune restauration, suppression ni réinitialisation du cabinet.</span></div>
<div class="diag">
<div class="row"><span>État</span><span>Runtime local indisponible</span></div>
<div class="row"><span>Code</span><span>{safe_code}</span></div>
<div class="row"><span>Journal</span><span>{safe_log_path}</span></div>
</div>
<div class="actions">
<a class="btn primary" href="{safe_ui_url}">Réessayer l’ouverture</a>
<button class="btn secondary" type="button" id="copy-log">Copier le chemin du journal</button>
</div>
<p class="hint">Si le problème persiste, conservez le journal technique. Ne supprimez pas les données ou réglages du cabinet pour tenter de redémarrer.<span id="copy-status" role="status" aria-live="polite"></span></p>
</section>
</div>
</main>
<script>
(function(){{
  const value = {log_path_js};
  const button = document.getElementById('copy-log');
  const status = document.getElementById('copy-status');
  button.addEventListener('click', async function(){{
    let copied = false;
    try {{ await navigator.clipboard.writeText(value); copied = true; }} catch (_) {{}}
    if (!copied) {{
      const input = document.createElement('textarea'); input.value = value; input.setAttribute('readonly',''); input.style.position='fixed'; input.style.opacity='0'; document.body.appendChild(input); input.select();
      try {{ copied = document.execCommand('copy'); }} catch (_) {{ copied = false; }}
      input.remove();
    }}
    status.textContent = copied ? ' Chemin copié.' : ' Copie indisponible : sélectionnez le chemin ci-dessus.';
  }});
}})();
</script>
</body>
</html>"""

    def open_recovery_page(self, reason_code: str = "RUNTIME_NOT_READY") -> bool:
        """Persist and open a self-contained recovery page that does not require FastAPI."""
        with self._recovery_guard:
            if self._recovery_opened:
                return True
            self.adapter.atomic_write_text(self.recovery_path, self._recovery_document(reason_code))
            opened = bool(self.adapter.open_uri(self.recovery_path.resolve().as_uri()))
            if opened:
                self._recovery_opened = True
            return opened

    def claim_or_focus_existing(
        self,
        *,
        open_existing: bool = True,
        timeout: float = 120.0,
    ) -> PlatformFileLock | None:
        lock = self.try_acquire_instance()
        if lock is not None:
            return lock

        if not self.wait_until_ready(timeout=timeout):
            self.open_recovery_page("INSTANCE_NOT_READY")
            raise RuntimeError(
                "Une instance Digital Crown détient le verrou mais son runtime local ne devient pas prêt."
            )
        if open_existing:
            self.adapter.open_uri(self.ui_url)
        return None

    def open_ui_when_ready(self, *, timeout: float = 120.0) -> bool:
        if not self.wait_until_ready(timeout=timeout):
            self.open_recovery_page("RUNTIME_NOT_READY")
            return False
        return self.adapter.open_uri(self.ui_url)
