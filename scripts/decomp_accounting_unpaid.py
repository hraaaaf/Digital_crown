from pathlib import Path
import textwrap

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/components/UnpaidPanel.tsx")
START = "      ) : activeTab === 'unpaid' ? (\n"
END = "      ) : null}"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Unpaid panel sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "UnpaidPanel" in text:
    raise SystemExit("UnpaidPanel already extracted; refusing duplicate refactor")

start = text.index(START) + len(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

if "debtData" not in body or "loadingDebts" not in body or "CheckCheck" not in body:
    raise SystemExit("Unpaid panel baseline changed; refusing automated refactor")

component = """import { CheckCheck, Loader2 } from 'lucide-react';

interface DebtData {
  total_patients: number;
  total_amount: number;
  items: Array<{
    patient_id: number;
    nom: string;
    prenom: string;
    telephone: string;
    assurance: string;
    total_billed: number;
    total_paid: number;
    remaining_due: number;
  }>;
}

interface UnpaidPanelProps {
  debtData: DebtData | null;
  loadingDebts: boolean;
}

export const UnpaidPanel = ({ debtData, loadingDebts }: UnpaidPanelProps) => (
""" + textwrap.indent(body, "  ") + "\n);\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(component, encoding="utf-8")

replacement = "        <UnpaidPanel debtData={debtData} loadingDebts={loadingDebts} />\n"
updated = text[:start] + replacement + text[end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { UnpaidPanel } from '../features/accounting/components/UnpaidPanel';\n",
    1,
)
updated = updated.replace("  CheckCheck\n", "", 1)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<UnpaidPanel debtData={debtData} loadingDebts={loadingDebts} />") != 1:
    raise SystemExit("UnpaidPanel replacement missing")
if "CheckCheck" in final:
    raise SystemExit("Unpaid icon implementation unexpectedly remains in AccountingPage")

print("P0-A step 2 prepared: unpaid panel extracted mechanically")
