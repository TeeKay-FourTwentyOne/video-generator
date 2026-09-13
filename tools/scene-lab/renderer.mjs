import { cameraMatrix } from './math.mjs';
import { validateReference } from './reference.mjs';

export const MAX_PROJECTIONS = 8;
export const MODES = ['beauty', 'clay', 'depth', 'normals', 'objects', 'coverage'];
const vertex = `#version 300 es
precision highp float;
layout(location=0) in vec3 aPosition;
layout(location=1) in vec3 aNormal;
layout(location=2) in vec3 aColor;
layout(location=3) in float aEmission;
layout(location=4) in float aObject;
uniform mat4 uVP;
out vec3 vPosition, vNormal, vColor;
out float vEmission;
flat out float vObject;
void main() {
  vPosition=aPosition; vNormal=aNormal; vColor=aColor; vEmission=aEmission; vObject=aObject;
  gl_Position=uVP*vec4(aPosition,1.);
}`;
const projectionUniforms = Array.from({length:MAX_PROJECTIONS},(_,i)=>`
uniform sampler2D uImage${i}, uDepth${i};
uniform mat4 uProjector${i};
uniform vec3 uProjectorEye${i};`).join('\n');
const projectionCode = Array.from({length:MAX_PROJECTIONS},(_,i)=>`
if (uCount > ${i}) {
  vec4 clip=uProjector${i}*vec4(vPosition,1.);
  vec3 q=clip.xyz/clip.w*.5+.5;
  if(clip.w>0. && q.x>0. && q.x<1. && q.y>0. && q.y<1. && q.z>0. && q.z<1.) {
    float visible=1.-step(.00035,abs(texture(uDepth${i},q.xy).r-q.z));
    float edge=smoothstep(0.,.08,min(min(q.x,1.-q.x),min(q.y,1.-q.y)));
    // This scene renders double-sided geometry; source depth determines visibility.
    float facing=abs(dot(n,normalize(uProjectorEye${i}-vPosition)));
    float center=pow(max(.001,1.-pow(2.*abs(q.x-.5),2.)),3.);
    float weight=visible*edge*center*max(.01,pow(facing,3.));
    pigment+=texture(uImage${i},q.xy).rgb*weight;
    confidence+=weight;
    coverage=max(coverage,visible*edge);
  }
}`).join('\n');

