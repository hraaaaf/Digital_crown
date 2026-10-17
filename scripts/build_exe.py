"""SEC-P0: retired executable builder, intentionally fail-closed.

This script used an unverified packaging route capable of shipping local
Firebase Admin credentials. It is not the Digital Crown certified release path.

Use the project's certified release pipeline and its INSTALLABLE_CERTIFIED
gate instead. Never ship an arbitrary PyInstaller output to a cabinet.
"""


_DISABLED_MESSAGE = (
    "SEC-P0: legacy builder disabled for safety. "
    "Use the DigitalCrown.spec certified release pipeline, obtain "
    "INSTALLABLE_CERTIFIED evidence and explicit human installation approval."
)


def build_executable() -> None:
    """Refuse legacy packaging, including when called by another script."""
    raise RuntimeError(_DISABLED_MESSAGE)


def main() -> None:
    """Refuse execution before any npm, PyInstaller or filesystem side effect."""
    raise SystemExit(_DISABLED_MESSAGE)


if __name__ == "__main__":
    main()
