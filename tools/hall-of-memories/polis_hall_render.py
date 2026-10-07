"""Local Hall, fictional record miniatures, and a facet-based coordinate change."""
import runpy
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
original_argv=sys.argv[:]
sys.argv=[*sys.argv,'--setup-only']
shared=runpy.run_path(str(HERE/'polis_render.py'))
sys.argv=original_argv
for key,value in shared.items():
    if not key.startswith('__'):globals()[key]=value
args.setup_only='--setup-only' in original_argv
# The Hall stands east of the established court, beyond its earlier coverage.
# Its interior is only an unplayed archive, with no human depiction or sound.
hallroot=empty('Hall architectural origin',(16,3,0));hallroot.rotation_euler[2]=-math.pi/2
def hall(obj):obj.parent=hallroot;return obj
hallmat=material('Hall muted violet stone',(.29,.29,.335),.9,.009)
interior=material('Hall inner slate',(.105,.115,.145),.92,.008)
archive=material('unplayed archive panels',(.17,.20,.22),.85,.003)
lamp=material('Hall quiet amber seam',(.48,.23,.075),.8,emission=.45)
hall(cube('Hall foundation',(0,3,-.12),(17,9,.28),stone,.05))
for side in [-1,1]:
    hall(cube('Hall front wing',(side*5.0,.28,3.6),(6,.7,7.2),hallmat,.12))
    hall(cube('Hall doorway reveal',(side*2.02,.12,2.7),(.20,1,5.4),lightstone,.05))
    hall(cube('Hall side wall',(side*8,4,3.6),(.4,8,7.2),hallmat,.10))
hall(cube('Hall lintel',(0,.28,6.2),(4.15,.7,2.0),hallmat,.08))
hall(cube('Hall doorway head',(0,.1,5.3),(4.2,1,.22),lightstone,.04))
hall(cube('Hall ceiling',(0,4,7.25),(16.3,8.4,.28),hallmat,.06))
hall(cube('Hall inner back wall',(0,8,3.5),(16,.35,7),interior,.05))
hall(cube('Hall inner floor',(0,4,.035),(16,8,.05),interior,.01))
for x in [-5.3,-3.6,-1.9,0,1.9,3.6,5.3]:
    for z in [1.1,2.2,3.3,4.4]:
        hall(cube('unplayed memory cabinet',(x,7.75,z),(1.25,.22,.76),archive,.035))
        hall(cube('cabinet lower seam',(x,7.60,z-.31),(1.02,.015,.015),lamp,.002))
for y in [1.5,3.5,5.5]:
    hall(cube('interior paving seam',(0,y,.064),(3.7,.025,.008),lightstone,.001))
# Exact local lettering, not generated image text.
font=bpy.data.curves.new('Hall name lettering','FONT');font.body='HALL OF MEMORIES'
font.align_x='CENTER';font.align_y='CENTER';font.size=.31;font.space_character=1.2;font.extrude=.001
sign=bpy.data.objects.new('Hall of Memories / exact inscription',font);scene.collection.objects.link(sign)
sign.data.materials.append(lightstone);sign.parent=hallroot;sign.location=(0,-.092,5.88);sign.rotation_euler=(math.pi/2,0,0)
for x in [4.0,5.35,6.7,8.05,9.4,10.75,12.1,13.45,14.8]:
    cube('eastward path slab',(x,3,.018),(1.13,3.8,.06),lightstone,.04)
area('Hall soft exterior',(11,-4,8),(16,3,3),1700,(.78,.79,1),8)
area('Hall interior reflected light',(19,3,5.8),(22,3,2),430,(.80,.70,.55),5)

START={name:Vector(pos) for name,pos in BASE.items()}
FINISH={'elder':Vector((14.65,3.1,.03)),'story':Vector((12.8,2.1,.03)),
        'challenge':Vector((12.6,4.65,.03)),'quiet':Vector((11.75,3.2,.03))}
WALK={'elder':(0,1.125),'story':(.34,.875),'challenge':(.14,.875),'quiet':(.60,.875)}

def angle_mix(a,b,q):return a+((b-a+math.pi)%math.tau-math.pi)*q

