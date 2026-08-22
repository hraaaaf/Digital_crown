from pathlib import Path
import textwrap

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/components/TreasuryPanel.tsx")
START = "      ) : activeTab === 'treasury' ? (\n"
END = "      ) : activeTab === 'insights' ? (\n"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Treasury panel sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "TreasuryPanel" in text:
    raise SystemExit("TreasuryPanel already extracted; refusing duplicate refactor")

start = text.index(START) + len(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

required = [
    "treasuryData",
    "overdueData",
    "loadingTreasury",
    "treasuryStatusFilter",
    "handleRelance",
    "handlePatientClick",
    "handleSendEmail",
    "handleViewDocument",
    "handleEncaisser",
]
if any(token not in body for token in required):
    raise SystemExit("Treasury panel baseline changed; refusing automated refactor")

component = """import { AlertTriangle, Loader2, Mail, Receipt, Search, Send } from 'lucide-react';
import { cn } from '../../../utils/cn';

interface TreasuryPanelProps {
  treasuryData: any;
  overdueData: any;
  loadingTreasury: boolean;
  searchTerm: string;
  setSearchTerm: (value: string) => void;
  treasuryStatusFilter: string;
  setTreasuryStatusFilter: (value: string) => void;
  sendingEmail: string | null;
  handleRelance: (itemId: string) => void | Promise<void>;
  handlePatientClick: (patientId: number) => void;
  handleSendEmail: (itemId: string | number) => void | Promise<void>;
  handleViewDocument: (url: string) => void | Promise<void>;
  handleEncaisser: (id: string | number) => void | Promise<void>;
}

export const TreasuryPanel = ({
  treasuryData,
  overdueData,
  loadingTreasury,
  searchTerm,
  setSearchTerm,
  treasuryStatusFilter,
  setTreasuryStatusFilter,
  sendingEmail,
  handleRelance,
  handlePatientClick,
  handleSendEmail,
  handleViewDocument,
  handleEncaisser,
}: TreasuryPanelProps) => (
""" + textwrap.indent(body, "  ") + "\n);\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(component, encoding="utf-8")

replacement = """        <TreasuryPanel
          treasuryData={treasuryData}
          overdueData={overdueData}
          loadingTreasury={loadingTreasury}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          treasuryStatusFilter={treasuryStatusFilter}
          setTreasuryStatusFilter={setTreasuryStatusFilter}
          sendingEmail={sendingEmail}
          handleRelance={handleRelance}
          handlePatientClick={handlePatientClick}
          handleSendEmail={handleSendEmail}
          handleViewDocument={handleViewDocument}
          handleEncaisser={handleEncaisser}
        />
"""
updated = text[:start] + replacement + text[end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { TreasuryPanel } from '../features/accounting/components/TreasuryPanel';\n",
    1,
)
updated = updated.replace("  AlertTriangle,\n", "", 1)
updated = updated.replace("  Send,\n", "", 1)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<TreasuryPanel") != 1:
    raise SystemExit("TreasuryPanel replacement missing")
if "AlertTriangle" in final or "<Send" in final:
    raise SystemExit("Treasury-only icon implementation unexpectedly remains in AccountingPage")

print("P0-A step 3 prepared: treasury panel extracted mechanically")
