// Minimal Chrome DevTools client. Uses the installed browser and Node's WebSocket.
// No npm download, account, browser profile, or remote generation endpoint.
import { spawn } from 'node:child_process';
import { mkdtemp, rm, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

async function chromePath() {
  const choices=[process.env.SCENE_LAB_CHROME,
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser',
    process.env.LOCALAPPDATA?join(process.env.LOCALAPPDATA,'Google/Chrome/Application/chrome.exe'):null,
  ].filter(Boolean);
  for(const path of choices){try{await access(path);return path;}catch{}}
  throw new Error('Chrome or Chromium was not found. Set SCENE_LAB_CHROME to an installed browser executable.');
}
export async function openBrowser(url) {
  const executable=await chromePath(),profile=await mkdtemp(join(tmpdir(),'meridian-chrome-'));
  let child,socket,closed=false,browserLogs='';
  const pending=new Map();let nextId=0;
  async function close(){
    if(closed)return;closed=true;
    for(const {reject,timer} of pending.values()){clearTimeout(timer);reject(new Error('Browser closed'));}pending.clear();
    socket?.close();
    if(child?.pid&&child.exitCode===null&&child.signalCode===null){
      const ended=new Promise(resolve=>child.once('exit',resolve));child.kill('SIGTERM');
      const timer=setTimeout(()=>child.kill('SIGKILL'),3000);await ended;clearTimeout(timer);
    }
    // Only remove the exact temporary Chrome profile created by this function.
    await rm(profile,{recursive:true,force:true,maxRetries:3,retryDelay:100});
  }
  try {
    child=spawn(executable,[
      '--headless=new','--remote-debugging-port=0',`--user-data-dir=${profile}`,
      '--no-first-run','--no-default-browser-check','--disable-background-networking',
      '--disable-component-update','--disable-sync','--disable-default-apps','--disable-extensions',
      '--disable-domain-reliability','--disable-breakpad','--metrics-recording-only',
      '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost',
      '--window-size=1440,1120','about:blank',
    ],{stdio:['ignore','ignore','pipe']});
    const endpoint=await new Promise((resolve,reject)=>{
      let logs='';const timer=setTimeout(()=>reject(new Error('Chrome did not start within 20 seconds.')),20000);
      child.once('error',error=>{clearTimeout(timer);reject(error);});
      child.once('exit',code=>{clearTimeout(timer);reject(new Error(`Chrome exited (${code}): ${logs.slice(-1500)}`));});
      child.stderr.on('data',data=>{logs=(logs+data).slice(-10000);browserLogs=logs;const match=logs.match(/DevTools listening on (ws:\/\/[^\s]+)/);if(match){clearTimeout(timer);resolve(match[1]);}});
    });
    socket=new WebSocket(endpoint);
    await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
    socket.addEventListener('message',event=>{
      const message=JSON.parse(event.data),request=pending.get(message.id);if(!request)return;
      pending.delete(message.id);clearTimeout(request.timer);
      if(message.error)request.reject(new Error(message.error.message));else request.resolve(message.result);
    });
    socket.addEventListener('close',event=>{for(const request of pending.values()){clearTimeout(request.timer);request.reject(new Error(`Chrome connection closed (${event.code}${event.reason?`: ${event.reason}`:''}). ${browserLogs.slice(-1600)}`));}pending.clear();});
    function send(method,params={},sessionId){
      return new Promise((resolve,reject)=>{
        const id=++nextId,timer=setTimeout(()=>{pending.delete(id);reject(new Error(`Chrome timeout: ${method}`));},30000);
        pending.set(id,{resolve,reject,timer});socket.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));
      });
    }
    const {targetId}=await send('Target.createTarget',{url:'about:blank'});
    const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
    const call=(method,params={})=>send(method,params,sessionId);
    await call('Page.enable');await call('Network.enable');
    // Restrict every page request to this loopback origin (including subresources).
    await call('Fetch.enable',{patterns:[{urlPattern:'*'}]});
    socket.addEventListener('message',event=>{
      const m=JSON.parse(event.data);
      if(m.method!=='Fetch.requestPaused'||m.sessionId!==sessionId)return;
      const allowed=m.params.request.url.startsWith(`${url}/`)||m.params.request.url===url;
      call(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:m.params.requestId,...(allowed?{}:{errorReason:'BlockedByClient'})}).catch(()=>{});
    });
    await call('Page.navigate',{url:`${url}/?render=1`});
    async function evaluate(expression){
      const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
      if(result.exceptionDetails)throw new Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);
      return result.result.value;
    }
    let transferId=0;
    async function evaluateLarge(expression){
      // Large PNGs can disconnect the native WebSocket when sent as one CDP
      // response. Serialize in the page, then pull bounded, ordered chunks.
      const key=JSON.stringify(`__sceneLabTransfer${++transferId}`);
      try{
        const length=await evaluate(`(async()=>{const value=JSON.stringify(await (${expression}));if(value===undefined)throw new Error('Expected a JSON-serializable result');globalThis[${key}]=value;return value.length;})()`);
        if(length>128*1024*1024)throw new Error('Browser result exceeds the 128 MiB transfer limit.');
        const chunks=[];
        for(let offset=0;offset<length;offset+=250000)chunks.push(await evaluate(`globalThis[${key}].slice(${offset},${offset+250000})`));
        return JSON.parse(chunks.join(''));
      }finally{await evaluate(`delete globalThis[${key}]`).catch(()=>{});}
    }
    const start=Date.now();
    while(Date.now()-start<25000){
      const ready=await evaluate('({ready:!!window.sceneLab,error:window.sceneLabError})');
      if(ready.error)throw new Error(ready.error);if(ready.ready)return {call,evaluate,evaluateLarge,close};
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    throw new Error('Scene Lab did not become ready within 25 seconds.');
  }catch(error){await close();throw error;}
}
