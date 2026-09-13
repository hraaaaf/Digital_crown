import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import '../../../../index.css';
import { DrugRow } from './DrugRow';
import type { DrugItem } from './prescriptionTypes';

const initialDrugs: DrugItem[] = [
  {
    id: 101,
    name: 'PARACÉTAMOL',
    dosage: '1G',
    forme: 'COMPRIMÉS',
    posologie: '1 comprimé, 3 fois par jour pendant 7 jours, après les repas.',
    type: 'MEDICAMENT',
    quantite: 1,
    non_substituable: false,
  },
  {
    id: 102,
    name: 'IBUPROFÈNE',
    dosage: '400MG',
    forme: 'COMPRIMÉS',
    posologie: '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.',
    type: 'MEDICAMENT',
    quantite: 1,
    non_substituable: false,
  },
];

function Fixture() {
  const [drugs, setDrugs] = useState(initialDrugs);

  const updateDrug = (id: number, field: keyof DrugItem, value: unknown) => {
    setDrugs(previous => previous.map(drug => drug.id === id ? { ...drug, [field]: value } : drug));
  };

  const removeDrug = (id: number) => setDrugs(previous => previous.filter(drug => drug.id !== id));

  const moveDrug = (id: number, direction: 'up' | 'down') => {
    setDrugs(previous => {
      const index = previous.findIndex(drug => drug.id === id);
      const target = direction === 'up' ? index - 1 : index + 1;
      if (index < 0 || target < 0 || target >= previous.length) return previous;
      const next = [...previous];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  };

  return (
    <main className="min-h-screen bg-background px-3 py-5 text-text-main sm:px-6 sm:py-8">
      <section className="mx-auto w-full max-w-5xl space-y-4" data-composer-visual-fixture>
        <header className="rounded-2xl border border-border-main bg-glass-bg/70 px-4 py-3 shadow-sm backdrop-blur-xl">
          <div className="text-[10px] font-black uppercase tracking-[0.18em] text-text-muted">Ordonnance</div>
          <h1 className="mt-1 text-lg font-black text-text-main">Prescription Composer</h1>
          <p className="mt-1 text-xs font-semibold text-text-muted">Fixture visuel du composant réel DrugRow</p>
        </header>

        {drugs.map((drug, idx) => (
          <DrugRow
            key={drug.id}
            drug={drug}
            idx={idx}
            drugsCount={drugs.length}
            assessment={null}
            validationErrors={[]}
            forcedDrugs={[]}
            activeSearchId={null}
            suggestions={{ medications: [], dosages: [], posologies: [] }}
            highlightedIdx={-1}
            medChecks={{}}
            onUpdateDrug={updateDrug}
            onRemoveDrug={removeDrug}
            onMove={moveDrug}
            onSearch={(id, field, value) => updateDrug(id, field as keyof DrugItem, value)}
            onKeyDown={() => undefined}
            onApplySuggestion={(id, field, value) => updateDrug(id, field as keyof DrugItem, value)}
            onFormeOpen={() => undefined}
            onForceAllergy={() => undefined}
            onToggleType={(id, type) => updateDrug(id, 'type', type)}
          />
        ))}
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Fixture />
  </React.StrictMode>,
);
