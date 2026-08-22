from pathlib import Path

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/hooks/useAccountingController.ts")
START = "export const AccountingPage = () => {\n"
END = "  const getStatusBadge = (item: HonoraireItem) => {\n"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Accounting controller sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "useAccountingController" in text:
    raise SystemExit("Accounting controller already extracted; refusing duplicate refactor")

start = text.index(START)
end = text.index(END, start)
controller_body = text[start + len(START):end]

required = [
    "const [items, setItems]",
    "const fetchHonoraires",
    "const fetchTreasury",
    "const handleExport",
    "const handleEncaisser",
    "const handleSendEmail",
    "const commitEdit",
    "const handlePatientClick",
    "const filteredItems",
]
if any(token not in controller_body for token in required):
    raise SystemExit("Accounting controller baseline changed; refusing automated refactor")

return_names = [
    "items", "loading", "exporting", "exportingCsv", "sendingEmail", "overdueData",
    "editingCell", "editingValue", "setEditingValue", "totalAmount", "totalCollected",
    "expandedGroups", "activeTab", "setActiveTab", "treasuryData", "loadingTreasury",
    "debtData", "loadingDebts", "loadingInsights", "financialData", "toggleGroup",
    "confirmDeleteId", "setConfirmDeleteId", "searchTerm", "setSearchTerm",
    "selectedAssurance", "setSelectedAssurance", "treasuryStatusFilter", "setTreasuryStatusFilter",
    "selectedMonth", "setSelectedMonth", "selectedYear", "setSelectedYear", "filterType",
    "setFilterType", "summaryByTitle", "months", "handleExport", "handleViewDocument",
    "handleDownloadDocument", "handleDelete", "confirmDelete", "handleEncaisser", "handleExportCsv",
    "handleSendEmail", "handleRelance", "startEdit", "cancelEdit", "commitEdit", "handlePatientClick",
    "filteredItems",
]

hook = """import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';
import type { HonoraireItem } from '../types';

export const useAccountingController = () => {
""" + controller_body + "\n  return {\n" + "\n".join(f"    {name}," for name in return_names) + "\n  };\n};\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(hook, encoding="utf-8")

replacement = """export const AccountingPage = () => {
  const {
""" + "\n".join(f"    {name}," for name in return_names) + "\n  } = useAccountingController();\n\n"

updated = text[:start] + replacement + text[end:]
updated = updated.replace("import React, { useState, useEffect, useCallback } from 'react';\n", "import React from 'react';\n", 1)
updated = updated.replace("import { Link, useSearchParams, useNavigate } from 'react-router-dom';\n", "import { Link } from 'react-router-dom';\n", 1)
updated = updated.replace("import toast from 'react-hot-toast';\n", "", 1)
updated = updated.replace("import { api } from '../services/api';\n\n", "", 1)
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { useAccountingController } from '../features/accounting/hooks/useAccountingController';\n",
    1,
)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("useAccountingController();") != 1:
    raise SystemExit("Accounting controller replacement missing")
if "const fetchHonoraires" in final or "const handleEncaisser" in final or "const commitEdit" in final:
    raise SystemExit("Controller implementation unexpectedly remains in AccountingPage")
if final.count(END) != 1:
    raise SystemExit("History rendering boundary changed unexpectedly")

print("P0-A controller step prepared: state/actions extracted mechanically")
