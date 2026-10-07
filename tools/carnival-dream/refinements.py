"""Successive full-film refinements, executed in the renderer's scene namespace.

Revision 2 changes lighting, choreography, prop interaction and construction.
Revision 3 applies a subsequent whole-film pass to palette, scenery, projection
clarity, acting and framing. Each rendered version captures its own recipe.
"""
from mathutils import Euler

base_at_frame = at_frame
revision = args.revision

# Projected light remains flat against the cyclorama. Transparency lets the
# wall's paper grain remain visible, unlike an opaque cutout on the set.
nd = shadowmat.node_tree.nodes
lk = shadowmat.node_tree.links
trans = nd.new('ShaderNodeBsdfTransparent')
blend = nd.new('ShaderNodeMixShader')
blend.inputs[0].default_value = .62
lk.new(trans.outputs[0], blend.inputs[1])
lk.new(se.outputs[0], blend.inputs[2])
lk.new(blend.outputs[0], nd.get('Material Output').inputs['Surface'])
shadowmat.surface_render_method = 'DITHERED'
se.inputs['Color'].default_value = (1.0, .39, .105, 1)
se.inputs['Strength'].default_value = 1.25

# A more restrained stage palette, darker miniature void, and tactile joins.
wallmat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .94
for ramp in [n for n in rose.node_tree.nodes if n.type == 'VALTORGB']:
    ramp.color_ramp.elements[0].color = (.25, .018, .038, 1)
    ramp.color_ramp.elements[1].color = (.66, .055, .095, 1)
for o in cols['rides'].objects:
    if o.name.startswith('Monochrome cyclorama'):
        o.data.materials.clear(); o.data.materials.append(ink)
    if o.name.startswith('Monochrome tabletop'):
        o.data.materials.clear(); o.data.materials.append(ink)

current = 'stage'
# Cut paper footlights and a few visible construction seams give the stage
# depth without adding another narrative element.
for x in [-4.4,-3.3,-2.2,-1.1,0,1.1,2.2,3.3,4.4]:
    cyl('Footlight paper cup', (x,-1.55,.06), .11,.09,ink)
    ball('Footlight glow',(x,-1.55,.12),(.060,.050,.035),bulbmat)
for side in [-1,1]:
    for j in range(5):
        box('Paper corner repair',(side*(4.5+j*.18),2.65,.8+j*.38),(.12,.016,.32),gold,bevel=.006)

# Two additional stars are gathered into the dancer's small constellation,
# then fall as material objects during the second loss.
gathered=[]
for j in range(2):
    o=star('Gathered paper star '+str(j),(0,0,1),.16 if j==0 else .125,gold)
    gathered.append(o)
fallen_hero=star('The first fallen star',(.33,-.20,.045),.18,gold)
fallen_hero.rotation_euler[0]=math.pi/2

current='backstage'
# A silhouette template lies beside the lamp: an unobtrusive construction clue.
template=empty('Uncut dancer template',(19.45,-.02,.814))
template.rotation_euler[0]=math.pi/2
sheet('Template paper rectangle',[(-.25,0,-.28),(.25,0,-.28),(.25,0,.42),(-.25,0,.42)],ivory,template)
ball('Template ink head',(0,-.018,.24),(.055,.012,.073),ink,template)
sheet('Template ink skirt',[(-.026,-.02,.14),(.026,-.02,.14),(.092,-.02,-.11),(-.092,-.02,-.11)],ink,template)
for side in [-1,1]:rod('Template arm',(side*.025,-.024,.13),(side*.13,-.024,.23),.012,ink,template)

