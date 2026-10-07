"""Persistent locally modeled polis, posed at eight samples/second.

Run inside Blender. No provider calls, raster replacements or optical flow.
"""
import argparse, hashlib, json, math, os, shutil, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser()
ap.add_argument('--run',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
ap.add_argument('--height',type=int,default=1080)
ap.add_argument('--samples',type=int,default=32)
ap.add_argument('--engine',choices=['eevee','cycles'],default='cycles')
ap.add_argument('--stills',action='store_true')
ap.add_argument('--bake-only',action='store_true')
ap.add_argument('--setup-only',action='store_true',help='Build the shared polis set and puppets for another scene recipe.')
ap.add_argument('--start',type=int,default=0)
ap.add_argument('--end',type=int)
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
timeline=json.loads((args.run/'timeline.json').read_text())
lines=timeline['lines'];duration=timeline['duration']
args.output.mkdir(parents=True,exist_ok=True)
if args.stills and any(args.output.glob('*.png')):
    raise RuntimeError('Refusing existing still-study images.')
if args.bake_only and (args.output/'polis-animation.blend').exists():
    raise RuntimeError('Refusing existing animation file.')
if not args.stills and not args.bake_only and not args.setup_only:
    end=min(args.end or math.ceil(duration*8),math.ceil(duration*8))
    if any((args.output/f'frame-{i:05d}.png').exists() for i in range(args.start,end)):
        raise RuntimeError('Refusing existing rendered frames before scene creation.')

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
if args.engine=='cycles':
    scene.render.engine='CYCLES'
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='METAL';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='METAL'
    scene.cycles.device='GPU';scene.cycles.samples=args.samples
    scene.cycles.use_denoising=True;scene.cycles.use_animated_seed=False;scene.cycles.seed=926
    scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
    scene.render.use_persistent_data=True
else:
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples=args.samples
    scene.eevee.use_raytracing=False
scene.render.resolution_x=args.height*16//9;scene.render.resolution_y=args.height
scene.render.resolution_percentage=100;scene.render.fps=24
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.use_file_extension=True;scene.render.film_transparent=False
scene.render.use_motion_blur=False
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.31,.30,.39,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.20
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.25
scene.use_nodes=True
nodes=scene.node_tree.nodes;nodes.clear()
source=nodes.new('CompositorNodeRLayers');glow=nodes.new('CompositorNodeGlare')
glow.glare_type='FOG_GLOW';glow.quality='HIGH';glow.threshold=1.3;glow.size=7
output=nodes.new('CompositorNodeComposite')
scene.node_tree.links.new(source.outputs['Image'],glow.inputs['Image'])
scene.node_tree.links.new(glow.outputs['Image'],output.inputs['Image'])

def material(name,color,rough=.8,bump=.0,emission=0):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    if bump:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=130 if 'graphite' in name else 22
        tex.inputs['Detail'].default_value=2;tex.inputs['Roughness'].default_value=.65
        b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.20;b.inputs['Distance'].default_value=bump
        l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs['Normal'],p.inputs['Normal'])
    return mat

stone=material('chalk stone / warm putty',(.38,.39,.355),.86,.012)
lightstone=material('chalk stone / pale edges',(.48,.49,.445),.83,.01)
darkstone=material('deep seams',(.20,.225,.224),.9)
violet=material('distant mauve plaster',(.255,.25,.30),.93,.009)
graphite=material('graphite puppet / soft matte',(.040,.047,.057),.77,.002)
graphite2=material('graphite puppet / challenger',(.050,.058,.063),.78,.002)
graphite3=material('graphite puppet / quiet',(.032,.046,.052),.78,.002)
eldermat=material('graphite puppet / elder',(.065,.073,.068),.84,.002)
jointmat=material('soft dark joint',(.047,.053,.058),.9)
amber=material('amber edge',(.95,.17,.002),.5,emission=2.0)
gold=material('yellow eye core',(1,.46,.008),.4,emission=3.3)
skydisc=material('split sky disc',(.45,.43,.40),.9,emission=.25)

