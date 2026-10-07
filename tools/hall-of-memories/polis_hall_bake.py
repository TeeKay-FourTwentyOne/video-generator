"""Bake the frozen Hall recipe, keying only objects that actually change."""
import json, os, runpy, sys
from pathlib import Path
import bpy
original=sys.argv[:]
args=original[original.index('--')+1:];run=Path(args[args.index('--run')+1]).resolve();out=Path(args[args.index('--output')+1]).resolve()
recipe=run/'render-v1/recipe/polis_hall_render.py'
sys.argv=[*original,'--setup-only'];g=runpy.run_path(str(recipe));sys.argv=original
scene=g['scene'];camera=g['camera'];count=g['count'];pose=g['pose_hall'];out.mkdir(parents=True,exist_ok=True)
target=out/'polis-hall-animation.blend'
if target.exists():raise RuntimeError('Refusing existing animation')
objects=[o for o in scene.objects if o.type in ['MESH','EMPTY','CAMERA']]
def state(o):return tuple(round(x,7) for row in o.matrix_basis for x in row)
pose(0);initial={o.name:state(o) for o in objects};initial_basis={o.name:o.matrix_basis.copy() for o in objects};changed=set()
for i in range(count):
    pose(i/8)
    for o in objects:
        if state(o)!=initial[o.name]:changed.add(o.name)
for o in objects:o.matrix_basis=initial_basis[o.name]
bpy.context.view_layer.update()
animated=[o for o in objects if o.name in changed];animated+=[] if camera in animated else [camera]
for i in range(count):
    f=i*3+1;scene.frame_set(f);pose(i/8)
    for o in animated:
        for prop in ['location','rotation_quaternion' if o.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:o.keyframe_insert(data_path=prop,frame=f)
    camera.data.keyframe_insert(data_path='lens',frame=f)
    for prop in ['focus_distance','aperture_fstop']:camera.data.dof.keyframe_insert(data_path=prop,frame=f)
    g['mixnode'].inputs[0].keyframe_insert(data_path='default_value',frame=f)
    for mat in g['archive_mats']:mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].keyframe_insert(data_path='default_value',frame=f)
for action in bpy.data.actions:
    for curve in action.fcurves:
        for key in curve.keyframe_points:key.interpolation='CONSTANT'
scene.frame_start=1;scene.frame_end=round(g['duration']*24);scene.frame_set(1)
strip=scene.sequence_editor_create().strips.new_sound('Hall editable scratch mix',str(run/'audio/mix.wav'),channel=1,frame_start=1)
strip.sound.filepath='//'+os.path.relpath(run/'audio/mix.wav',out)
for img in bpy.data.images:
    if img.source=='FILE' and img.filepath:img.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
report={'frames':scene.frame_end,'source_poses':count,'fps':24,'animated_objects':[o.name for o in animated],'interpolation':'CONSTANT','recipe':'../render-v1/recipe','texture':'packed Hall facet','audio':'relative link'}
(out/'bake.json').write_text(json.dumps(report,indent=2)+'\n')
print('HALL_BAKE_DONE',len(animated),flush=True)
