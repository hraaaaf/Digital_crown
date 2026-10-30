#!/usr/bin/env python3
"""G5 source-locked, UNSIGNED visual-reference replay. NEVER a clinical PDF.

The accepted REVIEW BOARD is a visual target, not expert-approved contours.
Dashed paths are uncertain estimates and cannot be imported as a signed trace.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import fitz
from scipy.interpolate import PchipInterpolator
import numpy as np

EXPECTED_SCHEMA='DIGITAL_CROWN_G5_VISUAL_REFERENCE_V1'
IDS={'cranial_base','maxilla','mandible','upper_incisor','lower_incisor','soft_tissue_profile'}

def read_reference(manifest:Path,source:Path|None=None)->dict:
    data=json.loads(manifest.read_text(encoding='utf-8'))
    if data.get('schema')!=EXPECTED_SCHEMA or data.get('clinical_approval') is not False:
        raise ValueError('UNSIGNED_VISUAL_REFERENCE_ONLY')
    if data.get('reference_state')!='PRACTITIONER_APPROVED_VISUAL_TARGET_NOT_CLINICALLY_SIGNED':
        raise ValueError('REFERENCE_STATE_INVALID')
    if len(data.get('curves',[]))!=6 or {c.get('id') for c in data['curves']}!=IDS:
        raise ValueError('G5_EXACT_SIX_REVIEW_LAYERS_REQUIRED')
    img=data['source'];width,height=img['width'],img['height']
    if (width,height)!=(1935,2400):raise ValueError('IMAGE_DIMENSION_MISMATCH')
    for c in data['curves']:
        if not c.get('provisional') or c.get('style') not in {'solid','dashed'}:
            raise ValueError('MISSING_NONCLINICAL_LAYER_FLAGS')
        points=c['points']
        if len(points)<7 or len(points)>150 or any(
            not isinstance(p,list) or len(p)!=2 or
            any(not isinstance(x,(int,float)) or isinstance(x,bool) for x in p) or
            not (0<=p[0]<width and 0<=p[1]<height)
            for p in points
        ):raise ValueError('INVALID_SOURCE_PIXEL_POINTS')
    states={c['id']:c['style'] for c in data['curves']}
    if states!={'soft_tissue_profile':'solid','mandible':'solid','maxilla':'dashed',
                'cranial_base':'dashed','upper_incisor':'dashed','lower_incisor':'dashed'}:
        raise ValueError('UNVERIFIED_LINES_MUST_REMAIN_DASHED')
    if source is not None:
        actual=sha256(source.read_bytes()).hexdigest()
        if actual!=img['display_sha256']:
            raise ValueError(f'WRONG_AARIZ_DISPLAY_SOURCE_SHA256 {actual}')
        with Image.open(source) as film:
            if film.size!=(width,height):raise ValueError('SOURCE_SIZE_MISMATCH')
    return data

def sample(points:list[list[float]])->list[tuple[float,float]]:
    a=np.asarray(points,dtype=float)
    length=np.linalg.norm(np.diff(a,axis=0),axis=1)
    if np.any(length<0.5):raise ValueError('DEGENERATE_REVIEW_PATH')
    distance=np.r_[0,np.cumsum(length)]
    t=np.linspace(0,distance[-1],max(100,12*len(points)))
    x=PchipInterpolator(distance,a[:,0])(t)
    y=PchipInterpolator(distance,a[:,1])(t)
    return [(round(float(u),1),round(float(v),1)) for u,v in zip(x,y)]

def font(size:int,bold:bool=False):
    names=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if bold else [
      '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for name in names:
        if Path(name).exists():return ImageFont.truetype(name,size)
    return ImageFont.load_default()

def render(data:dict,source:Path,out:Path)->dict:
    out.mkdir(parents=True,exist_ok=True)
    with Image.open(source) as film:overlay=film.convert('RGB')
    clean=Image.new('RGB',overlay.size,'white')
    for film,alone in ((overlay,False),(clean,True)):
        d=ImageDraw.Draw(film,'RGBA')
        for c in data['curves']:
            pts=sample(c['points']);rgb=tuple(bytes.fromhex(c['color'][1:]))
            if c['style']=='solid':
                d.line(pts,fill=(4,12,24,220) if not alone else (225,230,233,255),width=13,joint='curve')
                d.line(pts,fill=rgb+(255,),width=5,joint='curve')
            else:
                coords=np.asarray(pts)
                cumulative=np.r_[0,np.cumsum(np.linalg.norm(np.diff(coords,axis=0),axis=1))]
                for i in range(1,len(coords)):
                    if int(cumulative[i]/18)%2==0:
                        line=[tuple(coords[i-1]),tuple(coords[i])]
                        d.line(line,fill=(4,12,24,180) if not alone else (225,230,233,255),width=12)
                        d.line(line,fill=rgb+(255,),width=5)
            x,y=c['points'][0]
            d.ellipse((x-9,y-9,x+9,y+9),fill=rgb+(255,),outline=(0,0,0,230),width=2)
        d.rounded_rectangle((36,12,1050,96),radius=15,
                            fill=(16,23,35,230),outline=(245,165,100,255),width=2)
        d.text((58,27),'G5 / RÉFÉRENCE VISUELLE — NON CLINIQUE',
               fill='#FFF2DC',font=font(25,True))
    overlay_path=out/'G5_reference_overlay_UNAPPROVED.png'
    clean_path=out/'G5_reference_clean_UNAPPROVED.png'
    overlay.save(overlay_path)
    clean.save(clean_path)
    pdf_path=out/'G5_reference_two_views_REVIEW_ONLY.pdf'
    pdf=fitz.open()
    for picture,title in ((overlay_path,'Vue 1 / radio + courbes'),
                          (clean_path,'Vue 2 / courbes seules')):
        page=pdf.new_page(width=595.276,height=841.89)
        page.insert_text((26,31),'DIGITAL CROWN G5 / REFERENCE VISUELLE',
                         fontsize=13,fontname='helv',color=(0.15,0.2,0.3))
        page.insert_text((26,49),title,fontsize=10,fontname='helv')
        page.insert_image(fitz.Rect(23,64,572,744),filename=str(picture),keep_proportion=True)
        page.insert_text((26,781),'NON CLINIQUE / 4 CALQUES INCERTAINS EN POINTILLES',
                         fontsize=10,fontname='helv',color=(0.65,0.16,0.12))
        page.insert_text((26,800),'GO visuel de planche uniquement - pas de signature ni mesure.',
                         fontsize=8,fontname='helv')
    pdf.set_metadata({'title':'G5 reference visuelle non clinique','subject':'QA source-locked unapproved contours'})
    pdf.save(pdf_path,deflate=True)
    pdf.close()
    report={'schema':EXPECTED_SCHEMA,'clinical_approval':False,
            'source_display_sha256':data['source']['display_sha256'],
            'source_dimensions':[1935,2400],
            'layers':[{'id':c['id'],'style':c['style'],'guide_points':len(c['points']),
                       'sampled_points':len(sample(c['points']))} for c in data['curves']],
            'views':[overlay_path.name,clean_path.name],
            'review_pdf':pdf_path.name,'research_only':True,
            'approval_claim':'VISUAL_BOARD_ACCEPTED_ONLY_NOT_CLINICAL_CONTOUR_CERTIFICATION'}
    (out/'G5_reference_evidence.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--source',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    if bool(a.source)!=bool(a.out):p.error('--source and --out must be supplied together')
    data=read_reference(a.manifest,a.source)
    if a.source:
        report=render(data,a.source,a.out)
        print('G5_VISUAL_REFERENCE_TWO_VIEWS_PASS_NOT_CLINICAL',json.dumps(report,ensure_ascii=False))
    else: print('G5_REFERENCE_MANIFEST_VALID_NO_CLINICAL_PROMOTION')

if __name__=='__main__':main()
