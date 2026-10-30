import {afterEach,describe,expect,it,vi} from 'vitest';
import {
  G5_VISUAL_REFERENCE,G5_PAIRED_FILM_URL,
  g5ReferenceSvgPath,isG5ReferenceStudy,verifyG5ReferenceFilm,
} from './g5VisualReference';

const matched={
  image_original_path:G5_PAIRED_FILM_URL.slice(1),
  angles_data:{
    odf_lab_image_landmark_alignment:'VERIFIED_AARIZ_EXPERT_PAIR',
    odf_lab_display_png_sha256:G5_VISUAL_REFERENCE.source.display_sha256,
  },
};

describe('G5 reference — read-only source-verified visual target',()=>{
  afterEach(()=>vi.unstubAllGlobals());
  it('has exactly the unsigned practitioner visual six-layer contract',()=>{
    const curves=G5_VISUAL_REFERENCE.curves;
    expect(G5_VISUAL_REFERENCE.clinical_approval).toBe(false);
    expect([G5_VISUAL_REFERENCE.source.width,G5_VISUAL_REFERENCE.source.height])
      .toEqual([1935,2400]);
    expect(curves.map(c=>[c.id,c.points.length,c.style])).toEqual([
      ['soft_tissue_profile',44,'solid'],
      ['mandible',25,'solid'],
      ['maxilla',13,'dashed'],
      ['cranial_base',21,'dashed'],
      ['upper_incisor',12,'dashed'],
      ['lower_incisor',10,'dashed'],
    ]);
    expect(curves.every(c=>c.provisional)).toBe(true);
  });

  it('renders PCHIP source-pixel curves without changing control points',()=>{
    for (const curve of G5_VISUAL_REFERENCE.curves) {
      const snapshot=JSON.stringify(curve.points);
      const path=g5ReferenceSvgPath(curve.points);
      expect(path.startsWith('M ')).toBe(true);
      expect((path.match(/ C /g)||[]).length).toBe(curve.points.length-1);
      expect(JSON.stringify(curve.points)).toBe(snapshot);
    }
    expect(g5ReferenceSvgPath([[1,2],[1,2]])).toBe('');
  });

  it('rejects unrelated studies before trying to load the image',async()=>{
    const request=vi.fn<() => Promise<ArrayBuffer>>();
    for(const study of [
      {...matched,image_original_path:'/api/static/uploads/radios/other.png'},
      {...matched,angles_data:{...matched.angles_data,
        odf_lab_display_png_sha256:'0'.repeat(64)}},
      {...matched,angles_data:{...matched.angles_data,
        odf_lab_image_landmark_alignment:'UNVERIFIED'}},
    ]){
      expect(isG5ReferenceStudy(study)).toBe(false);
      expect(await verifyG5ReferenceFilm(study,request))
        .toBe(false);
    }
    expect(request).not.toHaveBeenCalled();
  });

  it('accepts ONLY authorized PNG bytes matching the exact SHA-256',async()=>{
    expect(isG5ReferenceStudy(matched)).toBe(true);
    const png=new Uint8Array(100001);
    png.set([137,80,78,71,13,10,26,10]);
    const expected=Uint8Array.from(G5_VISUAL_REFERENCE.source.display_sha256
      .match(/.{2}/g)!.map(h=>parseInt(h,16)));
    const digest=vi.fn().mockResolvedValue(expected.buffer);
    vi.stubGlobal('crypto',{subtle:{digest}});
    const authorized=vi.fn().mockResolvedValue(png.buffer);
    expect(await verifyG5ReferenceFilm(matched,authorized)).toBe(true);
    expect(authorized).toHaveBeenCalledOnce();
    expect(digest).toHaveBeenCalledOnce();
    digest.mockResolvedValue(new Uint8Array(32).buffer);
    expect(await verifyG5ReferenceFilm(matched,authorized)).toBe(false);
    const corrupted=vi.fn().mockResolvedValue(new TextEncoder().encode('not png').buffer);
    expect(await verifyG5ReferenceFilm(matched,corrupted)).toBe(false);
    expect(digest).toHaveBeenCalledTimes(2);
  });
});
