import {describe,expect,it,vi} from 'vitest';
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
    const request=vi.fn();
    for(const study of [
      {...matched,image_original_path:'/api/static/uploads/radios/other.png'},
      {...matched,angles_data:{...matched.angles_data,
        odf_lab_display_png_sha256:'0'.repeat(64)}},
      {...matched,angles_data:{...matched.angles_data,
        odf_lab_image_landmark_alignment:'UNVERIFIED'}},
    ]){
      expect(isG5ReferenceStudy(study)).toBe(false);
      expect(await verifyG5ReferenceFilm(study,request as unknown as typeof fetch))
        .toBe(false);
    }
    expect(request).not.toHaveBeenCalled();
  });

  it('fails closed for invalid bytes or a non-PNG source',async()=>{
    expect(isG5ReferenceStudy(matched)).toBe(true);
    const altered=vi.fn().mockResolvedValue(new Response('fake image',{
      status:200,headers:{'content-type':'image/png'},
    }));
    expect(await verifyG5ReferenceFilm(matched,altered)).toBe(false);
    const wrongFormat=vi.fn().mockResolvedValue(new Response('fake',{
      status:200,headers:{'content-type':'text/html'},
    }));
    expect(await verifyG5ReferenceFilm(matched,wrongFormat)).toBe(false);
  });
});
