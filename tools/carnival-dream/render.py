"""Borrowed Light: persistent paper miniature sets and articulated puppets.

Run inside Blender. All images are local renders; no network or model calls.
Delivery is 24 fps, with three-frame holds except at exact editorial cuts.
"""
import argparse, hashlib, json, math, os, random, shutil, sys, time
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ap=argparse.ArgumentParser()
ap.add_argument('--run',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--height',type=int,default=1080)
ap.add_argument('--samples',type=int,default=16)
ap.add_argument('--engine',choices=['cycles','eevee'],default='cycles')
ap.add_argument('--revision',type=int,choices=[1,2,3],default=1)
ap.add_argument('--stills',action='store_true')
ap.add_argument('--frame',type=int)
ap.add_argument('--frame-list',type=int,nargs='+')
ap.add_argument('--start',type=int,default=0)
ap.add_argument('--end',type=int)
ap.add_argument('--worker',action='store_true',help='Render a disjoint range using an already captured identical recipe')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
args.run=args.run.resolve();args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=True)
spec=json.loads((args.run/'timeline.json').read_text())
random.seed(421)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES' if args.engine=='cycles' else 'BLENDER_EEVEE_NEXT'
if args.engine=='cycles':
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='METAL'
    scene.cycles.device='GPU';scene.cycles.samples=args.samples
    scene.cycles.use_denoising=True;scene.cycles.use_animated_seed=False;scene.cycles.seed=421
    scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=2;scene.cycles.glossy_bounces=2
    scene.render.use_persistent_data=True
else:
    scene.eevee.taa_render_samples=args.samples;scene.eevee.use_raytracing=False
scene.render.resolution_x=args.height*16//9;scene.render.resolution_y=args.height
scene.render.resolution_percentage=100;scene.render.fps=24
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.compression=35;scene.render.use_motion_blur=False
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.17,.20,.32,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.06
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=.35
scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();links=scene.node_tree.links
rl=n.new('CompositorNodeRLayers');glare=n.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='MEDIUM';glare.threshold=1.2;glare.size=7
sat=n.new('CompositorNodeHueSat');out=n.new('CompositorNodeComposite')
links.new(rl.outputs['Image'],glare.inputs['Image']);links.new(glare.outputs['Image'],sat.inputs['Image']);links.new(sat.outputs['Image'],out.inputs['Image'])

cols={}
for name in ['stage','puppets','backstage','rides','lights']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);cols[name]=c
current='stage'
def put(o,name,mat=None,parent=None):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    cols[current].objects.link(o)
    if mat:o.data.materials.append(mat)
    if parent:o.parent=parent
    return o
def mat(name,color,rough=.8,texture=.018,emit=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nd=m.node_tree.nodes;lk=m.node_tree.links;p=nd.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
    if texture:
        noise=nd.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=44;noise.inputs['Detail'].default_value=3.5
        fine=nd.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=650;fine.inputs['Detail'].default_value=2
        mix=nd.new('ShaderNodeMath');mix.operation='MULTIPLY';lk.new(noise.outputs['Fac'],mix.inputs[0]);lk.new(fine.outputs['Fac'],mix.inputs[1])
        b=nd.new('ShaderNodeBump');b.inputs['Strength'].default_value=.34;b.inputs['Distance'].default_value=texture;lk.new(mix.outputs[0],b.inputs['Height']);lk.new(b.outputs[0],p.inputs['Normal'])
        ramp=nd.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.16;ramp.color_ramp.elements[0].color=(*[v*.55 for v in color],1)
        ramp.color_ramp.elements[1].position=.84;ramp.color_ramp.elements[1].color=(*color,1);lk.new(noise.outputs['Fac'],ramp.inputs[0]);lk.new(ramp.outputs[0],p.inputs['Base Color'])
    return m
ivory=mat('P01 ivory rag paper',(.88,.83,.70),texture=.009)
ivory_light=mat('Cut paper edge',(.96,.90,.78),texture=.006)
dressmat=mat('Borrowed color on ivory costume',(.9,.84,.72),texture=.012)
dress_ramp=next(n for n in dressmat.node_tree.nodes if n.type=='VALTORGB')
ink=mat('Blue black ink',(.013,.024,.045),texture=.008)
hairmat=mat('Layered indigo paper hair',(.027,.045,.064),texture=.011)
rose=mat('Rose silk gel',(.80,.055,.16),texture=.006,emit=.18)
blue=mat('Cobalt gel',(.045,.23,.7),texture=.006,emit=.3)
gold=mat('Amber foil',(.77,.41,.075),rough=.42,texture=.006)
lampmat=mat('Lamp warm core',(1,.36,.055),texture=0,emit=5)
bulbmat=mat('Tiny warm lamps',(1,.56,.18),texture=0,emit=3.5)
shadowmat=mat('L01 projected indigo silhouette',(.035,.053,.13),texture=0,emit=.35)
sn=shadowmat.node_tree.nodes;sl=shadowmat.node_tree.links
se=sn.new('ShaderNodeEmission');se.inputs['Color'].default_value=(.015,.022,.075,1);se.inputs['Strength'].default_value=.7
sl.new(se.outputs[0],sn.get('Material Output').inputs['Surface'])
floor_mat=mat('Midnight painted cardboard floor',(.029,.047,.073),texture=.025)
curtainmat=mat('Ink velvet paper curtain',(.019,.023,.043),texture=.025)
wallmat=mat('Blue grey paper cyclorama',(.095,.14,.21),texture=.025)
mache=mat('R01 newspaper pulp white',(.75,.73,.67),texture=.044)
mache_dark=mat('Graphite rubbed paper',(.11,.12,.13),texture=.028)
mache_grey=mat('R01 grey paper seams',(.35,.34,.32),texture=.02)
wood=mat('Warm dark paper board',(.17,.09,.045),texture=.024)

def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);cols[current].objects.link(o);o.location=loc
    if parent:o.parent=parent
    return o