current='puppets'
# Reach is solved with two fixed-length paper arm sections.
def arm(p, side, hand, l1=.30, l2=.29):
    shoulder=Vector((side*.235,0,1.53));hand=Vector(hand)
    v=hand-shoulder;distance=min(v.length,l1+l2-.006)
    if v.length<.001:return
    direction=v.normalized();hand=shoulder+direction*distance
    a=(l1*l1-l2*l2+distance*distance)/(2*distance)
    h=math.sqrt(max(0,l1*l1-a*a))
    perpendicular=Vector((direction.z,0,-direction.x)).normalized()
    if perpendicular.x*side<0:perpendicular*=-1
    elbow=shoulder+direction*a+perpendicular*h
    p.limb((side,'upper'),shoulder,elbow,.060)
    p.limb((side,'fore'),elbow,hand,.049)
    p.parts[side,'elbow'].location=elbow;p.parts[side,'hand'].location=hand
    if side==1:
        p.held.location=hand+Vector((.07,-.065,.17))


def walking_feet(p, shot, t):
    # Each planted foot stays in world space while the body travels over it.
    duration=shot['end']-shot['start'];local=max(0,t-shot['start'])
    ranges={'walk':(-.65,.45),'carry_star':(-.9,.4),'curtain':(.4,3.7),'feet':(-.7,.1),'final_step':(-.9,-.18)}
    if shot['kind'] not in ranges:return
    x0,x1=ranges[shot['kind']];speed=(x1-x0)/duration;period=120/88
    # The final step is one short, deliberate transfer of weight.
    if shot['kind']=='final_step':period=duration*1.25
    for side in [-1,1]:
        offset=0 if side<0 else .5
        cycle=local/period+offset;index=math.floor(cycle);phase=cycle-index
        swing=smooth((phase-.56)/.44)
        world_x=x0+(index-offset+swing)*speed*period+side*.14
        ankle=(world_x-p.root.location.x,-.015,.14+.13*math.sin(swing*math.pi))
        knee=(side*.11+ankle[0]*.38,-.035,.48+.018*math.sin(swing*math.pi))
        hip=(side*.105,0,.92)
        p.limb((side,'thigh'),hip,knee,.069);p.limb((side,'shin'),knee,ankle,.055)
        p.parts[side,'knee'].location=knee
        p.parts[side,'foot'].location=(ankle[0]+.035,ankle[1]-.025,ankle[2]-.04)
        p.parts[side,'foot'].rotation_euler[2]=-.20


def meet_projection():
    # Project the performer's hand onto the wall, stopping just short in screen
    # space. The partner can answer across the impossible physical distance.
    bpy.context.view_layer.update()
    point=performer.root.matrix_world @ performer.parts[1,'hand'].location
    ray=point-cam.location
    wall_y=partner.root.location.y
    target=cam.location+ray*((wall_y-cam.location.y)/ray.y)
    target.x+=.065;target.z+=.025
    local=partner.root.matrix_world.inverted() @ target
    arm(partner,1,local,l1=.31,l2=.30)


def assemble_material(kind,k,u,t):
    parts=ride_parts[kind];rot=ride_rotors[kind]
    if kind=='ferris':rot.rotation_euler[1]=.045*math.sin(t*7) if k.endswith('broken') else 0
    else:rot.rotation_euler[2]=.14+.045*math.sin(t*6) if k.endswith('broken') else .10+.15*u
    for o,loc,rotation,scale in parts:
        o.location=loc;o.rotation_euler=rotation;o.scale=scale
    bpy.context.view_layer.update()
    targets=[(o,o.matrix_world.copy()) for o,*_ in parts]
    targets.sort(key=lambda item:item[1].translation.z)
    if not(k.endswith('assemble') or k.endswith('dismantle')):return
    q=quant(u/.74,22) if k.endswith('assemble') else 1-quant((u-.10)/.78,22)
    for j,(o,matrix) in enumerate(targets):
        if o.name.startswith('Round pulp plinth'):continue
        progress=smooth((q-j/max(1,len(targets)-1)*.72)/.28)
        loc,rotation,scale=matrix.decompose()
        scattered=Vector((40+(((j*.6180339)%1)-.5)*5.1,-1.8+((j*.347)%1)*3.5,.16+.032*(j%5)))
        pile_rotation=Euler((math.pi/2,0,j*2.399)).to_quaternion()
        position=scattered.lerp(loc,progress)
        position.z+=.32*math.sin(progress*math.pi)
        orient=pile_rotation.slerp(rotation,progress)
        o.matrix_world=Matrix.LocRotScale(position,orient,scale)


