from pathlib import Path
import textwrap

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/components/AccountingHeader.tsx")
START = "      <header className=\"flex flex-col md:flex-row md:items-center justify-between gap-6 bg-card/80 backdrop-blur-xl border border-border-main p-8 rounded-[2.5rem] shadow-[0_8px_40px_rgba(0,0,0,0.04)]\">\n"
END = "      {/* SECTION INSIGHTS FINANCIERS */}\n"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Accounting header sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "AccountingHeader" in text:
    raise SystemExit("AccountingHeader already extracted; refusing duplicate refactor")

start = text.index(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

required = ["breakdown", "totalAmount", "totalCollected", "handleExportCsv", "handleExport", "Comptabilité & Honoraires"]
if any(token not in body for token in required):
    raise SystemExit("Accounting header baseline changed; refusing automated refactor")

component = """import { Download, FileSpreadsheet, Loader2, Receipt, TrendingUp } from 'lucide-react';

interface AccountingHeaderProps {
  breakdown: Record<string, number>;
  totalAmount: number;
  totalCollected: number;
  exportingCsv: boolean;
  exporting: boolean;
  itemsCount: number;
  handleExportCsv: () => void | Promise<void>;
  handleExport: () => void | Promise<void>;
}

export const AccountingHeader = ({
  breakdown,
  totalAmount,
  totalCollected,
  exportingCsv,
  exporting,
  itemsCount,
  handleExportCsv,
  handleExport,
}: AccountingHeaderProps) => (
""" + textwrap.indent(body, "  ") + "\n);\n"

component = component.replace("items.length", "itemsCount")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(component, encoding="utf-8")

replacement = """      <AccountingHeader
        breakdown={breakdown}
        totalAmount={totalAmount}
        totalCollected={totalCollected}
        exportingCsv={exportingCsv}
        exporting={exporting}
        itemsCount={items.length}
        handleExportCsv={handleExportCsv}
        handleExport={handleExport}
      />

"""
updated = text[:start] + replacement + text[end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { AccountingHeader } from '../features/accounting/components/AccountingHeader';\n",
    1,
)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<AccountingHeader") != 1:
    raise SystemExit("AccountingHeader replacement missing")
if "Comptabilité & Honoraires" in final:
    raise SystemExit("Header implementation unexpectedly remains in AccountingPage")

print("P0-A shell step prepared: accounting header extracted mechanically")