def finish(obj,name,mat,parent=None):
    obj.name=name;obj.data.materials.append(mat)
    if parent:obj.parent=parent
    for face in getattr(obj.data,'polygons',[]):face.use_smooth=True
    return obj

def ellipsoid(name,pos,scale,mat,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=1,location=pos)
    obj=finish(bpy.context.object,name,mat,parent);obj.scale=scale
    return obj

def cube(name,pos,size,mat,bevel=.07):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    obj=finish(bpy.context.object,name,mat);obj.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=obj.modifiers.new('soft stone edge','BEVEL');mod.width=bevel;mod.segments=3
        norm=obj.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return obj

def cylinder(name,pos,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius,depth=depth,location=pos)
    obj=finish(bpy.context.object,name,mat)
    bevel=obj.modifiers.new('rounded lip','BEVEL');bevel.width=.04;bevel.segments=3
    obj.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return obj

def empty(name,pos=(0,0,0),parent=None):
    obj=bpy.data.objects.new(name,None);scene.collection.objects.link(obj);obj.location=pos
    if parent:obj.parent=parent
    return obj

def eye_patch(name,center_x,radius,rx,rz,offset,mat,parent):
    # Emission lies on the curved face instead of becoming a protruding button.
    vertices=[]
    for i in range(49):
        a=(i-1)*math.tau/48
        x=center_x if i==0 else center_x+radius*math.cos(a)
        z=.295 if i==0 else .295+radius*math.sin(a)
        y=-.25*math.sqrt(max(.01,1-(x/rx)**2-((z-.285)/rz)**2))-offset
        vertices.append((x,y,z))
    faces=[(0,i,1 if i==48 else i+1) for i in range(1,49)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.parent=parent
    obj.data.materials.append(mat)
    for face in mesh.polygons:face.use_smooth=True
    return obj

def capsule(name,a,b,radius,mat,parent):
    obj=ellipsoid(name,(0,0,0),(1,1,1),mat,parent)
    set_bone(obj,a,b,radius)
    return obj

def set_bone(obj,a,b,radius):
    a,b=Vector(a),Vector(b);d=b-a
    obj.location=(a+b)/2;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=d.to_track_quat('Z','Y')
    obj.scale=(radius,radius,d.length/2+radius*.3)

def arc(name,x,y,z,radius,thickness,mat,start=0,end=math.pi):
    verts=[];faces=[];count=48
    for i in range(count+1):
        angle=start+(end-start)*i/count
        for yy in [y-.18,y+.18]:
            for r in [radius-thickness,radius]:verts.append((x+r*math.cos(angle),yy,z+r*math.sin(angle)))
    for i in range(count):
        a=i*4;b=(i+1)*4
        faces += [(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,a+2+4,a+2),(a+1,a+3,b+3,b+1)]
    faces += [(0,2,3,1),(count*4,count*4+1,count*4+3,count*4+2)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.data.materials.append(mat)
    mod=obj.modifiers.new('worn edges','BEVEL');mod.width=.035;mod.segments=2
    obj.modifiers.new('weighted normals','WEIGHTED_NORMAL')
    return obj

# One coherent courtyard. No named Hall or architecture commitment is made here.
cube('continuous square',(0,4,-.20),(70,70,.4),stone,.02)
cylinder('conversation court',(0,.65,.045),3.6,.14,lightstone)
for radius in [3.12,3.42]:
    bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.012,major_segments=128,minor_segments=6,location=(0,.65,.121))
    finish(bpy.context.object,'inlaid circular joint',darkstone)
for i in range(16):
    a=i*math.tau/16
    obj=cube('radial paving joint',(math.cos(a)*3.0,.65+math.sin(a)*3.0,.119),(.018,1.06,.003),darkstone,0)
    obj.rotation_euler[2]=a-math.pi/2
for x,y in [(-1.45,.10),(1.45,.25),(0,1.45)]:
    cylinder('low stone seat',(x,y+.10,.33),.31,.43,stone)
    cylinder('seat top',(x,y+.10,.553),.32,.04,lightstone)
for i in range(7):cube('path slab',(0,4.7+i*1.3,.018),(1.42,1.08,.06),lightstone,.06)
for x,y,r,h in [(-6,7,1.25,2.7),(5,8,1.4,2.8),(-3,12,1.5,3.5),(3.1,14,1.7,3.0)]:
    for side in [-1,1]:cube('open arcade pier',(x+side*(r-.13),y,h/2),(.27,.6,h),lightstone,.06)
    arc('open arcade crown',x,y,h,r,.26,lightstone)
    cube('arcade foot',(x,y,.04),(r*2+1,1.1,.18),stone,.05)
for x,y,w,h in [(-11,16,2,6),(-8,20,3,7),(8,19,2.7,6.5),(11,13,2.2,4.9),(5,24,3,8),(-1,26,2.4,6.5)]:
    cube('distant quiet building',(x,y,h/2),(w,2,h),violet,.30)
    cube('deep narrow recess',(x,y-1.03,h*.51),(.2,.035,h*.7),darkstone,.02)
# A split, displaced disc, not a conventional sun. Fixed set geometry.
arc('upper sky half',-.65,19,6.7,1.65,1.64,skydisc,0,math.pi)
arc('lower displaced sky half',.15,19,6.60,1.65,1.64,skydisc,math.pi,math.tau)

def area(name,pos,target,power,color,size):
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.color=color;light.shape='DISK';light.size=size
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj);obj.location=pos
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
area('large soft key',(-4,-5,7),(0,1,1),1100,(1,.87,.68),7)
area('cool sky rim',(3,6,7),(0,1,1),1250,(.60,.66,1),6)
area('quiet frontal fill',(3,-4,3),(0,1,1),200,(.82,.85,1),5)

