#!/usr/bin/env node
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const files=new Set(['index.html','style.css','app.mjs','renderer.mjs','scene.mjs','math.mjs','reference.mjs']);
export async function startServer(port=4317,assets=new Map()) {
  const server=createServer(async(req,res)=>{
    const name=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html';
    if(!['GET','HEAD'].includes(req.method)||(!files.has(name)&&!assets.has(name))){res.writeHead(404);res.end('Not found');return;}
    try{
      const asset=assets.get(name),body=asset?.body??await readFile(new URL(name,import.meta.url));
      res.writeHead(200,{
        'Content-Type':asset?.contentType??(name.endsWith('.html')?'text/html; charset=utf-8':name.endsWith('.css')?'text/css; charset=utf-8':'text/javascript; charset=utf-8'),
        'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
        'Content-Security-Policy':"default-src 'self'; img-src 'self' data: blob:; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
      });res.end(req.method==='HEAD'?undefined:body);
    }catch{res.writeHead(500);res.end('Could not load studio file');}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
  return {server,url:`http://127.0.0.1:${server.address().port}`};
}
if(process.argv[1]&&pathToFileURL(resolve(process.argv[1])).href===import.meta.url){
  const arg=process.argv.slice(2).find(v=>v.startsWith('--port=')),port=arg?Number(arg.slice(7)):4317;
  if(!Number.isInteger(port)||port<0||port>65535)throw new Error('Port must be an integer from 0 to 65535.');
  const {url}=await startServer(port);console.log(`Scene Lab: ${url}\nLocal files only. Press Ctrl+C to stop.`);
}
