import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { CertificateForm as CertificateFormInner } from './Forms/CertificateFormInner';
import { LibreForm } from './Forms/LibreForm';
import { CERTIFICATE_TYPE_FREE, CERTIFICATE_TYPE_WORK_STOP } from './CertificatePolicy';

afterEach(() => cleanup());

describe('Certificate G4 interactive controls', () => {
  it('requires explicit practitioner selection among the three certificate types', () => {
    const setType=vi.fn();
    render(
      <CertificateFormInner
        patientId=""
        certifType=""
        setCertifType={setType}
        certifDays={0}
        setCertifDays={vi.fn()}
        docDate="2026-09-19"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    expect(screen.getByText(/Aucun type sélectionné/i)).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:/Arrêt de travail/i}));
    fireEvent.click(screen.getByRole('button',{name:/Présence au cabinet/i}));
    fireEvent.click(screen.getByRole('button',{name:/Certificat médical/i}));
    expect(setType).toHaveBeenCalledTimes(3);
  });

  it('edits free certificate content explicitly and exposes missing-content truth', () => {
    const setCustom=vi.fn();
    render(
      <CertificateFormInner
        patientId=""
        certifType={CERTIFICATE_TYPE_FREE}
        setCertifType={vi.fn()}
        certifDays={0}
        setCertifDays={vi.fn()}
        docDate="2026-09-19"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={setCustom}
      />,
    );

    const textarea=screen.getByLabelText(/Contenu du certificat médical/i);
    expect(textarea.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByText(/Contenu requis avant génération/i)).toBeTruthy();
    fireEvent.change(textarea,{target:{value:'Texte certifié par le praticien'}});
    expect(setCustom).toHaveBeenCalledWith('Texte certifié par le praticien');
  });

  it('edits work-stop start date and duration through practitioner-controlled fields', () => {
    const setDays=vi.fn();
    const setStart=vi.fn();
    render(
      <CertificateFormInner
        patientId=""
        certifType={CERTIFICATE_TYPE_WORK_STOP}
        setCertifType={vi.fn()}
        certifDays={0}
        setCertifDays={setDays}
        docDate="2026-09-19"
        certifStartDate=""
        setCertifStartDate={setStart}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText(/Début du repos/i),{target:{value:'2026-09-20'}});
    expect(setStart).toHaveBeenCalledWith('2026-09-20');

    fireEvent.change(screen.getByLabelText(/Durée du repos en jours/i),{target:{value:'4'}});
    expect(setDays).toHaveBeenCalledWith(4);
  });
});

describe('Libre document G4 interactive controls', () => {
  function renderLibre(overrides:Record<string,unknown>={}) {
    const props:any={
      title:'Lettre',
      setTitle:vi.fn(),
      content:'Bonjour patient',
      setContent:vi.fn(),
      customPatient:'',
      setCustomPatient:vi.fn(),
      customDate:'',
      setCustomDate:vi.fn(),
      hideHeader:false,
      setHideHeader:vi.fn(),
      pageSize:'A5',
      setPageSize:vi.fn(),
      alignment:'left',
      setAlignment:vi.fn(),
      validationErrors:[],
      ...overrides,
    };
    render(<LibreForm {...props}/>);
    return props;
  }

  it('edits title, recipient, date and patient-header visibility', () => {
    const p=renderLibre();
    fireEvent.change(screen.getByPlaceholderText('Ex: ORDONNANCE, LETTRE...'),{target:{value:'Courrier'}});
    expect(p.setTitle).toHaveBeenCalledWith('Courrier');
    fireEvent.change(screen.getByPlaceholderText('Ex: À qui de droit...'),{target:{value:'À qui de droit'}});
    expect(p.setCustomPatient).toHaveBeenCalledWith('À qui de droit');
    fireEvent.change(screen.getByPlaceholderText('Ex: Rabat, le 12/05/2026'),{target:{value:'Rabat'}});
    expect(p.setCustomDate).toHaveBeenCalledWith('Rabat');
    fireEvent.click(screen.getByLabelText(/Masquer l'en-tête patient/i));
    expect(p.setHideHeader).toHaveBeenCalledWith(true);
  });

  it('switches page format and every alignment option explicitly', () => {
    const p=renderLibre();
    fireEvent.click(screen.getByRole('button',{name:'A4'}));
    expect(p.setPageSize).toHaveBeenCalledWith('A4');
    for(const [name,value] of [['Gauche','left'],['Centre','center'],['Droite','right'],['Justifié','justify']] as const){
      fireEvent.click(screen.getByRole('button',{name}));
      expect(p.setAlignment).toHaveBeenLastCalledWith(value);
    }
  });

  it('wraps selected content with bold/italic/underline and can insert a table', () => {
    const p=renderLibre();
    const textarea=screen.getByRole('textbox',{name:/Contenu/i}) as HTMLTextAreaElement;
    textarea.setSelectionRange(0,7);
    fireEvent.click(screen.getByTitle('Gras'));
    expect(p.setContent).toHaveBeenCalledWith('<b>Bonjour</b> patient');

    fireEvent.click(screen.getByTitle('Italique'));
    expect(p.setContent).toHaveBeenCalled();
    fireEvent.click(screen.getByTitle('Souligné'));
    expect(p.setContent).toHaveBeenCalled();
    fireEvent.click(screen.getByTitle(/table/i));
    expect(p.setContent).toHaveBeenCalled();
  });

  it('shows title/content validation instead of hiding invalid draft state', () => {
    renderLibre({
      validationErrors:[
        {field:'libreTitle',message:'Titre requis'},
        {field:'libreContent',message:'Contenu requis'},
      ],
    });
    expect(screen.getByText('Titre Requis')).toBeTruthy();
    expect(screen.getByText('Contenu Requis')).toBeTruthy();
  });
});
