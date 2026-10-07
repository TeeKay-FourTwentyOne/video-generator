// ANGLES: a fixed observer inside a machined, irregular spherical cavity.
// Units are artistic and intentionally carry no metrology calibration.
export const VERSION = 'angles-cavity-v1';
export const DURATION = 30;
export const POSE_FPS = 8;
export const OUTPUT_FPS = 24;
const rad = degrees => degrees * Math.PI / 180;
const unit = v => { const d = Math.hypot(...v); return v.map(x => x / d); };
export const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
export const dot = (a,b) => a.reduce((sum,x,i)=>sum+x*b[i],0);

export function basis(n) {
  const u = unit(cross(Math.abs(n[1])>.92?[1,0,0]:[0,1,0],n));
  return {u,v:cross(n,u),n};
}

export function buildScene() {
  // Large cutter planes leave actual spherical patches between planar facets.
  const planes = [];
  for(let i=0;i<14;i++) {
    const yaw = rad(i*137.507764+21), y = 1-2*(i+.5)/14;
    const n = [Math.sqrt(1-y*y)*Math.sin(yaw),y,Math.sqrt(1-y*y)*Math.cos(yaw)];
    const distance = 3.5 + .95*Math.sin(i*2.3+.4);
    planes.push({id:`cut-face-${i}`,normal:n,distance,...basis(n)});
  }
  const rings = [
    {id:'split-bearing',center:[.35,-.10,-2.70],normal:unit([.20,.12,1]),outer:1.92,inner:1.31,halfDepth:.15},
    {id:'reverse-collar',center:[-1.28,.58,2.68],normal:unit([-.16,.23,1]),outer:1.49,inner:1.03,halfDepth:.22},
    {id:'cross-bearing',center:[2.9,.65,.65],normal:unit([1,.2,-.21]),outer:1.60,inner:1.13,halfDepth:.12},
  ].map(r=>({...r,...basis(r.normal)}));
  return {version:VERSION,radius:5.8,planes,rings,eye:[0,0,0],units:'uncalibrated artistic units',lights:'fixed to cavity surfaces'};
}

// The cuts change orientation, never scene geometry or observer position.
export const SHOTS = [
  {start:0,end:6,id:'01_edge',label:'EDGE / the face catches light',from:[-20,7,-16],to:[27,14,-7],fov:49},
  {start:6,end:10.5,id:'02_reverse',label:'REVERSE / the same cavity turns dark',from:[160,-7,17],to:[199,-12,7],fov:49},
  {start:10.5,end:16.5,id:'03_flank',label:'FLANK / a curved surface becomes a blade',from:[58,13,-26],to:[120,-6,-5],fov:49},
  {start:16.5,end:21,id:'04_under',label:'UNDERCUT / opposing planes close in',from:[255,25,40],to:[303,40,25],fov:49},
  {start:21,end:25.5,id:'05_crown',label:'CROWN / facets interrupt the circle',from:[340,58,-20],to:[398,30,0],fov:49},
  {start:25.5,end:30,id:'06_return',label:'RETURN / the opening angle is recovered',from:[27,14,-7],to:[-20,7,-16],fov:49},
];

export function cameraAt(time) {
  if(!Number.isFinite(time)||time<0||time>DURATION)throw new Error('Time outside the 30-second study.');
  const shot=SHOTS.find(s=>time>=s.start&&time<s.end)||SHOTS.at(-1);
  // Give the eye time to register both endpoints. Holds are intentional.
  const t=Math.max(0,Math.min(1,(time-shot.start-.375)/(shot.end-shot.start-.875)));
  const e=t*t*(3-2*t),angles=shot.from.map((v,i)=>v+(shot.to[i]-v)*e);
  const [yaw,pitch,roll]=angles.map(rad);
  const forward=[Math.sin(yaw)*Math.cos(pitch),Math.sin(pitch),-Math.cos(yaw)*Math.cos(pitch)];
  const right=unit(cross(forward,[0,1,0])),up=cross(right,forward);
  const rolledRight=right.map((v,i)=>v*Math.cos(roll)+up[i]*Math.sin(roll));
  const rolledUp=up.map((v,i)=>v*Math.cos(roll)-right[i]*Math.sin(roll));
  return {eye:[0,0,0],forward,right:rolledRight,up:rolledUp,angles,fov:shot.fov,shot:shot.id,time};
}

export function cavityDistance(direction,scene=buildScene(),baseline=false) {
  const n=unit(direction);
  return baseline?scene.radius:Math.min(scene.radius,...scene.planes.map(p=>dot(n,p.normal)>0?p.distance/dot(n,p.normal):Infinity));
}
