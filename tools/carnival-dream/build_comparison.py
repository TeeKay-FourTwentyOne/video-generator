#!/usr/bin/env python3
"""Build a local, same-time comparison player for the three preserved drafts."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
run=ROOT/'data/workspace/carnival-dream'
dest=run/'review';dest.mkdir(exist_ok=True)
drafts=[]
notes=[
    ('Borrowed Light', 'The complete first staging: a paper performer follows a partner made of light. Monochrome rides assemble, fail and dismantle.'),
    ('The Light Answers', 'Reworked steps and reaches, persistent gathered stars, physical piles of ride parts, deeper stage lighting and two brief generated performances.'),
    ('A Deliberate Return', 'A further pass over the entire film, with smoother borrowed color, clearer projected silhouettes, richer paper scenery and more deliberate performance.')
]
for n,(title,note) in enumerate(notes,1):
    d=run/f'draft-v{n}'
    name='carnival-dream-borrowed-light-draft-1080p.mp4' if n==1 else f'carnival-dream-borrowed-light-draft-{n}-1080p.mp4'
    movie=d/'review'/name
    if not movie.exists():raise RuntimeError(f'Draft {n} is not complete')
    qa=json.loads((d/'qa/technical.json').read_text())
    assert qa['status']=='pass'
    budget=json.loads((d/'budget.json').read_text())
    for source,target in [(movie,dest/name),(d/'review/poster.png',dest/f'draft-{n}-poster.png')]:
        if not target.exists():os.link(source,target)
        elif not os.path.samefile(source,target):raise RuntimeError('Preserve an existing different review asset')
    drafts.append({'n':n,'title':title,'note':note,'file':name, 'poster':f'draft-{n}-poster.png','cost':budget.get('external_spend_estimate_usd',0)})
timeline=json.loads((run/'draft-v3/timeline.json').read_text())
chapters=[(0,'Opening'),(9.54,'First light'),(42.34,'First chorus'),(64.8,'Gathering stars'),(95.68,'One · two · three'),(119.26,'Behind the scenery'),(140.64,'The choice'),(145.68,'Final chorus'),(162.8,'Last gesture')]
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Carnival Dream · Three Drafts</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#101116;color:#ebe7de}body{max-width:1180px;margin:0 auto;padding:26px 24px 60px}header{display:flex;align-items:baseline;justify-content:space-between;gap:18px;flex-wrap:wrap}h1{font-size:25px;font-weight:550;margin:0 0 8px}p{line-height:1.5;color:#beb9b0;margin:10px 0}button,a{font:inherit}button{border:1px solid #4b4953;background:#22222c;color:#eee;border-radius:7px;padding:10px 15px;cursor:pointer}button:hover{border-color:#c3a575}button.active{background:#d0af78;color:#161419;border-color:#d0af78}.drafts,.chapters{display:flex;flex-wrap:wrap;gap:9px;margin:18px 0}.chapters button{padding:8px 11px;font-size:13px}video{display:block;width:100%;max-height:72vh;background:#000;border-radius:5px}#note{max-width:850px;min-height:48px}#status{font-variant-numeric:tabular-nums;font-size:13px;color:#b7ad9c}a{color:#d5b77e;text-underline-offset:4px}.links{display:flex;gap:22px;flex-wrap:wrap;margin:24px 0}small{display:block;line-height:1.65;color:#969097}kbd{border:1px solid #514b59;border-radius:3px;padding:1px 5px}h2{font-size:17px;font-weight:500;margin-top:30px}
</style><header><div><h1>Carnival Dream</h1><p>Borrowed Light · three complete drafts</p></div><span id="status"></span></header>
<div class="drafts" id="drafts"></div><video id="film" controls playsinline preload="metadata"></video><p id="note"></p>
<div class="chapters" id="chapters"></div><p>Switch drafts at the same point in the song. Keys <kbd>1</kbd>, <kbd>2</kbd>, <kbd>3</kbd> also switch versions.</p>
<div class="links" id="downloads"></div><small>Native 1920 × 1080 · 16:9 · full 2:50 song · song is the only audio · no 4K upscale.<br>All three exports are preserved. Generation and API estimates are recorded separately against each $30 ceiling; they are not billing invoices.</small>
<script>const drafts=DRAFTS,chapters=CHAPTERS;const film=document.querySelector('#film');let active=3;
function choose(n,seek=null){const t=seek===null?(film.currentTime||0):seek,playing=!film.paused;active=n;const d=drafts[n-1];film.poster=d.poster;film.src=d.file;film.onloadedmetadata=()=>{if(t>0)film.currentTime=Math.min(t,film.duration-.03);if(playing)film.play().catch(()=>{})};document.querySelectorAll('[data-draft]').forEach(b=>{b.classList.toggle('active',+b.dataset.draft===n);b.setAttribute('aria-pressed',+b.dataset.draft===n)});document.querySelector('#note').textContent=d.note;document.querySelector('#status').textContent=`Draft ${n} · ${d.title} · APIs ≈ $${d.cost.toFixed(2)} / $30`;}
drafts.forEach(d=>{let b=document.createElement('button');b.dataset.draft=d.n;b.textContent=`Draft ${d.n}`;b.onclick=()=>choose(d.n);document.querySelector('#drafts').append(b);let a=document.createElement('a');a.href=d.file;a.download='';a.textContent=`Download Draft ${d.n}`;document.querySelector('#downloads').append(a)});
chapters.forEach(([t,label])=>{const b=document.createElement('button');b.textContent=label;b.onclick=()=>{film.currentTime=t;film.scrollIntoView({behavior:'smooth',block:'center'})};document.querySelector('#chapters').append(b)});
document.addEventListener('keydown',e=>{if(['1','2','3'].includes(e.key)&&!['INPUT','TEXTAREA'].includes(e.target.tagName))choose(+e.key)});choose(3,0);
</script></html>'''.replace('DRAFTS',json.dumps(drafts)).replace('CHAPTERS',json.dumps(chapters))
(dest/'index.html').write_text(page)
(dest/'comparison.json').write_text(json.dumps({'drafts':drafts,'duration':timeline['duration'],'frames':timeline['frames'],'chapters':chapters},indent=2)+'\n')
print(dest/'index.html')
