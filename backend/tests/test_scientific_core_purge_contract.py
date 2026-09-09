from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PANORAMIC_DELETE_CANDIDATES = {
    "backend/services/panoramic_ai_advisor.py": (
        "panoramic_ai_advisor",
        "PanoramicAIAdvisor",
    ),
    "backend/services/panoramic_expert_engine.py": (
        "panoramic_expert_engine",
        "PanoramicExpertEngine",
    ),
    "backend/services/panoramic_vision_service.py": (
        "panoramic_vision_service",
        "panoramic_vision_engine",
        "PanoramicVisionEngine",
    ),
}

CEPHALO_DELETE_CANDIDATES = {
    "backend/services/ai_advisor.py": (
        "backend.services.ai_advisor",
        "ai_advisor",
        "AIAdvisor",
    ),
}

RUNTIME_TEXT_SUFFIXES = {
    ".py",
    ".pyi",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".txt",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".sh",
    ".ps1",
    ".html",
}


def test_dormant_treatment_plan_engine_is_removed():
    assert not (ROOT / "backend/services/treatment_plan_engine.py").exists()

    for relative in (
        "backend/services/elite_manager.py",
        "backend/routers/ia.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "treatment_plan_engine" not in source
        assert "TreatmentPlanEngine" not in source


def test_patient_plan_generation_remains_fail_closed():
    source = (ROOT / "backend/services/elite_manager.py").read_text(encoding="utf-8")
    assert "Génération automatique du plan de traitement désactivée" in source


def test_panoramic_delete_candidates_are_removed():
    for relative in PANORAMIC_DELETE_CANDIDATES:
        assert not (ROOT / relative).exists(), relative


def test_panoramic_delete_candidates_have_no_external_runtime_consumers():
    """Prove removed wrappers have no references in executable/runtime text."""
    excluded = {"backend/tests/test_scientific_core_purge_contract.py"}
    forbidden_tokens = {
        token
        for tokens in PANORAMIC_DELETE_CANDIDATES.values()
        for token in tokens
    }

    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in RUNTIME_TEXT_SUFFIXES:
            continue

        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded or "/node_modules/" in f"/{relative}/":
            continue

        source = path.read_text(encoding="utf-8", errors="ignore")
        matched = sorted(token for token in forbidden_tokens if token in source)
        if matched:
            offenders.append((relative, matched))

    assert not offenders, f"Removed panoramic wrappers still have runtime references: {offenders}"


def test_cephalo_advisor_wrapper_is_removed_and_unreachable():
    """The retired cephalo advisor must not reappear or remain imported by runtime code."""
    for relative in CEPHALO_DELETE_CANDIDATES:
        assert not (ROOT / relative).exists(), relative

    excluded = {
        "backend/tests/test_scientific_core_purge_contract.py",
        "docs/ORTHO_SCIENTIFIC_CORE_AUDIT.md",
        "docs/SCIENTIFIC_CORE_REBUILD_ROADMAP.md",
    }
    forbidden_tokens = {
        token
        for tokens in CEPHALO_DELETE_CANDIDATES.values()
        for token in tokens
    }

    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in RUNTIME_TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded or "/node_modules/" in f"/{relative}/":
            continue
        source = path.read_text(encoding="utf-8", errors="ignore")
        matched = sorted(token for token in forbidden_tokens if token in source)
        if matched:
            offenders.append((relative, matched))

    assert not offenders, f"Removed cephalo advisor still has runtime references: {offenders}"