def standing_legs(p,phase=None,amount=1,stride=.23):
    """Extend the same child limbs from seat to planted, then held walk poses."""
    for i,side in enumerate([-1,1]):
        foot_seat=Vector((side*.16,-.51,.075));knee_seat=Vector((side*.15,-.46,.59))
        # Fixed support foot travels backwards locally while the root advances.
        if phase is None:foot_stand=Vector((side*.15,-.03,.085));knee_stand=Vector((side*.15,-.035,.36))
        else:
            f=(phase/math.tau+i*.5)%1
            if f<.5:along=-stride+4*stride*f;lift=0
            else:
                u=(f-.5)*2;along=stride-2*stride*u;lift=.11*math.sin(math.pi*u)
            foot_stand=Vector((side*.15,along,.085+lift));knee_stand=Vector((side*.15,along*.45-.055,.37+lift*.35))
        hip=(side*.12,.02,.72 if p.elder else .66)
        knee=knee_seat.lerp(knee_stand,amount);foot=foot_seat.lerp(foot_stand,amount)
        set_bone(p.legs[i][0],hip,knee,.090);set_bone(p.legs[i][1],knee,foot,.072)
        p.feet[i].location=foot;p.feet[i].rotation_euler=(0,0,0)


shots=timeline['shots'];by={s['id']:s for s in shots};cues=timeline['cues'];count=round(duration*8)
end=min(args.end if args.end is not None else count,count)
scene.render.image_settings.compression=65
# Screen sits on the existing back wall. Other cabinets remain an archive.
selectedmat=material('selected record warm light',(.56,.34,.16),.8,emission=.65)
hall(cube('selected record frame',(0,7.43,3.25),(3.15,.18,2.0),darkstone,.045))
hall(cube('selected record surface',(0,7.31,3.25),(2.90,.035,1.75),selectedmat,.015))
def label(name,text,pos,size,parent,mat):
    c=bpy.data.curves.new(name,'FONT');c.body=text;c.align_x='CENTER';c.align_y='CENTER';c.size=size;c.extrude=.001
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.parent=parent;o.location=pos;o.rotation_euler=(math.pi/2,0,0);c.materials.append(mat);return o
label('fictional selected record','MARA',(0,7.275,3.25),.26,hallroot,darkstone)
area('archive soft key',(20,1,6),(20,4,1.4),750,(.82,.78,.66),5)
area('archive warm reflection',(23,3,4),(20,3,1.4),450,(1,.67,.39),4)
INSIDE={'elder':Vector((20.9,1.25,.08)),'story':Vector((19.65,1.2,.08)),
        'challenge':Vector((20.4,5.1,.08)),'quiet':Vector((19.2,3.35,.08))}

# An original tactile human miniature, distinct from the polis avatar family.
recordroot=empty('fictional memory room',(80,0,0))
record_objects=[]
def rec(o):o.parent=recordroot;record_objects.append(o);return o
plaster=material('record warm plaster',(.43,.35,.25),.93,.025)
wood=material('record worn wood',(.15,.074,.034),.86,.012)
blue=material('canonical chipped blue cup',(.025,.18,.27),.36,.003)
skin=material('Mara terracotta skin',(.46,.235,.13),.9,.006)
father_skin=material('father warm skin',(.48,.30,.20),.9,.006)
hair=material('Mara dark brown hair',(.045,.021,.014),.93,.006)
greyhair=material('father grey hair',(.28,.27,.235),.9,.007)
cloth=material('Mara rust cardigan',(.30,.065,.031),.98,.009)
cream=material('record cream linen',(.53,.48,.38),.96,.015)
ink=material('human eyes',(.012,.009,.007),.85)
rec(cube('record floor',(0,0,-.10),(12,10,.2),wood,.02))
rec(cube('record rear wall',(0,2.8,2.3),(12,.15,4.6),plaster,.02))
for x in [-3.4,0,3.4]:rec(cube('record vertical wall seam',(x,2.69,2.3),(.018,.01,4.3),wood,.002))
rec(cube('window dark reveal',(-2.8,2.65,2.7),(2.6,.12,2.4),wood,.02))
windowmat=material('window muted afternoon',(.44,.47,.49),.9,emission=.8)
rec(cube('window light',(-2.8,2.56,2.7),(2.4,.04,2.2),windowmat,.01))
for x in [-2.8]:rec(cube('window mullion',(x,2.50,2.7),(.075,.07,2.25),wood,.01))
rec(cube('window cross',(-2.8,2.5,2.7),(2.4,.07,.07),wood,.01))
table=rec(cube('same kitchen table',(0,0,.84),(3.4,1.8,.12),wood,.04))
for x in [-1.35,1.35]:
    for y in [-.6,.6]:rec(cube('table leg',(x,y,.41),(.1,.1,.8),wood,.02))