BASE={'story':(-1.45,.1,.12),'challenge':(1.45,.25,.12),'quiet':(0,1.45,.12),'elder':(3.1,-.3,.12)}
YAWS={'story':.30,'challenge':-.40,'quiet':.0,'elder':-1.5}

class Puppet:
    def __init__(self,name,mat,scale=1,elder=False):
        self.name=name;self.elder=elder;self.root=empty(name,BASE[name]);self.root.scale=(scale,scale,scale)
        self.root.rotation_euler[2]=YAWS[name]
        self.z=.15 if elder else 0
        z=self.z
        self.torso=ellipsoid(name+' soft torso',(0,0,.895+z),(.275,.185,.295),mat,self.root)
        ellipsoid(name+' pelvis',(0,.02,.66+z),(.23,.175,.135),mat,self.root)
        self.headroot=empty(name+' articulated head',(0,0,1.235+z),self.root)
        self.neck=ellipsoid(name+' neck',(0,0,1.215+z),(.13,.12,.11),mat,self.root)
        ellipsoid(name+' oval head',(0,0,.285),(.27 if elder else .29,.25,.38 if elder else .34),mat,self.headroot)
        for side in [-1,1]:
            eye_patch(name+' orange eye surround',side*.112,.058,.27 if elder else .29,.38 if elder else .34,.002,amber,self.headroot)
            eye_patch(name+' bright eye',side*.112,.047,.27 if elder else .29,.38 if elder else .34,.003,gold,self.headroot)
        self.arms=[];self.hands=[];self.legs=[];self.feet=[]
        for side in [-1,1]:
            arm=[]
            for part in ['upper','lower']:arm.append(capsule(name+' '+part+' arm',(0,0,0),(0,0,.3),.065,mat,self.root))
            hand=empty(name+' mitten',(0,0,0),self.root)
            hand.scale=(.82,.82,.82)
            ellipsoid(name+' palm',(0,0,0),(.082,.055,.105),mat,hand)
            for xx in [-.036,.009,.045]:ellipsoid(name+' rounded finger',(xx,-.008,.078),(.027,.043,.06),mat,hand)
            ellipsoid(name+' thumb',(-side*.065,-.012,.005),(.04,.048,.062),mat,hand)
            self.arms.append(arm);self.hands.append(hand)
            leg=[capsule(name+' thigh',(0,0,0),(0,0,.3),.095,mat,self.root),capsule(name+' calf',(0,0,0),(0,0,.3),.077,mat,self.root)]
            self.legs.append(leg)
            self.feet.append(ellipsoid(name+' foot',(side*.14,-.34,.07),(.115,.18,.08),mat,self.root))
        self.pose('rest',0,0,0)

    def pose(self,gesture,amount,head_yaw,head_roll,walk_phase=None):
        z=self.z
        rest=[(-.30,-.12,.70+z),(.30,-.12,.70+z)]
        goals={
            'match':[(-.49,-.12,1.24+z),(.56,-.15,1.04+z)],
            'count':[(-.32,-.22,.78+z),(.45,-.25,1.02+z)],
            'explain':[(-.45,-.25,.90+z),(.43,-.24,.89+z)],
            'point':[(-.31,-.13,.75+z),(.54,-.38,1.06+z)],
            'suggest':[(-.31,-.16,.77+z),(.31,-.30,.99+z)],
            'dismiss':[(-.33,-.12,.75+z),(.45,-.19,1.11+z)],
            'eyes':[(-.31,-.14,.77+z),(.30,-.31,1.48+z)],
            'offer':[(-.36,-.24,.81+z),(.54,-.37,.85+z)],
            'shrug':[(-.43,-.22,.98+z),(.43,-.22,.98+z)],
            'claim':[(-.32,-.15,.75+z),(.18,-.34,1.00+z)],
            'question':[(-.28,-.28,.78+z),(.28,-.28,.78+z)],
            'alone':[(-.18,-.33,.73+z),(.18,-.33,.73+z)],
            'look_out':[(-.24,-.24,.71+z),(.24,-.24,.71+z)],
            'welcome':[(-.29,-.13,.75+z),(.31,-.25,.86+z)]}
        targets=goals.get(gesture,rest)
        for i,side in enumerate([-1,1]):
            shoulder=Vector((side*.255,0,.99+z))
            hand=Vector(rest[i]).lerp(Vector(targets[i]),amount)
            elbow=shoulder.lerp(hand,.52)+Vector((side*.095,.035,-.055))
            set_bone(self.arms[i][0],shoulder,elbow,.070);set_bone(self.arms[i][1],elbow,hand,.060)
            self.hands[i].location=hand
            self.hands[i].rotation_euler=(.15+amount*.25,-side*.1,side*(.22+amount*.25))
            if self.elder:
                phase=0 if walk_phase is None else walk_phase+math.pi*i
                swing=0 if walk_phase is None else math.sin(phase)*.23
                lift=0 if walk_phase is None else max(0,math.cos(phase))*.10
                hip=(side*.12,0,.72);knee=(side*.135,swing*.45,.39+lift*.4);foot=(side*.15,swing-.08,.09+lift)
            else:
                hip=(side*.12,.02,.66);knee=(side*.15,-.46,.59);foot=(side*.16,-.51,.075)
            set_bone(self.legs[i][0],hip,knee,.090);set_bone(self.legs[i][1],knee,foot,.072)
            self.feet[i].location=foot
        self.headroot.rotation_euler=(.02*amount if gesture!='small_nod' else .09*amount,head_roll,head_yaw)
        self.torso.rotation_euler[0]=amount*.035

