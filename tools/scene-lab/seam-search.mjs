#!/usr/bin/env node
// Local frame-exact search. No credentials, external services, or video mutations.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {spawnSync} from 'node:child_process';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {startServer} from './server.mjs';
import {openBrowser} from './chrome.mjs';

export const WIDTH=270,HEIGHT=152;
const median=a=>{const s=[...a].sort((a,b)=>a-b);return s.length?s[Math.floor(s.length/2)]:0;};
export function delta(a,b){let sum=0;for(let i=0;i<a.length;i++)sum+=Math.abs(a[i]-b[i]);return sum/a.length;}
function run(name,args){const r=spawnSync(name,args,{maxBuffer:128*1024*1024});if(r.status!==0)throw new Error(`${name}: ${r.stderr?.toString()}`);return r.stdout;}
export function decode(path){
  const data=run('ffmpeg',['-v','error','-i',path,'-vf',`scale=${WIDTH}:${HEIGHT}:flags=area,format=gray`,'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','gray','-']);
  const size=WIDTH*HEIGHT;if(data.length%size)throw new Error('Invalid proxy frame size.');
  const frames=Array.from({length:data.length/size},(_,i)=>data.subarray(i*size,(i+1)*size));
  const adjacent=frames.slice(1).map((f,i)=>delta(frames[i],f));
  const means=frames.map(f=>f.reduce((s,v)=>s+v,0)/size);
  return {frames,adjacent,means};
}

export function comparePair(a,b,ai,bi){
  const x=a.frames[ai],y=b.frames[bi],offset=a.means[ai]-b.means[bi];
  let sum=0,mse=0,tone=0;
  for(let k=0;k<x.length;k++){const d=x[k]-y[k];sum+=Math.abs(d);mse+=d*d;tone+=Math.abs(d-offset);}
  const aMotion=median(a.adjacent.slice(Math.max(0,ai-8),ai));
  const bMotion=median(b.adjacent.slice(bi,bi+8));
  const neighbor=median([...a.adjacent.slice(Math.max(0,ai-11),ai),...b.adjacent.slice(bi,bi+12)]);
  const prev=a.frames[Math.max(0,ai-3)],next=b.frames[Math.min(b.frames.length-1,bi+3)];
  let dot=0,aa=0,bb=0;
  for(let k=0;k<x.length;k+=4){const p=x[k]-prev[k],q=next[k]-y[k];dot+=p*q;aa+=p*p;bb+=q*q;}
  const cosine=aa*bb>1?dot/Math.sqrt(aa*bb):null;
  const mae=sum/x.length,correctedMAE=tone/x.length;
  const velocityRatio=aMotion>.01?bMotion/aMotion:null;
  // Ranking only, not a perceptual approval gate. Keep the independent channels.
  const motionPenalty=cosine===null?0:(1-cosine)*Math.min(aMotion,bMotion,2)*.4;
  const score=correctedMAE*.8+mae*.2+motionPenalty;
  return {aFrame:ai,bFrame:bi,aTime:ai/24,bTime:bi/24,mae,correctedMAE,meanLumaOffset:offset,psnr:mse?10*Math.log10(255*255/(mse/x.length)):100,aMotion,bMotion,neighborMedian:neighbor,seamRatio:neighbor>.05?mae/neighbor:null,velocityRatio,motionCosine:cosine,score};
}

export function search(a,b,{aStart=24,aEnd=a.frames.length-1,bStart=0,bEnd=Math.min(60,b.frames.length-13),step=1}={}){
  const candidates=[];
  for(let ai=aStart;ai<=aEnd;ai+=step)for(let bi=bStart;bi<=bEnd;bi+=step)candidates.push(comparePair(a,b,ai,bi));
  candidates.sort((a,b)=>a.score-b.score);
  const top=[];
  for(const c of candidates){if(top.every(t=>Math.abs(c.aFrame-t.aFrame)+Math.abs(c.bFrame-t.bFrame)>=8))top.push(c);if(top.length===16)break;}
  return {baseline:comparePair(a,b,a.frames.length-1,0),top};
}

