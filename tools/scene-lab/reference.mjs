export function geometryHash(vertices) {
  let hash=2166136261;
  for(const byte of new Uint8Array(vertices.buffer,vertices.byteOffset,vertices.byteLength)) hash=Math.imul(hash^byte,16777619)>>>0;
  return hash.toString(16).padStart(8,'0');
}

export function validateReference(reference,scene) {
  if(reference?.schemaVersion!==1 || reference.sceneId!==scene.id || reference.geometryHash!==geometryHash(scene.vertices)) throw new Error('Camera metadata does not match this scene revision. Export a new reference pair.');
  const {width,height,camera}=reference;
  if(!Number.isInteger(width)||!Number.isInteger(height)||width<16||height<16||width>8192||height>8192) throw new Error('Invalid reference dimensions.');
  if(!camera || !['eye','target'].every(key=>Array.isArray(camera[key])&&camera[key].length===3&&camera[key].every(Number.isFinite)) || !Number.isFinite(camera.fov) || camera.fov<10 || camera.fov>120) throw new Error('Invalid reference camera.');
  if(Math.hypot(...camera.eye.map((v,i)=>v-camera.target[i]))<.001) throw new Error('Camera position and target must differ.');
  if(Math.hypot(camera.eye[0]-camera.target[0],camera.eye[2]-camera.target[2])<.001) throw new Error('Camera direction cannot be parallel to world up.');
  return reference;
}