def human(name,mat,coat,hmat):
    root=rec(empty(name));parts=[]
    def child(o):o.parent=root;parts.append(o);return o
    child(ellipsoid(name+' torso',(0,0,1.1),(.28,.2,.43),coat))
    child(ellipsoid(name+' neck',(0,0,1.53),(.09,.09,.12),mat))
    head=child(empty(name+' head',(0,0,1.8)))
    def face(o):o.parent=head;parts.append(o);return o
    face(ellipsoid(name+' face',(0,0,0),(.205,.18,.27),mat))
    face(ellipsoid(name+' hair cap',(0,.055,.13),(.216,.17,.17),hmat))
    face(ellipsoid(name+' nose',(0,-.187,-.02),(.045,.055,.065),mat))
    for side in [-1,1]:face(ellipsoid(name+' eye',(side*.078,-.172,.033),(.018,.010,.014),ink))
    face(ellipsoid(name+' mouth',(0,-.170,-.108),(.048,.008,.009),wood))
    arms=[]
    for side in [-1,1]:
        a=child(capsule(name+' arm',(side*.24,0,1.37),(side*.32,-.22,.94),.08,coat,None))
        b=child(capsule(name+' forearm',(side*.32,-.22,.94),(side*.28,-.53,.92),.065,coat,None))
        hand=child(ellipsoid(name+' hand',(side*.28,-.53,.92),(.07,.11,.045),mat));arms.append((a,b,hand))
        child(capsule(name+' trouser',(side*.13,0,.80),(side*.15,-.22,.32),.09,wood,None))
    return {'root':root,'head':head,'arms':arms,'parts':parts}

mara=human('Mara',skin,cloth,hair);dad=human('father',father_skin,cream,greyhair)
partner=human('silent recipient',father_skin,wood,hair)
# The audience sees the cup's light chip and handle in all four fragments.
def cup(name,pos):
    root=rec(empty(name,pos))
    def part(o):o.parent=root;return o
    part(cylinder(name+' body',(0,0,.10),.11,.20,blue))
    tea=material(name+' tea',(.045,.019,.005),.25)
    part(cylinder(name+' open tea surface',(0,0,.202),.09,.008,tea))
    bpy.ops.mesh.primitive_torus_add(major_radius=.065,minor_radius=.018,major_segments=24,minor_segments=8,location=(.14,0,.11),rotation=(math.pi/2,0,0))
    part(finish(bpy.context.object,name+' handle',blue))
    part(cube(name+' pale chip',(-.065,-.073,.195),(.037,.018,.024),cream,.004))
    return root
cup1=cup('blue cup with pale chip',(-.72,-.30,.90));cup2=cup('second cup',(1,-.2,.90))
letter=rec(cube('private letter',(.2,-.30,.915),(.60,.40,.008),cream,.002));letter.rotation_euler[2]=.16
# No readable private text or real record identifiers.
for j in range(5):
    o=rec(cube('unreadable ink stroke',(.2,-.42+j*.045,.924),(.40,.009,.001),wood,0));o.parent=letter;o.matrix_parent_inverse=letter.matrix_world.inverted()
bedroot=rec(empty('bedside setting'))
for o in [cube('bed frame',(0,0,.54),(2.1,1.2,.15),wood,.05),cube('linen cover',(0,0,.76),(2.0,1.12,.36),cream,.12),ellipsoid('pillow',(.68,0,.96),(.37,.47,.12),cream),cube('bed quilt',(-.35,0,1.08),(1.30,1.10,.36),cream,.12)]:o.parent=bedroot
area('record window key',(76,-2,5),(80,0,1),850,(1,.78,.51),4)
area('record fill',(83,-4,3),(80,0,1),260,(.73,.79,1),4)

# Spoon and chairs complete the ordinary tea-table action.
spoon=empty('father teaspoon',parent=dad['root'])
for o in [capsule('spoon handle',(0,0,0),(0,-.20,0),.008,cream,None),ellipsoid('spoon bowl',(0,-.23,0),(.031,.045,.010),cream)]:o.parent=spoon
for x in [-.85,.90]:
    rec(cube('kitchen chair seat',(x,.56,.60),(.62,.66,.10),wood,.03))
    rec(cube('kitchen chair back',(x,.89,1.04),(.63,.07,.88),wood,.04))
