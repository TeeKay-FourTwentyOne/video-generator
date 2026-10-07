"""Compare saved animation with the retained recipe across all source poses."""
import hashlib, json, runpy, sys
from pathlib import Path
import bpy
args=sys.argv[sys.argv.index('--')+1:];run=Path(args[args.index('--run')+1]).resolve()
timeline=json.loads((run/'timeline.json').read_text());count=round(timeline['duration']*8)
bpy.ops.wm.open_mainfile(filepath=str(run/'animation-v1/polis-hall-animation.blend'))

def state(t):
    scene=bpy.context.scene;camera=scene.camera;shot=next(s['shot'] for s in timeline['shots'] if s['start']<=t<s['end'])
    names=['story','challenge','quiet','elder'];objects=[]
    for obj in scene.objects:
        # Exclude unseen distant stages; compare all articulated actor geometry
        # in the visible record or polis, plus camera and lighting parameters.
        world=obj.matrix_world.translation
        if obj.type=='CAMERA' or (obj.type=='MESH' and (world.x>65 if shot in ['warm','letter','bedside','empty','facet','jewel'] else world.x<35)):objects.append(obj)
    values={o.name:[round(v,4) for row in o.matrix_world for v in row] for o in objects}
    values['camera_data']=[round(v,5) for v in [camera.data.lens,camera.data.dof.focus_distance,camera.data.dof.aperture_fstop]]
    values['facet_alpha']=round(bpy.data.objects['simulation inside the physical facet'].data.materials[0].node_tree.nodes['Mix Shader'].inputs[0].default_value,5)
    values['archive_lights']=[round(o.data.materials[0].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value,5) for o in sorted(scene.objects,key=lambda o:o.name) if o.name.startswith('unplayed memory cabinet')]
    return values
saved=[]
for i in range(count):
    bpy.context.scene.frame_set(i*3+1);bpy.context.view_layer.update();saved.append(state(i/8))
scene=bpy.context.scene
sound=scene.sequence_editor.strips[0].sound
sound_path=Path(bpy.path.abspath(sound.filepath)).resolve();assert sound_path==run/'audio/mix.wav' and sound_path.exists()
assert scene.frame_end==round(timeline['duration']*24) and scene.render.fps==24
assert all(k.interpolation=='CONSTANT' for action in bpy.data.actions for curve in action.fcurves for k in curve.keyframe_points)
original=sys.argv[:];sys.argv=[*original,'--output',str(run/'animation-audit-setup'),'--setup-only']
g=runpy.run_path(str(run/'render-v1/recipe/polis_hall_render.py'));sys.argv=original
mismatch=[];max_delta=0.0
def delta(a,b):
    if a is None or b is None:return float('inf')
    if isinstance(a,list):return max((abs(x-y) for x,y in zip(a,b)),default=0) if len(a)==len(b) else float('inf')
    return abs(a-b)
for i in range(count):
    g['pose_hall'](i/8);expected=state(i/8)
    diffs={k:delta(saved[i].get(k),expected.get(k)) for k in set(saved[i])|set(expected)}
    max_delta=max(max_delta,max(diffs.values(),default=0))
    keys=[k for k,d in diffs.items() if d>0.0002]
    if keys:
        mismatch.append({'pose':i,'objects':keys,'details':{k:{'saved':saved[i].get(k),'recipe':expected.get(k)} for k in keys}})
report={'source_poses_checked':count,'mismatch':mismatch,'relative_sound_link':'pass','constant_interpolation':'pass','frames':round(timeline['duration']*24),'passed':not mismatch,'maximum_rounded_numeric_delta':max_delta,'numeric_tolerance':0.0002}
(run/'qa/baked-animation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'poses':count,'mismatches':len(mismatch),'first':mismatch[:3]},indent=2))
if mismatch:raise RuntimeError('Saved animation differs from retained recipe')