const fragment = `#version 300 es
precision highp float;
in vec3 vPosition, vNormal, vColor;
in float vEmission;
flat in float vObject;
uniform vec3 uEye;
uniform int uMode, uCount;
uniform float uStrength;
${projectionUniforms}
out vec4 color;
vec3 pointLight(vec3 position, vec3 tint, vec3 n, vec3 albedo, float energy) {
  vec3 delta=position-vPosition;
  float d=length(delta);
  vec3 l=delta/d, view=normalize(uEye-vPosition), halfVector=normalize(l+view);
  float spec=pow(max(0.,dot(n,halfVector)),48.)*.22;
  return (albedo*max(0.,dot(n,l))+spec)*tint*energy/(1.+d*d*.14);
}
void main() {
  vec3 n=normalize(vNormal), albedo=vColor;
  if(uMode==1) albedo=vec3(.64,.66,.65);
  if(uMode!=1 && vPosition.y<.035 && vPosition.y>-.025 && abs(vPosition.x)<4.98 && abs(vPosition.z)<5.98) {
    vec2 tile=(vPosition.xz+vec2(20.))*1.3;
    float checker=mod(floor(tile.x)+floor(tile.y),2.);
    float vein=sin(vPosition.x*28.+sin(vPosition.z*15.)*2.)*.018;
    albedo=mix(vec3(.66,.66,.56),vec3(.13,.23,.23),checker)+vein;
    vec2 cell=fract(tile);
    if(min(min(cell.x,1.-cell.x),min(cell.y,1.-cell.y))<.015) albedo=vec3(.45,.34,.19);
  }
  float sky=max(n.y,0.);
  vec3 radiance=albedo*(vec3(.23,.28,.34)+sky*.12);
  radiance+=pointLight(vec3(0.,4.3,-1.8),vec3(1.,.73,.39),n,albedo,2.8);
  radiance+=pointLight(vec3(0.,3.5,4.),vec3(1.,.65,.38),n,albedo,1.5);
  radiance+=pointLight(vec3(-10.,3.8,0.),vec3(1.,.78,.53),n,albedo,2.4);
  radiance+=pointLight(vec3(10.,4.,0.),vec3(.48,.83,1.),n,albedo,2.4);
  radiance+=pointLight(vec3(0.,4.,-5.5),vec3(.42,.7,1.),n,albedo,1.7);
  radiance+=albedo*vEmission;
  vec3 beauty=pow(radiance/(radiance+vec3(.55)),vec3(1./2.2));
  beauty=mix(beauty,vec3(.10,.15,.19),1.-exp(-length(uEye-vPosition)*.008));
  vec3 pigment=vec3(0.); float confidence=0., coverage=0.;
  ${projectionCode}
  if(uMode==0 && confidence>0.) beauty=mix(beauty,pigment/confidence,uStrength*smoothstep(0.,.12,coverage));
  if(uMode==2) beauty=vec3(clamp(length(uEye-vPosition)/30.,0.,1.));
  if(uMode==3) beauty=n*.5+.5;
  if(uMode==4) beauty=fract(sin(vec3(vObject,vObject+37.,vObject+73.))*43758.5453);
  if(uMode==5) beauty=mix(vec3(.24,.09,.10),vec3(.26,.92,.64),smoothstep(0.,.12,coverage));
  color=vec4(beauty,1.);
}`;

function compile(gl,type,source) {
  const shader=gl.createShader(type); gl.shaderSource(shader,source); gl.compileShader(shader);
  if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
  return shader;
}
function program(gl,vs,fs) {
  const p=gl.createProgram(), shaders=[compile(gl,gl.VERTEX_SHADER,vs),compile(gl,gl.FRAGMENT_SHADER,fs)];
  shaders.forEach(s=>gl.attachShader(p,s)); gl.linkProgram(p);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  shaders.forEach(s=>gl.deleteShader(s)); return p;
}

