#!/usr/bin/env python3
"""Build a self-contained local analysis page around an existing audio copy.

Only Python's standard library is used. No server or network connection needed.
Optional review.json contains provisional sections, observations and questions.
"""
import argparse
import html
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path)
    args = ap.parse_args()
    root = args.directory
    analysis = json.loads((root / "analysis.json").read_text())
    plot = json.loads((root / "plot-data.json").read_text())
    review = json.loads((root / "review.json").read_text()) if (root / "review.json").exists() else {}
    audio = next(root.glob("source.*")).name
    data = json.dumps({"analysis": analysis, "plot": plot, "review": review}).replace("<", "\\u003c")
    title = html.escape(analysis.get("title", "Song"))
    page = TEMPLATE.replace("{{TITLE}}", title).replace("{{AUDIO}}", html.escape(audio, quote=True)).replace("{{DATA}}", data)
    (root / "index.html").write_text(page)
    print(root / "index.html")


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}} · Music video preparation</title>
<style>
:root{color-scheme:dark;--bg:#131915;--card:#1c251f;--line:#35443a;--ink:#eeeade;--muted:#b1b8a9;--green:#c4de9c;--gold:#e5b982}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:45px 28px 75px}
.eyebrow{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--green)}h1{font:clamp(36px,6vw,62px)/1.1 Georgia,serif;margin:12px 0 16px}h2{font:26px/1.2 Georgia,serif;margin:0 0 18px}p{max-width:850px;margin:12px 0;color:var(--muted)}a{color:var(--green)}.stats{display:flex;gap:35px;flex-wrap:wrap;margin:28px 0}.stat strong{display:block;font:28px Georgia,serif}.stat span{color:var(--muted);font-size:13px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:24px;margin:20px 0}.notice{border-left:3px solid var(--gold);padding-left:16px;font-size:14px}.controls{display:flex;align-items:center;gap:16px;flex-wrap:wrap}audio{width:min(600px,100%)}button{font:inherit;color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:7px;padding:9px 13px;cursor:pointer}button:hover,button:focus-visible{border-color:var(--green);background:#29372c}button[aria-pressed=true]{background:#405337;border-color:var(--green)}#clock{font-variant-numeric:tabular-nums;color:var(--green)}canvas{display:block;width:100%;height:200px;margin-top:20px;cursor:crosshair}input[type=range]{width:100%;accent-color:var(--green)}.micro{font-size:12px;color:var(--muted)}.cuegrid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.cue{text-align:left;display:grid;grid-template-columns:80px 1fr;gap:4px 14px;padding:16px}.cue .time{color:var(--green);font-size:14px}.cue .label{font-weight:600}.cue small{grid-column:2;color:var(--muted);font-size:13px;line-height:1.5}.cue.active{border-color:var(--gold)}.columns{display:grid;grid-template-columns:1fr 1fr;gap:28px}li{margin:9px 0;color:var(--muted)}ul,ol{padding-left:21px}.signal{width:100%;border-radius:6px;background:#fff}summary{cursor:pointer;color:var(--green)}.footer{font-size:12px;color:var(--muted);margin-top:30px}@media(max-width:700px){main{padding:28px 16px}.panel{padding:17px}.cuegrid,.columns{grid-template-columns:1fr}.stats{gap:22px}.cue{grid-template-columns:64px 1fr}}
</style></head><body><main>
<div class="eyebrow">Music video · analysis 01 · local review</div><h1>{{TITLE}}</h1>
<p>A listening map for planning movement, recurring images, and a few larger visual events. All section names below are provisional; choose a passage to cue it, then press play.</p>
<div class="stats"><div class="stat"><strong id="duration"></strong><span>full track</span></div><div class="stat"><strong id="tempo"></strong><span>working pulse · audition the feel</span></div><div class="stat"><strong id="spend">$0 / $10</strong><span>estimated external analysis spend / ceiling</span></div></div>
<p class="notice" id="scope-note">Timing, dynamics, and spectral changes were measured locally. Lyrics, instrumentation, meter, and emotional meaning have not been verified by listening. A recurring texture is evidence for a return, not proof of a chorus.</p>
<section class="panel"><h2>Listen against the structure</h2><div class="controls"><audio id="audio" controls preload="metadata" src="{{AUDIO}}"></audio><button id="loop" aria-pressed="false">Loop selected section</button><span id="clock">0:00.0</span></div>
<canvas id="wave" role="img" aria-label="Measured loudness with provisional section boundaries. Use the seek slider below for keyboard access."></canvas>
<input id="seek" type="range" min="0" step="0.01" value="0" aria-label="Seek within song"><div class="micro">Chart: 0.1-second RMS, displayed from −45 to −8 dBFS. Click to seek. Divisions are approximate planning cues, not approved edit points.</div>
<p id="selected" aria-live="polite"></p><div class="cuegrid" id="cues"></div></section>
<section class="panel" id="lyrics-panel" hidden><h2>Whisper lyric draft</h2><p id="lyrics-note"></p><div id="lyric-lines" class="cuegrid"></div></section>
<section class="panel columns"><div><h2>What the measurements suggest</h2><ul id="observations"></ul></div><div><h2>Decisions for our walkthrough</h2><ol id="questions"></ol></div></section>
<section class="panel"><h2>A production approach to test</h2><p id="approach"></p><p class="micro">The $10 ceiling applies to analysis. No music-video production spending has been authorized by this analysis.</p></section>
<details class="panel"><summary>Inspect the measurements and their limits</summary><p>Repeated spectral shapes can come from accompaniment or mixing as well as repeated musical sections. Strong transitions are prompts for listening; their exact musical downbeats remain unconfirmed.</p><img class="signal" src="signal-map.png" alt="RMS level, bass and transient trends, texture-change candidates, and a timbre similarity matrix"><p><a href="analysis.json">Measurements</a> · <a href="pulse-grid.json">Provisional pulse grid</a> · <a href="onsets.json">Detected attacks</a> · <a href="verification.json">Source-preservation checks</a> · <a href="README.md">Analysis notes</a></p></details>
<div class="footer" id="footer-note">Offline analysis · Source preserved and copied by checksum · No uploads or external APIs · No creative treatment selected</div>
</main><script>
const D={{DATA}}, A=D.analysis, P=D.plot, R=D.review, sections=R.sections||[];
const $=s=>document.querySelector(s), audio=$('#audio'), canvas=$('#wave'), ctx=canvas.getContext('2d');
let selected=0, looping=false;
function time(t,precise=false){const m=Math.floor(t/60),s=t-m*60;return m+':'+(precise?s.toFixed(1):Math.floor(s).toString()).padStart(precise?4:2,'0')}
$('#duration').textContent=time(P.duration,true);$('#tempo').textContent=R.working_tempo_label||'Unconfirmed';$('#seek').max=P.duration;
if(R.analysis_spend_label)$('#spend').textContent=R.analysis_spend_label;
if(R.scope_note)$('#scope-note').textContent=R.scope_note;
if(R.footer_note)$('#footer-note').textContent=R.footer_note;
if(R.lyrics?.length){$('#lyrics-panel').hidden=false;$('#lyrics-note').textContent=R.lyrics_note||'Automatic transcription, not an approved lyric sheet. Click a line to cue it; timing is approximate.';R.lyrics.forEach(s=>{const b=document.createElement('button');b.className='lyric-line cue';const stamp=document.createElement('span');stamp.className='time';stamp.textContent=time(s.start,true);const line=document.createElement('span');line.textContent=s.text;b.append(stamp,line);b.onclick=()=>seek(s.start);$('#lyric-lines').append(b)})}
audio.volume=.65;
for(const [id,items] of [['observations',R.observations],['questions',R.questions]])for(const text of items||[]){const li=document.createElement('li');li.textContent=text;$('#'+id).append(li)}
$('#approach').textContent=R.approach||'Confirm the section map through listening before developing a treatment.';
function select(i,seek=true){selected=i;const s=sections[i];if(seek)audio.currentTime=s.start;$('#selected').textContent=time(s.start)+'–'+time(s.end)+' · '+s.label+' — '+s.note;document.querySelectorAll('#cues .cue').forEach((b,n)=>{b.classList.toggle('active',n===i);b.setAttribute('aria-pressed',String(n===i))});draw()}
sections.forEach((s,i)=>{const b=document.createElement('button');b.className='cue';const ts=document.createElement('span');ts.className='time';ts.textContent=time(s.start);const title=document.createElement('span');title.className='label';title.textContent=s.label;const note=document.createElement('small');note.textContent=s.note;b.append(ts,title,note);b.onclick=()=>select(i);$('#cues').append(b)});
$('#loop').onclick=()=>{looping=!looping;$('#loop').setAttribute('aria-pressed',String(looping));if(looping&&sections[selected]&&(audio.currentTime<sections[selected].start||audio.currentTime>=sections[selected].end))audio.currentTime=sections[selected].start};
function seek(t){t=Math.max(0,Math.min(P.duration,t));const i=sections.findIndex(s=>s.start<=t&&s.end>t);if(i>=0)select(i,false);audio.currentTime=t;draw()}
$('#seek').oninput=e=>seek(Number(e.target.value));canvas.onclick=e=>{const b=canvas.getBoundingClientRect();seek((e.clientX-b.left)/b.width*P.duration)};
function draw(){const box=canvas.getBoundingClientRect(),scale=window.devicePixelRatio||1,w=box.width,h=box.height;canvas.width=w*scale;canvas.height=h*scale;ctx.scale(scale,scale);ctx.clearRect(0,0,w,h);const x=t=>t/P.duration*w,y=db=>h-25-Math.max(0,Math.min(1,(db+45)/37))*(h-40);sections.forEach((s,i)=>{ctx.fillStyle=i===selected?'#405337':'#202b23';ctx.fillRect(x(s.start),0,x(s.end-s.start)-1,h-24);ctx.fillStyle='#b1b8a9';ctx.font='11px system-ui';ctx.fillText(time(s.start),Math.min(w-37,x(s.start)+4),h-6)});ctx.strokeStyle='#c4de9c';ctx.lineWidth=1.25;ctx.beginPath();P.times.forEach((t,i)=>{if(i===0)ctx.moveTo(x(t),y(P.rms_dbfs[i]));else ctx.lineTo(x(t),y(P.rms_dbfs[i]))});ctx.stroke();ctx.strokeStyle='#e5b982';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x(audio.currentTime),0);ctx.lineTo(x(audio.currentTime),h-23);ctx.stroke()}
audio.ontimeupdate=()=>{if(looping&&sections[selected]&&audio.currentTime>=sections[selected].end)audio.currentTime=sections[selected].start;$('#clock').textContent=time(audio.currentTime,true);$('#seek').value=audio.currentTime;draw()};audio.onended=()=>{if(looping&&sections[selected]){audio.currentTime=sections[selected].start;audio.play().catch(()=>{})}};window.addEventListener('resize',draw);if(sections.length)select(0,false);else draw();
</script></body></html>'''


if __name__ == "__main__":
    main()