def box(name,loc,scale,ma,parent=None,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=put(bpy.context.object,name,ma,parent);o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:mod=o.modifiers.new('Soft hand cut edge','BEVEL');mod.width=bevel;mod.segments=2;o.modifiers.new('Weighted paper normals','WEIGHTED_NORMAL')
    return o
def ball(name,loc,scale,ma,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=put(bpy.context.object,name,ma,parent);o.scale=scale
    for p in o.data.polygons:p.use_smooth=True
    return o
def cyl(name,loc,radius,depth,ma,parent=None,vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc);o=put(bpy.context.object,name,ma,parent)
    mod=o.modifiers.new('Paper rolled edge','BEVEL');mod.width=min(.025,depth*.15);mod.segments=2;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
def curve(name,pts,radius,ma,parent=None,closed=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=2
    sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,q in zip(sp.points,pts):p.co=(*q,1)
    sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,cu);cols[current].objects.link(o);cu.materials.append(ma)
    if parent:o.parent=parent
    return o
def ring(name,center,radius,ma,parent=None,plane='XZ',wire=.025):
    pts=[]
    for i in range(80):
        a=i*math.tau/80;x=radius*math.cos(a);y=radius*math.sin(a)
        pts.append((center[0]+x,center[1]+(y if plane=='XY' else 0),center[2]+(y if plane=='XZ' else 0)))
    return curve(name,pts,wire,ma,parent,True)
def rod(name,a,b,r,ma,parent=None):
    a,b=Vector(a),Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,ma,parent,16);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def sheet(name,pts,ma,parent=None,thick=.018):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(pts,[],[list(range(len(pts)))]);mesh.update();o=bpy.data.objects.new(name,mesh);cols[current].objects.link(o);mesh.materials.append(ma)
    if parent:o.parent=parent
    if thick:mod=o.modifiers.new('Paper thickness','SOLIDIFY');mod.thickness=thick;mod=o.modifiers.new('Cut edge','BEVEL');mod.width=.008;mod.segments=2
    return o
def star(name,loc,r,ma,parent=None):
    pts=[]
    for i in range(10):
        a=math.pi/2+i*math.pi/5;rr=r if i%2==0 else r*.43;pts.append((math.cos(a)*rr,0,math.sin(a)*rr))
    o=sheet(name,pts,ma,parent);o.location=loc;return o
def aim(o,point):o.rotation_euler=(Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,pos,color,power,size,target):
    data=bpy.data.lights.new(name,'AREA');data.color=color;data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);cols['lights'].objects.link(o);o.location=pos;aim(o,target);return o
def spot(name,pos,color,power,target,angle=42):
    data=bpy.data.lights.new(name,'SPOT');data.color=color;data.energy=power;data.spot_size=math.radians(angle);data.spot_blend=.45;data.shadow_soft_size=.20
    o=bpy.data.objects.new(name,data);cols['lights'].objects.link(o);o.location=pos;aim(o,target);return o
def hidden(root,yes):
    for o in [root,*root.children_recursive]:o.hide_render=yes
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def mix(a,b,u):return a+(b-a)*u
def quant(x,steps=14):return math.floor(max(0,min(1,x))*steps)/steps

# A physical miniature theatre with a receding floor and layered proscenium.
box('Stage floor',(0,.6,-.15),(15,10,.26),floor_mat)
box('Rear paper wall',(0,3.3,3.0),(15,.15,6.2),wallmat)
for x in [-6.4,6.4]:
    for j in range(7):
        xx=x+(j-3)*.16;ball('Folded velvet paper',(xx,1.0,2.8),(.24,.30,3.0),curtainmat)
    box('Proscenium stile',(x,0,2.9),(.24,.35,5.8),gold)
box('Proscenium lintel',(0,0,5.68),(13.0,.35,.22),gold)
for x in range(-12,13):ball('Theatre bulb',(x*.50,-.21,5.55),(.045,.045,.045),bulbmat)
for i in range(21):
    x=-7+i*.7;curve('Floor board seam',[(x,-4,.004),(x,3,.004)],.009,ink)

# Hinged carnival scenery. The panels remain the same objects as they open.
scenery=[]
for side in [-1,1]:
    root=empty('Fold-out fairground',loc=(side*3.25,2.7,.02));scenery.append(root)
    sheet('Folded theatre wing',[(-1.5,0,0),(1.5,0,0),(1.4,0,2.65),(-1.3,0,2.85)],ink,root)
    if side<0:
        for r in [1.0,.86]:ring('Paper wheel',(0,-.09,1.75),r,gold,root)
        for j in range(12):
            a=j*math.tau/12;v=(math.cos(a),-.10,1.75+math.sin(a));rod('Wheel spoke',(0,-.09,1.75),v,.015,gold,root)
            ball('Wheel lamp',v,(.035,.025,.035),bulbmat,root)
            box('Small paper gondola',(v[0],-.13,v[2]-.12),(.15,.08,.16),rose if j%2 else blue,root)
        rod('Wheel support',(-.55,-.1,0),(0,-.1,1.75),.035,gold,root);rod('Wheel support',(.55,-.1,0),(0,-.1,1.75),.035,gold,root)
    else:
        for j in range(7):
            x=-1.35+j*.45;sheet('Striped paper tent',[(x,-.08,.6),(x+.45,-.08,.6),(0,-.08,2.9)],rose if j%2 else gold,root)
        ring('Tent festoon',(0,-.12,1.5),1,blue,root,wire=.02)
    for j in range(7):star('Scenery star',(-1.3+j*.43,-.17,3.2+.20*math.sin(j)),.09,gold,root)