puppets={'story':Puppet('story',graphite,.98),'challenge':Puppet('challenge',graphite2,1.0),
         'quiet':Puppet('quiet',graphite3,.89),'elder':Puppet('elder',eldermat,1.26,True)}

bpy.ops.object.camera_add(location=(0,-7,3))
camera=bpy.context.object;camera.name='one physical camera / editorial marks';scene.camera=camera
camera.data.sensor_width=36;camera.data.clip_end=150
camera.data.dof.use_dof=True;camera.data.dof.aperture_blades=8

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)

def line_at(t):
    found=lines[0]
    for line in lines:
        if t>=line['start']-.12:found=line
    return found

def set_camera(t,line):
    shot=line['shot']
    marks={
        'story':((.4,-3.7,2.10),(-1.45,.1,1.38),56,4.8),
        'challenge':((-.45,-3.8,2.12),(1.45,.25,1.40),58,4.8),
        'quiet':((.10,-3.3,1.94),(0,1.45,1.33),70,4.5),
        'two':((0,-6.6,2.30),(0,.35,1.05),47,6.5),
        'reveal':((0,-7.3,3.10),(0,.65,1.10),45,7),
        'empty':((2.5,-8.2,2.25),(.35,2.2,1.65),36,8),
        'elder':((-.8,2.0,3.0),(3.1,-.3,1.88),48,6.5)}
    pos,target,lens,fstop=marks[shot]
    if shot=='reveal':
        q=smooth((t-line['start'])/max(1,line['end']-line['start']))
        pos=Vector((0,-6.35,2.75)).lerp(Vector(pos),q)
    if line['id']=='P13' and t>line['end']+.9:
        pos,target,lens,fstop=marks['empty']
        shot='empty'
    camera.location=pos
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lens;camera.data.dof.aperture_fstop=fstop
    camera.data.dof.focus_distance=(Vector(target)-camera.location).length
    return shot