# Each cabinet is activated separately as individual voices enter.
archive_mats=[]
for obj in scene.objects:
    if obj.name.startswith('unplayed memory cabinet'):
        mat=obj.data.materials[0].copy();mat.name='individual archive light';obj.data.materials[0]=mat;archive_mats.append(mat)

# GEM-01: one reusable mesh, same uneven six-sided outline and diagonal inclusion.
gemroot=empty('GEM-01 housing origin',(80,20,0))
green=material('GEM-01 deep emerald',(.008,.16,.065),.21,.001)
green.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=.40
outline=[(-.76,-.60),(.36,-.80),(.85,-.15),(.60,.72),(-.40,.90),(-.90,.18)]
verts=[(x,-.30,z) for x,z in outline]+[(x*1.35,.10,z*1.35) for x,z in outline]+[(x*.72,.65,z*.72) for x,z in outline]
faces=[tuple(range(6))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]+[(i+6,(i+1)%6+6,(i+1)%6+12,i+12) for i in range(6)]+[tuple(range(12,18))]
mesh=bpy.data.meshes.new('GEM-01 canonical facets');mesh.from_pydata(verts,[],faces);mesh.update()
gem=bpy.data.objects.new('GEM-01 six-sided housing',mesh);scene.collection.objects.link(gem);gem.parent=gemroot;mesh.materials.append(green)
inclusion=material('GEM-01 pale diagonal inclusion',(.39,.61,.39),.3,emission=.12)
for i in range(7):
    x=-.51+i*.135;z=-.35+i*.12
    o=cube('GEM-01 pale inclusion segment',(x,-.308,z),(.18,.009,.014),inclusion,.003);o.rotation_euler[1]=-.63;o.parent=gemroot
rockmat=material('rock rough umber slate',(.105,.085,.061),.97,.09)
rng=__import__('random').Random(928)
for i in range(40):
    x=rng.uniform(-5,5);z=rng.uniform(-3,3)
    if abs(x)<1.35 and abs(z)<1.35:continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,.48+rng.uniform(-.12,.4),z))
    o=finish(bpy.context.object,'surrounding native rock',rockmat,gemroot);o.scale=(rng.uniform(.45,1.6),rng.uniform(.3,.65),rng.uniform(.35,1))
    o.rotation_euler=(rng.random(),rng.random(),rng.random())
o=cube('unbroken surrounding rock backing',(0,1.3,0),(12,.65,8),rockmat,.1);o.parent=gemroot
area('jewel grazing light',(77,15,4),(80,20,0),670,(.71,.88,1),3)
area('jewel warm rock edge',(83,18,1),(80,20,0),260,(1,.73,.40),2)
# The previous exterior image will occupy a facet, then dissolve into mineral.
facetmat=bpy.data.materials.new('simulation image on facet');facetmat.use_nodes=True
nn=facetmat.node_tree.nodes;ll=facetmat.node_tree.links;nn.clear()
outnode=nn.new('ShaderNodeOutputMaterial');mixnode=nn.new('ShaderNodeMixShader');transparent=nn.new('ShaderNodeBsdfTransparent');emit=nn.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=.7
tex=nn.new('ShaderNodeTexImage');tex.extension='EXTEND'
texture=args.run/'assets/hall-facet.png'
if texture.exists():tex.image=bpy.data.images.load(str(texture.resolve()),check_existing=True)
else:emit.inputs['Color'].default_value=(.4,.5,.37,1)
if tex.image:ll.new(tex.outputs['Color'],emit.inputs['Color'])
ll.new(emit.outputs[0],mixnode.inputs[1]);ll.new(transparent.outputs[0],mixnode.inputs[2]);ll.new(mixnode.outputs[0],outnode.inputs['Surface'])
fmesh=bpy.data.meshes.new('conceptual image facet');fmesh.from_pydata([(x*.997,-.316,z*.997) for x,z in outline],[],[tuple(range(6))]);fmesh.update()
facet=bpy.data.objects.new('simulation inside the physical facet',fmesh);scene.collection.objects.link(facet);facet.parent=gemroot;fmesh.materials.append(facetmat)
uv=fmesh.uv_layers.new(name='facet image coordinates')
for poly in fmesh.polygons:
    for li in poly.loop_indices:
        v=fmesh.vertices[fmesh.loops[li].vertex_index].co;uv.data[li].uv=(v.x/1.104+.5,(v.z-.035)/.621+.5)

