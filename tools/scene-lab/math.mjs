// Column-major matrices, right-handed world, Y up, camera looks along local -Z.
export const TAU = Math.PI * 2;
export const add = (a, b) => a.map((x, i) => x + b[i]);
export const sub = (a, b) => a.map((x, i) => x - b[i]);
export const dot = (a, b) => a.reduce((v, x, i) => v + x * b[i], 0);
export const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
export const normalize = a => { const n = Math.hypot(...a); return a.map(v => v / (n || 1)); };
export const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));

export function multiply(a, b) {
  const out = new Float32Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
    for (let k = 0; k < 4; k++) out[c*4+r] += a[k*4+r] * b[c*4+k];
  }
  return out;
}

export function transform(m, p) {
  const v = [...p.slice(0, 3), p[3] ?? 1];
  return [0, 1, 2, 3].map(r => v.reduce((s, x, c) => s + m[c*4+r] * x, 0));
}

export function perspective(fov, aspect, near = 0.08, far = 60) {
  const f = 1 / Math.tan(fov / 2), nf = 1 / (near - far);
  return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)*nf,-1, 0,0,2*far*near*nf,0]);
}

export function lookAt(eye, target, up = [0, 1, 0]) {
  const z = normalize(sub(eye, target)), x = normalize(cross(up, z)), y = cross(z, x);
  return new Float32Array([x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -dot(x,eye),-dot(y,eye),-dot(z,eye),1]);
}

export function cameraMatrix(camera, aspect) {
  return multiply(perspective(camera.fov * Math.PI/180, aspect), lookAt(camera.eye, camera.target));
}

export const SHOTS = {
  sweep: { name: 'Two revolutions', duration: 24, description: 'A locked camera. Two complete 360° sweeps.' },
  tour: { name: 'Library & return', duration: 24, description: 'Leave the atrium, enter the library, return to the same mark.' },
};

export function cameraAt(shot, progress) {
  if (!(shot in SHOTS)) throw new Error(`Unknown shot: ${shot}`);
  if (shot === 'sweep') {
    // Integer yaw prevents numerical differences between corresponding sweep frames.
    const phase = ((progress * 2) % 1 + 1) % 1;
    const yaw = Math.round(phase * 1e12) / 1e12 * TAU;
    const eye = [0, 1.7, 3.8];
    return { eye, target: add(eye, [Math.sin(yaw), -0.025, -Math.cos(yaw)]), fov: 64 };
  }
  const marks = [
    { t: 0, eye: [0,1.7,3.8], target: [0,2,-1.8] },
    { t: .16, eye: [-2.4,1.7,2.1], target: [-6,1.8,0] },
    { t: .32, eye: [-5.6,1.7,0], target: [-10.5,2,-.5] },
    { t: .50, eye: [-8.6,1.7,0], target: [-10.6,2,-2.8] },
    { t: .66, eye: [-8.6,1.7,0], target: [0,2,-1.8] },
    { t: .82, eye: [-4.2,1.7,0], target: [0,2,-1.8] },
    { t: 1, eye: [0,1.7,3.8], target: [0,2,-1.8] },
  ];
  const p = clamp(progress), i = Math.max(0, marks.findIndex((v, k) => k < marks.length - 1 && p <= marks[k+1].t));
  const a = marks[i], b = marks[i+1], u = clamp((p-a.t)/(b.t-a.t)), t = u*u*(3-2*u);
  return { eye: lerp(a.eye,b.eye,t), target: lerp(a.target,b.target,t), fov: 64 };
}
