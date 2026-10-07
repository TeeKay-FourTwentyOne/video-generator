"""Local Cycles study: solid silver metal, black cavity, white area lights.

Run through Blender: --background --factory-startup --python tools/angles/physical.py
  -- --output=data/workspace/angles/physical-look-v1 --size=720 --samples=96
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import time
import bpy
from mathutils import Vector, Quaternion

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--size',type=int,default=720,choices=[360,540,720,1080])
parser.add_argument('--samples',type=int,default=128)
parser.add_argument('--film',action='store_true')
parser.add_argument('--exposure',type=float,default=0)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
args.output.mkdir(parents=True,exist_ok=False)
(args.output/'frames').mkdir()
(args.output/'recipe').mkdir()
shutil.copyfile(__file__,args.output/'recipe/physical.py')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type='METAL'
prefs.get_devices()
for device in prefs.devices:device.use=device.type=='METAL'
scene.cycles.device='GPU'
scene.cycles.samples=args.samples
scene.cycles.use_denoising=True
scene.cycles.use_adaptive_sampling=True
scene.cycles.adaptive_threshold=.012
scene.cycles.seed=421
scene.cycles.use_animated_seed=False
scene.cycles.max_bounces=8
scene.cycles.diffuse_bounces=3
scene.cycles.glossy_bounces=5
scene.cycles.transmission_bounces=0
scene.cycles.transparent_max_bounces=0
scene.render.resolution_x=args.size*16//9
scene.render.resolution_y=args.size
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='BW'
scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False
scene.render.fps=24
scene.render.use_motion_blur=False
scene.render.use_persistent_data=True
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=args.exposure
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0

def metal(name,roughness=.22,radial=False):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    n=mat.node_tree.nodes; l=mat.node_tree.links
    bsdf=n.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(.82,.82,.82,1)
    bsdf.inputs['Metallic'].default_value=1
    bsdf.inputs['Roughness'].default_value=roughness
    bsdf.inputs['Transmission Weight'].default_value=0
    bsdf.inputs['Alpha'].default_value=1
    bsdf.inputs['Coat Weight'].default_value=0
    bsdf.inputs['Anisotropic'].default_value=.45
    tex=n.new('ShaderNodeTexCoord')
    if radial:
        sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Object'],sep.inputs[0])
        xy=n.new('ShaderNodeCombineXYZ');l.new(sep.outputs['X'],xy.inputs['X']);l.new(sep.outputs['Y'],xy.inputs['Y'])
        length=n.new('ShaderNodeVectorMath');length.operation='LENGTH';l.new(xy.outputs[0],length.inputs[0])
        mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=1500;l.new(length.outputs['Value'],mult.inputs[0])
        wave=n.new('ShaderNodeMath');wave.operation='SINE';l.new(mult.outputs[0],wave.inputs[0])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.00012
        l.new(wave.outputs[0],bump.inputs['Height']);l.new(bump.outputs[0],bsdf.inputs['Normal'])
    else:
        wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='X'
        wave.inputs['Scale'].default_value=220;wave.inputs['Distortion'].default_value=.10
        l.new(tex.outputs['Object'],wave.inputs['Vector'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.00015
        l.new(wave.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs[0],bsdf.inputs['Normal'])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=320;noise.inputs['Detail'].default_value=2
    l.new(tex.outputs['Object'],noise.inputs['Vector'])
    remap=n.new('ShaderNodeMapRange');remap.inputs['From Min'].default_value=0;remap.inputs['From Max'].default_value=1
    remap.inputs['To Min'].default_value=roughness-.015;remap.inputs['To Max'].default_value=roughness+.015
    l.new(noise.outputs['Fac'],remap.inputs['Value']);l.new(remap.outputs[0],bsdf.inputs['Roughness'])
    return mat

turned=metal('Opaque silver / fine turned finish',.205,True)
ground=metal('Opaque silver / ground face',.245)
polished=metal('Opaque silver / edge',.14)
black=bpy.data.materials.new('Blackened opaque metal cavity');black.use_nodes=True
b=black.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(.001,.001,.001,1)
b.inputs['Metallic'].default_value=1;b.inputs['Roughness'].default_value=.6;b.inputs['Transmission Weight'].default_value=0;b.inputs['Alpha'].default_value=1

def orient(obj,center,normal,roll=0):
    obj.location=center
    obj.rotation_mode='QUATERNION'
    obj.rotation_quaternion=Vector(normal).to_track_quat('Z','Y') @ Quaternion((0,0,1),math.radians(roll))

def lathe(name,profile,center,normal):
    count=768;verts=[];faces=[]
    for radius,z in profile:
        for i in range(count):
            a=math.tau*i/count;verts.append((radius*math.cos(a),radius*math.sin(a),z))
    for j in range(len(profile)):
        for i in range(count):faces.append((((j+1)%len(profile))*count+i,((j+1)%len(profile))*count+(i+1)%count,j*count+(i+1)%count,j*count+i))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.data.materials.append(turned)
    for p in mesh.polygons:p.use_smooth=True
    bevel=obj.modifiers.new('Physical edge radii','BEVEL');bevel.width=.012;bevel.segments=4;bevel.limit_method='ANGLE'
    weighted=obj.modifiers.new('Weighted face normals','WEIGHTED_NORMAL');weighted.keep_sharp=True
    orient(obj,center,normal)
    return obj

def block(name,dimensions,center,normal,roll=0,mat=ground):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj=bpy.context.object;obj.name=name;obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    bevel=obj.modifiers.new('Machined edge radius','BEVEL');bevel.width=.035;bevel.segments=6
    obj.modifiers.new('Weighted planar normals','WEIGHTED_NORMAL')
    orient(obj,center,normal,roll)
    return obj

# One turned shoulder, a flat jaw, and two opposing wedge faces. Large, sparse
# solids around the same fixed observer, inside a black spherical enclosure.
profile=[(1.24,.03),(1.30,.15),(1.44,.21),(2.18,.21),(2.19,.202),
         (2.20,.202),(2.21,.21),(2.42,.21),(2.49,.14),(2.49,-.38),
         (2.42,-.45),(1.30,-.45),(1.24,-.38)]
collar=lathe('Turned shoulder / closed solid',profile,(-.45,3.25,.1),(-.40,-1,.17))
block('Ground jaw / closed solid',(4.6,1.75,.64),(3.55,-.35,.1),(-1,.14,.5),-28)
block('Opposing wedge A / closed solid',(4.3,1.48,.70),(-1.70,-3.14,.80),(.35,1,.38),28)
block('Opposing wedge B / closed solid',(4.3,1.48,.70),(-1.67,-3.38,-.86),(.35,1,-.24),28,polished)
bpy.ops.mesh.primitive_uv_sphere_add(segments=128,ring_count=64,radius=7.5)
enclosure=bpy.context.object;enclosure.name='Black spherical enclosure';enclosure.data.materials.append(black)

def light(name,position,target,power,size,size_y):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='RECTANGLE';data.size=size;data.size_y=size_y
    data.color=(1,1,1)
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj

light('Broad white overhead',(0,.1,3.9),(0,1.5,0),2400,5.0,1.8)
light('Front white reflection card',(-3,-.5,1.6),(-.3,3,0),1600,2.3,4)
light('Lower white strip',(1.5,1.1,-2),(0,3,.4),850,2.7,.65)
light('Jaw softbox',(-.7,-1,1),(3.5,0,0),1200,1.2,3.5)
light('Reverse softbox',(0,.7,.3),(-2,-3,0),1400,1.3,4.2)

bpy.ops.object.camera_add(location=(0,0,0))
camera=bpy.context.object;camera.name='Fixed center / rotation only';scene.camera=camera
camera.data.lens=35;camera.data.sensor_width=36
camera.data.dof.use_dof=False
camera.data.clip_start=.03;camera.data.clip_end=30
def camera_angle(yaw,pitch,roll):
    y,p=map(math.radians,[yaw,pitch]);direction=Vector((math.sin(y)*math.cos(p),math.cos(y)*math.cos(p),math.sin(p)))
    camera.rotation_mode='QUATERNION';camera.rotation_quaternion=direction.to_track_quat('-Z','Y') @ Quaternion((0,0,1),math.radians(roll))

shots=[
 {'start':0,'end':6,'id':'turned_edge','from':[-17,2,-14],'to':[2,7,-6]},
 {'start':6,'end':11,'id':'ground_edge','from':[82,-2,14],'to':[105,6,3]},
 {'start':11,'end':17,'id':'opposed_faces','from':[204,5,-10],'to':[222,-6,4]},
 {'start':17,'end':22,'id':'turned_flank','from':[6,-7,17],'to':[-17,0,6]},
 {'start':22,'end':26,'id':'ground_flank','from':[99,-10,-7],'to':[81,-3,9]},
 {'start':26,'end':30,'id':'return','from':[2,7,-6],'to':[-17,2,-14]},
]
def angles_at(t):
    s=next((s for s in shots if s['start']<=t<s['end']),shots[-1])
    u=max(0,min(1,(t-s['start']-.375)/(s['end']-s['start']-.875)));u=u*u*(3-2*u)
    return [a+(b-a)*u for a,b in zip(s['from'],s['to'])],s['id']

jobs=[(0,[-17,2,-14],'turned_edge'),(6,[90,0,12],'ground_edge'),(11,[212,0,-6],'opposed_faces'),(17,[6,-7,17],'turned_flank')]
if args.film:jobs=[(i/8,*angles_at(i/8)) for i in range(240)]

materials=[]
for mat in [turned,ground,polished,black]:
    bsdf=mat.node_tree.nodes.get('Principled BSDF') if mat.use_nodes else None
    if not bsdf:continue
    rgba=list(bsdf.inputs['Base Color'].default_value)
    entry={'name':mat.name,'baseColor':rgba,'metallic':bsdf.inputs['Metallic'].default_value,'transmission':bsdf.inputs['Transmission Weight'].default_value,'alpha':bsdf.inputs['Alpha'].default_value}
    assert rgba[0]==rgba[1]==rgba[2] and entry['metallic']==1 and entry['transmission']==0 and entry['alpha']==1
    materials.append(entry)

manifest={'schema':2,'title':'ANGLES / solid silver','status':'material audition','renderer':'Blender Cycles '+bpy.app.version_string,'samples':args.samples,
 'size':[scene.render.resolution_x,scene.render.resolution_y],'duration':30,'poseFPS':8,'outputFPS':24,'shots':shots,'frames':[],
 'provenance':{'method':'Local physically based path tracing of closed metal meshes, physical bevels and white area lights. No captured metrology data.','providerCalls':0,'apiCostUSD':0},
 'constraints':{'cameraOrigin':[0,0,0],'palette':'neutral silver and black only','opaque':True,'transmission':0,'upscale':False,'fourKDeferred':True,'audio':'silent'},
 'materials':materials,'objects':[{'name':o.name,'type':o.type,'location':list(o.location)} for o in scene.objects]}
camera_angle(*jobs[0][1]);bpy.ops.wm.save_as_mainfile(filepath=str((args.output/'angles-solid-silver.blend').resolve()))
cache={}
for index,(t,angles,shot) in enumerate(jobs):
    camera_angle(*angles);start=time.time()
    relative=f'frames/frame-{index:04d}.png';scene.render.filepath=str((args.output/relative).resolve())
    key=tuple(round(a,10) for a in angles)
    if key in cache:shutil.copyfile(args.output/cache[key],args.output/relative)
    else:
        bpy.ops.render.render(write_still=True)
        cache[key]=relative
    manifest['frames'].append({'index':index,'time':t,'path':relative,'angles':angles,'shot':shot,'camera':{'eye':list(camera.location)},'sha256':hashlib.sha256((args.output/relative).read_bytes()).hexdigest(),'renderSeconds':round(time.time()-start,3)})
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'ANGLES_RENDER {index+1}/{len(jobs)} {time.time()-start:.2f}s',flush=True)
shutil.copyfile(args.output/'frames/frame-0000.png',args.output/'poster.png')
