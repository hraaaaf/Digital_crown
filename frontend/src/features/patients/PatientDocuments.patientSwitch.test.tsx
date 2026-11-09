import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import { PatientDocuments } from './PatientDocuments';

const { get, post } = vi.hoisted(() => ({get:vi.fn(),post:vi.fn()}));
vi.mock('../../services/api',async(importOriginal)=>{
  // Keep API_BASE and other real exports required by the auth/store import
  // graph; only intercept the patient document network calls for this test.
  const actual=await importOriginal<typeof import('../../services/api')>();
  return {...actual,api:{...actual.api,get,post}};
});
vi.mock('./CnssInsuranceAction',()=>({
  CnssInsuranceAction:()=>null,
  insuranceOrganizationFromAssurance:()=>null,
}));
vi.mock('./PatientPdfCanvasPreview',()=>({
  PatientPdfCanvasPreview:({blob}:{blob:Blob})=><div data-testid="patient-pdf-canvas-mocked" data-pdf-size={blob.size}/>,
}));

function Navigation() {
  const navigate=useNavigate();
  return <>
    <button onClick={()=>navigate('/patients/1/archives')}>Patient A</button>
    <button onClick={()=>navigate('/patients/2/archives')}>Patient B</button>
    <PatientDocuments/>
  </>;
}
function mount() {
  return render(
    <MemoryRouter initialEntries={['/patients/1/archives']}>
      <Routes>
        <Route path="/patients/:id/archives" element={<Navigation/>}/>
      </Routes>
    </MemoryRouter>,
  );
}
const doc=(name:string,id:string)=>({
  id,name,type:'CERTIFICAT',date:'2026-11-08',url:'',file_exists:false,
});
const patient=(id:number)=>({data:{id,assurance:null}});
const deferred=()=>{
  let resolve:(x:unknown)=>void=()=>{};
  const promise=new Promise(r=>{resolve=r;});
  return {promise,resolve};
};
describe('DC-DOS-01 patient document archive identity switch',()=>{
  beforeEach(()=>{
    get.mockReset();
    post.mockReset();
  });
  it('hides patient A archive synchronously when navigating to B before B response',async()=>{
    const slowB=deferred();
    get.mockImplementation((url:string)=>{
      if(url==='/patients/1/documents')return Promise.resolve({data:[doc('DC_DOS01_SECRET_A','11')]});
      if(url==='/patients/2/documents')return slowB.promise;
      if(url==='/patients/1')return Promise.resolve(patient(1));
      if(url==='/patients/2')return Promise.resolve(patient(2));
      throw Error('Unexpected fetch '+url);
    });
    mount();
    await screen.findByText('DC_DOS01_SECRET_A');
    fireEvent.click(screen.getByRole('button',{name:'Patient B'}));
    expect(screen.queryByText('DC_DOS01_SECRET_A')).not.toBeInTheDocument();
    expect(screen.queryByText('DC_DOS01_SECRET_B')).not.toBeInTheDocument();
    await act(async()=>{slowB.resolve({data:[doc('DC_DOS01_SECRET_B','22')]});await slowB.promise;});
    await screen.findByText('DC_DOS01_SECRET_B');
    expect(screen.queryByText('DC_DOS01_SECRET_A')).not.toBeInTheDocument();
  });
  it('ignores a late A document response after B has loaded and forbids A action buttons',async()=>{
    const slowA=deferred();
    get.mockImplementation((url:string)=>{
      if(url==='/patients/1/documents')return slowA.promise;
      if(url==='/patients/2/documents')return Promise.resolve({data:[doc('DC_DOS01_SECRET_B','22')]});
      if(url==='/patients/1')return Promise.resolve(patient(1));
      if(url==='/patients/2')return Promise.resolve(patient(2));
      throw Error('Unexpected fetch '+url);
    });
    mount();
    fireEvent.click(screen.getByRole('button',{name:'Patient B'}));
    await screen.findByText('DC_DOS01_SECRET_B');
    await act(async()=>{slowA.resolve({data:[doc('DC_DOS01_SECRET_A','11')]});await slowA.promise;});
    expect(screen.queryByText('DC_DOS01_SECRET_A')).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'Actions du document DC_DOS01_SECRET_A'})).not.toBeInTheDocument();
    expect(screen.getByText('DC_DOS01_SECRET_B')).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
    await waitFor(()=>expect(get).toHaveBeenCalledWith('/patients/2/documents'));
  });
  it.each(['Voir', 'Fichier'] as const)(
    'does not perform delayed patient A %s after navigating to B',
    async (action) => {
      const slowBlob = deferred();
      const oldCreate = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
      const createUrl = vi.fn(() => 'blob:stale-patient-a');
      Object.defineProperty(URL, 'createObjectURL', {
        configurable: true, writable: true, value: createUrl,
      });
      const openSpy = vi.spyOn(window, 'open').mockReturnValue(null);
      const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
      try {
        get.mockImplementation((url: string) => {
          if (url === '/patients/1/documents') {
            return Promise.resolve({ data: [{ ...doc('DC_DOS01_SECRET_A', '11'), file_exists: true }] });
          }
          if (url === '/patients/2/documents') return Promise.resolve({ data: [] });
          if (url === '/patients/1') return Promise.resolve(patient(1));
          if (url === '/patients/2') return Promise.resolve(patient(2));
          if (url === '/documents/11/download') return slowBlob.promise;
          throw Error('Unexpected fetch ' + url);
        });
        mount();
        await screen.findByText('DC_DOS01_SECRET_A');
        fireEvent.click(screen.getByRole('button', { name: action }));
        await waitFor(() => expect(get).toHaveBeenCalledWith(
          '/documents/11/download', { responseType: 'blob' },
        ));

        fireEvent.click(screen.getByRole('button', { name: 'Patient B' }));
        await screen.findByText('Aucune archive médicale');
        await act(async () => {
          slowBlob.resolve({ data: new Blob(['synthetic A'], { type: 'application/pdf' }) });
          await slowBlob.promise;
        });

        expect(createUrl).not.toHaveBeenCalled();
        expect(openSpy).not.toHaveBeenCalled();
        expect(alertSpy).not.toHaveBeenCalled();
      } finally {
        if (oldCreate) Object.defineProperty(URL, 'createObjectURL', oldCreate);
        else Reflect.deleteProperty(URL, 'createObjectURL');
        openSpy.mockRestore();
        alertSpy.mockRestore();
      }
    },
  );

  it.each(['navigation A→B', 'Escape'])('keeps A PDF inside the dossier and unmounts it on %s', async (exitMode) => {
    const originalCreate = Object.getOwnPropertyDescriptor(URL, 'createObjectURL');
    const createUrl = vi.fn(() => 'blob:unexpected-pdf');
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true, writable: true, value: createUrl,
    });
    const openSpy = vi.spyOn(window, 'open').mockReturnValue(null);
    try {
      get.mockImplementation((url: string) => {
        if (url === '/patients/1/documents') return Promise.resolve({
          data: [{ ...doc('DC_DOS01_SECRET_A_PDF', '11'), file_exists: true }],
        });
        if (url === '/patients/2/documents') return Promise.resolve({ data: [] });
        if (url === '/patients/1') return Promise.resolve(patient(1));
        if (url === '/patients/2') return Promise.resolve(patient(2));
        if (url === '/documents/11/download') return Promise.resolve({
          data: new Blob(['%PDF-1.4\\n% SYNTHETIC A\\n%%EOF'], { type: 'application/pdf' }),
        });
        throw Error('Unexpected fetch ' + url);
      });
      mount();
      await screen.findByText('DC_DOS01_SECRET_A_PDF');
      fireEvent.click(screen.getByRole('button', { name: 'Voir' }));
      const dialog = await screen.findByRole('dialog', { name: /Aperçu PDF du patient/ });
      expect(await screen.findByTestId('patient-pdf-canvas-mocked')).toBeInTheDocument();
      expect(dialog.querySelector('iframe')).toBeNull();
      expect(createUrl).not.toHaveBeenCalled();
      expect(openSpy).not.toHaveBeenCalled();

      if (exitMode === 'Escape') {
        fireEvent.keyDown(window, { key: 'Escape' });
      } else {
        fireEvent.click(screen.getByRole('button', { name: 'Patient B' }));
        await screen.findByText('Aucune archive médicale');
      }
      await waitFor(() => {
        expect(screen.queryByRole('dialog', { name: /Aperçu PDF du patient/ })).toBeNull();
        expect(screen.queryByTestId('patient-pdf-canvas-mocked')).toBeNull();
        expect(createUrl).not.toHaveBeenCalled();
      });
      if (exitMode !== 'Escape') {
        expect(screen.queryByText('DC_DOS01_SECRET_A_PDF')).not.toBeInTheDocument();
      }
    } finally {
      openSpy.mockRestore();
      if (originalCreate) Object.defineProperty(URL, 'createObjectURL', originalCreate);
      else Reflect.deleteProperty(URL, 'createObjectURL');

    }
  });

});
