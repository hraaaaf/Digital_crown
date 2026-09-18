import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { computeStep3Data } from './cephaloUtils';

const fixturePath = path.resolve(process.cwd(), '../audit/cephalo_r18_concordance_fixtures.json');
const outDir = path.resolve(process.cwd(), '../audit/out');
const fixtures = JSON.parse(fs.readFileSync(fixturePath, 'utf8')) as { cases: Array<{id:string; mmPerPixel:number|null; landmarks:any[]}> };

const blankToNull = (v: unknown) => v === '' || v === undefined ? null : v;

describe('R18 scientific concordance audit - frontend extraction', () => {
  it('executes the real Step 3 frontend geometry on all golden cases', () => {
    const output: Record<string, Record<string, number|null>> = {};
    for (const c of fixtures.cases) {
      const r: any = computeStep3Data(c.landmarks as any, 34, 'M', c.mmPerPixel, null);
      output[c.id] = {
        sna: blankToNull(r.osseuse?.sna) as number|null,
        snb: blankToNull(r.osseuse?.snb) as number|null,
        anb: blankToNull(r.osseuse?.anb) as number|null,
        i_na_angle: blankToNull(r.dentaire?.i_na_angle) as number|null,
        i_nb_angle: blankToNull(r.dentaire?.i_nb_angle) as number|null,
        fma: blankToNull(r.osseuse?.angle_tweed) as number|null,
        impa: blankToNull(r.dentaire?.impa) as number|null,
        fmia: blankToNull(r.dentaire?.fmia) as number|null,
        u1_frankfort: blankToNull(r.dentaire?.i_francfort) as number|null,
        interincisal: blankToNull(r.dentaire?.inter_incisif) as number|null,
        overjet: blankToNull(r.dentaire?.surplomb) as number|null,
        overbite: blankToNull(r.dentaire?.recouvrement) as number|null,
        eline_ls: blankToNull(r.esthetique?.ligne_e_ls) as number|null,
        eline_li: blankToNull(r.esthetique?.ligne_e_li) as number|null,
        i_na_mm: blankToNull(r.dentaire?.i_na_mm) as number|null,
        i_nb_mm: blankToNull(r.dentaire?.i_nb_mm) as number|null,
      };
    }
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(path.join(outDir, 'frontend.json'), JSON.stringify(output, null, 2));
    expect(Object.keys(output)).toHaveLength(fixtures.cases.length);
  });
});
