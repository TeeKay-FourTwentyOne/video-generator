"""Inspect the baked invitation in Blender without rendering or provider calls."""
import argparse, itertools, json, math, sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
tl=json.loads((args.run/'timeline.json').read_text());scene=bpy.context.scene;cam=scene.camera
assert scene.frame_start==1 and scene.frame_end==round(tl['duration']*24)
assert scene.render.fps==24
assert (scene.render.resolution_x,scene.render.resolution_y)==(1920,1080)
key_count=0
for action in bpy.data.actions:
    for curve in action.fcurves:
        for key in curve.keyframe_points:
            assert key.interpolation=='CONSTANT';key_count+=1
sound=scene.sequence_editor.strips[0].sound
assert sound.filepath.startswith('//') and Path(bpy.path.abspath(sound.filepath)).is_file()
checked=0;failures=[];minimum={'distance':999}
names=['story','challenge','quiet','elder']
for i in range(round(tl['duration']*8)):
    t=i/8;scene.frame_set(i*3+1);bpy.context.view_layer.update()
    for a,b in itertools.combinations(names,2):
        distance=(bpy.data.objects[a].matrix_world.translation-bpy.data.objects[b].matrix_world.translation).length
        if distance<minimum['distance']:minimum={'distance':distance,'pair':[a,b],'time':t}
    line=next((line for line in tl['lines'] if line['start']<=t<line['end']),None)
    if not line:continue
    name=line['speaker'];head=bpy.data.objects[name+' articulated head']
    target=head.matrix_world@Vector((0,0,.285));uv=world_to_camera_view(scene,cam,target)
    origin=cam.matrix_world.translation;direction=target-origin
    hit,location,normal,index,obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction.normalized(),distance=direction.length+.1)
    clear=hit and obj.name.startswith(name+' ')
    if not (.02<uv.x<.98 and .02<uv.y<.98 and uv.z>0 and clear):
        failures.append({'time':t,'line':line['id'],'screen':[uv.x,uv.y,uv.z],'first_surface':obj.name if hit else None})
    checked+=1
report={'status':'pass' if not failures else 'review required','frame_range':[scene.frame_start,scene.frame_end],
        'pose_count':round(tl['duration']*8),'animated_actions':len(bpy.data.actions),'constant_keys':key_count,
        'relative_audio_exists':True,'speaking_pose_visibility_checks':checked,'visibility_failures':failures,
        'minimum_root_separation':minimum,'scope':'All baked poses; active speaker head projection and camera-to-head occlusion ray during every spoken line. Not a listening or aesthetic review.'}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
if failures:raise RuntimeError('Speaker visibility needs inspection')
if minimum['distance']<.60:raise RuntimeError('Puppet roots approach too closely')
