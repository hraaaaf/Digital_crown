"""
preflight_data_audit.py — Audit PRÉ-PRODUCTION strictement EN LECTURE SEULE.

Sprint 0 de la roadmap de redressement Digital Crown.

GARANTIES NON-NÉGOCIABLES :
  - Aucune écriture. La session est ouverte en `SET TRANSACTION READ ONLY` :
    toute tentative d'INSERT/UPDATE/DELETE/DDL lèverait une erreur Postgres.
  - Aucune suppression / réinitialisation / migration.
  - Ne touche ni aux IDs ni aux numéros de dossier.
  - Se contente de COMPTER, VÉRIFIER l'intégrité, et ÉCRIRE UN RAPPORT
    horodaté sur disque (jamais dans la base).

Le rapport sert de référence "count before" : on le rejoue après chaque
sprint pour prouver que count_before == count_after.

Usage :
    .\\venv\\Scripts\\python.exe scripts\\preflight_data_audit.py
"""
from __future__ import annotations

import os
import sys
import json
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# --- Chargement de la configuration réelle de l'application -----------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_ROOT, "backend", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("[FATAL] DATABASE_URL introuvable dans backend/.env", file=sys.stderr)
    sys.exit(2)

# Tables qui portent des données patients / cliniques sensibles : on les
# surveille de près (orphelins, cohérence tenant).
TENANT_COLUMN = "employer_id"

OUT_DIR = os.path.join(_ROOT, "artifacts", "preflight")


def _safe_count(conn, table: str) -> int | str:
    try:
        return conn.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"ERR:{type(exc).__name__}"


