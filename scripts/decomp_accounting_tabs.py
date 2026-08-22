from pathlib import Path
import textwrap

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/components/AccountingTabs.tsx")
START = "      {/* TABS NAVIGATION */}\n"
END = "      {activeTab === 'history' ? (\n"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Accounting tabs sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "AccountingTabs" in text:
    raise SystemExit("AccountingTabs already extracted; refusing duplicate refactor")

start = text.index(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

required = ["setActiveTab", "treasuryData", "debtData", "Ghost Treasury Hub", "Visual Insights", "Impayés"]
if any(token not in body for token in required):
    raise SystemExit("Accounting tabs baseline changed; refusing automated refactor")

component = """import { AlertCircle, BarChart2, Calculator } from 'lucide-react';
import { cn } from '../../../utils/cn';

type AccountingTab = 'history' | 'treasury' | 'insights' | 'unpaid';

interface AccountingTabsProps {
  activeTab: AccountingTab;
  setActiveTab: (tab: AccountingTab) => void;
  treasuryData: any;
  debtData: { total_patients: number } | null;
}

export const AccountingTabs = ({ activeTab, setActiveTab, treasuryData, debtData }: AccountingTabsProps) => (
""" + textwrap.indent(body.replace("{/* TABS NAVIGATION */}\n", "", 1), "  ") + "\n);\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(component, encoding="utf-8")

replacement = """      <AccountingTabs
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        treasuryData={treasuryData}
        debtData={debtData}
      />

"""
updated = text[:start] + replacement + text[end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { AccountingTabs } from '../features/accounting/components/AccountingTabs';\n",
    1,
)
updated = updated.replace("  Calculator,\n", "", 1)
updated = updated.replace("  AlertCircle,\n", "", 1)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<AccountingTabs") != 1:
    raise SystemExit("AccountingTabs replacement missing")
if "Ghost Treasury Hub" in final or "Visual Insights" in final or "{/* TABS NAVIGATION */}" in final:
    raise SystemExit("Accounting tabs implementation unexpectedly remains in AccountingPage")

print("P0-A shell step prepared: accounting tabs extracted mechanically")
