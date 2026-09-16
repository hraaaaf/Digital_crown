from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / ".claude" / "rules" / "execution-scoring-verification.md"
VISUAL = ROOT / ".claude" / "rules" / "visual-closeout-human-validation.md"
PR_TEMPLATE = ROOT / ".github" / "pull_request_template.md"
AGENTS = ROOT / "AGENTS.md"
CLAUDE = ROOT / "CLAUDE.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_execution_scoring_policy_keeps_required_thresholds_and_minimum_rule():
    text = _read(POLICY)

    required_fragments = (
        "RETAINED_SCORE = min(EXECUTION_SCORE, ADVERSARIAL_SCORE)",
        "Jamais de moyenne",
        "> 0.5",
        "10/10",
        "9.4/10",
        "9.5/10",
        "7.9/10",
        "6.9/10",
        "5.9/10",
        "7.5/10",
        "le plus restrictif gagne",
        "Une moyenne interne est interdite",
        "RETAINED_SCORE >= 9.0/10",
        "Perfection Pass finale",
        "BLOCKED",
    )

    for fragment in required_fragments:
        assert fragment in text, fragment


def test_primary_agent_guides_require_the_scoring_policy():
    policy_ref = ".claude/rules/execution-scoring-verification.md"

    for path in (AGENTS, CLAUDE):
        text = _read(path)
        assert policy_ref in text, path
        assert "EXECUTION_SCORE" in text, path
        assert "ADVERSARIAL_SCORE" in text, path
        assert "VERIFIED" in text, path
        assert "Perfection Pass" in text, path


def test_visual_closeout_keeps_target_render_cap_and_human_gate():
    text = _read(VISUAL)

    assert "execution-scoring-verification.md" in text
    assert "Target ↔ Render" in text
    assert "7.5/10" in text
    assert "hard cap" in text
    assert "BLOQUÉ HUMAIN — VALIDATION CAPTURES" in text
    assert "validation humaine explicite" in text


def test_github_pr_template_exposes_scoring_and_verification_gates():
    text = _read(PR_TEMPLATE)

    required_fragments = (
        "Goal",
        "Succès observable",
        "Preuve",
        "EXECUTION_SCORE /10",
        "ADVERSARIAL_SCORE /10",
        "RETAINED_SCORE /10",
        "min(EXECUTION_SCORE, ADVERSARIAL_SCORE)",
        "> 0.5",
        "9.4/10",
        "9.5/10",
        "7.9/10",
        "6.9/10",
        "5.9/10",
        "7.5/10",
        "Target ↔ Render",
        "RETAINED_SCORE >= 9.0/10",
        "Perfection Pass finale",
        "VERIFIED",
        "BLOCKED",
    )

    for fragment in required_fragments:
        assert fragment in text, fragment
