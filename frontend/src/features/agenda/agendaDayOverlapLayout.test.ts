import {describe,it,expect} from 'vitest';
import {layoutAgendaDayOverlaps} from './agendaDayOverlapLayout';
const mk=(id:number,start:string,duration_minutes:number)=>({id,datetime_start:'2026-09-16T'+start+':00',duration_minutes});
describe('LOT07 P2 Agenda day visual-only lane safety',()=>{
  it('shows both simultaneous practitioner appointments without overlap',()=>{
    const result=layoutAgendaDayOverlaps([mk(201,'09:00',30),mk(211,'09:00',60),mk(212,'14:30',30)]);
    expect(result.get(201)).toMatchObject({lanes:2,lane:0,widthPercent:50});
    expect(result.get(211)).toMatchObject({lanes:2,lane:1,leftPercent:50});
    expect(result.get(212)).toMatchObject({lanes:1,lane:0,widthPercent:100});
  });
  it('never overlays a chained sequence and keeps nonoverlapping items full width',()=>{
    const result=layoutAgendaDayOverlaps([mk(1,'09:00',60),mk(2,'09:45',30),mk(3,'10:00',15),mk(4,'11:00',30)]);
    expect(result.get(1)?.lanes).toBe(3);
    expect(result.get(2)?.lanes).toBe(3);
    expect(result.get(3)?.lanes).toBe(3);
    expect(result.get(4)?.lanes).toBe(1);
    expect(new Set([result.get(1)?.lane,result.get(2)?.lane,result.get(3)?.lane]).size).toBe(3);
  });
  it('does not mutate backend source or invent practitioners',()=>{
    const source=[mk(1,'09:00',30),mk(2,'09:00',30)];
    const snapshot=JSON.stringify(source);
    layoutAgendaDayOverlaps(source);
    expect(JSON.stringify(source)).toBe(snapshot);
  });
  it('returns no fake geometry for malformed timestamps',()=>{
    expect(layoutAgendaDayOverlaps([mk(9,'INVALID',30)]).size).toBe(0);
  });
});
