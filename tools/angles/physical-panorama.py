"""Render a single center-view angular plate from the saved opaque-metal scene."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import bpy
import bmesh
from mathutils import Vector

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--width',type=int,default=16384)
p.add_argument('--samples',type=int,default=48)
p.add_argument('--latitude',type=float,default=45,choices=[45,90])
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.output.mkdir(parents=True,exist_ok=False)
s=bpy.context.scene;c=s.camera
assert list(c.location)==[0,0,0]
checks=[]
for obj in s.objects:
    if obj.type=='MESH':
        mesh=bmesh.new();mesh.from_mesh(obj.data)
        check={'name':obj.name,'closedManifold':all(e.is_manifold for e in mesh.edges),'signedVolume':mesh.calc_volume(signed=True)}
        checks.append(check);assert check['closedManifold'] and check['signedVolume']>0
        mesh.free()
        for m in obj.data.materials:
            b=m.node_tree.nodes.get('Principled BSDF')
            assert b is not None
            assert b.inputs['Transmission Weight'].default_value==0 and b.inputs['Alpha'].default_value==1
            assert b.inputs['Metallic'].default_value==1
            color=b.inputs['Base Color'].default_value
            assert color[0]==color[1]==color[2]
    elif obj.type=='LIGHT':assert tuple(obj.data.color)==(1,1,1)

deps=bpy.context.evaluated_depsgraph_get();distances=[]
for i in range(180):
    angle=math.tau*i/180;d=Vector((math.sin(angle),math.cos(angle),0))
    hit,point,*rest=s.ray_cast(deps,Vector((0,0,0)),d)
    assert hit;distances.append(point.length)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=a.samples
s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*a.latitude/180)
s.render.image_settings.color_mode='BW';s.render.image_settings.color_depth='16'
c.data.type='PANO';c.data.panorama_type='EQUIRECTANGULAR'
c.data.latitude_min=-math.radians(a.latitude);c.data.latitude_max=math.radians(a.latitude)
c.data.longitude_min=-math.pi;c.data.longitude_max=math.pi
c.rotation_mode='XYZ';c.rotation_euler=(math.pi/2,0,-math.pi/2)
meta={'method':'Cycles spherical-center radiance plate; fixed camera and static scene. Perspective frames are ray-direction reprojections, not camera translations.',
 'palette':'black and neutral opaque metal','meshChecks':checks,'equatorRadialDistanceMinMax':[min(distances),max(distances)],
 'materialsOpaque':True,'materialsMetallic':True,'neutralMaterialsAndLights':True,'cameraOrigin':list(c.location),
 'width':a.width,'height':s.render.resolution_y,'latitudeDegrees':[-a.latitude,a.latitude],'longitudeDegrees':[-180,180],
 'mapping':f'u = 0.5 - atan2(world_y, world_x)/(2*pi); v = ({a.latitude}deg - asin(world_z))/{2*a.latitude}deg',
 'samples':a.samples,'source':'angles-solid-silver.blend','providerCalls':0,'apiCostUSD':0}
bpy.ops.wm.save_as_mainfile(filepath=str((a.output/'angles-solid-silver-panorama.blend').resolve()))
s.render.filepath=str((a.output/'radiance.png').resolve());start=time.time();bpy.ops.render.render(write_still=True)
meta['renderSeconds']=time.time()-start
meta['sha256']=hashlib.sha256((a.output/'radiance.png').read_bytes()).hexdigest()
(a.output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
print('PANORAMA_COMPLETE',meta['renderSeconds'],flush=True)
