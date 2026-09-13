#!/usr/bin/env node
// Original score synthesized locally from oscillators. No samples, downloads, or music APIs.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {command,saveJSON} from './tour-finish.mjs';

const CHORDS=[
  {name:'Dm(add9)',bass:38,notes:[62,65,69,76]},
  {name:'Dm(add9)',bass:38,notes:[62,65,69,76]},
  {name:'Bbmaj7',bass:34,notes:[62,65,69,74]},
  {name:'Gm9',bass:31,notes:[62,65,67,70]},
  {name:'F(add9)',bass:29,notes:[60,65,69,74]},
  {name:'C(add9)',bass:36,notes:[60,64,67,74]},
  {name:'A7sus4',bass:33,notes:[62,64,67,69]},
  {name:'Dm(add9)',bass:38,notes:[62,65,69,74]},
];
const hz=midi=>440*2**((midi-69)/12);
export function loudnessJSON(log){
  const blocks=[...log.matchAll(/\{\s*"input_i"\s*:[\s\S]*?\}/g)];
  if(!blocks.length)throw new Error('No loudnorm measurement in FFmpeg output.');
  return JSON.parse(blocks.at(-1)[0]);
}
export function compose({duration=24,sampleRate=48000}={}){
  if(!(duration>=2&&duration<=120&&sampleRate>=8000&&sampleRate<=96000))throw new Error('Invalid score duration/rate.');
  const count=Math.round(duration*sampleRate),left=new Float32Array(count),right=new Float32Array(count),events=[];
  function tone(midi,start,length,amp,pan,type){
    const begin=Math.round(start*sampleRate),end=Math.min(count,Math.round((start+length)*sampleRate));
    const f=hz(midi),lg=Math.cos((pan+1)*Math.PI/4),rg=Math.sin((pan+1)*Math.PI/4);
    events.push({midi,start,length,amp,pan,type});
    for(let i=begin;i<end;i++){
      if(i<0)continue;
      const t=(i-begin)/sampleRate,phase=2*Math.PI*f*t;
      let sample;
      if(type==='bell'){
        const envelope=(1-Math.exp(-t/0.009))*Math.exp(-t/.72)*Math.min(1,(length-t)/.08);
        sample=envelope*(Math.sin(phase)+.28*Math.exp(-t/.3)*Math.sin(phase*2.002)+.08*Math.exp(-t/.16)*Math.sin(phase*4.006));
      }else{
        const envelope=Math.min(1,t/.7)*Math.min(1,(length-t)/.9);
        const vibrato=.008*Math.sin(2*Math.PI*.16*t);
        sample=envelope*(Math.sin(phase+vibrato)+.14*Math.sin(phase*2.0003));
      }
      left[i]+=sample*amp*lg;right[i]+=sample*amp*rg;
    }
  }
  const bar=duration/8,pattern=[0,2,1,3,2,1,3,2];
  for(let b=0;b<8;b++){
    const c=CHORDS[b],at=b*bar;
    tone(c.bass,at,bar+1.1,.027,0,'pad');
    for(let j=0;j<c.notes.length;j++)tone(c.notes[j]-12,at+.03*j,bar+.95,.012,(j-1.5)/4,'pad');
    for(let j=0;j<8;j++){
      // Let the final tonic ring; no last-second busy flourish.
      if(b===7&&j>3)continue;
      const note=c.notes[pattern[j]],level=j%2===0?.028:.018;
      tone(note,at+j*bar/8,1.7,level,Math.sin((b*8+j)*1.7)*.3,'bell');
    }
  }
  // Sparse upper melody, independent of the arpeggio pattern.
  for(const [beat,note] of [[1,74],[3,76],[5,77],[7,81],[10,77],[13,79],[16,81],[18,79],[21,76],[25,76],[27,73],[29,74]])
    tone(note,beat*duration/32,2.4,.022,.12,'bell');
  // Small, decaying stereo echoes; derived solely from this original synthesis.
  for(const [delay,gain] of [[.113,.13],[.229,.09],[.367,.045]]){
    const n=Math.round(delay*sampleRate);
    for(let i=count-1;i>=n;i--){left[i]+=right[i-n]*gain;right[i]+=left[i-n]*gain;}
  }
  let peak=0;
  for(let i=0;i<count;i++){
    const t=i/sampleRate,fade=Math.min(1,t/.6)*Math.min(1,(duration-t)/1.45);
    left[i]*=fade;right[i]*=fade;peak=Math.max(peak,Math.abs(left[i]),Math.abs(right[i]));
  }
  const gain=.35/Math.max(peak,.001);
  for(let i=0;i<count;i++){left[i]*=gain;right[i]*=gain;}
  return {left,right,sampleRate,duration,events,chords:CHORDS,gain};
}