def at_frame(frame):
    info=base_at_frame(frame)
    shot=next(s for s in spec['shots'] if s['id']==info['shot'])
    t=info['seconds'];k=shot['kind'];u=max(0,min(1,(t-shot['start'])/(shot['end']-shot['start'])))
    isride=info['monochrome'];isback=k in ['lantern_macro','backstage','mechanism','wind']
    for o in gathered:o.hide_render=True
    fallen_hero.hide_render=isride or isback or t<113.70
    if t>=86.66:
        for j in [8,10]:stars[j].hide_render=True
    # The light figure and costume share a palette. It flickers away with the
    # second loss rather than behaving as a second solid person.
    warmth=.5+.5*math.sin(t*.6)
    se.inputs['Color'].default_value=(1.0,mix(.20,.55,warmth),mix(.055,.15,warmth),1)
    se.inputs['Strength'].default_value=.85+.12*math.sin(t*1.1)
    blend.inputs[0].default_value=.52
    if k in ['recede','separation','lose_stars']:blend.inputs[0].default_value=mix(.56,.22,smooth(u))
    if k in ['near_touch','return_light','final_reach','end']:blend.inputs[0].default_value=.66
    # Paper folds retain some ivory even at maximum color.
    for e in dress_ramp.color_ramp.elements:
        c=e.color;e.color=(c[0]*.85,c[1]*.82,c[2]*.71,1)
    if not isride and not isback:
        walking_feet(performer,shot,t)
        performer.root.rotation_euler[1]+=.018*math.sin(t*math.tau*88/60)
        if k in ['reach','near_touch','return_light','recede','pass','final_reach','end']:
            q=smooth(u/.72) if k in ['reach','near_touch','return_light','final_reach'] else 1 if k=='end' else .85
            arm(performer,1,(mix(.30,.72,q),-.08,mix(1.06,1.72,q)))
            performer.head.rotation_euler[2]=.035+.14*q
            performer.head.rotation_euler[1]=-.06+.065*math.sin(t)
        if k in ['bloom','dance_return','spin']:
            phase=t*math.tau*88/60/2
            performer.root.rotation_euler[2]+=.16*math.sin(phase)
            performer.skirt.rotation_euler[2]+=.11*math.sin(phase-.5)
            for side in [-1,1]:arm(performer,side,(side*(.60+.025*math.cos(phase)),-.08,1.65+side*.18*math.sin(phase)))
        if k=='pluck_star':
            height=mix(1.54,2.03,smooth(u/.32)) if u<.32 else mix(2.03,1.54,smooth((u-.40)/.48))
            arm(performer,1,(.36,-.14,height));pluckable.location.z=2.255
            pluck_thread.data.splines[0].points[-1].co=(.68,-.205,2.255,1)
        if k in ['carry_star','stars','effort']:arm(performer,1,(.40,-.14,1.58 if k=='carry_star' else 1.97))
        if k in ['spin','dance_return']:hidden(performer.held,False)
        if k in ['stars','spin','dance_return','effort','lose_stars']:
            for j,o in enumerate(gathered):
                o.hide_render=False
                angle=t*.7+j*math.pi
                x=performer.root.location.x+.52*math.cos(angle)
                z=1.93+.30*math.sin(angle)
                if k=='lose_stars':z=mix(z,.13,smooth(u));x+=.60*(j*2-1)*smooth(u)
                position=Vector((x,-.14,z))
                if k=='stars':position=stars[[8,10][j]].location.lerp(position,smooth(u/.36))
                o.location=position;o.rotation_euler=(0,t*.3+j,0);o.scale=(1,1,1)
        if t>=114.04:
            for j,o in enumerate(gathered):
                o.hide_render=False;o.location=(-.1+(j*2-1)*.85,-.14,.045);o.rotation_euler=(math.pi/2,0,j*.8);o.scale=(1,1,1)
        if k=='lose_stars':hidden(performer.held,t>=113.70)
        if k in ['near_touch','return_light','final_reach','end']:
            meet_projection()
        # Mild, shot-specific dolly movement, held on the same pose cadence.
        if k in ['face','near_touch','return_light','choice','empty_light']:
            old=cam.location.copy();cam.location=old.lerp(focus.location,.018*smooth(u));aim(cam,focus.location)
        if k=='light_close':camera((1.35,-6.4,2.8),(-.35,0,1.48),67)
        if k=='choice':performer.head.rotation_euler[2]=mix(.15,-.12,smooth(u))
        key.data.energy*=.87;fill.data.energy*=.90;rim.data.energy*=1.10
    if isback:
        if k=='backstage':
            performer.root.rotation_euler[2]=.30
            performer.head.rotation_euler[2]=mix(.08,.22,smooth(u))
        if k=='wind':
            performer.root.rotation_euler[2]=-.12
            performer.head.rotation_euler[2]=-.18
            performer.head.rotation_euler[1]=.12
            phase=t*1.8
            hand=(-.56,-.05+.025*math.sin(phase),.91+.025*math.cos(phase))
            elbow=(-.40,-.10,1.22);shoulder=(-.235,0,1.53)
            performer.limb((-1,'upper'),shoulder,elbow,.060);performer.limb((-1,'fore'),elbow,hand,.049)
            performer.parts[-1,'hand'].location=hand
            wind.rotation_euler[0]=phase
        if k=='lantern_macro':camera((21.65,-3.0,2.4),(20,.5,1.50),82)
        backkey.data.energy*=.82
    if isride:
        kind=k.split('_')[0];assemble_material(kind,k,u,t)
        ridekey.data.energy=950;ridekey.data.size=3.0;ridefill.data.energy=1100;ridefill.data.size=2.0
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.08
        if not k.endswith('broken'):
            a=mix(-.07,.07,u)
            camera((40+4*math.cos(a)-10.8*math.sin(a),-10.8*math.cos(a)-4*math.sin(a),5),(40,0,1.90),54)
    info['revision']=revision
    return info