def main() -> int:
    started = datetime.now()
    engine = create_engine(DATABASE_URL)
    insp = inspect(engine)
    tables = sorted(insp.get_table_names())

    report: dict = {
        "generated_at": started.isoformat(timespec="seconds"),
        "database": DATABASE_URL.split("@")[-1],  # host/db, jamais les creds
        "table_count": len(tables),
        "counts": {},
        "fk_orphans": [],
        "tenant_checks": {},
        "uniqueness_checks": {},
        "warnings": [],
    }

    with engine.connect() as conn:
        # Verrou matériel : toute écriture échouera.
        conn.execute(text("SET TRANSACTION READ ONLY"))

        # 1) Comptage exhaustif ------------------------------------------------
        for t in tables:
            report["counts"][t] = _safe_count(conn, t)

        # 2) Orphelins de clés étrangères -------------------------------------
        for t in tables:
            for fk in insp.get_foreign_keys(t):
                ref_t = fk.get("referred_table")
                cols = fk.get("constrained_columns") or []
                ref_cols = fk.get("referred_columns") or []
                if not ref_t or not cols or len(cols) != len(ref_cols):
                    continue
                col, ref_col = cols[0], ref_cols[0]
                # On ignore les FK composites (rares ici) pour rester simple.
                if len(cols) != 1:
                    continue
                try:
                    q = text(
                        f'SELECT COUNT(*) FROM "{t}" c '
                        f'WHERE c."{col}" IS NOT NULL AND NOT EXISTS '
                        f'(SELECT 1 FROM "{ref_t}" p WHERE p."{ref_col}" = c."{col}")'
                    )
                    orphans = conn.execute(q).scalar()
                    if orphans:
                        report["fk_orphans"].append({
                            "table": t, "column": col,
                            "references": f"{ref_t}.{ref_col}",
                            "orphan_rows": orphans,
                        })
                except Exception as exc:
                    report["warnings"].append(
                        f"FK check skip {t}.{col} -> {ref_t}.{ref_col}: {type(exc).__name__}"
                    )

        # 3) Cohérence multi-tenant : employer_id NULL sur tables sensibles ----
        for t in tables:
            colnames = {c["name"] for c in insp.get_columns(t)}
            if TENANT_COLUMN in colnames:
                try:
                    null_tenant = conn.execute(text(
                        f'SELECT COUNT(*) FROM "{t}" WHERE "{TENANT_COLUMN}" IS NULL'
                    )).scalar()
                    report["tenant_checks"][t] = {"null_employer_id": null_tenant}
                except Exception as exc:
                    report["warnings"].append(f"tenant check skip {t}: {type(exc).__name__}")

        # 4) numero_dossier : collisions globales vs. multi-tenant -------------
        #    P0.4 — l'index unique est GLOBAL ; on mesure le risque réel.
        if "patients" in tables:
            pcols = {c["name"] for c in insp.get_columns("patients")}
            if "numero_dossier" in pcols:
                # doublons globaux (devraient être 0 vu l'index unique global)
                dup_global = conn.execute(text(
                    'SELECT COUNT(*) FROM ('
                    '  SELECT numero_dossier FROM patients '
                    '  WHERE numero_dossier IS NOT NULL '
                    '  GROUP BY numero_dossier HAVING COUNT(*) > 1'
                    ') x'
                )).scalar()
                # nb de numero_dossier identiques portés par des employer_id
                # DIFFÉRENTS : ce sont eux qui rendraient impossible le passage
                # à un index unique (numero_dossier, employer_id) SANS rien
                # casser. S'il vaut 0, la migration P0.4 est sûre.
                cross = conn.execute(text(
                    'SELECT COUNT(*) FROM ('
                    '  SELECT numero_dossier FROM patients '
                    '  WHERE numero_dossier IS NOT NULL '
                    '  GROUP BY numero_dossier '
                    '  HAVING COUNT(DISTINCT employer_id) > 1'
                    ') x'
                )).scalar()
                null_nd = conn.execute(text(
                    'SELECT COUNT(*) FROM patients WHERE numero_dossier IS NULL'
                )).scalar()
                report["uniqueness_checks"]["numero_dossier"] = {
                    "duplicates_global": dup_global,
                    "shared_across_employers": cross,
                    "null_values": null_nd,
                    "note": (
                        "shared_across_employers == 0 => migration vers index "
                        "unique composite (numero_dossier, employer_id) sans risque."
                    ),
                }

    # --- Écriture du rapport (hors base) ------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = started.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(OUT_DIR, f"preflight_audit_{stamp}.json")
    md_path = os.path.join(OUT_DIR, f"preflight_audit_{stamp}.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    _write_markdown(md_path, report)

    # --- Sortie console ------------------------------------------------------
    print("=" * 64)
    print("AUDIT PRÉ-PRODUCTION (LECTURE SEULE) — Digital Crown")
    print("=" * 64)
    print(f"Base       : {report['database']}")
    print(f"Tables     : {report['table_count']}")
    print(f"Patients   : {report['counts'].get('patients')}")
    print(f"RDV        : {report['counts'].get('appointments')}")
    print(f"Actes      : {report['counts'].get('actes')}")
    print(f"Dossiers   : {report['counts'].get('dossiers_cliniques')}")
    print(f"Documents  : {report['counts'].get('document_archives')}")
    print(f"Paiements  : {report['counts'].get('payments')}")
    print("-" * 64)
    print(f"Orphelins FK            : {len(report['fk_orphans'])} cas")
    nd = report["uniqueness_checks"].get("numero_dossier", {})
    print(f"numero_dossier doublons : {nd.get('duplicates_global')}")
    print(f"  partagés entre tenants: {nd.get('shared_across_employers')} "
          f"(0 = migration P0.4 sûre)")
    bad_tenant = {k: v for k, v in report["tenant_checks"].items()
                  if v.get("null_employer_id")}
    print(f"employer_id NULL        : {len(bad_tenant)} table(s) concernée(s)")
    if report["warnings"]:
        print(f"Avertissements          : {len(report['warnings'])}")
    print("-" * 64)
    print(f"Rapport JSON : {json_path}")
    print(f"Rapport MD   : {md_path}")
    print("=" * 64)
    return 0


def _write_markdown(path: str, r: dict) -> None:
    lines = [
        "# Audit pré-production — Digital Crown",
        "",
        f"- **Généré le** : {r['generated_at']}",
        f"- **Base** : `{r['database']}`",
        f"- **Tables** : {r['table_count']}",
        "- **Mode** : lecture seule (`SET TRANSACTION READ ONLY`) — aucune écriture",
        "",
        "## Comptes par table (référence \"before\")",
        "",
        "| Table | Lignes |",
        "|---|---|",
    ]
    for t, n in sorted(r["counts"].items()):
        lines.append(f"| {t} | {n} |")

    lines += ["", "## Intégrité référentielle (orphelins FK)", ""]
    if r["fk_orphans"]:
        lines += ["| Table | Colonne | Référence | Orphelins |", "|---|---|---|---|"]
        for o in r["fk_orphans"]:
            lines.append(
                f"| {o['table']} | {o['column']} | {o['references']} | {o['orphan_rows']} |"
            )
    else:
        lines.append("✅ Aucun orphelin de clé étrangère détecté.")

    lines += ["", "## Cohérence multi-tenant (`employer_id` NULL)", ""]
    bad = {k: v for k, v in r["tenant_checks"].items() if v.get("null_employer_id")}
    if bad:
        lines += ["| Table | employer_id NULL |", "|---|---|"]
        for t, v in bad.items():
            lines.append(f"| {t} | {v['null_employer_id']} |")
    else:
        lines.append("✅ Aucune ligne sans `employer_id` sur les tables concernées.")

    nd = r["uniqueness_checks"].get("numero_dossier")
    if nd:
        lines += [
            "", "## numero_dossier (P0.4 — collision multi-tenant)", "",
            f"- Doublons globaux : **{nd['duplicates_global']}**",
            f"- Partagés entre `employer_id` différents : **{nd['shared_across_employers']}**",
            f"- Valeurs NULL : {nd['null_values']}",
            "",
            f"> {nd['note']}",
        ]

    if r["warnings"]:
        lines += ["", "## Avertissements", ""]
        lines += [f"- {w}" for w in r["warnings"]]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
