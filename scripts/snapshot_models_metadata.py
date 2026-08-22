from __future__ import annotations

import enum
import importlib
import json
from typing import Any

from sqlalchemy.orm import configure_mappers

SATELLITES = (
    "backend.models_catalog_plan",
    "backend.models_clinical_p3",
    "backend.models_imaging_p4",
    "backend.models_identity_p4",
)


def _default(value: Any) -> Any:
    if value is None:
        return None
    arg = getattr(value, "arg", value)
    if callable(arg):
        return {"callable": getattr(arg, "__qualname__", getattr(arg, "__name__", type(arg).__name__))}
    return str(arg)


def _constraint(constraint: Any) -> dict[str, Any]:
    columns = sorted(column.name for column in getattr(constraint, "columns", ()))
    elements = sorted(getattr(element, "target_fullname", str(element)) for element in getattr(constraint, "elements", ()))
    sqltext = getattr(constraint, "sqltext", None)
    return {
        "type": type(constraint).__name__,
        "name": constraint.name,
        "columns": columns,
        "targets": elements,
        "sqltext": str(sqltext) if sqltext is not None else None,
    }


def _relationship(rel: Any) -> dict[str, Any]:
    order_by = rel.order_by
    if order_by is False or order_by is None:
        order = []
    else:
        try:
            order = [str(item) for item in order_by]
        except TypeError:
            order = [str(order_by)]
    return {
        "key": rel.key,
        "target": rel.mapper.class_.__name__,
        "direction": rel.direction.name,
        "uselist": rel.uselist,
        "back_populates": rel.back_populates,
        "cascade": sorted(str(item) for item in rel.cascade),
        "secondary": rel.secondary.name if rel.secondary is not None else None,
        "local_columns": sorted(column.name for column in rel.local_columns),
        "remote_side": sorted(column.name for column in rel.remote_side),
        "order_by": order,
        "lazy": str(rel.lazy),
        "viewonly": rel.viewonly,
        "passive_deletes": str(rel.passive_deletes),
        "single_parent": rel.single_parent,
    }


def snapshot() -> dict[str, Any]:
    models = importlib.import_module("backend.models")
    for module_name in SATELLITES:
        importlib.import_module(module_name)

    configure_mappers()
    Base = models.Base

    tables: dict[str, Any] = {}
    for table_name, table in sorted(Base.metadata.tables.items()):
        columns = []
        for column in table.columns:
            foreign_keys = sorted(
                ({
                    "target": fk.target_fullname,
                    "ondelete": fk.ondelete,
                    "onupdate": fk.onupdate,
                } for fk in column.foreign_keys),
                key=lambda item: (item["target"], item["ondelete"] or "", item["onupdate"] or ""),
            )
            columns.append({
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "primary_key": column.primary_key,
                "unique": column.unique,
                "index": column.index,
                "default": _default(column.default),
                "onupdate": _default(column.onupdate),
                "server_default": _default(column.server_default),
                "foreign_keys": foreign_keys,
            })

        constraints = sorted(
            (_constraint(constraint) for constraint in table.constraints),
            key=lambda item: (item["type"], item["name"] or "", item["columns"], item["targets"]),
        )
        indexes = sorted(
            ({
                "name": index.name,
                "unique": index.unique,
                "expressions": [str(expr) for expr in index.expressions],
            } for index in table.indexes),
            key=lambda item: (item["name"] or "", item["unique"], item["expressions"]),
        )
        tables[table_name] = {
            "columns": columns,
            "constraints": constraints,
            "indexes": indexes,
        }

    mappers = []
    for mapper in Base.registry.mappers:
        mappers.append({
            "class": mapper.class_.__name__,
            "table": mapper.local_table.name,
            "relationships": sorted((_relationship(rel) for rel in mapper.relationships), key=lambda item: item["key"]),
        })
    mappers.sort(key=lambda item: (item["class"], item["table"]))

    exports = []
    for name, value in vars(models).items():
        if name.startswith("_") or not isinstance(value, type):
            continue
        try:
            is_model = issubclass(value, Base)
        except TypeError:
            is_model = False
        try:
            is_enum = issubclass(value, enum.Enum)
        except TypeError:
            is_enum = False
        if is_model or is_enum:
            exports.append(name)

    return {
        "tables": tables,
        "mappers": mappers,
        "exports": sorted(exports),
        "table_count": len(tables),
        "mapper_count": len(mappers),
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False, sort_keys=True, indent=2))