# Deterministic restrained acting. Holds are intentional, with no random fidget.
def active(t):return next((s for s in shots if s['start']<=t<s['end']),shots[-1])
def camera_set(pos,target,lens=48,fstop=8):
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lens;camera.data.dof.focus_distance=(Vector(target)-camera.location).length;camera.data.dof.aperture_fstop=fstop

def pose_record(shot,t):
    for h in [mara,dad,partner]:
        h['root'].scale=(1,1,1);h['root'].rotation_euler=(0,0,0);h['head'].rotation_euler=(0,0,0)
    mara['root'].location=(-.85,.55,0);dad['root'].location=(.90,.55,0);partner['root'].location=(20,0,0)
    table.location.z=.84;bedroot.location=(20,0,0);letter.location.z=-4
    for obj in record_objects:
        if obj.name.startswith('table leg'):obj.location.z=-4 if shot=='bedside' else .41
        elif obj.name.startswith('kitchen chair seat'):obj.location.z=-4 if shot=='bedside' else .60
        elif obj.name.startswith('kitchen chair back'):obj.location.z=-4 if shot=='bedside' else 1.04
    cup1.location=(-.72,-.3,.9);cup2.location=(1,-.2,.9)
    if shot=='warm':
        q=smooth((t-by['H03']['start']-.5)/1.0)
        mara['head'].rotation_euler[2]=-.25;dad['head'].rotation_euler[2]=.20
        # Small spoon offer, then a pose held for the joke.
        a,b,h=dad['arms'][0];hand=Vector((-.28,-.53,.92)).lerp(Vector((-.43,-.41,1.15)),q)
        set_bone(b,(-.32,-.22,.94),hand,.065);h.location=hand
    else:
        a,b,h=dad['arms'][0];set_bone(b,(-.32,-.22,.94),(-.28,-.53,.92),.065);h.location=(-.28,-.53,.92)
    if shot=='letter':
        dad['root'].location=(20,0,0);partner['root'].location=(1,.50,0);partner['head'].rotation_euler[0]=.15
        letter.location.z=.915;mara['head'].rotation_euler[2]=-.25
    elif shot=='bedside':
        table.location.z=-4;bedroot.location=(0,.30,0)
        dad['root'].location=(-.66,.45,1.08);dad['root'].rotation_euler[1]=math.pi/2;dad['root'].scale=(.70,.70,.70)
        mara['root'].location=(-1.15,-.20,0);mara['head'].rotation_euler[0]=.18;mara['head'].rotation_euler[2]=-.30
        cup1.location=(-1.0,-.72,.70);cup2.location.z=-4
    elif shot=='empty':
        dad['root'].location=(20,0,0);mara['root'].location=(-.85,.55,0);mara['head'].rotation_euler[0]=.15
        q=smooth((t-by['H07']['start']-.2)/1.0);cup2.location=(.45+.55*q,-.2,.90)
    spoon.location=dad['arms'][0][2].location+Vector((0,-.045,.04))
    spoon.scale=(1,1,1) if shot=='warm' else (0,0,0)
    target=(80,0,1.10)
    if shot=='bedside':camera_set((77.0,-4.2,2.9),(79.8,.0,1.0),53,6.5)
    elif shot=='empty':camera_set((81.7,-5.0,2.45),(80,.05,1.20),53,6.5)
    elif shot=='letter':camera_set((79.2,-4.8,2.65),(80,0,1.03),55,8)
    else:camera_set((80,-5.6,2.5),target,51,7)


