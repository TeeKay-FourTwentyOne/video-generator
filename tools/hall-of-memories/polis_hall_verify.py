"""Audit every speaking pose and entry separation in the authored Hall recipe."""
import runpy, sys, json, math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
original=sys.argv[:];sys.argv=[*sys.argv,'--setup-only']
g=runpy.run_path(str(Path(__file__).with_name('polis_hall_render.py')));sys.argv=original
scene=g['scene'];camera=g['camera'];timeline=g['timeline'];puppets=g['puppets'];report={'speaking_poses':0,'speaker_out_of_frame':[],'head_top_out_of_frame':[],'min_root_separation':100,'entry_samples':[]}
for i in range(round(timeline['duration']*8)):
    t=i/8;g['pose_hall'](t)
    for l in timeline['lines']:
        if l['speaker'] in puppets and l['start']<=t<=l['end']:
            p=puppets[l['speaker']];center=p.headroot.matrix_world@Vector((0,-.20,.285));top=p.headroot.matrix_world@Vector((0,0,.65))
            v=world_to_camera_view(scene,camera,center);vt=world_to_camera_view(scene,camera,top);report['speaking_poses']+=1
            if not (.02<v.x<.98 and .02<v.y<.98 and v.z>0):report['speaker_out_of_frame'].append({'frame':i,'line':l['id'],'ndc':list(v)})
            if not (.015<vt.x<.985 and .015<vt.y<.985 and vt.z>0):report['head_top_out_of_frame'].append({'frame':i,'line':l['id'],'ndc':list(vt)})
    if t<6.5:
        points=[p.root.location.copy() for p in puppets.values()]
        sep=min((x-y).length for j,x in enumerate(points) for y in points[j+1:]);report['min_root_separation']=min(report['min_root_separation'],sep)
        report['entry_samples'].append({'frame':i,'min_root_separation':sep})
report['passed']=not report['speaker_out_of_frame'] and not report['head_top_out_of_frame'] and report['min_root_separation']>.65
(g['args'].run/'qa/recipe-acting.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='entry_samples'},indent=2))
if not report['passed']:raise RuntimeError('Acting audit requires correction')