stars=[]
for i in range(19):
    x=-4.6+i*.51;z=2.6+.7*math.sin(i*.8)+.4*(i%3)
    curve('Star suspension',[(x,2.85,5.4),(x,2.85,z)],.006,ink)
    s=star('Hanging painted star',(x,2.76,z),.09+.035*(i%3),gold if i%3 else ivory);stars.append(s)

current='puppets'
class Puppet:
    def __init__(self,name,shadow=False):
        self.shadow=shadow;self.root=empty(name);self.ma=shadowmat if shadow else ivory
        self.body=ball(name+' bodice',(0,0,1.32),(.24,.095,.37),self.ma if shadow else dressmat,self.root)
        self.neck=box(name+' folded neck',(0,0,1.66),(.13,.055,.20),self.ma,self.root)
        self.head=empty(name+' head pivot',(0,0,1.94),self.root)
        ball(name+' face',(0,-.014,0),(.265,.085,.35),self.ma,self.head)
        # Hair is a stack of cut paper leaves, not a smooth helmet.
        for j in range(11):
            a=.1+j*math.pi/10;x=.235*math.cos(a);z=.04+.26*math.sin(a)
            o=ball(name+' hair leaf',(x,.006,z),(.065,.05,.21),shadowmat if shadow else hairmat,self.head);o.rotation_euler[1]=-.5*math.cos(a)
        if not shadow:
            self.lids=[];self.openeyes=[]
            for side in [-1,1]:
                self.lids.append(curve(name+' ink eyelid',[(side*.10-.044,-.099,.03),(side*.10,-.109,.007),(side*.10+.043,-.098,.025)],.008,ink,self.head))
                self.openeyes.append(ball(name+' paper eye',(side*.10,-.106,.025),(.044,.012,.027),ivory_light,self.head))
                self.openeyes.append(ball(name+' ink pupil',(side*.10+.008,-.119,.025),(.016,.008,.020),ink,self.head))
                ball(name+' cheek tint',(side*.16,-.092,-.08),(.046,.007,.019),rose,self.head)
            sheet(name+' folded nose',[(-.025,-.105,.035),(.019,-.12,.025),(.015,-.153,-.065),(-.022,-.105,-.055)],ivory_light,self.head)
            curve(name+' small mouth',[(-.034,-.099,-.14),(0,-.111,-.148),(.030,-.099,-.137)],.006,rose,self.head)
        self.skirt=empty(name+' pleated skirt',(0,0,1.12),self.root)
        for j in range(24):
            a=j*math.tau/24;b=(j+1)*math.tau/24;rr=.46 if j%2 else .51
            sheet(name+' skirt pleat',[(.16*math.cos(a),.12*math.sin(a),0),(.16*math.cos(b),.12*math.sin(b),0),(rr*math.cos(b),.28*math.sin(b),-.60),(.46*math.cos(a),.28*math.sin(a),-.60)],self.ma if shadow else dressmat,self.skirt)
        self.parts={}
        for side in [-1,1]:
            for piece in ['upper','fore','thigh','shin']:
                self.parts[side,piece]=ball(name+piece,(0,0,0),(.07,.032,.2),self.ma,self.root)
            self.parts[side,'hand']=ball(name+' paper hand',(0,0,0),(.079,.035,.115),self.ma,self.root)
            self.parts[side,'foot']=ball(name+' paper shoe',(0,0,0),(.10,.10,.065),shadowmat if shadow else ink,self.root)
            for part in ['shoulder','elbow','knee']:
                self.parts[side,part]=ball(name+' hinge',(0,0,0),(.032,.043,.032),shadowmat if shadow else gold,self.root)
        if not shadow:
            for j in range(5):ball(name+' bodice button',(0,-.095,1.18+j*.077),(.014,.014,.014),gold,self.root)
        self.held=star(name+' carried star',(.38,-.13,1.65),.18,gold,self.root)
    def limb(self,key,a,b,r):
        a,b=Vector(a),Vector(b);o=self.parts[key];o.location=(a+b)/2;o.scale=(r,.035,(b-a).length/2+.015);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    def pose(self,x,t,gesture='rest',yaw=0,scale=1,y=0,lean=0,progress=0,awake=False):
        self.root.location=(x,y,.055);self.root.rotation_euler=(0,lean,yaw);self.root.scale=(scale,.10 if self.shadow else 1,scale)
        sw=math.sin(t*math.tau*88/60/2);walk=gesture in ['walk','carry','step'];dance=gesture in ['dance','reach','effort','spin','return']
        self.head.rotation_euler=(0,.06*math.sin(t*1.1)+( .17 if gesture=='down' else -.08),.09*math.sin(t*.7))
        if not self.shadow:
            eyes_open=awake and (t%4.25)>.16
            for o in self.lids:o.hide_render=eyes_open
            for o in self.openeyes:o.hide_render=not eyes_open
        self.skirt.rotation_euler=(.06*sw if dance else 0,.03*math.sin(t),.08*sw if dance else 0)
        hidden(self.held,gesture not in ['carry','star','effort','lose'])
        for side in [-1,1]:
            shoulder=(side*.235,0,1.53);elbow=(side*.29,-.015,1.21);hand=(side*.31,-.035,.97)
            if gesture in ['reach','return']:
                if side==1:elbow=(.45,-.04,1.57+.06*sw);hand=(.71,-.065,1.72+.06*sw)
                else:elbow=(-.31,-.04,1.25);hand=(-.15,-.13,1.28)
            elif gesture in ['dance','spin']:
                elbow=(side*(.42+.025*sw),-.025,1.60+side*.20*sw);hand=(side*.64,-.07,1.75+side*.24*sw)
            elif gesture=='effort':elbow=(side*.35,-.10,1.71);hand=(side*.40,-.16,1.96+.04*sw)
            elif gesture in ['star','carry','lose']:
                if side==1:
                    hz=1.54
                    if gesture=='star':hz=mix(1.54,2.20,smooth(progress/.32)) if progress<.32 else mix(2.20,1.54,smooth((progress-.40)/.48))
                    elbow=(.35,-.09,min(1.78,hz-.18));hand=(.36,-.14,hz)
                else:elbow=(-.32,-.03,1.2);hand=(-.20,-.13,1.1)
            elif gesture=='wind' and side==-1:elbow=(-.40,-.10,1.22);hand=(-.56,-.05,.91+.035*sw)
            elif walk:elbow=(side*.28,-.06*sw*side,1.22);hand=(side*.27,-.14*sw*side,.97)
            self.limb((side,'upper'),shoulder,elbow,.060);self.limb((side,'fore'),elbow,hand,.049);self.parts[side,'hand'].location=hand
            self.parts[side,'shoulder'].location=shoulder;self.parts[side,'elbow'].location=elbow
            self.parts[side,'hand'].rotation_euler[1]=side*(.3 if dance else -.12)
            stride=.18*sw*side if walk else .10*sw*side if dance else 0
            hip=(side*.105,0,.92);knee=(side*(.15+abs(stride)*.25),stride*.5,.48);ankle=(side*.17,stride,.14+max(0,stride)*.35)
            self.limb((side,'thigh'),hip,knee,.069);self.limb((side,'shin'),knee,ankle,.055);self.parts[side,'knee'].location=knee;self.parts[side,'foot'].location=(ankle[0],ankle[1]-.055,ankle[2]-.04)
        hand=self.parts[1,'hand'].location;self.held.location=hand+Vector((.07,-.065,.17));self.held.rotation_euler[1]=math.sin(t)*.08