export function wav(score){
  const {left,right,sampleRate}=score,n=left.length;
  if(right.length!==n)throw new Error('Channel length mismatch.');
  const bytes=Buffer.alloc(44+n*4);
  bytes.write('RIFF',0);bytes.writeUInt32LE(bytes.length-8,4);bytes.write('WAVEfmt ',8);bytes.writeUInt32LE(16,16);
  bytes.writeUInt16LE(1,20);bytes.writeUInt16LE(2,22);bytes.writeUInt32LE(sampleRate,24);bytes.writeUInt32LE(sampleRate*4,28);bytes.writeUInt16LE(4,32);bytes.writeUInt16LE(16,34);bytes.write('data',36);bytes.writeUInt32LE(n*4,40);
  for(let i=0;i<n;i++)for(const [channel,values] of [[0,left],[1,right]]){
    if(!Number.isFinite(values[i]))throw new Error('Nonfinite audio sample.');
    bytes.writeInt16LE(Math.round(Math.max(-1,Math.min(1,values[i]))*32767),44+i*4+channel*2);
  }
  return bytes;
}

export async function finishScore(dir,picture,output){
  await mkdir(output);
  const score=compose(),scoreFile=join(output,'meridian-after-hours.wav');
  await writeFile(scoreFile,wav(score),{flag:'wx'});
  await saveJSON(join(output,'score.json'),{title:'After Hours at Meridian House',origin:'Original local oscillator synthesis; no third-party samples, recordings, or generation services',composer:'Astra / Codex',duration:score.duration,sampleRate:score.sampleRate,tempoBPM:80,chords:score.chords,events:score.events,paidRequests:0,auditioned:false});
  const inputs=Array.from({length:6},(_,i)=>join(dir,`clips/shot-${i+1}.mp4`));
  const graph=inputs.map((_,i)=>`[${i}:a]atrim=end=${88/24},asetpts=PTS-STARTPTS,atempo=${88/96},apad,atrim=duration=4,aresample=48000,aformat=channel_layouts=stereo,highpass=f=100,lowpass=f=7000,volume=-16dB,afade=t=in:d=0.04,afade=t=out:st=3.94:d=0.06[a${i}]`);
  graph.push(`${inputs.map((_,i)=>`[a${i}]`).join('')}concat=n=6:v=0:a=1[room]`);
  graph.push('[6:a]aformat=channel_layouts=stereo[music]');
  graph.push('[room][music]amix=inputs=2:duration=longest:normalize=0,atrim=duration=24,afade=t=out:st=22.7:d=1.3[mix]');
  const mix=join(output,'mix.wav');
  await command('ffmpeg',['-hide_banner','-loglevel','error','-n',...inputs.flatMap(p=>['-i',p]),'-i',scoreFile,'-filter_complex',graph.join(';'),'-map','[mix]','-c:a','pcm_s24le','-ar','48000',mix]);
  const scan=await command('ffmpeg',['-hide_banner','-i',mix,'-af','loudnorm=I=-19:TP=-1.5:LRA=8:print_format=json','-f','null','-']);
  const measured=loudnessJSON(scan.err);
  const normalization=`loudnorm=I=-19:TP=-1.5:LRA=8:measured_I=${measured.input_i}:measured_TP=${measured.input_tp}:measured_LRA=${measured.input_lra}:measured_thresh=${measured.input_thresh}:offset=${measured.target_offset}:linear=true:print_format=json`;
  const file=join(output,'meridian-house-tour-v2.mp4');
  const render=await command('ffmpeg',['-hide_banner','-loglevel','info','-n','-i',picture,'-i',mix,'-map','0:v:0','-map','1:a:0','-c:v','copy','-af',normalization,'-c:a','aac','-b:a','192k','-ar','48000','-t','24','-movflags','+faststart',file]);
  const normalResult=loudnessJSON(render.err);
  const probe=JSON.parse((await command('ffprobe',['-v','error','-show_streams','-show_format','-of','json',file])).out);
  await saveJSON(join(output,'manifest.json'),{status:'local-finish-pending-final-QA',output:file,pictureSource:picture,pictureSourceSHA256:createHash('sha256').update(await readFile(picture)).digest('hex'),outputSHA256:createHash('sha256').update(await readFile(file)).digest('hex'),probe,audio:{score:scoreFile,nativeVeoBed:'original six clips, lightly time-stretched, band-limited and lowered 16 dB; generic ambience, not dialogue synchronization',loudnessScan:measured,normalizationResult:normalResult,auditioned:false},paidRequests:0});
  console.log(JSON.stringify({file,normalization:normalResult}));
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
  const dir=resolve(process.argv[2]||'data/workspace/meridian-house/veo-tour-v1');
  const picture=resolve(process.argv[3]||join(dir,'edit/local-v2/retime-1080/tour-retimed.mp4'));
  const output=resolve(process.argv[4]||join(dir,'edit/local-v2/finished'));
  finishScore(dir,picture,output).catch(e=>{console.error(e.message);process.exitCode=1;});
}
