from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"P11 contract failed: {path} missing {missing}")


def forbid(path: str, *needles: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    present = [needle for needle in needles if needle in text]
    if present:
        raise SystemExit(f"P11 contract failed: {path} contains forbidden {present}")


require(
    "backend/core/runtime_supervisor.py",
    "open_recovery_page",
    "RUNTIME_NOT_READY",
    "RUNTIME_START_FAILED",
    "INSTANCE_NOT_READY",
    "atomic_write_text",
    "recovery_path.resolve().as_uri()",
    "Cet écran de récupération ne lance aucune restauration, suppression ni réinitialisation du cabinet.",
    "Réessayer l’ouverture",
    "Copier le chemin du journal",
)
forbid(
    "backend/core/runtime_supervisor.py",
    "Vos données cabinet n’ont pas été modifiées",
)
require(
    "run.py",
    'supervisor.open_recovery_page("RUNTIME_START_FAILED")',
    "except RuntimeError:",
)
require(
    "frontend/src/components/DigitalCrownLoader.tsx",
    "Démarrage de Digital Crown...",
)
require(
    "frontend/src/features/admin/Settings/tabs/SecurityTab.tsx",
    'data-testid="restore-lifecycle"',
    "{index + 1} · {label}",
    "Analyse",
    "Secours",
    "Restauration",
    "Vérification",
    "Étape suivante : créer le point de secours",
    "Vérification du redémarrage",
    "Retour à l’état précédent",
    "min-h-[48px]",
)
forbid(
    "frontend/src/features/admin/Settings/tabs/SecurityTab.tsx",
    ".dcbundle",
    "Préflight validé",
    "Préflight bloqué",
    "Smoke check :",
    "Rollback :",
)
print("P11_LAUNCHER_RECOVERY_CONTRACT=SUCCESS")