export class Renderer {
  constructor(canvas,scene) {
    const gl=canvas.getContext('webgl2',{antialias:true,preserveDrawingBuffer:true,alpha:false});
    if(!gl) throw new Error('WebGL 2 is required. Enable hardware acceleration in your browser.');
    this.gl=gl; this.canvas=canvas; this.scene=scene; this.projections=[];
    this.program=program(gl,vertex,fragment);
    this.depthProgram=program(gl,`#version 300 es
      layout(location=0) in vec3 aPosition; uniform mat4 uVP;
      void main(){gl_Position=uVP*vec4(aPosition,1.);}`,`#version 300 es
      precision highp float; void main(){}`);
    this.vao=gl.createVertexArray(); gl.bindVertexArray(this.vao);
    const buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.bufferData(gl.ARRAY_BUFFER,scene.vertices,gl.STATIC_DRAW);
    let offset=0;
    [3,3,3,1,1].forEach((size,i)=>{ gl.enableVertexAttribArray(i);gl.vertexAttribPointer(i,size,gl.FLOAT,false,44,offset*4);offset+=size; });
    gl.enable(gl.DEPTH_TEST);
    // Bind complete placeholder textures for inactive projectors; no network assets.
    this.emptyImage=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,this.emptyImage);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([0,0,0,255]));
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    this.emptyDepth=this.createDepth(1,1);
    this.locations=new Map();
  }
  uniform(name) {
    if(!this.locations.has(name)) this.locations.set(name,this.gl.getUniformLocation(this.program,name));
    return this.locations.get(name);
  }
  createDepth(width,height) {
    const gl=this.gl,texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.DEPTH_COMPONENT24,width,height,0,gl.DEPTH_COMPONENT,gl.UNSIGNED_INT,null);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    return texture;
  }
  async addProjection(image,reference) {
    if(this.projections.length>=MAX_PROJECTIONS) throw new Error(`This preview supports ${MAX_PROJECTIONS} projections. Clear them before starting another set.`);
    validateReference(reference,this.scene);
    if(image.naturalWidth*reference.height!==image.naturalHeight*reference.width) throw new Error('Image aspect ratio must match the reference exactly; cropping changes camera alignment.');
    const gl=this.gl, width=image.naturalWidth, height=image.naturalHeight;
    if(Math.max(width,height)>gl.getParameter(gl.MAX_TEXTURE_SIZE)) throw new Error('Image exceeds this GPU’s texture size limit.');
    const texture=gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    const depth=this.createDepth(width,height), framebuffer=gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER,framebuffer);gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,depth,0);
    gl.drawBuffers([gl.NONE]);gl.readBuffer(gl.NONE);
    if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE) throw new Error('Projection depth framebuffer is incomplete.');
    const vp=cameraMatrix(reference.camera,width/height);
    gl.viewport(0,0,width,height);gl.clear(gl.DEPTH_BUFFER_BIT);gl.useProgram(this.depthProgram);gl.bindVertexArray(this.vao);
    gl.uniformMatrix4fv(gl.getUniformLocation(this.depthProgram,'uVP'),false,vp);
    gl.drawArrays(gl.TRIANGLES,0,this.scene.vertices.length/11);
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.deleteFramebuffer(framebuffer);
    this.projections.push({texture,depth,vp,reference});
    return this.projections.length;
  }
  clearProjections() {
    for(const p of this.projections) {this.gl.deleteTexture(p.texture);this.gl.deleteTexture(p.depth);}
    this.projections=[];
  }
  render(camera,{width=this.canvas.width,height=this.canvas.height,mode='beauty',strength=1}={}) {
    if(!MODES.includes(mode)) throw new Error(`Unknown render mode: ${mode}`);
    const gl=this.gl;
    if(this.canvas.width!==width || this.canvas.height!==height){this.canvas.width=width;this.canvas.height=height;}
    gl.bindFramebuffer(gl.FRAMEBUFFER,null);gl.viewport(0,0,width,height);
    gl.clearColor(.035,.06,.095,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.useProgram(this.program);gl.bindVertexArray(this.vao);
    gl.uniformMatrix4fv(this.uniform('uVP'),false,cameraMatrix(camera,width/height));
    gl.uniform3fv(this.uniform('uEye'),camera.eye);gl.uniform1i(this.uniform('uMode'),MODES.indexOf(mode));
    gl.uniform1i(this.uniform('uCount'),this.projections.length);gl.uniform1f(this.uniform('uStrength'),strength);
    for(let i=0;i<MAX_PROJECTIONS;i++) {
      const p=this.projections[i];
      gl.activeTexture(gl.TEXTURE0+i*2);gl.bindTexture(gl.TEXTURE_2D,p?.texture||this.emptyImage);gl.uniform1i(this.uniform(`uImage${i}`),i*2);
      gl.activeTexture(gl.TEXTURE0+i*2+1);gl.bindTexture(gl.TEXTURE_2D,p?.depth||this.emptyDepth);gl.uniform1i(this.uniform(`uDepth${i}`),i*2+1);
      if(p){gl.uniformMatrix4fv(this.uniform(`uProjector${i}`),false,p.vp);gl.uniform3fv(this.uniform(`uProjectorEye${i}`),p.reference.camera.eye);}
    }
    gl.drawArrays(gl.TRIANGLES,0,this.scene.vertices.length/11);
  }
  png() { return this.canvas.toDataURL('image/png'); }
  pixels() { const gl=this.gl, bytes=new Uint8Array(this.canvas.width*this.canvas.height*4);gl.readPixels(0,0,this.canvas.width,this.canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,bytes);return bytes; }
}
