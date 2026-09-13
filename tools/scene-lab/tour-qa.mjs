#!/usr/bin/env node
// Local-only contact sheets and technical checks. No vision API or credentials.
import {readFile,writeFile,mkdir,access} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {spawn} from 'node:child_process';
import {startServer} from './server.mjs';
import {openBrowser} from './chrome.mjs';

const [directory,shotNumber]=process.argv.slice(2),dir=resolve(directory||'data/workspace/meridian-house/veo-tour-v1'),shot=Number(shotNumber);
if(!Number.isInteger(shot)||shot<1||shot>6)throw new Error('Usage: tour-qa.mjs RUN_DIRECTORY SHOT_NUMBER');
const plan=JSON.parse(await readFile(join(dir,'plan.json'),'utf8')),spec=plan.shots.find(s=>s.id===shot);
const stem=`shot-${shot}${spec.take>1?`-take-${spec.take}`:''}`;
const path=join(dir,`clips/${stem}.mp4`),output=join(dir,`qa/${stem}`);
try{await access(output);throw new Error('QA directory exists; inspect its results instead of overwriting.');}catch(e){if(e.code!=='ENOENT')throw e;}
function command(name,args){return new Promise((yes,no)=>{const child=spawn(name,args,{stdio:['ignore','pipe','pipe']});let out='',err='';child.stdout.on('data',c=>out+=c);child.stderr.on('data',c=>err+=c);child.on('error',no);child.on('close',code=>code===0?yes({out,err}):no(new Error(`${name} failed: ${err}`)));});}
const probe=JSON.parse((await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',path])).out);
const video=probe.streams.find(s=>s.codec_type==='video'),audio=probe.streams.find(s=>s.codec_type==='audio');
const n=Number(video.nb_frames),[top,bottom]=video.r_frame_rate.split('/').map(Number),fps=top/bottom;
if(!Number.isFinite(n)||n<16||!Number.isFinite(fps))throw new Error('Missing frame count/rate.');
const indices=Array.from({length:16},(_,i)=>Math.round(i*(n-1)/15));
await mkdir(output);
await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',path,'-vf',`select='${indices.map(i=>`eq(n,${i})`).join('+')}'`,'-fps_mode','vfr',join(output,'sample-%02d.png')]);
const diagnostics=await command('ffmpeg',['-hide_banner','-i',path,'-vf','blackdetect=d=0.08:pix_th=0.1,freezedetect=n=-50dB:d=0.75','-af','astats=metadata=1:reset=0','-f','null','-']);
await writeFile(join(output,'technical.log'),diagnostics.err,{flag:'wx'});
const similarities=[];
for(const [name,sample,anchor] of [['first',1,spec.start],['last',16,spec.end]]){
  const result=await command('ffmpeg',['-hide_banner','-i',join(output,`sample-${String(sample).padStart(2,'0')}.png`),'-i',join(dir,plan.anchors[anchor].image),'-filter_complex','[0:v][1:v]ssim','-f','null','-']);
  similarities.push({endpoint:name,ssim:Number(result.err.match(/All:([0-9.]+)/)?.[1]),anchor:plan.anchors[anchor].image});
}
const blackFreeze=diagnostics.err.split('\n').filter(l=>/black_start|freeze_start|freeze_duration/.test(l));
const metrics={shot,take:spec.take??1,video:path,duration:Number(probe.format.duration),width:video.width,height:video.height,frameRate:fps,frameCount:n,pixelFormat:video.pix_fmt,audio:audio?{codec:audio.codec_name,rate:audio.sample_rate,channels:audio.channels}:null,endpointSimilarities:similarities,blackFreeze,technicalPass:video.width===1920&&video.height===1080&&fps===24&&n===spec.durationSeconds*24&&!!audio&&blackFreeze.length===0,visualReview:'pending',samples:indices.map((index,i)=>({file:`sample-${String(i+1).padStart(2,'0')}.png`,frame:index,time:index/fps}))};
await writeFile(join(output,'metrics.json'),JSON.stringify(metrics,null,2)+'\n',{flag:'wx'});
const assets=new Map();for(let i=0;i<16;i++)assets.set(`qa-${i}`,{body:await readFile(join(output,metrics.samples[i].file)),contentType:'image/png'});
const {server,url}=await startServer(0,assets);let browser;
try{
  browser=await openBrowser(url);
  const png=await browser.evaluateLarge(`(async()=>{const c=document.createElement('canvas');c.width=1920;c.height=1200;const x=c.getContext('2d');x.fillStyle='#f1f0e9';x.fillRect(0,0,c.width,c.height);x.font='600 14px system-ui';x.textBaseline='middle';const times=${JSON.stringify(metrics.samples.map(s=>s.time))};for(let i=0;i<16;i++){const img=new Image();img.src=${JSON.stringify(url)}+'/qa-'+i;await img.decode();const a=(i%4)*480,b=Math.floor(i/4)*300;x.drawImage(img,a,b,480,270);x.fillStyle='#24382f';x.fillText('SHOT ${shot}  /  '+times[i].toFixed(3)+'s',a+12,b+286);}return c.toDataURL('image/png');})()`);
  await writeFile(join(output,'contact.png'),Buffer.from(png.split(',')[1],'base64'),{flag:'wx'});
}finally{await browser?.close();await new Promise(r=>server.close(r));}
console.log(JSON.stringify(metrics,null,2));
