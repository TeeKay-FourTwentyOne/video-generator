import { TAU, cross, normalize, sub } from './math.mjs';

export const SCENE_ID = 'meridian-house-v1';
export const MATERIALS = {
  stone: { color: [.64,.66,.62] }, ivory: { color: [.86,.81,.68] },
  dark: { color: [.10,.16,.19] }, jade: { color: [.10,.31,.26] },
  wood: { color: [.20,.095,.06] }, brass: { color: [.70,.44,.17] },
  gold: { color: [.94,.69,.30] }, velvet: { color: [.35,.14,.21] },
  teal: { color: [.12,.38,.38] }, leaf: { color: [.14,.37,.23] },
  leafLight: { color: [.31,.52,.28] }, soil: { color: [.10,.07,.04] },
  blue: { color: [.12,.24,.39] }, paper: { color: [.71,.64,.44] },
  light: { color: [1,.75,.35], emission: 1.8 }, moon: { color: [.52,.85,1], emission: 1.2 },
  sky: { color: [.035,.065,.13], emission: .5 },
};

function rotate(p, r = [0,0,0]) {
  let [x,y,z] = p;
  [y,z] = [y*Math.cos(r[0])-z*Math.sin(r[0]), y*Math.sin(r[0])+z*Math.cos(r[0])];
  [x,z] = [x*Math.cos(r[1])+z*Math.sin(r[1]), -x*Math.sin(r[1])+z*Math.cos(r[1])];
  [x,y] = [x*Math.cos(r[2])-y*Math.sin(r[2]), x*Math.sin(r[2])+y*Math.cos(r[2])];
  return [x,y,z];
}

