"""Prove the transition's replacement takes change only the male figure."""
import importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path('tools/carnival-dream/kinetic-theatre');sp=importlib.util.spec_from_file_location('kinetic',root/'render.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
clips=[c for c in r.SHOTS if c['lock_except_male_color']];images=[];masks=[]
for c in clips:
 expected=np.array(r.render(c['start_frame']));actual=np.array(Image.open(r.RUN/'frames'/f"frame-{c['start_frame']:05d}.png"))
 assert np.array_equal(expected,actual),'Delivered color take differs from current recipe'
 images.append(actual);masks.append(np.array(r.MALE_MASK)>0)
base=images[0];union=np.logical_or.reduce(masks);results=[]
for c,im in zip(clips,images):
 diff=np.any(im!=base,axis=2);outside=int(np.sum(diff & ~union));inside=int(np.sum(diff & union));assert outside==0
 if c['male_color']!='black':assert inside>1000
 results.append({'clip':c['id'],'color':c['male_color'],'changed_pixels_outside_male':outside,'changed_pixels_inside_male':inside,'start_s':c['start']})
q=r.RUN/'qa';(q/'male-only-color-proof.json').write_text(json.dumps({'status':'pass','verified_against_actual_rendered_pngs':True,'entire_background_and_princess_pixel_identical':True,'takes':results},indent=2))
out=Image.new('RGB',(1920,2*294),(17,19,25));d=ImageDraw.Draw(out)
for i,(c,im) in enumerate(zip(clips,images)):
 thumb=Image.fromarray(im).resize((384,216));x=i%5*384;y=i//5*294;out.paste(thumb,(x,y));d.text((x+8,y+225),f"{c['start']:.3f}s / {c['male_color']}",fill='white');d.text((x+8,y+247),'All other pixels identical',fill=(211,181,119))
out.save(q/'color-replacement-proof.jpg',quality=94)
print(json.dumps({'status':'pass','takes':len(clips),'outside_male_changed_pixels':0},indent=2))