def pose_hall(t):
    t=math.floor(t*8+1e-6)/8;s=active(t);shot=s['shot'];local=t-s['start']
    # Preserve the exact last entrance marks; stagger through the open doorway.
    for name,p in puppets.items():
        offset,period=WALK[name];offset=.90 if name=='quiet' else offset;q=max(0,min(1,(t-offset)/5.8))
        via=Vector((16.4,3+({'elder':-.1,'story':-.48,'challenge':.50,'quiet':0}[name]),.08))
        split=.28 if name=='elder' else .52
        if q<split:pos=FINISH[name].lerp(via,q/split);toward=via-FINISH[name]
        else:pos=via.lerp(INSIDE[name],(q-split)/(1-split));toward=INSIDE[name]-via
        p.root.location=pos
        yaw=math.atan2(toward.x,-toward.y) if q<1 else math.pi/2
        p.root.rotation_euler[2]=yaw
        gesture='rest';amount=0;head=0
        line=next((l for l in lines if l['speaker']==name and l['start']-.2<=t<=l['end']+.8),None)
        if line:
            gesture=line.get('gesture','rest');amount=smooth((t-line['start']+.2)/.4)*(1-smooth((t-line['end']-.1)/.8))
        if shot in ['elder','select'] and name=='elder':
            p.root.rotation_euler[2]=-2.5;head=0
        if shot=='quiet' and name=='quiet':p.root.rotation_euler[2]=.4
        if shot=='first_voice' and t>cues['first_voice']+1 and name=='quiet':
            gesture='alone';amount=smooth((t-cues['first_voice']-1)/.75);head=-.08
        p.pose(gesture,amount,head,0)
        phase=t*math.tau/period if 0<q<1 else None
        standing_legs(p,phase,1,.19)
    mixnode.inputs[0].default_value=1
    for i,mat in enumerate(archive_mats):
        at=cues['many']+([0,2.5,5,7,8.5,10,11.1,12,12.8,13.5,14,14.4][i%12])+(i//12)*.2
        strength=.65*smooth((t-at)/.75) if t>=cues['many'] else 0
        node=mat.node_tree.nodes.get('Principled BSDF');node.inputs['Emission Color'].default_value=(.48,.31,.16,1);node.inputs['Emission Strength'].default_value=strength
    if shot=='enter':
        if t<3.5:camera_set((6.0,-3.7,3.5),(15.5,3.0,2.65),28,8)
        else:camera_set((22.5,4.6,3.3),(17.4,3.0,1.8),34,9)
    elif shot=='select':camera_set((18,-.20,2.9),(22,2.6,2.35),37,8)
    elif shot in ['warm','letter','bedside','empty']:pose_record(shot,t)
    elif shot=='elder':camera_set((18.8,4.4,2.8),(20.9,1.25,2.02),52,6.5)
    elif shot=='quiet' or (shot=='first_voice' and local>=2.25):camera_set((22.4,1.8,2.05),(19.2,3.35,1.35),64,6.5)
    elif shot=='first_voice':camera_set((18.0,3.0,2.5),(23.3,3.0,3.2),62,8)
    elif shot=='many':
        if local<6:camera_set((18.2,-.1,3.2),(21.1,3.2,2.35),34,9)
        else:
            q=smooth((local-6)/11);camera_set(Vector((19,2.9,3.9)).lerp(Vector((16.7,3,4.6)),q),(23,3,2.75),26,11)
    elif shot=='withdraw':
        q=smooth(local/7);camera_set(Vector((13.8,-.4,3.4)).lerp(Vector((5,-4,4.8)),q),(16,3,3.0),35,11)
    elif shot in ['facet','jewel']:
        if shot=='facet':
            q=smooth(local/4.5);mixnode.inputs[0].default_value=smooth((local-1.1)/2.9)
            camera_set((80,18.12-2.9*q,.035),(80,20,.035),51,10)
        else:
            q=smooth(local/3.5);camera_set((80,15.22-2.0*q,.035),(80,20,.035),51,10)
    bpy.context.view_layer.update()
    return {'time':t,'shot':shot,'id':s['id']}

SOURCES=['polis_render.py','polis_hall_render.py','polis_audio.py','polis_hall_audio.py','sound.py','polis_hall.json','polis_hall_verify.py']
pose_hall(0)
if args.setup_only:
    pass
elif args.bake_only:
    target=(args.output/'polis-hall-animation.blend').resolve()
    if target.exists():raise RuntimeError('Refusing existing animation')
    animated=[o for o in scene.objects if o.type in ['MESH','EMPTY','CAMERA']]
    for i in range(count):
        f=i*3+1;scene.frame_set(f);pose_hall(i/8)
        for obj in animated:
            for prop in ['location','rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:obj.keyframe_insert(data_path=prop,frame=f)
        for prop in ['lens']:camera.data.keyframe_insert(data_path=prop,frame=f)
        for prop in ['focus_distance','aperture_fstop']:camera.data.dof.keyframe_insert(data_path=prop,frame=f)
        mixnode.inputs[0].keyframe_insert(data_path='default_value',frame=f)
        for mat in archive_mats:mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].keyframe_insert(data_path='default_value',frame=f)
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for key in curve.keyframe_points:key.interpolation='CONSTANT'
    scene.frame_start=1;scene.frame_end=round(duration*24);scene.frame_set(1)
    strip=scene.sequence_editor_create().strips.new_sound('Hall editable scratch mix',str((args.run/'audio/mix.wav').resolve()),channel=1,frame_start=1)
    strip.sound.filepath='//'+os.path.relpath((args.run/'audio/mix.wav').resolve(),args.output.resolve())
    for img in bpy.data.images:
        if img.source=='FILE' and img.filepath:img.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
    (args.output/'bake.json').write_text(json.dumps({'frames':scene.frame_end,'source_poses':count,'fps':24,'objects':len(animated),'interpolation':'CONSTANT'},indent=2)+'\n')
elif args.stills:
    selected=[('01-entry',0),('02-select',by['H02']['start']+1),('03-warm',by['H03']['start']+2),('04-letter',by['H05']['start']+2),('05-bedside',by['H06']['start']+2),('06-empty',by['H07']['start']+2),('07-quiet',by['H08']['start']+.8),('08-elder',by['H09']['start']+1),('09-first-voice',by['H10']['start']+3),('10-many',by['H13']['start']+10),('11-withdraw',by['H14']['end']-.125),('12-facet',by['H15']['start']+1.5),('13-jewel',duration-.125)]
    meta=[]
    for name,t in selected:
        info=pose_hall(t);scene.render.filepath=str((args.output/f'{name}.png').resolve());bpy.ops.render.render(write_still=True);meta.append({'file':name+'.png',**info})
    (args.output/'frames.json').write_text(json.dumps(meta,indent=2)+'\n')
else:
    if any((args.output/f'frame-{i:05d}.png').exists() for i in range(args.start,end)):raise RuntimeError('Refusing existing rendered range')
    recipe=args.output.parent/'recipe';recipe.mkdir(exist_ok=True)
    for name in SOURCES:
        source=HERE/name;dest=recipe/name
        if dest.exists() and dest.read_bytes()!=source.read_bytes():raise RuntimeError('Changed recipe on resume')
        if not dest.exists():shutil.copy2(source,dest)
    dest=recipe/'timeline.json'
    if dest.exists() and dest.read_bytes()!=(args.run/'timeline.json').read_bytes():raise RuntimeError('Changed timeline on resume')
    if not dest.exists():shutil.copy2(args.run/'timeline.json',dest)
    scene_file=(args.output.parent/'polis-hall-scene.blend').resolve()
    if not scene_file.exists():bpy.ops.wm.save_as_mainfile(filepath=str(scene_file),compress=True)
    meta=[];cache={};started=time.time()
    for i in range(args.start,end):
        path=args.output/f'frame-{i:05d}.png';info=pose_hall(i/8);scene.render.filepath=str(path.resolve())
        state=[round(v,6) for obj in scene.objects if obj.type in ['MESH','CAMERA'] for row in obj.matrix_world for v in row]
        state += [camera.data.lens,camera.data.dof.focus_distance,camera.data.dof.aperture_fstop,mixnode.inputs[0].default_value]+[mat.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value for mat in archive_mats]
        sig=hashlib.sha256(json.dumps(state).encode()).hexdigest();previous=cache.get(sig)
        if previous is None:
            if shutil.disk_usage(args.run).free<450*1024**2:raise RuntimeError('Storage reserve reached; preserve existing output and resume later')
            bpy.ops.render.render(write_still=True);cache[sig]=path
        else:os.link(previous,path)
        meta.append({'frame':i,'cached_pose':None if previous is None else previous.name,**info})
        if i%16==0:print(f'HALL_PROGRESS {i+1}/{count} unique={len(cache)} elapsed={time.time()-started:.1f}s',flush=True)
    (args.output/f'frames-{args.start:05d}-{end:05d}.json').write_text(json.dumps(meta,indent=2)+'\n')
print('HALL_RENDER_DONE',flush=True)