export function buildScene() {
  const vertices = [], objects = [];
  let active, counter = 0;
  const begin = (name, material) => {
    active = { id: ++counter, name, material, first: vertices.length / 11, count: 0 };
    objects.push(active);
  };
  function tri(a,b,c,normals) {
    const material = MATERIALS[active.material], n = normalize(cross(sub(b,a), sub(c,a)));
    [a,b,c].forEach((p,i) => vertices.push(...p, ...(normals?.[i] || n), ...material.color, material.emission || 0, active.id));
    active.count += 3;
  }
  function box(name, material, center, size, rotation) {
    begin(name, material);
    const p = (x,y,z) => rotate([x*size[0]/2,y*size[1]/2,z*size[2]/2],rotation).map((v,i)=>v+center[i]);
    for (const face of [
      [[1,-1,-1],[1,1,-1],[1,1,1],[1,-1,1]],
      [[-1,-1,1],[-1,1,1],[-1,1,-1],[-1,-1,-1]],
      [[-1,1,-1],[-1,1,1],[1,1,1],[1,1,-1]],
      [[-1,-1,1],[-1,-1,-1],[1,-1,-1],[1,-1,1]],
      [[1,-1,1],[1,1,1],[-1,1,1],[-1,-1,1]],
      [[-1,-1,-1],[-1,1,-1],[1,1,-1],[1,-1,-1]],
    ]) { const v=face.map(q=>p(...q)); tri(v[0],v[1],v[2]); tri(v[0],v[2],v[3]); }
  }
  function cylinder(name, material, center, radius, height, topRadius=radius, segments=24) {
    begin(name, material);
    const p = (a,y,r) => [center[0]+Math.cos(a)*r,center[1]+y,center[2]+Math.sin(a)*r];
    for(let i=0;i<segments;i++) {
      const a=i/segments*TAU,b=(i+1)/segments*TAU;
      const a0=p(a,-height/2,radius),b0=p(b,-height/2,radius),a1=p(a,height/2,topRadius),b1=p(b,height/2,topRadius);
      const na=normalize([Math.cos(a),(radius-topRadius)/height,Math.sin(a)]), nb=normalize([Math.cos(b),(radius-topRadius)/height,Math.sin(b)]);
      tri(a0,a1,b1,[na,na,nb]); tri(a0,b1,b0,[na,nb,nb]);
      tri(p(0,height/2,0),b1,a1); tri(p(0,-height/2,0),a0,b0);
    }
  }
  function sphere(name, material, center, scale, rotation, segments=20, rings=12) {
    begin(name,material);
    const point=(a,b)=> {
      const normal=[Math.sin(b)*Math.cos(a),Math.cos(b),Math.sin(b)*Math.sin(a)];
      return { p:rotate(normal.map((v,i)=>v*scale[i]),rotation).map((v,i)=>v+center[i]), n:normalize(rotate(normal.map((v,i)=>v/scale[i]),rotation)) };
    };
    for(let i=0;i<segments;i++) for(let j=0;j<rings;j++) {
      const a=i/segments*TAU,b=(i+1)/segments*TAU,u=j/rings*Math.PI,v=(j+1)/rings*Math.PI;
      const ps=[point(a,u),point(a,v),point(b,v),point(b,u)];
      tri(ps[0].p,ps[2].p,ps[1].p,[ps[0].n,ps[2].n,ps[1].n]);
      tri(ps[0].p,ps[3].p,ps[2].p,[ps[0].n,ps[3].n,ps[2].n]);
    }
  }
  function torus(name,material,center,radius,tube,rotation,arc=TAU) {
    begin(name,material);
    const point=(a,b)=>rotate([(radius+tube*Math.cos(b))*Math.cos(a),tube*Math.sin(b),(radius+tube*Math.cos(b))*Math.sin(a)],rotation).map((v,i)=>v+center[i]);
    for(let i=0;i<64;i++) for(let j=0;j<8;j++) {
      const a=i/64*arc,b=(i+1)/64*arc,u=j/8*TAU,v=(j+1)/8*TAU;
      tri(point(a,u),point(a,v),point(b,v)); tri(point(a,u),point(b,v),point(b,u));
    }
  }
  function arch(name, center, yaw=0, width=2.7, height=4.5) {
    const local=(p)=>rotate(p,[0,yaw,0]).map((v,i)=>v+center[i]);
    for(const x of [-width/2,width/2]) {
      box(`${name} pillar`,'ivory',local([x,(height-width/2)/2,0]),[.24,height-width/2,.42],[0,yaw,0]);
      box(`${name} foot`,'brass',local([x,.14,0]),[.37,.28,.5],[0,yaw,0]);
      box(`${name} capital`,'brass',local([x,height-width/2,0]),[.36,.16,.5],[0,yaw,0]);
    }
    begin(`${name} arch`,'ivory');
    const radius=width/2, spring=height-radius;
    for(let i=0;i<32;i++) {
      const a=i/32*Math.PI,b=(i+1)/32*Math.PI;
      const p=(angle,r,z)=>local([Math.cos(angle)*r,spring+Math.sin(angle)*r,z]);
      for(const z of [-.2,.2]) { tri(p(a,radius,z),p(b,radius,z),p(b,radius+.24,z)); tri(p(a,radius,z),p(b,radius+.24,z),p(a,radius+.24,z)); }
      tri(p(a,radius,-.2),p(a,radius,.2),p(b,radius,.2)); tri(p(a,radius,-.2),p(b,radius,.2),p(b,radius,-.2));
    }
  }
  function sconce(x,z,yaw=0) {
    box('Sconce back','brass',[x,2.45,z],[.22,.7,.11],[0,yaw,0]);
    sphere('Sconce pearl','light',[x+Math.sin(yaw)*.15,2.6,z+Math.cos(yaw)*.15],[.13,.28,.13]);
  }
  function plant(name,x,z,height=2.2) {
    cylinder(`${name} planter`,'jade',[x,.29,z],.42,.58,.52);
    torus(`${name} lip`,'brass',[x,.58,z],.5,.035);
    cylinder(`${name} soil`,'soil',[x,.57,z],.46,.03);
    cylinder(`${name} stem`,'wood',[x,height/2+.4,z],.025,height-.5,.014,8);
    for(let i=0;i<11;i++) {
      const a=i*2.39996,y=.7+i/11*(height-.6),r=.3+Math.sin(i/11*Math.PI)*.22;
      sphere(`${name} leaf ${i}`,i%3?'leaf':'leafLight',[x+Math.cos(a)*r,y,z+Math.sin(a)*r],[.17,.10,.58],[.3,a+Math.PI/2,.2],10,6);
    }
  }
  // Three rooms share continuous floors and real, traversable openings.
  box('Atrium floor','ivory',[0,-.16,0],[10,.3,12]);
  box('Library floor','wood',[-9,-.16,0],[8,.3,10]);
  box('Conservatory floor','stone',[9,-.16,0],[8,.3,10]);
  box('North wall','dark',[0,3,-6],[10,6,.24]);
  box('South wall','jade',[0,3,6],[10,6,.24]);
  for(const x of [-5,5]) {
    for(const z of [-3.8,3.8]) box('Atrium doorway wall','jade',[x,3,z],[.24,6,4.4]);
    box('Atrium doorway lintel','jade',[x,5.45,0],[.24,1.1,3.2]);
    arch(x<0?'Library portal':'Conservatory portal',[x,0,0],Math.PI/2,3.1,4.8);
  }
  for(const z of [-5.82,5.82]) {
    box('Atrium skirting','brass',[0,.18,z],[9.8,.09,.09]);
    box('Atrium cornice','brass',[0,5.65,z],[9.8,.13,.15]);
  }
  for(const x of [-4.8,4.8]) for(const z of [-3.8,3.8]) {
    box('Side cornice','brass',[x,5.65,z],[.15,.13,4.3]);
    box('Side skirting','brass',[x,.18,z],[.09,.09,4.3]);
  }
  // Roof ring leaves a genuine skylight; beams span its opening.
  for(const x of [-4,4]) box('Ceiling border','dark',[x,6.05,0],[2,.22,12]);
  for(const z of [-5,5]) box('Ceiling border','dark',[0,6.05,z],[6,.22,2]);
  for(const z of [-3,-1,1,3]) box('Skylight rib','brass',[0,6.1,z],[6,.10,.08]);
  box('Skylight night','sky',[0,7.5,0],[10,.05,12]);
  // Tall north window and celestial motif.
  arch('Celestial window',[0,.7,-5.8],0,3.3,4.5);
  box('Window sky','sky',[0,2.7,-5.83],[3.05,3.85,.03]);
  sphere('Distant moon','moon',[.35,3.5,-5.74],[.63,.63,.05],undefined,32,20);
  for(const x of [-1.5,0,1.5]) box('Window mullion','brass',[x,2.55,-5.64],[.065,3.7,.065]);
  box('Window transom','brass',[0,3.1,-5.64],[3.15,.055,.07]);
  for(const x of [-3.6,3.6]) {
    cylinder('Fluted column','ivory',[x,2.6,-4.8],.23,5.2);
    cylinder('Column base','brass',[x,.16,-4.8],.36,.3);
    cylinder('Column crown','brass',[x,5.15,-4.8],.36,.2);
    for(let j=0;j<12;j++) {
      const a=j/12*TAU;
      cylinder('Column flute','stone',[x+Math.cos(a)*.23,2.7,-4.8+Math.sin(a)*.23],.027,4.6,.027,6);
    }
    sconce(x,-5.72);
  }
  // The orrery is a persistent mesh, including each individual planet and orbit.
  const oz=-1.8;
  cylinder('Orrery bottom step','dark',[0,.10,oz],1.30,.20,1.30,64);
  cylinder('Orrery plinth','ivory',[0,.63,oz],.78,1.05,.62,48);
  cylinder('Orrery lip','brass',[0,1.2,oz],.84,.12,.84,48);
  cylinder('Orrery axle','brass',[0,1.75,oz],.065,1.2);
  sphere('Orrery sun','light',[0,2.15,oz],[.27,.27,.27],undefined,32,20);
  torus('Equatorial orbit','brass',[0,2.15,oz],1.05,.028,[.22,0,.2]);
  torus('Meridian orbit','gold',[0,2.15,oz],1.28,.035,[Math.PI/2,.25,.25]);
  torus('Ecliptic orbit','brass',[0,2.15,oz],1.5,.023,[.45,0,-.65]);
  sphere('Jade planet','teal',[1.01,2.15,oz+.17],[.16,.16,.16]);
  sphere('Ruby planet','velvet',[-.9,2.74,oz+.55],[.12,.12,.12]);
  sphere('Small moon','moon',[.27,1.2,oz-.83],[.085,.085,.085]);
  for(const r of [1.6,1.67,2.05]) torus('Floor meridian','brass',[0,.013,oz],r,.013);
  for(let i=0;i<24;i++) { const a=i/24*TAU; box('Compass tick','brass',[Math.cos(a)*1.87,.014,oz+Math.sin(a)*1.87],[.025,.012,i%3===0?.24:.12],[0,-a+Math.PI/2,0]); }
  // Seating, wall panels, and a recognizable return landmark.
  for(const x of [-3.25,3.25]) {
    box('Velvet settee seat','velvet',[x,.55,3.1],[1.5,.28,.85]);
    box('Velvet settee back','velvet',[x,.94,3.46],[1.5,.66,.17]);
    for(const dx of [-.62,.62]) for(const dz of [-.29,.29]) cylinder('Settee leg','brass',[x+dx,.23,3.1+dz],.035,.45, .035,8);
    for(const dx of [-.78,.78]) box('Settee arm','brass',[x+dx,.83,3.1],[.06,.17,.83]);
    plant('Atrium fern',x,4.7,2.3);
    sconce(x,5.78,Math.PI);
    arch('South inset',[x,.45,5.76],0,1.65,4.6);
  }
  box('South center panel','dark',[0,2.7,5.77],[2.25,4.5,.09]);
  torus('South brass clock','brass',[0,3.2,5.64],.7,.05,[Math.PI/2,0,0]);
  box('Clock hour','gold',[.14,3.37,5.57],[.035,.45,.035],[0,0,-.7]);
  box('Clock minute','gold',[-.15,3.37,5.55],[.025,.6,.025],[0,0,.7]);
  // Library: cobalt walls, walnut bookshelves, reading table, and red chair.
  box('Library west wall','blue',[-13,2.8,0],[.24,5.6,10]);
  for(const z of [-5,5]) box('Library end wall','blue',[-9,2.8,z],[8,5.6,.24]);
  box('Library ceiling','dark',[-9,5.6,0],[8,.2,10]);
  for(const z of [-4.65,4.65]) {
    box('Bookcase back','wood',[-9,2.5,z],[7.4,4.8,.22]);
    for(let shelf=0;shelf<6;shelf++) {
      const y=.35+shelf*.75;
      box('Library shelf','brass',[-9,y,z+(z<0?.22:-.22)],[7.4,.065,.48]);
      for(let book=0;book<35;book++) {
        const h=.33+((book*7+shelf*11)%13)/13*.28, w=.095+(book%3)*.022;
        box(`Book ${z<0?'N':'S'} ${shelf}-${book}`,['jade','velvet','blue','paper','wood'][((book*3+shelf*7)%5)],[-12.55+book*.208,y+h/2+.04,z+(z<0?.28:-.28)],[w,h,.26]);
      }
    }
    for(const x of [-12.75,-10.25,-7.75,-5.25]) box('Bookcase upright','wood',[x,2.5,z],[.1,4.8,.6]);
  }
  box('Library rug','velvet',[-10,.006,0],[3.5,.01,3.6]);
  box('Library table','wood',[-10.6,.87,-1.35],[2.4,.15,1]);
  for(const x of [-11.6,-9.6]) for(const z of [-1.7,-1]) cylinder('Reading table leg','brass',[x,.42,z],.04,.84,.04,10);
  cylinder('Reading lamp foot','brass',[-11.2,1,-1.35],.19,.08);
  cylinder('Reading lamp stem','brass',[-11.2,1.24,-1.35],.025,.5);
  sphere('Reading lamp shade','jade',[-11.2,1.48,-1.35],[.38,.18,.22]);
  sphere('Reading lamp bulb','light',[-11.2,1.41,-1.35],[.13,.035,.1]);
  box('Open atlas','paper',[-10.2,.974,-1.35],[.6,.025,.46],[0,.16,0]);
  box('Reading chair cushion','velvet',[-11,.52,1.3],[1.05,.3,1.05]);
  box('Reading chair back','velvet',[-11,.95,1.75],[1.05,1.0,.2]);
  for(const x of [-11.55,-10.45]) box('Reading chair arm','wood',[x,.7,1.3],[.12,.23,1.1]);
  for(const x of [-11.4,-10.6]) for(const z of [.9,1.7]) cylinder('Reading chair foot','brass',[x,.2,z],.04,.4,.04,8);
  arch('Library chart frame',[-12.82,.55,0],Math.PI/2,2.6,4.5);
  // Opaque inset, deliberately not a fake reflection.
  box('Library celestial inset','dark',[-12.79,2.5,0],[.07,3.7,2.4]);
  torus('Library star chart','brass',[-12.73,2.75,0],.85,.025,[0,0,Math.PI/2]);
  for(const z of [-3.2,3.2]) sconce(-12.77,z,Math.PI/2);
  // Conservatory: structural glasshouse ribs, foliage, and shallow lily pool.
  for(const z of [-5,5]) box('Conservatory end wall','dark',[9,1.2,z],[8,2.4,.16]);
  box('Conservatory east sill','jade',[13,.5,0],[.18,1,10]);
  box('Conservatory night','sky',[13.2,3.2,0],[.06,6.4,10.2]);
  for(const z of [-4.8,-3.2,-1.6,0,1.6,3.2,4.8]) {
    box('Glasshouse mullion','brass',[12.86,3.1,z],[.09,4.4,.09]);
    box('Glasshouse roof rib','brass',[9,5.25,z],[8,.09,.09]);
  }
  for(const y of [1.1,3.2,5.2]) box('Glasshouse transom','brass',[12.86,y,0],[.08,.08,10]);
  cylinder('Lily basin','ivory',[10,.22,0],1.7,.44,1.7,64);
  cylinder('Still water','teal',[10,.451,0],1.52,.018,1.52,64);
  for(let i=0;i<7;i++) {
    const a=i*2.4,r=.4+(i%3)*.32;
    cylinder('Lily pad','leaf',[10+Math.cos(a)*r,.467,Math.sin(a)*r],.19,.015,.19,20);
  }
  for(const z of [-3.5,3.5]) for(const x of [7,9.5,12]) plant('Conservatory palm',x,z,2.5+((x*2)%1)*.8);
  sphere('Conservatory moon','moon',[13.13,4.1,-2.3],[.025,.48,.48]);
  // Hanging warm globes establish depth without any image textures.
  for(const x of [-2.8,2.8]) for(const z of [-1.8,2.3]) {
    cylinder('Pendant cable','brass',[x,5.05,z],.016,1.8,.016,8);
    sphere('Pendant globe','light',[x,4.12,z],[.22,.22,.22]);
    torus('Pendant band','brass',[x,4.12,z],.226,.025);
  }
  return {
    id: SCENE_ID, name: 'The Meridian House', vertices: new Float32Array(vertices), objects,
    rooms: [ { name:'Atrium', bounds:[-5,-6,5,6] }, { name:'Library', bounds:[-13,-5,-5,5] }, { name:'Conservatory', bounds:[5,-5,13,5] } ],
    description: 'A nocturnal mansion: jade atrium, brass orrery, cobalt library, moonlit conservatory. Static set, no generated textures.',
  };
}

export function exportOBJ(scene) {
  const obj = ['# Meridian House, metres, Y up', 'mtllib meridian-house.mtl'];
  const data=scene.vertices;
  for(let i=0;i<data.length;i+=11) obj.push(`v ${data[i]} ${data[i+1]} ${data[i+2]}`);
  for(let i=0;i<data.length;i+=11) obj.push(`vn ${data[i+3]} ${data[i+4]} ${data[i+5]}`);
  for(const item of scene.objects) {
    obj.push(`o ${item.id}_${item.name.replace(/[^a-zA-Z0-9_-]/g,'_')}`,`usemtl ${item.material}`);
    for(let i=item.first+1;i<item.first+item.count+1;i+=3) obj.push(`f ${i}//${i} ${i+1}//${i+1} ${i+2}//${i+2}`);
  }
  const mtl=Object.entries(MATERIALS).flatMap(([name,m])=>[`newmtl ${name}`,`Kd ${m.color.join(' ')}`,`Ke ${m.color.map(v=>v*(m.emission||0)).join(' ')}`,'']);
  return { obj:obj.join('\n')+'\n', mtl:mtl.join('\n') };
}
