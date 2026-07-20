"""Validate the Claude Code scientific-agent infrastructure.

This validator checks static governance assets only. It never imports the
application, opens a database, reads patient media, or runs a migration.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

EXPECTED_AGENTS = {
    "scientific-architect",
    "pharmacology-engineer",
    "clinical-diagnosis-engineer",
    "cephalometry-engineer",
    "radiology-engineer",
    "scientific-test-engineer",
    "scientific-reviewer",
}
EXPECTED_SKILLS = {
    "scientific-source-research",
    "implement-scientific-rule",
    "audit-prescription-flow",
    "audit-clinical-diagnosis-flow",
    "implement-cephalo-measurement",
    "validate-cephalo-pipeline",
    "implement-radiology-finding",
    "audit-panoramic-report-pipeline",
    "generate-scientific-golden-tests",
    "scientific-database-migration",
    "review-scientific-pull-request",
}
AUDIT_SKILLS = {
    "scientific-source-research",
    "audit-prescription-flow",
    "audit-clinical-diagnosis-flow",
    "validate-cephalo-pipeline",
    "audit-panoramic-report-pipeline",
    "review-scientific-pull-request",
}
IMPLEMENTATION_SKILLS = {
    "implement-scientific-rule",
    "implement-cephalo-measurement",
    "implement-radiology-finding",
}
STATUSES = {
    "candidate",
    "needs_review",
    "approved-by-clinician",
    "rejected",
    "superseded",
    "license-blocked",
    "insufficient-evidence",
    "conflicting-sources",
    "license_uncertain",
}
AGENT_SECTIONS = {
    "Role",
    "When to invoke",
    "Read first",
    "Scope",
    "Out of scope",
    "Mandatory workflow",
    "Source policy",
    "Forbidden actions",
    "Testing requirements",
    "Deliverables",
    "Handoff",
    "Definition of done",
}
SKILL_SECTIONS = {"Trigger", "Workflow", "Output contract"}
FORBIDDEN_MARKERS = (r"\bbypassPermissions\b", r"\bTODO\b", r"\bTBD\b")
SECRET_PATTERNS = (
    r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
)
PATIENT_PATTERNS = (
    r"(?i)patient\s*:\s*[A-Z][a-z]+\s+[A-Z][a-z]+",
    r"\b(?:\+212|0)[5-7]\d{8}\b",
)


def _frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    try:
        _, raw, body = text.split("---", 2)
    except ValueError as exc:
        raise ValueError(f"{path}: malformed frontmatter") from exc
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: frontmatter is not a mapping")
    return data, body


def _check_forbidden(path: Path, text: str, errors: list[str]) -> None:
    for pattern in FORBIDDEN_MARKERS + SECRET_PATTERNS + PATIENT_PATTERNS:
        if re.search(pattern, text):
            errors.append(f"{path}: forbidden or sensitive pattern: {pattern}")


def _validate_agents(root: Path, errors: list[str]) -> None:
    agent_dir = root / ".claude" / "agents"
    found = {p.stem for p in agent_dir.glob("*.md") if p.stem in EXPECTED_AGENTS}
    if found != EXPECTED_AGENTS:
        errors.append(f"agents mismatch: missing={sorted(EXPECTED_AGENTS-found)}")
    seen: set[str] = set()
    for name in EXPECTED_AGENTS:
        path = agent_dir / f"{name}.md"
        if not path.exists():
            continue
        try:
            meta, body = _frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if meta.get("name") != name or name in seen:
            errors.append(f"{path}: invalid or duplicate name")
        seen.add(name)
        for key in ("description", "model", "effort", "tools", "permissionMode", "skills"):
            if key not in meta:
                errors.append(f"{path}: missing frontmatter field {key}")
        for section in AGENT_SECTIONS:
            if f"## {section}" not in body and f"# {section}" not in body:
                errors.append(f"{path}: missing section {section}")
        if name in {"scientific-architect", "scientific-reviewer"}:
            tools = str(meta.get("tools", ""))
            if any(tool in tools for tool in ("Edit", "Write")) or meta.get("permissionMode") != "plan":
                errors.append(f"{path}: read-only agent is writable")
        _check_forbidden(path, path.read_text(encoding="utf-8"), errors)


def _validate_skills(root: Path, errors: list[str]) -> None:
    skill_dir = root / ".claude" / "skills"
    found = {p.name for p in skill_dir.iterdir() if p.is_dir() and p.name in EXPECTED_SKILLS}
    if found != EXPECTED_SKILLS:
        errors.append(f"skills mismatch: missing={sorted(EXPECTED_SKILLS-found)}")
    for name in EXPECTED_SKILLS:
        path = skill_dir / name / "SKILL.md"
        eval_path = skill_dir / name / "evals" / "evals.json"
        if not path.exists() or not eval_path.exists():
            errors.append(f"{name}: missing SKILL.md or evals.json")
            continue
        try:
            meta, body = _frontmatter(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if meta.get("name") != name or not meta.get("description"):
            errors.append(f"{path}: invalid name/description")
        for section in SKILL_SECTIONS:
            present = (("## Workflow" in body or "## Read-only workflow" in body) if section == "Workflow" else f"## {section}" in body)
            if not present:
                errors.append(f"{path}: missing section {section}")
        tools = str(meta.get("allowed-tools", ""))
        if name in AUDIT_SKILLS and any(tool in tools for tool in ("Edit", "Write")):
            errors.append(f"{path}: audit/research/review skill allows writes")
        if name in AUDIT_SKILLS and meta.get("context") != "fork":
            errors.append(f"{path}: audit/research/review skill must use context fork")
        if name in {"implement-scientific-rule", "implement-cephalo-measurement"}:
            lower = body.lower()
            required = ("approved", "conflict", "unit", "population", "license")
            if any(word not in lower for word in required):
                errors.append(f"{path}: incomplete implementation blocking gates")
        if name == "implement-radiology-finding":
            lower = body.lower()
            required = ("approved", "conflict", "license", "modality", "localization")
            if any(word not in lower for word in required):
                errors.append(f"{path}: incomplete implementation blocking gates")
        if name == "scientific-database-migration" and meta.get("disable-model-invocation") is not True:
            errors.append(f"{path}: migration skill must be user-invoked only")
        _check_forbidden(path, path.read_text(encoding="utf-8"), errors)
        try:
            ev = json.loads(eval_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{eval_path}: invalid JSON: {exc}")
            continue
        expected_counts = {
            "positive_triggers": 3,
            "negative_triggers": 3,
            "ambiguous_cases": 2,
            "collision_cases": 2,
            "dangerous_under_specified": 1,
        }
        if ev.get("skill") != name or ev.get("version") != "2.0":
            errors.append(f"{eval_path}: wrong skill or version")
        for key, minimum in expected_counts.items():
            values = ev.get(key)
            if not isinstance(values, list) or len(values) < minimum:
                errors.append(f"{eval_path}: {key} requires at least {minimum} cases")
            elif any(not isinstance(case, dict) or not case.get("prompt") or not case.get("expected") for case in values):
                errors.append(f"{eval_path}: malformed {key} case")
        _check_forbidden(eval_path, eval_path.read_text(encoding="utf-8"), errors)


def _validate_schemas_and_registry(root: Path, errors: list[str]) -> None:
    docs = root / "docs" / "scientific-ai"
    schemas = sorted((docs / "templates").glob("*.schema.yaml"))
    if len(schemas) != 7:
        errors.append(f"expected 7 schemas, found {len(schemas)}")
    for path in schemas:
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid YAML: {exc}")
            continue
        if not isinstance(doc, dict) or doc.get("schema_version") != "2.0":
            errors.append(f"{path}: schema version must be 2.0")
            continue
        if doc.get("type") != "object" or not isinstance(doc.get("required"), list) or not isinstance(doc.get("properties"), dict):
            errors.append(f"{path}: incomplete machine-readable schema")
        _check_forbidden(path, path.read_text(encoding="utf-8"), errors)

    registry_path = docs / "SOURCE_REGISTRY.yaml"
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{registry_path}: invalid YAML: {exc}")
        return
    sources = registry.get("sources") if isinstance(registry, dict) else None
    if registry.get("schema_version") != "2.0" or not isinstance(sources, list):
        errors.append(f"{registry_path}: invalid registry structure")
        return
    ids: set[str] = set()
    required = {
        "source_id", "domain", "title", "organization", "publication_date",
        "accessed_at", "source_type", "jurisdiction", "population", "url",
        "license", "evidence_level", "claims_supported", "limitations",
        "implementation_targets", "status",
    }
    for record in sources:
        if not isinstance(record, dict) or not required.issubset(record):
            errors.append(f"{registry_path}: source missing required fields")
            continue
        source_id = record["source_id"]
        if source_id in ids:
            errors.append(f"{registry_path}: duplicate source_id {source_id}")
        ids.add(source_id)
        if record["status"] not in STATUSES:
            errors.append(f"{registry_path}: invalid status for {source_id}")
        if record["status"] == "approved-by-clinician":
            if not record.get("reviewed_by") or not record.get("reviewed_at") or record.get("approval_evidence") in (None, "", "none; candidate research record only"):
                errors.append(f"{registry_path}: untraceable clinical approval for {source_id}")
        if not str(record.get("url", "")).startswith("https://"):
            errors.append(f"{registry_path}: non-HTTPS source URL for {source_id}")
    _check_forbidden(registry_path, registry_path.read_text(encoding="utf-8"), errors)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    _validate_agents(root, errors)
    _validate_skills(root, errors)
    _validate_schemas_and_registry(root, errors)
    required_docs = {
        "README.md", "GOVERNANCE.md", "REPO_MAP.md", "SOURCE_POLICY.md",
        "SOURCE_REGISTRY.yaml", "AGENT_HANDOFF_PROTOCOL.md",
        "REVIEW_BACKLOG_V2.md",
    }
    docs = root / "docs" / "scientific-ai"
    for name in required_docs:
        if not (docs / name).exists():
            errors.append(f"missing required document {name}")
    review_names = {
        "AGENT_REVIEW.md", "SKILL_REVIEW.md", "PHARMACOLOGY_REVIEW.md",
        "CLINICAL_DIAGNOSIS_REVIEW.md", "CEPHALOMETRY_REVIEW.md",
        "RADIOLOGY_REVIEW.md",
    }
    for name in review_names:
        if not (docs / "reviews" / name).exists():
            errors.append(f"missing review {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("SCIENTIFIC_AGENT_SYSTEM_LOCKED_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