performer=Puppet('P01 performer');partner=Puppet('L01 shadow partner',True)
for o in partner.root.children_recursive:o.visible_shadow=False
pluckable=star('One star within reach',(.68,-.205,2.425),.18,gold)
pluck_thread=curve('One star thread',[(.68,-.205,4.1),(.68,-.205,2.425)],.005,ink)

# Black-and-white miniature rides. Individual parts retain their physical
# identity through assembly, failure, and disassembly.
current='rides'
ride_roots={};ride_parts={};ride_rotors={};ride_defects={}
box('Monochrome tabletop',(40,0,-.12),(13,12,.22),mache_dark)
box('Monochrome cyclorama',(40,4,3.3),(14,.12,7),mache_grey)
def horse(name,loc,parent):
    root=empty(name,loc,parent)
    ball('Pulp horse body',(0,0,.1),(.28,.065,.15),mache,root)
    o=ball('Horse neck',(.19,0,.28),(.09,.055,.21),mache,root);o.rotation_euler[1]=-.35
    ball('Horse head',(.24,-.005,.43),(.13,.055,.075),mache,root)
    for side in [-1,1]:
        for x in [-.18,.13]:rod('Horse folded leg',(x,side*.04,.06),(x-.035,side*.04,-.17),.027,mache,root)
    curve('Horse tail',[(-.23,0,.16),(-.37,0,.13),(-.40,0,-.03)],.035,mache_grey,root)
    return root