if revision == 3:
    # A single, broad band of borrowed color runs through the whole costume.
    # Paper grain stays in the normal map; it no longer mottles the dye.
    nd=dressmat.node_tree.nodes;lk=dressmat.node_tree.links
    coord=nd.new('ShaderNodeTexCoord');coord.object=performer.root
    separate=nd.new('ShaderNodeSeparateXYZ');lk.new(coord.outputs['Object'],separate.inputs[0])
    slope=nd.new('ShaderNodeMath');slope.operation='MULTIPLY';slope.inputs[1].default_value=.32
    lk.new(separate.outputs['Z'],slope.inputs[0])
    diagonal=nd.new('ShaderNodeMath');diagonal.operation='ADD'
    lk.new(separate.outputs['X'],diagonal.inputs[0]);lk.new(slope.outputs[0],diagonal.inputs[1])
    lk.new(diagonal.outputs[0],dress_ramp.inputs[0])
    dress_ramp.color_ramp.elements[0].position=.06;dress_ramp.color_ramp.elements[1].position=.63
    # An opaque emission silhouette avoids multiply layered arm/head seams.
    # Fine world-space grain gives it the same paper surface as the wall.
    nd=shadowmat.node_tree.nodes;lk=shadowmat.node_tree.links
    geometry=nd.new('ShaderNodeNewGeometry');grain=nd.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value=95;grain.inputs['Detail'].default_value=2
    lk.new(geometry.outputs['Position'],grain.inputs['Vector'])
    lightgrain=nd.new('ShaderNodeMapRange');lightgrain.inputs['To Min'].default_value=.88;lightgrain.inputs['To Max'].default_value=1.08
    lk.new(grain.outputs['Fac'],lightgrain.inputs['Value']);lk.new(lightgrain.outputs[0],se.inputs['Strength'])

    current='stage'
    # A scalloped paper canopy and a crescent finish the little theatre.
    # These are present from the establishing shot onward.
    for j in range(18):
        x=-5.1+j*.60
        sheet('Cut paper scalloped canopy',[(x,2.67,4.54),(x+.60,2.67,4.54),(x+.49,2.67,4.20),(x+.30,2.67,4.12),(x+.11,2.67,4.20)],ink)
        rod('Canopy gold stitch',(x,2.65,4.47),(x+.53,2.65,4.47),.008,gold)
    # Crescent is a single concave paper shape, not a new light source.
    pts=[]
    for j in range(25):
        a=math.pi/2+j*math.pi/24;pts.append((-2.15+.41*math.cos(a),2.70,3.65+.41*math.sin(a)))
    for j in range(25):
        a=3*math.pi/2-j*math.pi/24;pts.append((-2.05+.29*math.cos(a),2.70,3.65+.41*math.sin(a)))
    sheet('Thin crescent of ivory paper',pts,ivory)
    motes=[]
    for j in range(24):
        o=sheet('Suspended paper fibre',[(0,0,0),(.014,0,.004),(.020,0,.037),(.005,0,.027)],gold)
        motes.append(o)

    current='puppets'
    # A restrained row of punched foil details follows the actual skirt rig.
    for j in range(24):
        a=(j+.5)*math.tau/24
        x,y=.475*math.cos(a),.28*math.sin(a)
        o=ball('Skirt punched foil hem',(x,y,-.535),(.014,.014,.020),gold,performer.skirt)
    for side in [-1,1]:
        sheet('Folded ivory collar',[(side*.018,-.09,1.67),(side*.13,-.09,1.62),(side*.065,-.11,1.55)],ivory_light,performer.root)

    revision_two_at_frame=at_frame
    def continuous_reach(hand):
        # A forward/downward elbow pole preserves a continuous bend while the
        # wrist crosses shoulder height; two fixed paper sections stay joined.
        shoulder=Vector((.235,0,1.53));hand=Vector(hand)
        direction=(hand-shoulder).normalized();distance=min((hand-shoulder).length,.584)
        hand=shoulder+direction*distance
        along=(.30**2-.29**2+distance**2)/(2*distance)
        height=math.sqrt(max(0,.30**2-along**2))
        pole=Vector((.8,-.35,-.65));pole=(pole-direction*pole.dot(direction)).normalized()
        elbow=shoulder+direction*along+pole*height
        performer.limb((1,'upper'),shoulder,elbow,.060);performer.limb((1,'fore'),elbow,hand,.049)
        performer.parts[1,'elbow'].location=elbow;performer.parts[1,'hand'].location=hand

    def at_frame(frame):
        info=revision_two_at_frame(frame)
        s=next(s for s in spec['shots'] if s['id']==info['shot'])
        t=info['seconds'];k=s['kind'];u=max(0,min(1,(t-s['start'])/(s['end']-s['start'])))
        isride=info['monochrome'];isback=k in ['lantern_macro','backstage','mechanism','wind']
        if not isride and not isback:
            if k in ['return_light','final_reach','end']:
                continuous_reach(performer.parts[1,'hand'].location.copy())
            performer.root.location.z-=.105
            if k=='pluck_star':
                pluckable.location.z-=.105
                pluck_thread.data.splines[0].points[-1].co.z-=.105
        borrowed=max(0,min(1,(.6888-dress_ramp.color_ramp.elements[1].color[1])/.6601))
        for e,cream,tint in zip(dress_ramp.color_ramp.elements,[(.65,.60,.49),(.90,.84,.72)],[(.038,.12,.27),(.70,.065,.12)]):
            e.color=(*[mix(c,v,borrowed) for c,v in zip(cream,tint)],1)
        blend.inputs[0].default_value=1
        se.inputs['Color'].default_value=(.95,.48+.055*math.sin(t*.55),.16,1)
        # Calm suspended fibres reveal air in the light without a sparkle burst.
        for j,o in enumerate(motes):
            o.hide_render=isride or isback
            o.location=(-2.6+(j*.731)%5.3+.06*math.sin(t*.35+j),.35+(j*.397)%2.1,.32+(j*.277+t*.033)%3.45)
            o.rotation_euler=(.15*math.sin(t*.4+j),.4*math.sin(t*.3+j),j*2.4)
            o.scale=(.45,.45,.45) if k in ['intro_wide','alone','empty_light'] else (1,1,1)
        if not isride and not isback:
            if k=='light_close':camera((1.35,-6.9,2.9),(-.35,0,1.48),63)
            if k=='face':camera((.8,-4.02,2.35),(-.18,.02,1.95),78)
            if k=='color_leaves':camera((1.5,-5.2,2.5),(.15,.15,1.62),68)
            if k in ['shadow_arrives','reach','recede','pass','separation']:
                camera(cam.location.lerp(focus.location,.033*smooth(u)),focus.location,cam.data.lens)
            if k in ['near_touch','return_light','final_reach','end']:
                # Put the projected answering hand just above the physical hand;
                # a clear gap makes the impossible distance visible.
                bpy.context.view_layer.update()
                point=performer.root.matrix_world @ performer.parts[1,'hand'].location
                ray=point-cam.location;target=cam.location+ray*((partner.root.location.y-cam.location.y)/ray.y)
                target.x-=.10;target.z+=.45
                arm(partner,1,partner.root.matrix_world.inverted()@target,l1=.34,l2=.34)
            if k in ['empty_light','color_leaves','lose_stars','alone']:
                performer.head.rotation_euler[1]=.04+.17*smooth(u)
                performer.head.rotation_euler[2]=-.10
            if k=='choice':
                # Looking back, stopping, then turning toward the light reads as
                # a decision before the final chorus, rather than idle swaying.
                performer.head.rotation_euler[2]=mix(.26,-.16,smooth((u-.25)/.55))
                arm(performer,1,(mix(.30,.42,smooth((u-.60)/.4)),-.08,mix(1.06,1.38,smooth((u-.60)/.4))))
                performer.root.rotation_euler[1]=-.025*smooth(u)
            if k=='pluck_star':
                performer.head.rotation_euler[1]=-.16*math.sin(u*math.pi)
            if k in ['stars','effort']:
                performer.head.rotation_euler[1]=-.13
            if k=='final_step':
                performer.head.rotation_euler[2]=-.12
                arm(performer,1,(mix(.30,.38,smooth(u)),-.08,mix(1.06,1.25,smooth(u))))
            key.data.energy*=1.05;fill.data.energy*=.78;rim.data.energy*=1.15
            if k in ['bloom','dance_return','spin']:
                performer.head.rotation_euler[2]=.11*math.sin(t*math.pi*88/60)
        if isback:
            backfill.data.energy=310
            if k=='backstage':
                performer.root.location.z-=.105
                performer.root.rotation_euler[2]=mix(.55,.95,smooth(u))
                performer.head.rotation_euler[2]=mix(.12,.35,smooth(u))
                performer.head.rotation_euler[1]=mix(-.05,.08,smooth(u))
                continuous_reach((mix(.30,.56,smooth((u-.4)/.6)),-.08,mix(1.06,1.53,smooth((u-.4)/.6))))
                camera(cam.location.lerp(focus.location,.07*smooth(u)),focus.location,cam.data.lens)
            if k=='mechanism':
                camera((20.80-.16*u,-2.65,2.15),(20,.40,1.49),79)
            if k=='wind':
                camera((22.4,-6.2,3.0),(20.65,.4,1.50),62)
                # The winding begins after a short consideration and settles
                # into a hold. The lamp itself continues turning.
                turn=3.9*smooth((u-.15)/.60)
                wind.rotation_euler[0]=turn
                hand=Vector((-.56,-.05+.025*math.sin(turn),.91+.025*math.cos(turn)))
                performer.limb((-1,'fore'),(-.40,-.10,1.22),hand,.049)
                performer.parts[-1,'hand'].location=hand
        if isride:
            # More raking light emphasizes torn edges and physical debris.
            ridekey.data.energy=1080;ridekey.data.size=2.4
            ridefill.data.energy=900;ridefill.data.size=2.7
        return info
