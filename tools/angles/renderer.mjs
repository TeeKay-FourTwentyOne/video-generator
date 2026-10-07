import {buildScene,cameraAt} from './scene.mjs';

const vertex=`#version 300 es
in vec2 p; void main(){gl_Position=vec4(p,0,1);}`;
const fragment=`#version 300 es
precision highp float;
uniform vec2 size;
uniform vec3 forward,right,up;
uniform float fov;
uniform int baseline,look,mode;
uniform vec4 planes[14];
uniform vec3 ringC[3],ringU[3],ringV[3],ringN[3],ringD[3];
out vec4 color;
const float PI=3.14159265359;
struct Hit{float t; vec3 p; vec3 n; vec2 uv; vec3 u; vec3 v; float id;};
void candidate(inout Hit h,float t,vec3 ro,vec3 rd,vec3 n,vec3 u,vec3 v,vec3 c,float id){
  if(t>.0004&&t<h.t){h.t=t;h.p=ro+rd*t;h.n=dot(n,rd)>0.?-n:n;h.u=u;h.v=v;h.uv=vec2(dot(h.p-c,u),dot(h.p-c,v));h.id=id;}
}
Hit intersect(vec3 ro,vec3 rd){
  Hit h;h.t=1e5;h.id=-1.;
  float b=dot(ro,rd),c=dot(ro,ro)-5.8*5.8,d=b*b-c;
  if(d>0.){
    float t=-b+sqrt(d);vec3 p=ro+rd*t,n=-normalize(p);
    vec3 u=normalize(cross(abs(n.y)>.99?vec3(1,0,0):vec3(0,1,0),n)),v=cross(n,u);
    candidate(h,t,ro,rd,n,u,v,vec3(0),20.);
    h.uv=vec2(atan(p.x,p.z)*3.,asin(p.y/5.8)*3.);
  }
  if(baseline==1)return h;
  for(int i=0;i<14;i++){
    vec3 n=planes[i].xyz;
    float den=dot(n,rd);
    if(den>.00001){
      float t=(planes[i].w-dot(n,ro))/den;
      vec3 u=normalize(cross(abs(n.y)>.92?vec3(1,0,0):vec3(0,1,0),n)),v=cross(n,u);
      candidate(h,t,ro,rd,-n,u,v,vec3(0),float(i));
    }
  }
  for(int i=0;i<3;i++){
    vec3 q=ro-ringC[i];
    vec3 o=vec3(dot(q,ringU[i]),dot(q,ringV[i]),dot(q,ringN[i]));
    vec3 d=vec3(dot(rd,ringU[i]),dot(rd,ringV[i]),dot(rd,ringN[i]));
    for(int j=0;j<2;j++){
      float z=(j==0?-1.:1.)*ringD[i].z;
      float t=(z-o.z)/d.z;vec3 p=o+d*t;
      if(dot(p.xy,p.xy)<ringD[i].x*ringD[i].x&&dot(p.xy,p.xy)>ringD[i].y*ringD[i].y)
        candidate(h,t,ro,rd,ringN[i]*(j==0?-1.:1.),ringU[i],ringV[i],ringC[i],30.+float(i)*3.);
    }
    float a=dot(d.xy,d.xy),b=dot(o.xy,d.xy);
    if(a<.000001)continue;
    for(int j=0;j<2;j++){
      float r=j==0?ringD[i].x:ringD[i].y,c=dot(o.xy,o.xy)-r*r,det=b*b-a*c;
      if(det<0.)continue;
      for(int k=0;k<2;k++){
        float t=(-b+(k==0?-1.:1.)*sqrt(det))/a;vec3 p=o+d*t;
        if(abs(p.z)<=ringD[i].z){
          vec3 n=normalize(p.x*ringU[i]+p.y*ringV[i]);
          candidate(h,t,ro,rd,n,ringU[i],ringV[i],ringC[i],31.+float(i)*3.);
        }
      }
    }
  }
  return h;
}
float line(float x,float width){return 1.-smoothstep(width,width+fwidth(x)*1.4,abs(x));}
vec3 studio(vec3 d){
  // An analytic reflection fill supplies the unresolved higher-order bounces.
  vec3 c=vec3(.010,.012,.015);
  c+=vec3(2.5,2.7,2.9)*pow(max(0.,dot(d,normalize(vec3(-.5,.75,-.3)))),16.);
  c+=vec3(1.6)*smoothstep(.915,.97,abs(d.x))*(.65+.35*d.y);
  c+=vec3(.75,.83,1.0)*pow(max(0.,dot(d,normalize(vec3(.1,-.7,1)))),26.);
  c+=vec3(3.0,2.7,2.2)*pow(max(0.,dot(d,normalize(vec3(.7,.4,.5)))),50.);
  return c;
}
vec3 aces(vec3 x){return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14),0.,1.);}
vec3 trace(vec3 ro,vec3 rd){
  vec3 sum=vec3(0),throughput=vec3(1);
  for(int bounce=0;bounce<3;bounce++){
    Hit h=intersect(ro,rd);
    if(h.id<0.){sum+=throughput*studio(rd);break;}
    if(bounce==0&&mode==1)return vec3(h.t/6.5);
    if(bounce==0&&mode==2)return h.n*.5+.5;
    if(bounce==0&&mode==3)return vec3(.42,.45,.48)*(.2+.8*max(0.,dot(h.n,normalize(vec3(-.3,.65,.9)))));
    vec2 uv=h.uv;
    float rad=length(uv),theta=atan(uv.y,uv.x);
    float isRing=step(29.,h.id);
    float isFace=1.-step(.5,mod(h.id-30.,3.));
    float freq=mix(40.,110.,isRing);
    float grain=sin(rad*freq)*.5+.5;
    float fine=sin(rad*freq*3.+sin(theta*53.)*.12);
    // Continuous, object-local tool marks. No per-frame random texture.
    float rough=mix(.055,.07,grain);
    if(look==1)rough*=.36;
    if(look==2)rough*=1.7;
    vec3 n=h.n;
    vec2 grad=uv/max(rad,.01);
    float bump=(sin(rad*freq)*.0007+fine*.00012)*(look==1?.3:1.);
    n=normalize(n+(h.u*grad.x+h.v*grad.y)*bump);
    if(isRing>.5&&isFace>.5){
      int i=int((h.id-30.)/3.);
      float edge=min(ringD[i].x-rad,rad-ringD[i].y);
      float edgeSign=rad>(ringD[i].x+ringD[i].y)*.5?1.:-1.;
      float bevel=1.-smoothstep(0.,.045,edge);
      n=normalize(n+(h.u*grad.x+h.v*grad.y)*bevel*edgeSign*.8);
    }
    float seam=0.,emission=0.;
    if(h.id<20.){
      // The light cards are fixed to particular faces of the cavity.
      float sid=mod(h.id,4.);
      if(sid<.5){emission=line(uv.x-.7,.055)*(1.-smoothstep(1.6,1.8,abs(uv.y)));}
      if(sid>1.5&&sid<2.5){emission=(1.-smoothstep(.06,.08,abs(uv.x+.3)))*(1.-smoothstep(1.70,1.74,abs(uv.y-.4)));}
      seam=line(mod(uv.y+.52,1.04)-.52,.006)*.7;
    }
    float groove=0.;
    if(isRing>.5&&isFace>.5){
      int i=int((h.id-30.)/3.);
      groove=max(line(rad-(ringD[i].x-.11),.016),line(rad-(ringD[i].y+.09),.012));
      float ticks=line(mod(theta+.065,.13)-.065,.003)*(1.-smoothstep(.075,.11,ringD[i].x-rad));
      groove=max(groove,ticks*.6);
    }
    vec3 metal=mix(vec3(.74,.77,.80),vec3(.91,.92,.94),isRing)*(1.-groove*.82)*(1.-seam*.82);
    vec3 tint=look==2?vec3(.91,.84,.73):vec3(1.);
    vec3 ref=reflect(rd,n);
    float facing=abs(dot(rd,n));
    vec3 broad=studio(normalize(ref+n*rough*1.8));
    vec3 diffuse=vec3(.007,.009,.013)*(1.-grain*.08);
    vec3 light=vec3(1.05,1.10,1.16)*emission*4.;
    float polish=look==1?.28:.60;
    sum+=throughput*(light+diffuse+metal*broad*polish);
    throughput*=metal*tint*(1.-polish)*(1.-emission);
    if(max(throughput.x,max(throughput.y,throughput.z))<.01)break;
    ro=h.p+n*.001;rd=ref;
    if(bounce==2)sum+=throughput*studio(ref)*.9;
  }
  return sum;
}
void main(){
  vec3 c=vec3(0);
  for(int i=0;i<4;i++){
    vec2 offset=vec2(float(i%2),float(i/2))*.5-.25;
    vec2 p=(gl_FragCoord.xy+offset-size*.5)/size.y;
    vec3 rd=normalize(forward+(p.x*right+p.y*up)*2.*tan(radians(fov)*.5));
    c+=trace(vec3(0),rd)*.25;
  }
  if(mode==0)c=pow(aces(c*.95),vec3(1./2.2));
  color=vec4(c,1.);
}`;