export async function pairBoard(pairs,output){
  const assets=new Map();const labels=[];
  for(let i=0;i<pairs.length;i++){
    const p=pairs[i];
    for(const [which,path,frame] of [['A',p.a,p.aFrame],['B',p.b,p.bFrame]]){
      const key=`pair-${labels.length}`;
      assets.set(key,{body:run('ffmpeg',['-v','error','-i',path,'-vf',`select=eq(n\\,${frame})`,'-frames:v','1','-f','image2pipe','-vcodec','png','-']),contentType:'image/png'});
      labels.push({key,label:`${p.label} / ${which} ${frame} (${(frame/24).toFixed(3)}s)`});
    }
  }
  const {server,url}=await startServer(0,assets);let browser;
  try{
    browser=await openBrowser(url);
    const data=await browser.evaluateLarge(`(async()=>{const entries=${JSON.stringify(labels)},c=document.createElement('canvas');c.width=1920;c.height=Math.ceil(entries.length/4)*306;const x=c.getContext('2d');x.fillStyle='#f1f0e9';x.fillRect(0,0,c.width,c.height);x.font='600 15px system-ui';x.textBaseline='middle';for(let i=0;i<entries.length;i++){const img=new Image();img.src=${JSON.stringify(url)}+'/'+entries[i].key;await img.decode();const a=i%4*480,b=Math.floor(i/4)*306;x.drawImage(img,a,b,480,270);x.fillStyle='#203b31';x.fillText(entries[i].label,a+12,b+288,456);}return c.toDataURL('image/png');})()`);
    await writeFile(output,Buffer.from(data.split(',')[1],'base64'),{flag:'wx'});
  }finally{await browser?.close();await new Promise(r=>server.close(r));}
}

async function main(){
  const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
  const output=resolve(process.argv[3]||join(dir,'edit/local-v2'));
  await mkdir(output);
  const paths=Array.from({length:6},(_,i)=>join(dir,`clips/shot-${i+1}.mp4`));
  const data=paths.map(decode);const joins=[],pairs=[];
  for(let i=0;i<5;i++){
    const result=search(data[i],data[i+1]);joins.push({join:i+1,a:paths[i],b:paths[i+1],...result});
    for(const [label,p] of [['OLD',result.baseline],['MATCH',result.top[0]]])pairs.push({label:`JOIN ${i+1} ${label}`,a:paths[i],b:paths[i+1],aFrame:p.aFrame,bFrame:p.bFrame});
    console.log(JSON.stringify({join:i+1,baseline:result.baseline,top:result.top.slice(0,5)}));
  }
  const alternatePath=join(dir,'clips/shot-3-take-2.mp4'),alternate=decode(alternatePath);
  const alternatives=[{join:'2-to-long-3',a:paths[1],b:alternatePath,...search(data[1],alternate,{bStart:72,bEnd:120})},{join:'long-3-to-4',a:alternatePath,b:paths[3],...search(alternate,data[3],{aStart:144})}];
  for(const r of alternatives)console.log(JSON.stringify({alternate:r.join,baseline:r.baseline,top:r.top.slice(0,3)}));
  const sources=[];for(const path of [...paths,alternatePath])sources.push({path,sha256:createHash('sha256').update(await readFile(path)).digest('hex')});
  await writeFile(join(output,'seam-search.json'),JSON.stringify({createdAt:new Date().toISOString(),method:'frame-exact 270x152 luma search; brightness-normalized MAE with modest motion-direction penalty; visual review required',proxy:{width:WIDTH,height:HEIGHT},sources,joins,alternatives,paidRequests:0},null,2)+'\n',{flag:'wx'});
  await pairBoard(pairs,join(output,'seam-candidates.png'));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)main().catch(e=>{console.error(e);process.exitCode=1;});