def pose_scene(t):
    t=math.floor(t*8+1e-6)/8;line=line_at(t)
    for name,p in puppets.items():
        active=name==line['speaker']
        last=next((l for l in reversed(lines) if l['speaker']==name and l['start']<=t+.12),None)
        gesture=last['gesture'] if last else 'rest'
        a=0
        if last:
            a=smooth((t-last['start']+.25)/.4)*(1-.55*smooth((t-last['end']-.35)/.85))
            if last['id']=='P01' and t<.5:a=1
            if t>last['end']+2:a*=.7
        if name=='story' and t<.5:gesture='match';a=1
        yaw=0;roll=0
        if not active and name!='elder':
            dx=BASE[line['speaker']][0]-BASE[name][0]
            yaw=max(-.44,min(.44,dx*.17))
            if line['id'] in ['P07','P10'] and name=='quiet':roll=.06
        elif active:
            yaw={'story':.12,'challenge':-.15,'quiet':0,'elder':-.20}[name]
            roll=.045*math.sin((t-line['start'])*2.0) if gesture in ['question','alone','suggest'] else 0
        if name=='quiet' and line['id']=='P14':yaw=-.20*smooth((t-line['start'])/.8)
        if name!='elder' and t>timeline['elder_walk_start']+1.45:
            q=smooth((t-timeline['elder_walk_start']-1.45)/.8)
            dx=BASE['elder'][0]-BASE[name][0];dy=BASE['elder'][1]-BASE[name][1]
            towards=math.atan2(dx,-dy)-YAWS[name]
            yaw=yaw*(1-q)+max(-1.5,min(1.5,towards))*q
        phase=None
        if name=='elder':
            q=smooth((t-timeline['elder_walk_start'])/(timeline['elder_arrival']-timeline['elder_walk_start']))
            p.root.location=Vector((6.1,2.0,.12)).lerp(Vector((3.1,-.3,.12)),q)
            radial=math.hypot(p.root.location.x,p.root.location.y-.65)
            p.root.location.z=.12*smooth((3.6-radial)/.35)
            # Keep elder outside the early shots and reveal only on the approach.
            if t<timeline['elder_walk_start']:p.root.location=(1000,1000,-1000)
            elif q<1:phase=(t-timeline['elder_walk_start'])*math.tau/1.25
            p.root.rotation_euler[2]=-1.5
        p.pose(gesture,a,yaw,roll,phase)
    shot=set_camera(t,line)
    bpy.context.view_layer.update()
    return {'time':t,'line':line['id'],'speaker':line['speaker'],'camera_mark':shot}

