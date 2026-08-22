import type { GroupedItem, HonoraireItem } from './types';

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
