#!/usr/bin/env node
import { readFile, writeFile, access } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { startServer } from './server.mjs';
import { openBrowser } from './chrome.mjs';

const [reviewPath,outputPath]=process.argv.slice(2);
if(!reviewPath||!outputPath)throw new Error('Usage: node tools/scene-lab/style-board.mjs REVIEW_JSON OUTPUT_PNG');
const source=resolve(reviewPath),output=resolve(outputPath),review=JSON.parse(await readFile(source,'utf8'));
if(!Array.isArray(review.frames)||review.frames.length!==8)throw new Error('Expected eight reviewed style frames.');
try{await access(output);throw new Error(`Output already exists: ${output}`);}catch(error){if(error.code!=='ENOENT')throw error;}
const assets=new Map();
for(let i=0;i<review.frames.length;i++)assets.set(`board-image-${i}`,{contentType:'image/png',body:await readFile(resolve(dirname(source),review.frames[i].image))});
const {server,url}=await startServer(0,assets);let browser;
try{
  browser=await openBrowser(url);
  const frames=review.frames.map((frame,i)=>({url:`${url}/board-image-${i}`,label:`${String(i+1).padStart(2,'0')}  ${frame.style.toUpperCase()}  /  ${frame.yawDegrees}\u00b0`}));
  const png=await browser.evaluateLarge(`(async()=>{
    const frames=${JSON.stringify(frames)},canvas=document.createElement('canvas');
    canvas.width=1920;canvas.height=620;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#f1f0e9';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
    ctx.font='600 14px system-ui, sans-serif';ctx.fillStyle='#24382f';ctx.textBaseline='middle';
    for(let i=0;i<frames.length;i++){
      const img=new Image();img.src=frames[i].url;await img.decode();
      const x=(i%4)*480,y=Math.floor(i/4)*310;
      ctx.drawImage(img,x,y,480,270);ctx.fillText(frames[i].label,x+12,y+291,456);
    }
    return canvas.toDataURL('image/png');
  })()`);
  await writeFile(output,Buffer.from(png.split(',')[1],'base64'),{flag:'wx'});
  console.log(`Saved ${output}`);
}finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