if not args.setup_only:pose_scene(0)
if args.setup_only:
    pass
elif args.bake_only:
    animated=[camera]
    for puppet in puppets.values():
        animated += [puppet.root,puppet.torso,puppet.headroot,*puppet.hands,*puppet.feet]
        animated += [part for limb in [*puppet.arms,*puppet.legs] for part in limb]
    count=math.ceil(duration*8)
    for i in range(count):
        frame=i*3+1;scene.frame_set(frame);pose_scene(i/8)
        for obj in animated:
            for prop in ['location','rotation_quaternion' if obj.rotation_mode=='QUATERNION' else 'rotation_euler','scale']:
                obj.keyframe_insert(data_path=prop,frame=frame)
        camera.data.keyframe_insert(data_path='lens',frame=frame)
        camera.data.dof.keyframe_insert(data_path='focus_distance',frame=frame)
        camera.data.dof.keyframe_insert(data_path='aperture_fstop',frame=frame)
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for key in curve.keyframe_points:key.interpolation='CONSTANT'
    scene.frame_start=1;scene.frame_end=round(duration*24);scene.frame_set(1)
    editor=scene.sequence_editor_create()
    sound=editor.strips.new_sound('Temporary complete dialogue and sound',str((args.run/'audio/mix.wav').resolve()),channel=1,frame_start=1)
    sound.sound.filepath='//'+os.path.relpath((args.run/'audio/mix.wav').resolve(),args.output.resolve())
    target=(args.output/'polis-animation.blend').resolve()
    if target.exists():raise RuntimeError('Refusing existing animation file.')
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (args.output/'bake.json').write_text(json.dumps({'animated_objects':len(animated),'pose_keys_per_object':count,'frames':scene.frame_end,'fps':24,'interpolation':'CONSTANT','audio':'relative link to retained mix'},indent=2)+'\n')
elif args.stills:
    selected=[('01-match',.4),('02-reveal',lines[1]['start']+1),('03-challenger',lines[6]['start']+.5),
              ('04-quiet',lines[12]['start']+1),('05-empty',lines[13]['start']+1),('06-elder',lines[14]['start']+1)]
    meta=[]
    for name,t in selected:
        info=pose_scene(t);scene.render.filepath=str((args.output/f'{name}.png').resolve())
        bpy.ops.render.render(write_still=True);meta.append({'file':name+'.png',**info})
    (args.output/'frames.json').write_text(json.dumps(meta,indent=2)+'\n')
else:
    count=math.ceil(duration*8);end=min(args.end or count,count);meta=[]
    scene_file=(args.output.parent/'polis-scene.blend').resolve()
    if not scene_file.exists():bpy.ops.wm.save_as_mainfile(filepath=str(scene_file))
    started=time.time();pose_cache={}
    for i in range(args.start,end):
        path=args.output/f'frame-{i:05d}.png'
        if path.exists():raise RuntimeError('Refusing existing frame '+str(i))
        info=pose_scene(i/8);scene.render.filepath=str(path.resolve())
        state=[round(v,6) for obj in scene.objects if obj.type in ['MESH','CAMERA'] for row in obj.matrix_world for v in row]
        state += [camera.data.lens,camera.data.dof.focus_distance,camera.data.dof.aperture_fstop]
        signature=hashlib.sha256(json.dumps(state).encode()).hexdigest()
        reused=pose_cache.get(signature)
        if reused is None:
            bpy.ops.render.render(write_still=True);pose_cache[signature]=path
        else:shutil.copyfile(reused,path)
        meta.append({'frame':i,'cached_pose':None if reused is None else reused.name,**info})
        if i%16==0:print(f'POLIS_PROGRESS {i+1}/{count} elapsed={time.time()-started:.1f}s',flush=True)
    (args.output/f'frames-{args.start:05d}-{end:05d}.json').write_text(json.dumps(meta,indent=2)+'\n')
if not args.setup_only:print('POLIS_RENDER_DONE',flush=True)
