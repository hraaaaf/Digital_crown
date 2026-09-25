import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { PrescriptionForm } from './Forms/PrescriptionForm';

afterEach(() => cleanup());

const drug = {
  id: 1,
  name: 'AMOXICILLINE',
  dosage: '1g',
  forme: 'Gélules (Bte de 12)',
  posologie: '1 matin et soir',
  type: 'MEDICAMENT' as const,
};

function renderForm(overrides: Record<string, unknown> = {}) {
  const props = {
    drugs: [drug],
    onAddDrug: vi.fn(),
    onRemoveDrug: vi.fn(),
    onUpdateDrug: vi.fn(),
    loadingSmart: false,
    smartSuggestion: null,
    onApplySmart: vi.fn(),
    onApplyPreset: vi.fn(),
    validationErrors: [],
    coherenceWarnings: [],
    contextLibelle: '',
    ...overrides,
  };
  render(<PrescriptionForm {...props as any} />);
  return props;
}

describe('PrescriptionForm G4 interactive controls', () => {
  it('applies each quick prescription through the preset boundary', () => {
    const props=renderForm();
    for (const name of ['Post-Op Standard','Infection / Abcès','Parodontie','Urgence Douleur']) {
      fireEvent.click(screen.getByRole('button',{name:new RegExp(name,'i')}));
    }
    expect(props.onApplyPreset).toHaveBeenCalledTimes(4);
  });

  it('edits medication name, dosage and posology through explicit field callbacks', () => {
    const props=renderForm();
    fireEvent.change(screen.getByDisplayValue('AMOXICILLINE'),{target:{value:'ibuprofene'}});
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'name','IBUPROFENE');

    fireEvent.change(screen.getByDisplayValue('1g'),{target:{value:'500mg'}});
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'dosage','500mg');

    fireEvent.change(screen.getByDisplayValue('1 matin et soir'),{target:{value:'1 x 3/j'}});
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'posologie','1 x 3/j');
  });

  it('changes package quantity and pharmaceutical form without mutating unrelated fields', () => {
    const props=renderForm();

    fireEvent.click(screen.getByRole('button',{name:'20'}));
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'forme','Gélules (Bte de 20)');

    fireEvent.click(screen.getByRole('button',{name:/Comprimés/i}));
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'forme','Comprimés (Bte de 12)');
  });

  it('supports custom form detail after selecting Autre', () => {
    const props=renderForm({
      drugs:[{...drug,forme:'Autre: Radio'}],
    });
    fireEvent.change(screen.getByPlaceholderText('Précisez la forme (ex: Radio, Analyse...)'),{target:{value:'Analyse'}});
    expect(props.onUpdateDrug).toHaveBeenCalledWith(1,'forme','Autre: Analyse');
  });

  it('removes and adds prescription rows through separate controls', () => {
    const props=renderForm();

    const buttons=screen.getAllByRole('button');
    const remove=buttons.find(b=>b.querySelector('svg') && !b.textContent?.trim());
    if (!remove) throw new Error('remove control not found');
    fireEvent.click(remove);
    expect(props.onRemoveDrug).toHaveBeenCalledWith(1);

    fireEvent.click(screen.getByRole('button',{name:/Ajouter une prescription/i}));
    expect(props.onAddDrug).toHaveBeenCalledTimes(1);
  });

  it('applies an available smart suggestion only on explicit user action', () => {
    const props=renderForm({
      smartSuggestion:{protocol_name:'Protocole Test',applied:false},
    });
    expect(props.onApplySmart).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button',{name:'Appliquer'}));
    expect(props.onApplySmart).toHaveBeenCalledTimes(1);
  });

  it('exposes validation and antibiotic warnings instead of hiding unsafe states', () => {
    renderForm({
      validationErrors:[
        {field:'drugs',message:'Au moins un médicament est requis'},
        {field:'drug_0',message:'Posologie requise'},
      ],
      coherenceWarnings:[{message:'Attention antibiotique'}],
    });

    expect(screen.getByText('Au moins un médicament est requis')).toBeTruthy();
    expect(screen.getByText('Attention antibiotique')).toBeTruthy();
    expect(screen.getByText('Posologie Requise')).toBeTruthy();
  });
});
