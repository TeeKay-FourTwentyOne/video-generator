"""Audition material and lighting changes against a fixed saved ANGLES scene."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import bpy
from mathutils import Matrix, Vector, Quaternion

p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
p.add_argument('--variant',choices=['current','polished','shaped'],required=True)
p.add_argument('--panorama',action='store_true')
p.add_argument('--samples',type=int,default=96)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
a.output.mkdir(parents=True,exist_ok=False)
shutil.copyfile(__file__,a.output/'metal-audition.py')
s=bpy.context.scene;c=s.camera
def geometry_hash():
    digest=hashlib.sha256()
    for obj in sorted((o for o in s.objects if o.type=='MESH'),key=lambda o:o.name):
        digest.update(obj.name.encode())
        for row in obj.matrix_world:
            for x in row:digest.update(struct.pack('<d',x))
        for v in obj.data.vertices:
            for x in v.co:digest.update(struct.pack('<d',x))
        for poly in obj.data.polygons:
            for x in poly.vertices:digest.update(struct.pack('<I',x))
    return digest.hexdigest()
before=geometry_hash()
changes=[]
if a.variant!='current':
    for name,roughness in [('Opaque silver / ground face',.145),('Opaque silver / edge',.105)]:
        m=bpy.data.materials[name];nodes=m.node_tree.nodes;b=nodes.get('Principled BSDF')
        b.inputs['Base Color'].default_value=(.9,.9,.9,1)
        b.inputs['Anisotropic'].default_value=.6
        for n in nodes:
            if n.bl_idname=='ShaderNodeMapRange':
                n.inputs['To Min'].default_value=roughness-.009
                n.inputs['To Max'].default_value=roughness+.009
            elif n.bl_idname=='ShaderNodeBump':n.inputs['Strength'].default_value=.15
        changes.append({'material':name,'roughnessCenter':roughness,'roughnessRange':.009,'neutralReflectance':.9,'anisotropy':.6,'bumpStrength':.15})
if a.variant=='shaped':
    lower=bpy.data.materials['Opaque silver / edge'].node_tree.nodes
    lower.get('Principled BSDF').inputs['Anisotropic'].default_value=.35
    for node in lower:
        if node.bl_idname=='ShaderNodeMapRange':
            node.inputs['To Min'].default_value=.061;node.inputs['To Max'].default_value=.069
    changes.append({'material':'Opaque silver / edge','roughnessCenter':.065,'roughnessRange':.004,'anisotropy':.35})
    reverse=bpy.data.objects['Reverse softbox'].data
    reverse.size=.72;reverse.energy=1050
    obj=bpy.data.objects['Opposing wedge B / closed solid']
    n=(obj.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
    point=obj.location+n*.35
    view=(-point).normalized()
    direction=2*n.dot(view)*n-view
    location=point+direction*3.1
    # A physical strip source is aligned with the long machined edge.
    z=(location-point).normalized();edge=obj.matrix_world.to_3x3()@Vector((1,0,0))
    x=(edge-z*edge.dot(z)).normalized();y=z.cross(x)
    data=bpy.data.lights.new('White strip / opposed face','AREA')
    data.shape='RECTANGLE';data.size=4.5;data.size_y=.08;data.energy=160;data.color=(1,1,1)
    light=bpy.data.objects.new('White strip / opposed face',data);s.collection.objects.link(light)
    light.location=location;light.rotation_mode='QUATERNION';light.rotation_quaternion=Matrix((x,y,z)).transposed().to_quaternion()
    changes.append({'light':'Reverse softbox','width':.72,'energy':1050})
    changes.append({'light':light.name,'position':list(location),'size':[4.5,.08],'energy':160,'color':[1,1,1]})
assert geometry_hash()==before
assert list(c.location)==[0,0,0]
materials=[]
for m in bpy.data.materials:
    b=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
    if b and m.users:
        rgba=list(b.inputs['Base Color'].default_value)
        assert rgba[0]==rgba[1]==rgba[2]
        assert b.inputs['Transmission Weight'].default_value==0 and b.inputs['Alpha'].default_value==1
        assert b.inputs['Metallic'].default_value==1
        materials.append({'name':m.name,'neutral':True,'opaque':True,'metallic':1})
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.cycles.samples=a.samples;s.cycles.seed=421;s.cycles.use_animated_seed=False
s.render.image_settings.color_mode='BW';s.render.film_transparent=False
s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
s.render.use_motion_blur=False;s.view_settings.exposure=0
if a.panorama:
    # This cropped angular plate covers the full 11–14 s field of view at
    # sufficient angular density for native 1080p perspective sampling.
    s.render.resolution_x=5120;s.render.resolution_y=3072
    s.render.image_settings.color_depth='16'
    c.data.type='PANO';c.data.panorama_type='EQUIRECTANGULAR'
    # Cycles uses the negative world azimuth for this camera orientation.
    # Its [65,165] longitude interval yields world azimuths [-65,-165].
    c.data.longitude_min=math.radians(65);c.data.longitude_max=math.radians(165)
    c.data.latitude_min=math.radians(-30);c.data.latitude_max=math.radians(30)
    c.rotation_mode='XYZ';c.rotation_euler=(math.pi/2,0,-math.pi/2)
    file='radiance.png'
else:
    s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.image_settings.color_depth='8'
    c.data.type='PERSP';c.data.lens=35;c.data.sensor_width=36
    t=13;u=(t-11-.375)/(6-.875);u=u*u*(3-2*u)
    angles=[x+(y-x)*u for x,y in zip([204,5,-10],[222,-6,4])]
    yaw,pitch,roll=map(math.radians,angles)
    direction=Vector((math.sin(yaw)*math.cos(pitch),math.cos(yaw)*math.cos(pitch),math.sin(pitch)))
    c.rotation_mode='QUATERNION';c.rotation_quaternion=direction.to_track_quat('-Z','Y')@Quaternion((0,0,1),roll)
    file='at-13s.png'
s.render.filepath=str((a.output/file).resolve())
bpy.ops.wm.save_as_mainfile(filepath=str((a.output/'scene.blend').resolve()))
bpy.ops.render.render(write_still=True)
meta={'variant':a.variant,'scope':'seconds 11 through 14 of solid-silver-v2','changes':changes,'geometryHash':before,'geometryUnchanged':True,
 'cameraOrigin':[0,0,0],'materials':materials,'size':[s.render.resolution_x,s.render.resolution_y],'samples':a.samples,
 'panorama':a.panorama,'longitudeDegrees':[-165,-65] if a.panorama else None,'latitudeDegrees':[-30,30] if a.panorama else None,
 'render':file,'sha256':hashlib.sha256((a.output/file).read_bytes()).hexdigest(),'providerCalls':0,'apiCostUSD':0}
(a.output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
print('METAL_AUDITION_COMPLETE',a.variant,flush=True)
