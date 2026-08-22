from __future__ import annotations

import ast
import re
from pathlib import Path

MODELS = Path("backend/models.py")
BASE_OUT = Path("backend/models_base.py")
PLATFORM_OUT = Path("backend/models_platform.py")
OPERATIONS_OUT = Path("backend/models_operations.py")
BOT_OUT = Path("backend/models_bot_settings.py")

EXPECTED_SIZE = 74684
EXPECTED_LINES = 1444

text = MODELS.read_text(encoding="utf-8")
if MODELS.stat().st_size != EXPECTED_SIZE or len(text.splitlines()) != EXPECTED_LINES:
    raise SystemExit(
        f"models.py baseline changed: {MODELS.stat().st_size} B / {len(text.splitlines())} lines; "
        f"expected {EXPECTED_SIZE} B / {EXPECTED_LINES} lines"
    )

for output in (BASE_OUT, PLATFORM_OUT, OPERATIONS_OUT, BOT_OUT):
    if output.exists():
        raise SystemExit(f"output already exists: {output}")


def pop_class(source: str, class_name: str) -> tuple[str, str]:
    tree = ast.parse(source)
    nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    if len(nodes) != 1:
        raise SystemExit(f"expected exactly one class {class_name}, got {len(nodes)}")
    node = nodes[0]
    if node.end_lineno is None:
        raise SystemExit(f"missing end_lineno for {class_name}")
    lines = source.splitlines(keepends=True)
    block = "".join(lines[node.lineno - 1 : node.end_lineno]).rstrip() + "\n"
    updated = "".join(lines[: node.lineno - 1] + lines[node.end_lineno :])
    return updated, block


# These enums belong exclusively to the domains being extracted but remain
# re-exported through backend.models for historical import compatibility.
text, agenda_mode_src = pop_class(text, "AgendaMode")
text, lab_job_status_src = pop_class(text, "LabJobStatus")
text, base_src = pop_class(text, "Base")

orm_import = "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship"
if text.count(orm_import) != 1:
    raise SystemExit("SQLAlchemy ORM import baseline changed")
text = text.replace(
    orm_import,
    "from sqlalchemy.orm import Mapped, mapped_column, relationship\nfrom backend.models_base import Base",
    1,
)

platform_marker = "# ==============================================================================\n# --- OBSERVABILITY : AUDIT LOGS ---"
operations_marker = "# ==============================================================================\n# LAB JOBS — SUIVI DES TRAVAUX PROTHÉTIQUES"
bot_marker = "# ==============================================================================\n# --- PHASE 6 : CROWN BOT SESSIONS (CHAT HISTORY) ---"
for marker in (platform_marker, operations_marker, bot_marker):
    if text.count(marker) != 1:
        raise SystemExit(f"domain marker changed or duplicated: {marker.splitlines()[-1]}")

platform_start = text.index(platform_marker)
operations_start = text.index(operations_marker, platform_start)
bot_start = text.index(bot_marker, operations_start)

platform_body = text[platform_start:operations_start].rstrip() + "\n"
operations_body = text[operations_start:bot_start].rstrip() + "\n"
bot_body = text[bot_start:].rstrip() + "\n"
main_body = text[:platform_start].rstrip() + "\n"

common_imports = """import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models_base import Base

"""

BASE_OUT.write_text(
    "from sqlalchemy.orm import DeclarativeBase\n\n" + base_src,
    encoding="utf-8",
)
PLATFORM_OUT.write_text(common_imports + platform_body, encoding="utf-8")
OPERATIONS_OUT.write_text(common_imports + lab_job_status_src + "\n" + operations_body, encoding="utf-8")
BOT_OUT.write_text(common_imports + agenda_mode_src + "\n" + bot_body, encoding="utf-8")


def class_names(source: str) -> list[str]:
    return re.findall(r"(?m)^class\s+([A-Za-z_]\w*)", source)


platform_names = class_names(platform_body)
operations_names = class_names(lab_job_status_src + "\n" + operations_body)
bot_names = class_names(agenda_mode_src + "\n" + bot_body)

if not {"AuditLog", "JourneyMilestone", "MilestoneType"}.issubset(platform_names):
    raise SystemExit("platform domain extraction incomplete")
if not {"LabJobStatus", "Lab", "LabJob", "StockItem", "PartnerOrder", "PartnerCatalogProduct"}.issubset(operations_names):
    raise SystemExit("operations domain extraction incomplete")
if not {"AgendaMode", "BotSession", "BotMessage", "BotPendingAction", "CabinetSettings", "AgendaException"}.issubset(bot_names):
    raise SystemExit("bot/settings domain extraction incomplete")


def import_block(module: str, names: list[str]) -> str:
    joined = ",\n    ".join(names)
    return f"from {module} import (\n    {joined},\n)\n"


facade = (
    "\n# ==============================================================================\n"
    "# P0-C — COMPATIBILITY FACADE FOR EXTRACTED MODEL DOMAINS\n"
    "# Definitions moved mechanically; historical backend.models imports remain valid.\n"
    "# ==============================================================================\n\n"
    + import_block("backend.models_platform", platform_names)
    + "\n"
    + import_block("backend.models_operations", operations_names)
    + "\n"
    + import_block("backend.models_bot_settings", bot_names)
)
MODELS.write_text(main_body + facade, encoding="utf-8")

final = MODELS.read_text(encoding="utf-8")
if "class Base(DeclarativeBase)" in final:
    raise SystemExit("Base definition still duplicated in backend.models")
if "DeclarativeBase" in final:
    raise SystemExit("DeclarativeBase leaked into compatibility facade")
if final.count("from backend.models_base import Base") != 1:
    raise SystemExit("backend.models must import exactly one shared Base")
for name in platform_names + operations_names + bot_names:
    if not re.search(rf"\b{name}\b", facade):
        raise SystemExit(f"historical export missing from facade: {name}")

size = MODELS.stat().st_size
lines = len(final.splitlines())
print(f"models.py after extraction: {size} bytes / {lines} lines")
if size >= 50000 or lines >= 1000:
    raise SystemExit(f"P0 exit criterion not met: {size} bytes / {lines} lines")

print(
    "P0-C extraction prepared mechanically: one shared Base, compatibility facade, "
    f"{len(platform_names)} platform + {len(operations_names)} operations + {len(bot_names)} bot/settings exports"
)
