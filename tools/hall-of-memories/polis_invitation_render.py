"""Extend the baseline polis set for an invitation, walk and Hall threshold.

Run in Blender with the same CLI as polis_render.py. The shared setup preserves
the baseline puppet meshes/materials; this file authors the new set and acting.
"""
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

cues=timeline['cues'];byid={line['id']:line for line in lines}
count=round(duration*8)
end=min(args.end if args.end is not None else count,count)
if not args.stills and not args.bake_only:
    if any((args.output/f'frame-{i:05d}.png').exists() for i in range(args.start,end)):
        raise RuntimeError('Refusing existing rendered frame range.')
    recipe=args.output.parent/'recipe';recipe.mkdir(exist_ok=True)
    for name in ['polis_render.py','polis_invitation_render.py','polis_audio.py','polis_invitation_audio.py','polis_invitation.json']:
        src=HERE/name;dest=recipe/name
        if dest.exists():
            if dest.read_bytes()!=src.read_bytes():raise RuntimeError('Recipe differs; resume with the retained recipe or use a new render directory.')
        else:shutil.copy2(src,dest)
    dest=recipe/'timeline.json'
    if dest.exists() and dest.read_bytes()!=(args.run/'timeline.json').read_bytes():
        raise RuntimeError('Timeline differs from the retained rendering recipe.')
    if not dest.exists():shutil.copy2(args.run/'timeline.json',dest)

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

def active_line(t):
    found=lines[0]
    for line in lines:
        if t>=line['start']-.125:found=line
    return found

def camera_mark(t,line):
    marks={
      'quiet':((3.35,1.5,2.0),(0,1.45,1.34),65,5.6),
      'story':((1.6,-2.9,2.05),(-1.45,.1,1.36),59,5.6),
      'challenge':((4.2,-2.35,2.15),(1.45,.25,1.4),60,5.6),
      'elder':((-.8,2.,3.),(3.1,-.3,1.88),48,6.5),
      'group':((5.8,-6.6,3.3),(.55,.65,1.1),43,7),
      'invite':((5.8,-6.6,3.3),(.55,.65,1.1),43,7),
      'hall':((5.0,-7.5,4.2),(16,3.0,3.0),35,8),
      'arrival_children':((15.5,.2,2.65),(12.4,3.1,1.28),48,8),
      'arrival_elder':((11.0,1.6,2.72),(14.65,3.1,2.03),52,6.5),
      'threshold_children':((14.3,3.45,2.05),(11.75,3.2,1.35),55,5.6),
      'threshold':((6.0,-3.7,3.5),(15.5,3.0,2.65),28,8)}
    shot=line['shot']
    if cues['walk_start']<=t<cues['hall_reveal']:
        shot='crossing'
        center=sum((p.root.location for p in puppets.values()),Vector())/4
        pos=(center.x+.8,-7.0,2.8);target=(center.x+.5,center.y,1.25);lens=35;fstop=8
    else:
        if cues['hall_reveal']<=t<byid['I09']['start']:shot='hall'
        pos,target,lens,fstop=marks[shot]
    camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=lens;camera.data.dof.focus_distance=(Vector(target)-camera.location).length;camera.data.dof.aperture_fstop=fstop
    return shot

