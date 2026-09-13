#!/usr/bin/env node
// Compare the old edit and local finish without sending footage to a review provider.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {decode,comparePair,pairBoard} from './seam-search.mjs';
import {command,saveJSON} from './tour-finish.mjs';
import {startServer} from './server.mjs';
import {openBrowser} from './chrome.mjs';

const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
const base=join(dir,'edit/local-v2'),output=join(base,'qa');
const file=join(base,'final/meridian-house-tour-v2.mp4');
const oldFile=join(dir,'edit/review-v1/tour-review.mp4');
await mkdir(output);
const current=decode(file),raw=Array.from({length:6},(_,i)=>decode(join(dir,`clips/shot-${i+1}.mp4`)));
const before=raw.slice(0,5).map((a,i)=>({join:i+1,...comparePair(a,raw[i+1],95,0)}));
const after=[96,192,288,384,480].map((n,i)=>({join:i+1,...comparePair(current,current,n-1,n)}));
const median=values=>{const v=[...values].sort((a,b)=>a-b);return v[Math.floor(v.length/2)];};
const motionCrossCheck11Pairs=[96,192,288,384,480].map((n,i)=>{
  const baseA11=median(current.adjacent.slice(n-12,n-1)),baseB11=median(current.adjacent.slice(n,n+11));
  return {join:i+1,baseA11,baseB11,velocityRatio11:baseB11/baseA11};
});
const bounds={seamRatio:[.6,1.5],velocityRatio:[.7,1.4]};
const withinBounds=after.every(m=>m.seamRatio>=.6&&m.seamRatio<=1.5&&m.velocityRatio>=.7&&m.velocityRatio<=1.4);
const technical=await command('ffmpeg',['-hide_banner','-i',file,'-vf','blackdetect=d=0.08:pix_th=0.1,freezedetect=n=-50dB:d=0.5','-af','astats=metadata=1:reset=0','-f','null','-']);
await writeFile(join(output,'technical.log'),technical.err,{flag:'wx'});
const blackFreeze=technical.err.split('\n').filter(l=>/black_start|freeze_start|freeze_duration/.test(l));
const peakMatches=[...technical.err.matchAll(/Peak level dB: (-?[0-9.]+)/g)];
const audioPeakDBFS=Math.max(...peakMatches.map(m=>Number(m[1])));
const [pictureHash,exportHash]=await Promise.all([join(base,'retime-1080/tour-retimed.mp4'),file].map(p=>command('ffmpeg',['-v','error','-i',p,'-map','0:v','-c:v','copy','-f','hash','-hash','sha256','-'])));
const pictureUnchangedByAudioMux=pictureHash.out===exportHash.out;
const probe=JSON.parse((await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',file])).out);
const v=probe.streams.find(s=>s.codec_type==='video'),a=probe.streams.find(s=>s.codec_type==='audio');
const technicalPass=v.width===1920&&v.height===1080&&v.r_frame_rate==='24/1'&&v.nb_frames==='576'&&Number(v.duration)===24&&!!a&&Math.abs(Number(a.duration)-24)<.03&&blackFreeze.length===0&&audioPeakDBFS<0&&pictureUnchangedByAudioMux;
await saveJSON(join(output,'metrics.json'),{method:'270x152 grayscale proxies; mean absolute pixel delta; motion medians over eight pairs with a separate eleven-pair cross-check; photometric baseline pools eleven incoming and twelve outgoing pairs. Direct sample review still required.',before,after,bounds,motionCrossCheck11Pairs,allCutsWithinConfiguredBounds:withinBounds,thresholdCaveat:'These provisional diagnostic bands are not a guarantee of perceptual invisibility and are not a geometry-consistency test.',returnComparison:comparePair(current,current,575,0),blackFreeze,audioPeakDBFS,audioAuditioned:false,pictureUnchangedByAudioMux,technicalPass,probe,paidRequests:0});

const pairs=[];
for(let i=0;i<5;i++){
  const n=(i+1)*96;
  pairs.push({label:`JOIN ${i+1} ORIGINAL`,a:oldFile,b:oldFile,aFrame:n-1,bFrame:n});
  pairs.push({label:`JOIN ${i+1} FINISHED`,a:file,b:file,aFrame:n-1,bFrame:n});
}
await pairBoard(pairs,join(output,'before-after-joins.png'));
for(let i=0;i<5;i++){
  const n=(i+1)*96,pairs=[];
  for(let j=-8;j<8;j+=2)pairs.push({label:`JOIN ${i+1}`,a:file,b:file,aFrame:n+j,bFrame:n+j+1});
  await pairBoard(pairs,join(output,`join-${i+1}-dense.png`));
}
const interiorIndices=[10,38,66,104,128,156,198,224,256,306,344,368,402,438,466,490,530,570];
await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',file,'-vf',`select='${interiorIndices.map(n=>`eq(n,${n})`).join('+')}',scale=480:270,tile=3x6`,'-frames:v','1',join(output,'interior-check.png')]);
await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',file,'-vf','select=eq(n\\,0)','-frames:v','1',join(base,'final/poster.png')]);

const {server,url}=await startServer(0);let browser;
try{
  browser=await openBrowser(url);
  const png=await browser.evaluateLarge(`(()=>{const c=document.createElement('canvas');c.width=1920;c.height=1080;const x=c.getContext('2d');x.fillStyle='#f1f0e9';x.fillRect(0,0,1920,1080);x.fillStyle='#203b31';x.textBaseline='middle';x.font='600 48px system-ui';x.fillText('MERIDIAN HOUSE / MATCHING THE HANDOFFS',48,92);x.font='25px system-ui';x.fillText('Same six Veo clips. Matched anchor frames. Gently retimed camera moves.',48,151);x.font='600 24px system-ui';x.fillText('01 / ORIGINAL EDIT',48,218);x.fillText('02 / LOCAL FINISH',976,218);x.font='24px system-ui';x.fillText('The clips continued past their anchor positions.',48,805);x.fillText('The camera hands off at the matching view.',976,805);x.font='600 28px system-ui';x.fillText('The missing handoffs were already in the footage.',48,902);x.font='22px system-ui';x.fillText('No new generations. Original local music. Interior Veo prop changes remain.',48,950);x.fillStyle='#68786c';x.font='18px system-ui';x.fillText('https://github.com/TeeKay-FourTwentyOne/video-generator',48,1028);return c.toDataURL('image/png');})()`);
  await writeFile(join(output,'comparison-plate.png'),Buffer.from(png.split(',')[1],'base64'),{flag:'wx'});
}finally{await browser?.close();await new Promise(r=>server.close(r));}

const graph='[0:v]scale=896:504:flags=lanczos,setsar=1[old];[1:v]scale=896:504:flags=lanczos,setsar=1[new];[2:v][old]overlay=48:256:format=auto[first];[first][new]overlay=976:256:format=auto,format=yuv420p[v]';
const comparison=join(base,'final/before-after.mp4');
await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-i',oldFile,'-i',file,'-loop','1','-framerate','24','-i',join(output,'comparison-plate.png'),'-filter_complex',graph,'-map','[v]','-map','1:a','-t','24','-frames:v','576','-c:v','libx264','-preset','fast','-crf','18','-c:a','copy','-movflags','+faststart',comparison]);
await command('ffmpeg',['-hide_banner','-loglevel','error','-n','-ss','8.02','-i',comparison,'-frames:v','1',join(output,'comparison-poster.png')]);
console.log(JSON.stringify({file,comparison,technicalPass,allCutsWithinConfiguredBounds:withinBounds,after:after.map(m=>({join:m.join,seamRatio:m.seamRatio,velocityRatio:m.velocityRatio})),audioPeakDBFS,pictureUnchangedByAudioMux}));
