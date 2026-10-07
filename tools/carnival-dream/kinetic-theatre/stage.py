"""Render a persistent physically lit miniature proscenium and its foreground matte."""
import bpy, math, random
from pathlib import Path
from mathutils import Vector
R=Path('data/workspace/carnival-dream/draft-v5-kinetic/assets').resolve()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
sc.render.resolution_x=2560;sc.render.resolution_y=1440;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.20,.26,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.22
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.1
random.seed(42)
def mat(name,col,rough=.5,metal=0,wood=False,fabric=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=5 if wood else 170;tex.inputs['Detail'].default_value=3.5
 coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(4,90,3) if wood else (1,1,1);l.new(coord.outputs['Generated'],mapping.inputs[0]);l.new(mapping.outputs[0],tex.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*[v*.32 for v in col],1);ramp.color_ramp.elements[1].color=(*col,1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.014 if fabric else .022;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 if fabric:p.inputs['Sheen Weight'].default_value=.10;p.inputs['Sheen Roughness'].default_value=.65
 return m
wood=mat('Worn walnut wood grain',(.23,.094,.033),.40,wood=True)
gold=mat('Tarnished brass',(.54,.32,.09),.27,.8)
velvet=mat('Burgundy folded velvet',(.12,.008,.016),.91,fabric=True)
canvas=mat('Warm unbleached woven screen',(.78,.68,.50),.98,fabric=True)
black=mat('Blackened stage iron',(.024,.031,.033),.36,.7)
floor=mat('Scratched stage boards',(.18,.10,.048),.6,wood=True)
blue=mat('Blue glass footlight housing',(.018,.09,.22),.22,.35)
red=mat('Red silk tassel',(.49,.029,.035),.6,fabric=True)
foreground=[]
def mesh(name,verts,faces,material,fg=True):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(material)
 if fg:foreground.append(o)
 return o
def box(name,loc,scale,ma,bev=.04,fg=True):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma)
 if bev:b=o.modifiers.new('Soft worn corners','BEVEL');b.width=bev;b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 if fg:foreground.append(o)
 return o
def ball(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 foreground.append(o);return o
def cord(name,pts,r,ma):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,cu);sc.collection.objects.link(o);cu.materials.append(ma);foreground.append(o);return o
# Screen and real slatted floor. Foreground identity remains constant for every angle.
screen=box('Stretched woven theatre screen',(0,2.1,4.8),(16,.15,8.7),canvas,fg=False)
for i in range(27):
 x=-8.1+i*.62
 box('Individual scratched floorboard',(x,-.7,.80),(.602,8,.18),floor,.018)
 for yy in [-3.7,.7,2.8]:
  for dx in [-.22,.22]:ball('Dark nail head',(x+dx,yy,.90),(.016,.016,.009),black)
# Solid proscenium posts and nested mouldings.
for side in [-1,1]:
 x=side*7.12
 box('Carved walnut column',(x,-.18,4.65),(.72,.55,8.25),wood)
 for dx in [-.31,.31]:box('Brass vertical moulding',(x+dx,-.49,4.65),(.045,.055,8.1),gold,.018)
 for z in [1,1.2,8.15,8.38]:box('Column capital',(x,-.3,z),(.94,.74,.17),wood)
 for z in [2.0,4.3,6.6]:
  ball('Carved central rosette',(x,-.50,z),(.13,.055,.13),gold)
  for i in range(8):a=i*math.tau/8;ball('Carved rosette leaf',(x+.22*math.cos(a),-.50,z+.22*math.sin(a)),(.11,.045,.067),wood)
for z,dep,width in [(8.55,.8,.36),(8.27,.62,.15),(8.09,.4,.075)]:box('Top carved cornice',(0,-.1,z),(15.2,dep,width),wood)
box('Fine upper gilded edge',(0,-.55,8.33),(14.7,.05,.042),gold,.014)
# Folded velvet mesh curtains, scalloped and gathered: cloth has actual 3D relief.
for side in [-1,1]:
 verts=[];faces=[];nx,nz=70,60
 for j in range(nz+1):
  v=j/nz;z=.96+7.15*v
  inner=5.94+.47*math.sin(v*math.pi)
  for i in range(nx+1):
   u=i/nx;x=side*(inner+(7.0-inner)*u);y=-.04+.20*math.sin(u*math.tau*5)+.08*math.sin(v*math.pi*2+u*5)
   verts.append((x,y,z))
 for j in range(nz):
  for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 o=mesh('Heavy velvet side curtain',verts,faces,velvet)
 for p in o.data.polygons:p.use_smooth=True
 cord('Braided curtain tie',[(side*(6.07+.8*u),-.29,3.3-.15*math.sin(u*math.pi)) for u in [i/30 for i in range(31)]],.035,gold)
 # Consistent red tassel on right, tied to curtain cord.
 if side==1:
  cord('Red tassel cord',[(6.12,-.3,3.3),(6.06,-.34,2.8)],.026,gold)
  for i in range(15):
   a=i*math.tau/15;cord('Silk tassel fringe',[(6.06,-.34,2.85),(6.06+.09*math.cos(a),-.34+.09*math.sin(a),2.49)],.009,red)
# Upper velvet swag drapes with folds.
verts=[];faces=[]
for j in range(14):
 v=j/13
 for i in range(241):
  x=-7+14*i/240;bottom=7.82-.33*abs(math.sin(x*math.pi/4.6));z=bottom+(8.36-bottom)*v;y=-.20+.085*math.sin(x*13)
  verts.append((x,y,z))
for j in range(13):
 for i in range(240):a=j*241+i;faces.append((a,a+1,a+242,a+241))
mesh('Scalloped velvet valance',verts,faces,velvet)
# Repeated physical details: five-point centre medallion, blue footlight, crank key.
verts=[(0,-.58,8.53)]
for i in range(10):a=math.pi/2+i*math.pi/5;r=.25 if i%2==0 else .115;verts.append((r*math.cos(a),-.59,8.53+r*math.sin(a)))
star=mesh('Brass star centre medallion',verts,[(0,i+1,(i+1)%10+1) for i in range(10)],gold)
for i in range(15):
 x=-6.5+i*.93
 box('Footlight cast bracket',(x,-3.95,.88),(.26,.24,.10),blue if i==3 else black)
 m=bpy.data.materials.get('Warm lamp')
 if not m:
  m=bpy.data.materials.new('Warm lamp');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(1,.63,.23,1);p.inputs['Emission Color'].default_value=(1,.48,.12,1);p.inputs['Emission Strength'].default_value=3
 ball('Warm footlight globe',(x,-3.96,1.00),(.06,.06,.09),m)
cord('Loose brass winding key stem',[(-5.5,-2.8,.94),(-4.8,-2.8,.94)],.033,gold)
for x in [-5.64,-5.37]:cord('Winding key loops',[(x+.13*math.cos(i*math.tau/40),-2.8+.13*math.sin(i*math.tau/40),.94) for i in range(41)],.027,gold)
def area(name,pos,power,color,size,target):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
area('Warm side softbox',(-5,-5,8),950,(1,.72,.46),6,(0,1,4))
area('Cool opposing bounce',(5,-3,5),650,(.55,.70,1),5,(0,1,4))
area('Top beam',(0,-1,9.8),700,(1,.76,.5),5,(0,1,3))
area('Screen wash',(0,-1,5.3),400,(1,.88,.64),4,(0,2,4.6))
bpy.ops.object.camera_add(location=(0,-22,7.7));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,4.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=16;sc.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=str(R/'miniature-stage.blend'))
sc.render.film_transparent=False;sc.render.filepath=str(R/'stage-full.png');bpy.ops.render.render(write_still=True)
screen.hide_render=True;sc.render.film_transparent=True;sc.render.filepath=str(R/'stage-foreground.png');bpy.ops.render.render(write_still=True)
print('STAGE PLATES COMPLETE',flush=True)
