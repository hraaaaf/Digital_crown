from pathlib import Path
import textwrap

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting/components/InsightsPanel.tsx")
START = "      ) : activeTab === 'insights' ? (\n"
END = "      ) : activeTab === 'unpaid' ? (\n"
IMPORT_ANCHOR = "import { groupByPatientDate } from '../features/accounting/utils';\n"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("Insights panel sentinels changed; refusing automated refactor")
if IMPORT_ANCHOR not in text:
    raise SystemExit("AccountingPage import baseline changed; refusing automated refactor")
if "InsightsPanel" in text:
    raise SystemExit("InsightsPanel already extracted; refusing duplicate refactor")

start = text.index(START) + len(START)
end = text.index(END, start)
body = textwrap.dedent(text[start:end]).rstrip()

if "loadingInsights" not in body or "financialData" not in body or "<BarChart" not in body:
    raise SystemExit("Insights panel baseline changed; refusing automated refactor")

component = """import { EliteGhostLoader } from '../../../components/EliteGhostLoader';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface InsightsPanelProps {
  loadingInsights: boolean;
  financialData: any;
}

export const InsightsPanel = ({ loadingInsights, financialData }: InsightsPanelProps) => (
""" + textwrap.indent(body, "  ") + "\n);\n"

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(component, encoding="utf-8")

replacement = "        <InsightsPanel loadingInsights={loadingInsights} financialData={financialData} />\n"
updated = text[:start] + replacement + text[end:]
updated = updated.replace(
    IMPORT_ANCHOR,
    IMPORT_ANCHOR + "import { InsightsPanel } from '../features/accounting/components/InsightsPanel';\n",
    1,
)
updated = updated.replace("  BarChart, \n", "", 1)
updated = updated.replace("  Bar,\n", "", 1)
PAGE.write_text(updated, encoding="utf-8")

final = PAGE.read_text(encoding="utf-8")
if final.count("<InsightsPanel loadingInsights={loadingInsights} financialData={financialData} />") != 1:
    raise SystemExit("InsightsPanel replacement missing")
if "<BarChart" in final:
    raise SystemExit("Insights chart implementation unexpectedly remains in AccountingPage")

print("P0-A step 4 prepared: insights panel extracted mechanically")