for kind in ['ferris','carousel','swings']:
    root=empty(kind+' ride',(40,0,0));ride_roots[kind]=root
    cyl('Round pulp plinth',(0,0,.1),1.9,.2,mache_dark,root)
    if kind=='ferris':
        for yy in [-.27,.27]:
            rod('A-frame support',(-.90,yy,.2),(0,yy,2.12),.07,mache,root);rod('A-frame support',(.90,yy,.2),(0,yy,2.12),.07,mache,root)
        axle=rod('Axle',(0,-.45,2.12),(0,.45,2.12),.11,mache_dark,root)
        rot=empty('Wheel rotor',(0,0,2.12),root);ride_rotors[kind]=rot
        for yy in [-.23,.23]:
            ring('Laminated wheel rim',(0,yy,0),1.62,mache,rot,wire=.065)
            ring('Wheel rim inner',(0,yy,0),1.48,mache_grey,rot,wire=.025)
            for j in range(10):
                a=j*math.tau/10;rod('Paper spoke',(0,yy,0),(1.55*math.cos(a),yy,1.55*math.sin(a)),.032,mache,rot)
        cabs=[]
        for j in range(10):
            a=j*math.tau/10;cx,cz=1.6*math.cos(a),1.6*math.sin(a)
            rod('Gondola axle',(cx,-.26,cz),(cx,.26,cz),.025,mache_dark,rot)
            if j==1:continue
            cab=empty('Hanging paper basket',(cx,0,cz),rot);cabs.append((cab,a))
            box('Gondola seat',(0,0,-.35),(.39,.44,.08),mache,cab)
            curve('Basket cage',[(-.19,-.2,-.35),(-.23,-.2,-.12),(0,-.2,.015),(.23,-.2,-.12),(.19,-.2,-.35)],.021,mache_grey,cab)
            box('Basket back',(0,.18,-.26),(.37,.04,.17),mache,cab)
        ride_defects[kind]=cabs
    elif kind=='carousel':
        cyl('Carousel disk',(0,0,.30),1.55,.18,mache,root)
        cyl('Central mast',(0,0,1.52),.10,2.45,mache_dark,root)
        rot=empty('Carousel rotor',(0,0,0),root);ride_rotors[kind]=rot
        for j in range(12):
            a=j*math.tau/12;b=(j+1)*math.tau/12
            sheet('Striped conical canopy',[(0,0,3.0),(1.7*math.cos(a),1.7*math.sin(a),2.37),(1.7*math.cos(b),1.7*math.sin(b),2.37)],mache if j%2 else mache_grey,rot)
        ring('Canopy lip',(0,0,2.37),1.7,mache_dark,rot,'XY',.045)
        for j in range(6):
            a=j*math.tau/6;x,y=1.05*math.cos(a),1.05*math.sin(a);rod('Horse mounting pole',(x,y,.38),(x,y,2.4),.022,mache_dark,rot)
            if j==4:continue
            h=horse('Papier-mache horse',(x,y,1.14),rot);h.rotation_euler[2]=a+math.pi/2
        star('Canopy finial',(0,-.01,3.20),.17,mache,rot)
    else:
        cyl('Swing column',(0,0,1.42),.16,2.5,mache_dark,root)
        rot=empty('Swing crown rotor',(0,0,2.57),root);ride_rotors[kind]=rot
        cyl('Swing crown',(0,0,0),1.32,.12,mache,rot)
        bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=1.40,radius2=.14,depth=.50,location=(0,0,.30));put(bpy.context.object,'Swing paper roof',mache_grey,rot)
        for j in range(8):
            a=j*math.tau/8;x,y=1.17*math.cos(a),1.17*math.sin(a)
            rod('Swing chain left',(x-.09,y,0),(x-.09,y,-1.65),.013,mache_dark,rot)
            if j!=6:rod('Swing chain right',(x+.09,y,0),(x+.09,y,-1.65),.013,mache_dark,rot)
            else:rod('Broken chain stub',(x+.09,y,0),(x+.09,y,-.42),.013,mache_dark,rot)
            seat=box('Swing chair',(x,y,-1.66),(.30,.33,.07),mache,rot)
            if j==6:seat.rotation_euler[1]=.62;seat.location.z+=.05
        star('Swing crown star',(0,0,.80),.16,mache,rot)
    parts=[]
    for o in root.children_recursive:
        if o.type in ['MESH','CURVE']:parts.append((o,o.location.copy(),o.rotation_euler.copy(),o.scale.copy()))
    ride_parts[kind]=parts

current='backstage'
box('Backstage floor',(20,0,-.13),(11,10,.22),wood)
box('Backstage dark wall',(20,3,3),(11,.13,6),curtainmat)
table=box('Lantern table',(20,.6,.69),(2.7,1.5,.16),wood)
for x in [18.9,21.1]:
    for y in [.1,1.1]:box('Table leg',(x,y,.31),(.12,.12,.64),wood)
lantern=empty('Rotating lantern',(20,.6,.79))
cyl('Lantern foot',(0,0,.04),.54,.11,ink,lantern)
cyl('Lantern brass collar',(0,0,.12),.46,.09,gold,lantern)
drum=empty('Lantern paper drum',(0,0,.70),lantern)
cyl('Drum lower ring',(0,0,-.48),.47,.09,ink,drum);cyl('Drum upper ring',(0,0,.48),.47,.09,ink,drum)
for j in range(12):
    a=j*math.tau/12;x,y=.46*math.cos(a),.46*math.sin(a)
    rod('Lantern strut',(x,y,-.48),(x,y,.48),.024,gold,drum)
    if j%3==0:star('Rotating gel star',(x,y,.05),.20,rose if j%2 else blue,drum)
ball('Lantern glowing bulb',(0,0,.67),(.16,.16,.29),lampmat,lantern)
cyl('Lantern lid',(0,0,1.25),.53,.10,ink,lantern)
ring('Lantern handle',(0,0,1.50),.25,gold,lantern)
rod('Winding spindle',(.44,0,.17),(.78,0,.17),.028,gold,lantern)
wind=box('Winding key',(.80,0,.17),(.10,.06,.35),gold,lantern)
for i in range(9):
    s=star('Loose gel on workbench',(19.1+i*.21,.18,.81),.11,rose if i%2 else blue);s.rotation_euler[0]=math.pi/2
