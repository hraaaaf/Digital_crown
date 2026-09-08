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


def test_panoramic_delete_candidates_have_no_external_runtime_consumers():
    """Prove DELETE candidates are not referenced outside their own deletion set."""
    excluded = set(PANORAMIC_DELETE_CANDIDATES)
    excluded.add("backend/tests/test_scientific_core_purge_contract.py")
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

    assert not offenders, f"Panoramic DELETE candidates still have runtime consumers: {offenders}"
