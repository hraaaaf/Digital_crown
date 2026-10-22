import { useEffect } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { authorizeLayout, GEOMETRIES, getPreset, PRESETS, projectLayoutPreference,
  validLayout, type Layout, type WorkspaceContext } from './studioLayouts';
import { geometryGridStyle, geometrySlotStyle } from './studioGeometry';
import { StudioLayoutFrame } from './StudioLayoutFrame';

const context: WorkspaceContext = {
  authenticated:true,userId:'T2-user',workstationId:'T2-workstation',tenantId:'T2-tenant',
  patientId:17,cssViewportWidth:1920,
  allowedModules:['dossier','agenda','imagerie','galerie','cephalo','photos','traitement','suivi','documents','presentation'],
};
afterEach(() => cleanup());

describe('07.1.A/B nine-layout registry FUE-0: defensive client contracts only', () => {
  it('has the nine owner-approved product directions in French, favourite first', () => {
    expect(PRESETS.map(p => p.label)).toEqual([
      'Vue d’ensemble','Consultation','Agenda du cabinet','Imagerie',
      'Comparaison orthodontique','Planification des traitements',
      'Suivi clinique','Gestion administrative','Présentation au patient',
    ]);
    expect(new Set(PRESETS.map(p => p.id)).size).toBe(9);
    expect(PRESETS.every(validLayout)).toBe(true);
    expect(getPreset('not-real')).toBeUndefined();
  });

  it('describes seven different geometries, including horizontal, vertical, 1+2 and focus', () => {
    expect(GEOMETRIES).toHaveLength(7);
    for (const geometry of GEOMETRIES) {
      expect(geometryGridStyle(geometry).display).toBe('grid');
      expect(geometryGridStyle(geometry).gridTemplateColumns).toBeTruthy();
    }
    expect(geometrySlotStyle('hero-two',0).gridRow).toBe('1 / span 2');
    expect(geometrySlotStyle('focus-rail',0).gridRow).toBe('1 / span 2');
    expect(geometryGridStyle('two-columns',999).gridTemplateColumns).toContain('63fr');
  });

  it('rejects unknown modules, invalid layout geometry and repeated slot keys', () => {
    const p=getPreset('consultation')!;
    expect(validLayout({...p,geometry:'three-columns'})).toBe(false);
    expect(validLayout({...p,slots:[p.slots[0],p.slots[0]]})).toBe(false);
    expect(validLayout({...p,slots:[p.slots[0],{id:'unknown',module:'billing-secret' as never}]})).toBe(false);
    expect(authorizeLayout(undefined,context)).toEqual({ok:false,reason:'INVALID_LAYOUT'});
    expect(validLayout({...p,slots:null} as unknown as Layout)).toBe(false);
    expect(validLayout({...p,slots:[null,p.slots[1]]} as unknown as Layout)).toBe(false);
    expect(authorizeLayout(p,{...context,allowedModules:null as unknown as never[]}))
      .toEqual({ok:false,reason:'MODULE_DENIED'});
  });

  it('denies rendering without auth, workstation, tenant, patient or every required module', () => {
    const p=getPreset('vue-ensemble')!;
    expect(authorizeLayout(p,{...context,authenticated:false})).toEqual({ok:false,reason:'SESSION_NOT_VERIFIED'});
    expect(authorizeLayout(p,{...context,userId:null})).toEqual({ok:false,reason:'SESSION_NOT_VERIFIED'});
    expect(authorizeLayout(p,{...context,workstationId:null})).toEqual({ok:false,reason:'SESSION_NOT_VERIFIED'});
    expect(authorizeLayout(p,{...context,tenantId:null})).toEqual({ok:false,reason:'SESSION_NOT_VERIFIED'});
    expect(authorizeLayout(p,{...context,patientId:null})).toEqual({ok:false,reason:'PATIENT_MISSING'});
    expect(authorizeLayout(p,{...context,allowedModules:['agenda']})).toEqual({ok:false,reason:'MODULE_DENIED'});
    expect(authorizeLayout(p,context).ok).toBe(true);
  });

  it('enforces desktop-only based on CSS pixels, including effective 200% zoom widths', () => {
    for (const width of [390,430,720,768,1024,1279]) {
      expect(authorizeLayout(getPreset('consultation'),{...context,cssViewportWidth:width}))
        .toEqual({ok:false,reason:'DESKTOP_ONLY'});
    }
  });

  it('does not create two Céphalo stores without proven independent instances or enough width', () => {
    const p=getPreset('comparaison-orthodontique')!;
    expect(authorizeLayout(p,context)).toEqual({ok:false,reason:'INSTANCE_ISOLATION_MISSING'});
    expect(authorizeLayout(p,{...context,independentlyMountable:['cephalo'],cssViewportWidth:1440}))
      .toEqual({ok:false,reason:'UNREADABLE_LAYOUT'});
    expect(authorizeLayout(p,{...context,independentlyMountable:['cephalo']}).ok).toBe(true);
  });

  it('refuses narrow clinical panes even if total layout width would appear to fit', () => {
    const two: Layout={id:'narrow-cephalo',label:'Céphalo + Agenda',geometry:'two-columns',
      slots:[{id:'cephalo',module:'cephalo'},{id:'agenda',module:'agenda'}]};
    expect(authorizeLayout(two,{...context,cssViewportWidth:1280},37))
      .toEqual({ok:false,reason:'UNREADABLE_LAYOUT'});
    expect(authorizeLayout(two,{...context,cssViewportWidth:1920},50).ok).toBe(true);
    const three=getPreset('comparaison-orthodontique')!;
    expect(authorizeLayout(three,{...context,independentlyMountable:['cephalo'],cssViewportWidth:1600}))
      .toEqual({ok:false,reason:'UNREADABLE_LAYOUT'});
  });

  it('projects only module/geometry IDs into local user+workstation layout preferences', () => {
    const enriched={...getPreset('consultation')!,patientId:987,token:'SECRET-TEST',slots:[
      {id:'dossier',module:'dossier' as const,patientId:987,document:'PRIVATE-TEST'},
      {id:'agenda',module:'agenda' as const},
    ]};
    const pref=projectLayoutPreference(enriched,'user-A','poste-A',105);
    expect(pref).toMatchObject({version:1,userId:'user-A',workstationId:'poste-A',ratio:63});
    const serialized=JSON.stringify(pref);
    expect(serialized).not.toContain('patientId');
    expect(serialized).not.toContain('987');
    expect(serialized).not.toContain('SECRET-TEST');
    expect(serialized).not.toContain('PRIVATE-TEST');
    expect(projectLayoutPreference(enriched,'user-A','')).toBeNull();
    const sneaky: Layout={id:'patient-987',label:'A patient secret',geometry:'two-columns',
      slots:[{id:'pat-987',module:'dossier'},{id:'secret-987',module:'agenda'}]};
    expect(validLayout(sneaky)).toBe(true);
    const safeCustom=projectLayoutPreference(sneaky,'user-A','poste-A');
    expect(JSON.stringify(safeCustom)).not.toContain('987');
    expect(JSON.stringify(safeCustom)).not.toContain('secret');
    expect(safeCustom?.id).toBe('custom-two-columns-dossier-agenda');
    expect(safeCustom?.slots[0].id).toBe('slot-1');
  });

  it('NEVER mounts or invokes clinical viewers if a guard denies this layout', () => {
    const view=vi.fn((slot:{id:string})=><p>Protected media {slot.id}</p>);
    const p=getPreset('vue-ensemble')!;
    const {rerender}=render(<StudioLayoutFrame layout={p}
      context={{...context,allowedModules:['agenda']}} renderSlot={view}/>);
    expect(screen.getByRole('alert').textContent).toContain('indisponibles');
    expect(view).not.toHaveBeenCalled();
    rerender(<StudioLayoutFrame layout={p} context={context} renderSlot={view}/>);
    expect(screen.getAllByLabelText(/^Panneau /)).toHaveLength(3);
    expect(view).toHaveBeenCalledTimes(3);
  });

  it('remounts old clinical slot children when the patient changes; future adapter still needs async cancellation', () => {
    const mounted=vi.fn();
    const unmounted=vi.fn();
    function Module() {
      useEffect(() => { mounted(); return () => unmounted(); }, []);
      return <p>Fake module</p>;
    }
    const p=getPreset('consultation')!;
    const renderSlot=()=><Module/>;
    const {rerender}=render(<StudioLayoutFrame layout={p} context={context} renderSlot={renderSlot}/>);
    expect(mounted).toHaveBeenCalledTimes(2);
    rerender(<StudioLayoutFrame layout={p} context={{...context,patientId:18}} renderSlot={renderSlot}/>);
    expect(unmounted).toHaveBeenCalledTimes(2);
    expect(mounted).toHaveBeenCalledTimes(4);
  });

  it('supports structural personal 2x2 arrangements without persisting clinical state', () => {
    const custom: Layout={id:'ma-disposition',label:'Ma disposition',geometry:'grid-2x2',
      slots:[{id:'agenda',module:'agenda'},{id:'dossier',module:'dossier'},
        {id:'imagerie',module:'imagerie'},{id:'suivi',module:'suivi'}]};
    expect(validLayout(custom)).toBe(true);
    expect(authorizeLayout(custom,context).ok).toBe(true);
    expect(projectLayoutPreference(custom,'u','w')?.slots).toHaveLength(4);
  });
});