# Small paper dancer mounted inside the lantern makes the mechanism legible.
mini=empty('Lantern silhouette cutout',(0,-.29,.63),lantern)
mini.scale=(1.5,1.5,1.5)
ball('Tiny silhouette head',(0,0,.25),(.055,.02,.075),ink,mini)
sheet('Tiny silhouette skirt',[(-.025,0,.17),(.025,0,.17),(.09,0,-.04),(-.09,0,-.04)],ink,mini)
for side in [-1,1]:rod('Tiny silhouette arm',(side*.02,0,.13),(side*.16,0,.24),.016,ink,mini)
curtain_edge=box('Side of folded wing',(18.1,1.4,2.4),(.25,1.4,4.8),curtainmat)

current='lights'
key=area('Soft theatre key',(-3,-4,6),(.69,.79,1),700,5,(0,0,1.3))
rim=area('Amber rim',(4,2.5,4),(1,.48,.21),900,3,(0,0,1.4))
fill=area('Subtle face fill',(0,-5,2.7),(.80,.85,1),180,3,(0,0,1.7))
gel1=spot('Rose traveling projection',(-3,-3,4.3),(1,.055,.17),1500,(0,2,1.4),42)
gel2=spot('Amber traveling projection',(-3.15,-3,4.2),(1,.51,.11),1100,(0,2,1.4),27)
gel3=spot('Blue traveling projection',(2,-2,3.5),(.05,.20,1),600,(0,1,1.4),49)
ridekey=area('Monochrome key',(37,-4,7),(1,1,1),1300,5,(40,0,1.6))
ridefill=area('Monochrome rim',(43,3,5),(1,1,1),1100,4,(40,0,1.5))
backkey=area('Backstage amber key',(18,-2,5),(1,.51,.24),500,3,(20,0,1.1))
backfill=area('Backstage blue rim',(22,2,4),(.21,.36,.8),430,3,(20,0,1.4))
bpy.ops.object.camera_add(location=(3,-10,3.4));cam=put(bpy.context.object,'Film camera');scene.camera=cam;cam.data.lens=52;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=5.6
focus=empty('Camera focus');cam.data.dof.focus_object=focus

