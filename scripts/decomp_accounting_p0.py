from pathlib import Path

PAGE = Path("frontend/src/pages/AccountingPage.tsx")
OUT = Path("frontend/src/features/accounting")
START = "// --- COMPOSANTS INTERNES ---"
END = "export const AccountingPage = () => {"

text = PAGE.read_text(encoding="utf-8")

if text.count(START) != 1 or text.count(END) != 1:
    raise SystemExit("AccountingPage sentinels changed; refusing automated refactor")
if "interface HonoraireItem" not in text or "const groupByPatientDate" not in text:
    raise SystemExit("AccountingPage baseline changed; refusing automated refactor")

start = text.index(START)
end = text.index(END)
replacement = (
    "import type { HonoraireItem } from '../features/accounting/types';\n"
    "import { groupByPatientDate } from '../features/accounting/utils';\n\n"
)
PAGE.write_text(text[:start] + replacement + text[end:], encoding="utf-8")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "types.ts").write_text("""export interface HonoraireItem {
  id: number | string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  title: string;
  amount: number;
  file_url: string;
  payment_status?: string;
  is_collected?: boolean;
  validated_by?: string;
}

export interface GroupedItem {
  key: string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  total: number;
  notes: HonoraireItem[];
}
""", encoding="utf-8")

(OUT / "utils.ts").write_text("""import type { GroupedItem, HonoraireItem } from './types';

export const groupByPatientDate = (items: HonoraireItem[]): GroupedItem[] => {
  const map = new Map<string, GroupedItem>();
  items.forEach(item => {
    const dateKey = new Date(item.date).toLocaleDateString('fr-FR');
    const key = `${item.patient_id}_${dateKey}`;
    if (!map.has(key)) {
      map.set(key, {
        key,
        patient_id: item.patient_id,
        patient_name: item.patient_name,
        assurance: item.assurance,
        date: item.date,
        total: 0,
        notes: [],
      });
    }
    const group = map.get(key)!;
    group.total += item.amount;
    group.notes.push(item);
  });
  return Array.from(map.values());
};
""", encoding="utf-8")

updated = PAGE.read_text(encoding="utf-8")
if "interface HonoraireItem" in updated or "const groupByPatientDate" in updated:
    raise SystemExit("Extraction incomplete")
if "from '../features/accounting/types'" not in updated or "from '../features/accounting/utils'" not in updated:
    raise SystemExit("Extraction imports missing")

print("P0-A step 1 prepared: types + pure grouping helper extracted")