def pose_invitation(t):
    t=math.floor(t*8+1e-6)/8;line=active_line(t)
    for name,p in puppets.items():
        offset,period=WALK[name]
        stand=smooth((t-cues['stand_start']-(0 if name=='elder' else offset*.45))/1.0)
        travel=max(0,min(1,(t-cues['walk_start']-offset)/(cues['walk_end']-cues['walk_start']-offset)))
        last=next((l for l in reversed(lines) if l['speaker']==name and l['start']<=t+.125),None)
        gesture=last['gesture'] if last else 'rest';amount=0
        if last:
            amount=smooth((t-last['start']+.25)/.4)*(1-.65*smooth((t-last['end']-.3)/.8))
            if t>last['end']+2:amount*=.65
        pos=START[name].lerp(FINISH[name],travel)
        # Rise forward off the retained stools before translating toward the Hall.
        if name!='elder':pos.y-=.30*stand*(1-travel)
        radial=math.hypot(pos.x,pos.y-.65)
        pos.z=max(.03,.12*smooth((3.6-radial)/.35))
        p.root.location=pos
        initial=YAWS[name]
        direction=math.atan2(FINISH[name].x-START[name].x,-(FINISH[name].y-START[name].y))
        turn=smooth((t-cues['stand_start']-.25)/1.25)
        rootyaw=angle_mix(initial,direction,turn)
        if travel>=1:rootyaw=angle_mix(direction,-math.pi/2 if name=='elder' else math.pi/2,smooth((t-cues['walk_end'])/.75))
        p.root.rotation_euler[2]=rootyaw
        if travel>0 and travel<1:
            gesture='rest';amount=0;yaw=0
        else:
            other=FINISH['elder'] if travel>=1 else START['elder']
            if name=='elder':other=(FINISH['quiet'] if travel>=1 else START[line['speaker']] if line['speaker']!='elder' else START['quiet'])
            wanted=math.atan2(other.x-pos.x,-(other.y-pos.y))-rootyaw
            yaw=max(-1.3,min(1.3,(wanted+math.pi)%math.tau-math.pi))
        if t>=cues['threshold_hold']:
            q=smooth((t-cues['threshold_hold'])/1.0)
            p.root.rotation_euler[2]=angle_mix(rootyaw,math.pi/2,q);yaw*=1-q;amount*=1-q
        p.pose(gesture,amount,yaw,0)
        phase=(t-cues['walk_start']-offset)*math.tau/period if 0<travel<1 else None
        speed=(FINISH[name]-START[name]).length/(cues['walk_end']-cues['walk_start']-offset)
        standing_legs(p,phase,1 if name=='elder' else stand,speed/float(p.root.scale.x)*period/4)
        # A small opposing arm swing, with no movement in the final held tableau.
        if phase is not None:
            for i,side in enumerate([-1,1]):
                hand=Vector((side*.30,-.08+math.sin(phase+i*math.pi)*.12,.71+p.z))
                shoulder=Vector((side*.255,0,.99+p.z));elbow=shoulder.lerp(hand,.52)+Vector((side*.07,.02,-.04))
                set_bone(p.arms[i][0],shoulder,elbow,.07);set_bone(p.arms[i][1],elbow,hand,.06);p.hands[i].location=hand
    shot=camera_mark(t,line);bpy.context.view_layer.update()
    return {'time':t,'line':line['id'],'speaker':line['speaker'],'camera_mark':shot}

pose_invitation(0)
if args.bake_only:
    target=(args.output/'polis-invitation-animation.blend').resolve()
    if target.exists():raise RuntimeError('Refusing existing invitation animation.')
    animated=[camera]
    for p in puppets.values():
        animated += [p.root,p.torso,p.headroot,*p.hands,*p.feet]
        animated += [part for limb in [*p.arms,*p.legs] for part in limb]
    for i in range(count):
        frame=i*3+1;scene.frame_set(frame);pose_invitation(i/8)
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
    sound=scene.sequence_editor_create().strips.new_sound('Invitation dialogue and sound',str((args.run/'audio/mix.wav').resolve()),channel=1,frame_start=1)
    sound.sound.filepath='//'+os.path.relpath((args.run/'audio/mix.wav').resolve(),args.output.resolve())
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    (args.output/'bake.json').write_text(json.dumps({'objects':len(animated),'pose_keys':count,'frames':scene.frame_end,'fps':24,'interpolation':'CONSTANT'},indent=2)+'\n')
elif args.stills:
    selected=[('01-question',.875),('02-elder',byid['I02']['start']+.75),('03-invitation',byid['I08']['start']+.5),
              ('04-standing',cues['stand_start']+.875),('05-crossing',cues['walk_start']+3),
              ('06-hall',byid['I09']['start']+.5),('07-children',byid['I10']['start']+.5),
              ('08-elder-at-hall',byid['I11']['start']+.5),('09-threshold-question',byid['I12']['start']+.5),('10-threshold',duration-.25)]
    meta=[]
    for name,t in selected:
        info=pose_invitation(t);scene.render.filepath=str((args.output/f'{name}.png').resolve())
        bpy.ops.render.render(write_still=True);meta.append({'file':name+'.png',**info})
    (args.output/'frames.json').write_text(json.dumps(meta,indent=2)+'\n')
else:
    scene_file=(args.output.parent/'polis-invitation-scene.blend').resolve()
    if not scene_file.exists():bpy.ops.wm.save_as_mainfile(filepath=str(scene_file))
    meta=[];cache={};started=time.time()
    for i in range(args.start,end):
        path=args.output/f'frame-{i:05d}.png';info=pose_invitation(i/8);scene.render.filepath=str(path.resolve())
        state=[round(v,6) for obj in scene.objects if obj.type in ['MESH','CAMERA'] for row in obj.matrix_world for v in row]
        state += [camera.data.lens,camera.data.dof.focus_distance,camera.data.dof.aperture_fstop]
        sig=hashlib.sha256(json.dumps(state).encode()).hexdigest();previous=cache.get(sig)
        if previous is None:bpy.ops.render.render(write_still=True);cache[sig]=path
        else:shutil.copyfile(previous,path)
        meta.append({'frame':i,'cached_pose':None if previous is None else previous.name,**info})
        if i%16==0:print(f'INVITATION_PROGRESS {i+1}/{count} elapsed={time.time()-started:.1f}s',flush=True)
    (args.output/f'frames-{args.start:05d}-{end:05d}.json').write_text(json.dumps(meta,indent=2)+'\n')
print('INVITATION_RENDER_DONE',flush=True)