export function createRenderer(canvas){
  const gl=canvas.getContext('webgl2',{antialias:false,preserveDrawingBuffer:true,alpha:false});
  if(!gl)throw new Error('WebGL 2 required');
  const compile=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s;};
  const program=gl.createProgram();gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));gl.useProgram(program);
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  const p=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
  const scene=buildScene(),loc=name=>gl.getUniformLocation(program,name);
  gl.uniform4fv(loc('planes'),new Float32Array(scene.planes.flatMap(p=>[...p.normal,p.distance])));
  for(const [key,name] of [['center','ringC'],['u','ringU'],['v','ringV'],['n','ringN']])gl.uniform3fv(loc(name),new Float32Array(scene.rings.flatMap(r=>r[key])));
  gl.uniform3fv(loc('ringD'),new Float32Array(scene.rings.flatMap(r=>[r.outer,r.inner,r.halfDepth])));
  const ext=gl.getExtension('WEBGL_debug_renderer_info');
  return {scene,info:{renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)},render({time=0,width=1280,height=720,baseline=false,look=0,mode=0,camera=null}={}){
    if(width/height!==16/9||width>1920||height>1080)throw new Error('Audition requires 16:9 at no more than native 1080p');
    canvas.width=width;canvas.height=height;gl.viewport(0,0,width,height);gl.useProgram(program);
    const c=camera??cameraAt(time);
    gl.uniform2f(loc('size'),width,height);gl.uniform1f(loc('fov'),c.fov);
    for(const key of ['forward','right','up'])gl.uniform3fv(loc(key),c[key]);
    gl.uniform1i(loc('baseline'),baseline?1:0);gl.uniform1i(loc('look'),look);gl.uniform1i(loc('mode'),mode);
    gl.drawArrays(gl.TRIANGLES,0,3);gl.finish();
    const error=gl.getError();if(error)throw new Error(`WebGL error ${error}`);
    return {png:canvas.toDataURL('image/png'),camera:c,baseline,look,mode};
  }};
}