def camera(pos,target,lens=52):cam.location=pos;aim(cam,target);focus.location=target;cam.data.lens=lens
def at_frame(frame):
    shot=next((s for s in spec['shots'] if s['start_frame']<=frame<s['end_frame']),spec['shots'][-1]);pose=max(shot['start_frame'],frame//3*3);t=pose/24;k=shot['kind'];u=max(0,min(1,(t-shot['start'])/(shot['end']-shot['start'])))
    isride=any(k.startswith(x+'_') for x in ride_roots);isback=k in ['lantern_macro','backstage','mechanism','wind']
    cols['stage'].hide_render=isride or isback;cols['backstage'].hide_render=not isback;cols['rides'].hide_render=not isride
    cols['puppets'].hide_render=isride or k in ['lantern_macro','mechanism']
    sat.inputs['Saturation'].default_value=0 if isride else 1
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.06 if not isride else .22
    cam.data.dof.aperture_fstop=5.6
    hidden(partner.root,isride or isback or k in ['intro_wide','light_close','feet','face','empty_light','pluck_star','carry_star','curtain','choice','alone'])
    for name,root in ride_roots.items():hidden(root,not k.startswith(name+'_'))
    for s in stars:s.hide_render=False;s.scale=(1,1,1)
    # Reset the stage before selecting each exact shot.
    x=-.95;px=.75;gesture='rest';yaw=0;py=3.16
    lightpower=1;beamx=.2+1.0*math.sin(t*.48)
    opened=0 if t<42.34 else 1
    if k=='bloom':opened=smooth(u)
    if k in ['empty_light','alone','final_step','final_reach','end']:opened=.23
    for j,o in enumerate(scenery):o.rotation_euler[2]=(1-opened)*(1 if j else -1)*1.28
    for j,s in enumerate(stars):s.rotation_euler[1]=.07*math.sin(t+j);s.scale=(.25+.75*opened,)*3
    if k=='intro_wide':x=-1.15;lightpower=.08;camera((4,-12,4.2),(.2,.6,1.65),49)
    elif k=='light_close':x=-.55;beamx=mix(-1.4,.7,u);lightpower=mix(.4,1.1,u);camera((1.7,-5.8,2.6),(-.35,0,1.37),72)
    elif k=='shadow_arrives':x=-.95;px=mix(2,.55,smooth(u));gesture='reach';camera((3,-9,3.2),(0,1,1.5),53)
    elif k=='reach':x=mix(-1.1,-.5,smooth(u));px=.65;gesture='reach';camera((2.2,-7.6,2.9),(.15,1,1.5),61)
    elif k=='feet':x=mix(-.7,.1,u);gesture='walk';camera((1.5,-4.3,.9),(x,.1,.48),70)
    elif k=='face':x=-.30;gesture='reach';camera((.8,-3.15,2.16),(-.20,0,1.90),88);cam.data.dof.aperture_fstop=4
    elif k=='recede':x=.25;px=mix(.8,2.6,u);gesture='reach';camera((-2,-9,3.0),(.45,1.0,1.5),59)
    elif k in ['bloom','dance_return']:x=-.40+.30*math.sin(t*.8);px=.7+.25*math.sin(t*.8);gesture='dance';beamx=x+.4;camera((4-mix(0,.4,u),-11,3.6),(0,1.1,1.75),49)
    elif k in ['near_touch','return_light']:x=-.38;px=.54;gesture='reach' if k=='near_touch' else 'return';beamx=.15;camera((1.2,-6.5,2.65),(.17,1.1,1.75),71)
    elif k=='color_leaves':x=.15;px=2.2;gesture='down';lightpower=1-smooth(u)*.95;beamx=mix(.2,3,u);camera((1.5,-4.9,2.4),(.15,.15,1.5),78)
    elif k in ['pass','walk','separation']:x=mix(-.65,.45,u);px=mix(.8,2.6,u);gesture='walk' if k=='walk' else 'reach';beamx=px;camera((-2.8,-10,3.1),(.3,1,1.6),58)
    elif k=='empty_light':x=.35;lightpower=.30;gesture='down';camera((4,-12,4.0),(.2,1,1.55),50)
    elif k=='pluck_star':x=.25;gesture='star';camera((1.6,-5.2,2.9),(.35,.4,1.85),77)
    elif k=='carry_star':x=mix(-.9,.4,u);gesture='carry';camera((-1.4,-7,2.7),(x,.3,1.55),68)
    elif k=='stars':x=-.5;px=.85;gesture='effort';camera((3.2,-10,3.8),(0,1.1,1.9),54)
    elif k=='spin':x=.4*math.sin(u*math.tau);px=.7+.4*math.sin(u*math.tau);gesture='spin';yaw=.25*math.sin(u*math.tau);camera((mix(3,1,u),-9,3.5),(0,1,1.6),58)
    elif k=='effort':x=-.2;px=.7;gesture='effort';camera((2,-7.1,2.9),(.2,1.1,1.65),65)
    elif k=='lose_stars':x=-.10;px=1.8;gesture='lose';lightpower=1-smooth(u)*.80;beamx=2.1;camera((1.8,-6.0,2.9),(.25,.6,1.7),70)
    elif k=='curtain':x=mix(.4,3.7,u);gesture='walk';beamx=-1.8;camera((5,-10,3.5),(mix(.8,3.6,u),1,1.6),58)
    elif k=='choice':x=-.90;px=.85;gesture='rest';beamx=mix(2.5,-.3,u);camera((2.6,-7.5,3.0),(-.2,.7,1.6),65)
    elif k=='alone':x=-.7;lightpower=.16;gesture='down';camera((4,-13,4.5),(0,.8,1.6),48)
    elif k=='final_step':x=mix(-.9,-.18,smooth(u));px=.78;gesture='step';beamx=.05;camera((2.1,-7.5,3.0),(.2,.8,1.6),62)
    elif k in ['final_reach','end']:x=-.18;px=.66;gesture='reach';beamx=.15;camera((1.4,-7.4,2.75),(.25,1.1,1.62),65)
    performer.pose(x,t,gesture,yaw=yaw,progress=u,awake=t>=124.64)
    pluckable.hide_render=k!='pluck_star' or u>=.34
    pluck_thread.hide_render=k!='pluck_star'
    if k=='pluck_star':hidden(performer.held,u<.34)
    if k=='lose_stars':
        performer.held.location.z-=1.6*smooth(u)
        performer.held.rotation_euler[1]=u*3.5
        hidden(performer.held,u>.92)
    partner.pose(px,t+.15,'dance' if gesture in ['dance','spin'] else 'reach',yaw=-.06,scale=1.06,y=py)
    partner.root.scale.x*=-1
    if k=='shadow_arrives':partner.root.scale*=max(.01,smooth(u))
    for lamp,target in [(gel1,(beamx,2.9,1.45)),(gel2,(beamx-.2,.4,1.25)),(gel3,(beamx+.6,2.6,1.3))]:aim(lamp,target)
    gel1.data.energy=1250*lightpower;gel2.data.energy=850*lightpower;gel3.data.energy=600*lightpower
    key.data.energy=170 if k not in ['intro_wide','alone'] else 90
    rim.data.energy=320;fill.data.energy=65
    borrowed=smooth(1-abs(x-beamx)/1.65)*lightpower
    if k in ['bloom','near_touch','dance_return','effort','return_light','final_reach','end']:borrowed=1
    if k in ['color_leaves','lose_stars']:borrowed=1-smooth(u)
    if k in ['intro_wide','empty_light','alone','choice','curtain','backstage','mechanism','wind']:borrowed=0
    cream=(.90,.84,.72);cold=(.035,.09,.65);warm=(.90,.035,.16)
    dress_ramp.color_ramp.elements[0].color=(*[mix(c*.65,v,borrowed) for c,v in zip(cream,cold)],1)
    dress_ramp.color_ramp.elements[1].color=(*[mix(c,v,borrowed) for c,v in zip(cream,warm)],1)
    if isback:
        performer.pose(21.36 if k=='wind' else 18.8,t,'wind' if k=='wind' else 'rest',yaw=0 if k=='wind' else -.25,y=.55 if k=='wind' else -.15,awake=True)
        drum.rotation_euler[2]=t*.55;mini.rotation_euler[2]=t*.55;wind.rotation_euler[0]=t*1.8
        if k=='lantern_macro':camera((21.8,-2.7,2.5),(20,.5,1.45),85);backkey.data.energy=180
        elif k=='backstage':camera((23.3,-7.5,3.6),(19.7,.5,1.45),58);backkey.data.energy=480
        elif k=='mechanism':camera((20.8,-2.4,2.15),(20,.4,1.52),80);backkey.data.energy=340;cam.data.dof.aperture_fstop=5.6
        else:camera((22.4,-5.7,2.9),(20.65,.4,1.48),67);backkey.data.energy=480
    if isride:
        kind=k.split('_')[0];root=ride_roots[kind];parts=ride_parts[kind];rot=ride_rotors[kind]
        rot.rotation_euler=(0,0,0)
        if kind=='ferris':rot.rotation_euler[1]=.05*math.sin(t*3) if k.endswith('broken') else 0
        else:rot.rotation_euler[2]=.22*math.sin(t*.7) if k.endswith('broken') else .04*t
        for j,(o,loc,rotation,scale) in enumerate(parts):
            o.location=loc;o.rotation_euler=rotation;o.scale=scale
            if k.endswith('assemble') or k.endswith('dismantle'):
                q=quant(u/.72,18) if k.endswith('assemble') else 1-quant((u-.13)/.78,18)
                # Each material piece rises from a small pile into its own slot.
                progress=smooth((q-j/max(1,len(parts))*.70)/.30)
                o.scale=scale*max(.012,progress)
                o.location=loc+Vector((.24*math.sin(j)* (1-progress),.15*math.cos(j)*(1-progress),-min(loc.z,1.2)*(1-progress)))
        if kind=='ferris':
            for cab,a in ride_defects[kind]:cab.rotation_euler[1]=-rot.rotation_euler[1]
        camera((44,-10.8,5),(40,0,1.90),54)
        if k.endswith('broken'):
            if kind=='ferris':camera((42.1,-7.6,4.0),(40.35,0,2.40),64)
            elif kind=='carousel':camera((38.3,-5.0,2.5),(39.475,-.91,1.38),59)
            else:camera((40.3,-6.4,2.5),(40,-1.03,1.65),65)
    scene.frame_set(frame+1)
    return {'frame':frame,'pose_frame':pose,'seconds':round(t,6),'shot':shot['id'],'kind':k,'camera':list(cam.location),'target':list(focus.location),'monochrome':isride}

extension=Path(__file__).with_name('refinements.py')
if args.revision>1:
    exec(compile(extension.read_text(),str(extension),'exec'),globals())
recipe=args.run/'recipe';recipe.mkdir(exist_ok=True)
fingerprint=hashlib.sha256(Path(__file__).read_bytes()+(args.run/'timeline.json').read_bytes()+(extension.read_bytes() if args.revision>1 else b'')+str(args.revision).encode()).hexdigest()
manifest=args.output/'render.json'
if manifest.exists() and json.loads(manifest.read_text()).get('recipe_sha256')!=fingerprint:
    raise RuntimeError('Changed render recipe; use a new output directory.')
manifest.write_text(json.dumps({'recipe_sha256':fingerprint,'revision':args.revision,'height':args.height,'engine':args.engine,'samples':args.samples,'fps':24,'pose_fps':8},indent=2)+'\n')
if args.frame_list:
    records=[]
    for frame in args.frame_list:
        info=at_frame(frame);path=args.output/f'frame-{frame:05d}.png'
        scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        records.append({'file':path.name,**info})
    (args.output/'frames.json').write_text(json.dumps(records,indent=2)+'\n')
elif args.stills:
    records=[]
    for s in spec['shots']:
        frame=(s['start_frame']+s['end_frame'])//2;info=at_frame(frame);path=args.output/(s['id']+'-'+s['kind']+'.png')
        if not path.exists():scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        records.append({'file':path.name,**info});print('STILL',s['id'],flush=True)
    (args.output/'stills.json').write_text(json.dumps(records,indent=2)+'\n')
elif args.frame is not None:
    info=at_frame(args.frame);scene.render.filepath=str(args.output/f'frame-{args.frame:05d}.png');bpy.ops.render.render(write_still=True)
    (args.output/'frame.json').write_text(json.dumps(info,indent=2)+'\n')
else:
    if args.worker:
        captured=hashlib.sha256((recipe/'render.py').read_bytes()+(recipe/'timeline.json').read_bytes()+((recipe/'refinements.py').read_bytes() if args.revision>1 else b'')+str(args.revision).encode()).hexdigest()
        if captured!=fingerprint:raise RuntimeError('Worker must match the captured recipe')
        at_frame(0)
    else:
        shutil.copy2(__file__,recipe/'render.py');shutil.copy2(args.run/'timeline.json',recipe/'timeline.json')
        if args.revision>1:shutil.copy2(extension,recipe/'refinements.py')
        at_frame(0);bpy.ops.wm.save_as_mainfile(filepath=str(recipe/'miniatures.blend'))
    end=min(args.end or spec['frames'],spec['frames']);cache={};starttime=time.time();rendered=0
    for frame in range(args.start,end):
        target=args.output/f'frame-{frame:05d}.png'
        shot=next(s for s in spec['shots'] if s['start_frame']<=frame<s['end_frame']);pose=max(shot['start_frame'],frame//3*3);sig=(shot['id'],pose)
        if target.exists():cache[sig]=target;continue
        if sig in cache:os.link(cache[sig],target);continue
        if shutil.disk_usage(args.run).free<5*1024**3:raise RuntimeError('Stopped before storage reserve exhausted')
        at_frame(frame);scene.render.filepath=str(target);bpy.ops.render.render(write_still=True);cache[sig]=target;rendered+=1
        if rendered%8==0:print(json.dumps({'frame':frame,'of':spec['frames'],'renders':rendered,'elapsed_s':round(time.time()-starttime,1),'shot':shot['id']}),flush=True)
    print('RENDER_COMPLETE',end,flush=True)
