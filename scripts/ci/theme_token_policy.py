"""Digital Crown application-wide semantic theme token guard.

Reads the whole tracked React/CSS source tree. Records legacy palette debt.
Fails closed on NEW violations relative to the review base; existing debt is
reported, never misrepresented as a global clean result.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "frontend" / "src"
OUT = ROOT / "artifacts" / "theme-token-audit" / "report.json"
PALETTES = (
    "slate|gray|zinc|neutral|stone|blue|indigo|emerald|green|amber|orange|"
    "rose|red|cyan|teal|purple|pink|yellow|lime|violet|fuchsia|sky|white|black"
)
FIXED = re.compile(
    r"(?<![\w/-])(?:[\w-]+:)*(?:bg|text|border|ring|outline|fill|stroke|"
    r"from|via|to|decoration|placeholder|accent|caret|shadow)-(?:"
    + PALETTES + r")(?:-\d{2,3})?(?:/\d+)?(?![\w/-])"
)
HEX = re.compile(
    r"(?<![\w#])(?:color|background(?:Color|-color)?|borderColor|-color)\s*"
    r"[:=]\s*['\"]?\s*#[0-9a-fA-F]{3,8}\b"
)
CSS_COLOR = re.compile(r"(?<![\w-])(?:rgb|rgba|hsl|hsla)\(\s*\d")
ARBITRARY = re.compile(
    r"(?<![\w/-])(?:[\w-]+:)*(?:bg|text|border|ring|outline|fill|stroke|"
    r"from|via|to)-\[(?:#[0-9a-fA-F]{3,8}|rgba?\([^]]+|hsla?\([^]]+)\]"
)
SOURCE_EXTS = (".tsx", ".jsx", ".ts", ".js", ".css")
TEST_ENDINGS = (
    ".test.ts", ".test.tsx", ".test.js", ".test.jsx",
    ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx",
)
# Design-token definitions are the one permitted palette source.
ALLOWED = {"frontend/src/index.css"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def production_source(path: str) -> bool:
    return (path.startswith("frontend/src/") and path.endswith(SOURCE_EXTS)
            and not path.endswith(TEST_ENDINGS) and path not in ALLOWED
            and "/test/" not in path and "/__tests__/" not in path
            and not Path(path).name.endswith("Lab.tsx"))


def source_at(path: str, ref: str | None) -> str:
    try:
        if ref is None:
            return (ROOT / path).read_text(encoding="utf-8")
        return git("show", ref + ":" + path)
    except (subprocess.CalledProcessError, FileNotFoundError, UnicodeDecodeError):
        return ""


def signatures(src: str) -> Counter[str]:
    # Exact token counts protect against "replacing" a new hardcoded brand
    # class with a legacy class at the same count.
    found = Counter(FIXED.findall(src))
    found.update("literal:" + m.group(0) for m in HEX.finditer(src))
    found.update("function:" + m.group(0) for m in CSS_COLOR.finditer(src))
    found.update("arbitrary:" + m.group(0) for m in ARBITRARY.finditer(src))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="Verified PR base SHA")
    parser.add_argument("--strict", action="store_true",
                        help="Require zero debt everywhere (not currently met)")
    options = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", options.base):
        raise SystemExit("REFUSED: require immutable base commit SHA")
    git("cat-file", "-e", options.base + "^{commit}")
    files = sorted(p for p in git("ls-files", "frontend/src").splitlines()
                   if production_source(p))
    all_violations: list[dict] = []
    new_violations: list[dict] = []
    for p in files:
        tokens = signatures(source_at(p, None))
        if not tokens:
            continue
        all_violations.append({
            "file": p, "total": sum(tokens.values()),
            "tokens": dict(tokens.most_common(12))
        })
        baseline = signatures(source_at(p, options.base))
        delta = tokens - baseline
        if delta:
            new_violations.append({"file": p, "introduced": dict(delta)})
    all_violations.sort(key=lambda x: x["total"], reverse=True)
    by_area: dict[str, dict[str, int]] = {}
    for row in all_violations:
        parts = Path(row["file"]).parts
        area = parts[2] + ("/" + parts[3] if len(parts) > 3 and parts[2] == "features" else "")
        counts = by_area.setdefault(area, {"files": 0, "instances": 0})
        counts["files"] += 1
        counts["instances"] += row["total"]
    areas = [{"area": area, **counts} for area, counts in by_area.items()]
    areas.sort(key=lambda item: item["instances"], reverse=True)
    tokens_css = (SOURCE / "index.css").read_text(encoding="utf-8")
    for token in (
        "--color-primary", "--color-on-primary", "--color-card",
        "--color-background", "--color-text-main", "--color-text-muted",
        "--color-border-main", "--color-warning-surface",
        "--color-success-surface", "--color-danger-surface",
        "--color-info-surface",
    ):
        if token + ":" not in tokens_css:
            raise SystemExit("MISSING THEME ROLE: " + token)
    for theme in ("emerald", "rose", "ocean", "graphite",
                  "prestige", "dark", "high-contrast"):
        if "[data-theme='" + theme + "']" not in tokens_css:
            raise SystemExit("MISSING THEME: " + theme)
    result = {
        "schema": "DIGITAL_CROWN_APP_WIDE_THEME_TOKEN_GUARD_V1",
        "baseCommit": options.base,
        "headCommit": git("rev-parse", "HEAD").strip(),
        "productionFilesScanned": len(files),
        "filesWithLegacyDebt": len(all_violations),
        "legacyInstances": sum(v["total"] for v in all_violations),
        "newViolations": new_violations,
        "remainingLegacyByArea": areas,
        "globalComplianceProven": not all_violations,
        "largestLegacySources": all_violations[:60],
        "policy": "New UI palette/literal color prohibited. Legacy debt OPEN.",
        "scope": "All tracked frontend/src production TS/TSX/JS/JSX/CSS, excluding tests and test labs.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("THEME_TOKEN_AUDIT", json.dumps({
        key: result[key] for key in ("productionFilesScanned", "filesWithLegacyDebt",
                                    "legacyInstances", "newViolations")
    }, ensure_ascii=False))
    if new_violations:
        print("THEME_TOKEN_NEW_VIOLATIONS_REFUSED")
        return 1
    if options.strict and all_violations:
        print("THEME_TOKEN_FULL_COMPLIANCE_NOT_CERTIFIED")
        return 1
    print("THEME_TOKEN_NO_NEW_DEBT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
