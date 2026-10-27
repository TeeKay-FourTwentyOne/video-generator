#!/usr/bin/env python3
"""Build a project's collaboration status page from briefs/<project-id>/status.json.

Reads the Git-bound status source, validates it (stable IDs, known statuses, no
money text), inlines small thumbnails of the anchors or local renders it names, embeds
the current draft's player when its review copy has been published as an
artifact asset (recorded in the ignored <workspace>/status/assets.json),
and writes a self-contained HTML page under the ignored workspace. No media is
written, no provider is called. The page is a summary authored by the agent; it
never infers progress from files appearing on disk.

    python3 tools/production/status-page.py PROJECT_ID [--workspace PATH] [--out PATH] [--check] [--no-images]
"""
import argparse
import base64
import io
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).with_suffix('.html')
MONEY = re.compile(r'(\$\s?\d|\d\s?(?:USD|usd|dollars?)\b|\bUSD\s?\d|€\s?\d|£\s?\d)')
TONES = ('muted', 'active', 'attention', 'good', 'bad')
DECISION_TONE = {'open': 'attention', 'decided': 'good'}
THUMB_WIDTH = 360
VIDEO = ('.mp4', '.mov', '.webm', '.mkv')


def fail(message):
    raise SystemExit(f'status-page: {message}')


def esc(text):
    import html
    return html.escape(str(text), quote=True)


def walk_strings(value, path='$'):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, f'{path}.{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, f'{path}[{index}]')


def portable(relative):
    path = Path(relative)
    return not path.is_absolute() and '..' not in path.parts and relative.strip() != ''


def validate(data, project_id):
    if data.get('schemaVersion') != 1:
        fail('schemaVersion must be 1')
    if data.get('projectId') != project_id:
        fail('projectId does not match the brief folder')
    for key in ('title', 'updated', 'logline', 'overall', 'next', 'statuses', 'scenes'):
        if key not in data:
            fail(f'missing top-level field: {key}')
    date.fromisoformat(data['updated'])
    statuses = data['statuses']
    if not isinstance(statuses, dict) or not statuses:
        fail('statuses must be a non-empty map')
    for key, status in statuses.items():
        if not re.fullmatch(r'[a-z][a-z0-9-]*', key):
            fail(f'status key must be lowercase: {key}')
        if status.get('tone') not in TONES or not status.get('label'):
            fail(f'status {key} needs a label and a tone from {TONES}')
    scene_ids = [scene.get('id') for scene in data['scenes']]
    if len(set(scene_ids)) != len(scene_ids):
        fail('duplicate scene ids')
    for scene in data['scenes']:
        for key in ('id', 'number', 'title', 'status', 'summary', 'segments'):
            if key not in scene:
                fail(f'scene {scene.get("id")} is missing {key}')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', scene['id']):
            fail(f'scene id must be lowercase letters, digits and hyphens: {scene["id"]}')
        if scene['status'] not in statuses:
            fail(f'unknown status {scene["status"]} on scene {scene["id"]}')
        segment_ids = [segment.get('id') for segment in scene['segments']]
        if len(set(segment_ids)) != len(segment_ids):
            fail(f'duplicate segment ids in scene {scene["id"]}')
        for segment in scene['segments']:
            for key in ('id', 'title', 'status'):
                if key not in segment:
                    fail(f'segment in scene {scene["id"]} is missing {key}')
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', segment['id']):
                fail(f'segment id must be lowercase letters, digits and hyphens: {segment["id"]}')
            if segment['status'] not in statuses:
                fail(f'unknown status {segment["status"]} on segment {scene["id"]}/{segment["id"]}')
    for decision in data.get('decisions', []):
        for key in ('id', 'title', 'status', 'detail'):
            if key not in decision:
                fail(f'decision is missing {key}')
        if decision['status'] not in DECISION_TONE:
            fail(f'decision {decision["id"]} status must be open or decided')
    for entry in data.get('log', []):
        date.fromisoformat(entry['date'])
        if not entry.get('text'):
            fail('log entries need text')
    versions = [draft.get('version') for draft in data.get('drafts', [])]
    if len(set(versions)) != len(versions):
        fail('duplicate draft versions')
    for index, draft in enumerate(data.get('drafts', [])):
        validate_draft(draft, index)
    for path, text in walk_strings(data):
        if MONEY.search(text):
            fail(f'money text at {path}; prices and budgets stay in the ignored workspace')
        if path.endswith('.image') and not portable(text):
            fail(f'image path must be workspace-relative: {text}')


def validate_draft(draft, index):
    """A draft is a cut the director can watch: a version, its film and an integer-frame shot timeline."""
    where = f'drafts[{index}]'
    for key in ('version', 'date', 'film', 'fps', 'frames', 'segments'):
        if key not in draft:
            fail(f'{where} is missing {key}')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', str(draft['version'])):
        fail(f'{where}.version must be a short lowercase tag such as v1')
    date.fromisoformat(draft['date'])
    if not portable(draft['film']):
        fail(f'{where}.film must be workspace-relative')
    if draft.get('poster') and not portable(draft['poster']):
        fail(f'{where}.poster must be workspace-relative')
    fps, frames = draft['fps'], draft['frames']
    if not (isinstance(fps, int) and fps > 0 and isinstance(frames, int) and frames > 0):
        fail(f'{where} needs positive integer fps and frames')
    poster_frame = draft.get('posterFrame')
    if poster_frame is not None and not (isinstance(poster_frame, int) and 0 <= poster_frame < frames):
        fail(f'{where}.posterFrame must be a frame index inside the draft')
    position = 0
    labels = set()
    for segment in draft['segments']:
        for key in ('label', 'shot', 'frame', 'frames'):
            if key not in segment:
                fail(f'{where} segment is missing {key}')
        if segment['label'] in labels:
            fail(f'{where} repeats the segment label {segment["label"]}')
        labels.add(segment['label'])
        if segment['frame'] != position or not isinstance(segment['frames'], int) or segment['frames'] <= 0:
            fail(f'{where} segment {segment["label"]} must start at frame {position} with a positive length')
        source_frame = segment.get('sourceFrame', 0)
        if not isinstance(source_frame, int) or source_frame < 0:
            fail(f'{where} segment {segment["label"]} sourceFrame must be a non-negative integer')
        if segment.get('source') and not portable(segment['source']):
            fail(f'{where} segment {segment["label"]} source must be workspace-relative')
        position += segment['frames']
    if position != frames:
        fail(f'{where} segments cover {position} frames, not {frames}')


def frame_at(path, seconds=None):
    """One PNG frame of a video: the middle frame by default, else the frame at `seconds`."""
    if seconds is None:
        probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                'stream=duration', '-of', 'json', str(path)], capture_output=True, text=True, check=True)
        seconds = (float(json.loads(probe.stdout)['streams'][0].get('duration') or 0) or 0.0) / 2
    out = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{seconds:.3f}', '-i', str(path), '-frames:v', '1',
                          '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True, check=True)
    return out.stdout


def thumbnail(workspace, relative, width=THUMB_WIDTH, seconds=None, quality=72):
    """Return (data URI, width, height) for an image or one frame of a video, or None when absent."""
    path = workspace / relative
    if not path.is_file():
        return None
    from PIL import Image
    if path.suffix.lower() in VIDEO:
        image = Image.open(io.BytesIO(frame_at(path, seconds)))
    else:
        image = Image.open(path)
    image = image.convert('RGB')
    source_width, source_height = image.size
    if source_width > width:
        image = image.resize((width, max(1, round(source_height * width / source_width))), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, 'JPEG', quality=quality, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii'), image.size[0], image.size[1]


def published_asset(workspace, film):
    """The artifact asset that carries this film's review copy, from the ignored status/assets.json, or None."""
    index = workspace / 'status' / 'assets.json'
    if not index.is_file():
        return None
    entry = json.loads(index.read_text()).get(film)
    return entry if isinstance(entry, dict) and entry.get('url') else None


PLAYER_SCRIPT = r'''<script>
(() => {
  const fps = __FPS__, total = __FRAMES__, segs = __SEGMENTS__;
  const root = document.getElementById('draft'), v = document.getElementById('draft-video');
  if (!root || !v) return;
  const timeEl = document.getElementById('tc-time'), frameEl = document.getElementById('tc-frame'), srcEl = document.getElementById('tc-src');
  const copyButton = document.getElementById('tc-copy');
  const rows = Array.from(root.querySelectorAll('tr[data-seek]'));
  const fmt = f => (f / fps).toFixed(3);
  const clamp = f => Math.min(total - 1, Math.max(0, f));
  const fromTime = t => clamp(Math.floor(t * fps + 1e-4));
  const segAt = f => { let s = segs[0]; for (const x of segs) { if (x.frame <= f) s = x; else break; } return s; };
  let frame = -1, seg = segs[0], sourceFrame = 0;
  function show(f) {
    if (f === frame) return;
    frame = f; seg = segAt(f); sourceFrame = seg.sourceFrame + (f - seg.frame);
    timeEl.textContent = fmt(f);
    frameEl.textContent = 'frame ' + f;
    srcEl.textContent = seg.label + ' · src ' + fmt(sourceFrame) + ' s · frame ' + sourceFrame;
    rows.forEach(r => r.classList.toggle('now', Number(r.dataset.seek) === seg.frame));
  }
  function seek(f) { f = clamp(f); v.pause(); v.currentTime = (f + 0.5) / fps; show(f); }
  const sync = () => show(fromTime(v.currentTime));
  if ('requestVideoFrameCallback' in HTMLVideoElement.prototype) {
    const onFrame = (now, meta) => { show(fromTime(meta.mediaTime)); v.requestVideoFrameCallback(onFrame); };
    v.requestVideoFrameCallback(onFrame);
  } else {
    const tick = () => { sync(); if (!v.paused && !v.ended) requestAnimationFrame(tick); };
    v.addEventListener('play', tick);
  }
  ['loadedmetadata', 'seeked', 'pause', 'ended'].forEach(name => v.addEventListener(name, sync));
  show(0);
  document.addEventListener('click', e => {
    const target = e.target.closest('[data-seek], [data-step]');
    if (!target) return;
    if (target.dataset.step) { seek(frame + Number(target.dataset.step)); return; }
    if (target.tagName === 'A') { e.preventDefault(); root.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    seek(Number(target.dataset.seek));
  });
  document.addEventListener('keydown', e => {
    if (!root.contains(document.activeElement) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === ',') { e.preventDefault(); seek(frame - 1); }
    else if (e.key === '.') { e.preventDefault(); seek(frame + 1); }
  });
  if (copyButton) copyButton.addEventListener('click', () => {
    const text = 'edit ' + fmt(frame) + ' (f' + frame + ') · ' + seg.label + ' src ' + fmt(sourceFrame) + ' (f' + sourceFrame + ')';
    const done = ok => { copyButton.textContent = ok ? 'Copied' : text; setTimeout(() => { copyButton.textContent = 'Copy timestamp'; }, 1600); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(() => done(true), () => done(false));
    else done(false);
  });
})();
</script>'''


def draft_section(draft, earlier, asset, poster_uri):
    fps, frames = draft['fps'], draft['frames']
    t = lambda f: f'{f / fps:.3f}'
    parts = ['<section class="draft" id="draft">', '<div class="draft-head"><p class="eyebrow">Current draft</p>',
             f'<h2>{esc(draft["version"])} · {esc(draft.get("title", "Draft"))}</h2>']
    meta = f'{esc(draft["date"])} · {t(frames)} s · {frames} frames at {fps} fps'
    if draft.get('width') and draft.get('height'):
        meta += f' · {draft["width"]} × {draft["height"]}'
    parts.append(f'<p class="draft-meta">{meta}</p></div>')
    if asset:
        size = f' width="{asset["width"]}" height="{asset["height"]}"' if asset.get('width') and asset.get('height') else ''
        poster = f' poster="{poster_uri}"' if poster_uri else ''
        parts.append('<div class="player">')
        parts.append(f'<video id="draft-video" controls playsinline preload="metadata" src="{esc(asset["url"])}"{size}{poster}></video>')
        parts.append('<div class="readout">'
                     '<div class="tc"><span id="tc-time">0.000</span><span class="tc-unit">s</span><span class="tc-frame" id="tc-frame">frame 0</span></div>'
                     '<div class="tc-src" id="tc-src"></div>'
                     '<div class="controls"><button type="button" data-step="-1">−1 frame</button><button type="button" data-step="1">+1 frame</button>'
                     '<button type="button" id="tc-copy">Copy timestamp</button></div>'
                     '<p class="hint">Edit time in seconds to the millisecond, with the frame number; src is the frame inside that segment’s source. The keys , and . step one frame while the player has focus. Click a shot below, or a time beside a beat, to jump there.</p>'
                     '</div></div>')
    else:
        parts.append(f'<p class="player-pending">The draft video is not on this page yet; the review film is <code>{esc(draft["film"])}</code> in the workspace.</p>')
    if draft.get('note'):
        parts.append(f'<p class="detail">{esc(draft["note"])}</p>')
    parts.append('<div class="timeline-wrap"><table class="timeline"><thead><tr><th>Shot</th><th class="num">In</th><th class="num">Out</th>'
                 '<th class="num">Length</th><th class="num">Src in</th><th>Source</th></tr></thead><tbody>')
    for segment in draft['segments']:
        start, length = segment['frame'], segment['frames']
        source_frame = segment.get('sourceFrame', 0)
        source = segment.get('source') or f'{segment["shot"]} take'
        parts.append(f'<tr data-seek="{start}"><td><button type="button" data-seek="{start}">{esc(segment["label"])}</button></td>'
                     f'<td class="num">{t(start)}</td><td class="num">{t(start + length)}</td><td class="num">{t(length)}</td>'
                     f'<td class="num">{t(source_frame)}</td><td class="src">{esc(source)}</td></tr>')
    parts.append('</tbody></table></div>')
    if earlier:
        parts.append('<p class="fine">Earlier drafts: ' + '; '.join(f'{esc(d["version"])} ({esc(d["date"])})' for d in earlier) + '.</p>')
    if asset:
        segments = json.dumps([{'label': s['label'], 'frame': s['frame'], 'sourceFrame': s.get('sourceFrame', 0)} for s in draft['segments']])
        parts.append(PLAYER_SCRIPT.replace('__FPS__', str(fps)).replace('__FRAMES__', str(frames)).replace('__SEGMENTS__', segments))
    parts.append('</section>')
    return '\n'.join(parts)


def shot_code(segment):
    match = re.match(r'([A-Z]{1,3}\d{1,3}[a-z]?)\b', segment['title'])
    return match.group(1) if match else segment['id']


def chip(statuses, key):
    status = statuses[key]
    return (f'<span class="chip tone-{status["tone"]}" title="{esc(status.get("description", ""))}">'
            f'{esc(status["label"])}</span>')


def render(data, workspace, with_images):
    statuses = data['statuses']
    counts = {}
    images_used = 0
    parts = []
    parts.append('<header class="masthead">')
    parts.append(f'<p class="eyebrow">Production status</p>')
    parts.append(f'<h1>{esc(data["title"])}</h1>')
    if data.get('format'):
        parts.append(f'<p class="format">{esc(data["format"])}</p>')
    phase = data.get('phase')
    parts.append('<div class="stateline">')
    if phase:
        parts.append(f'<span class="phase">{esc(phase)}</span>')
    parts.append(f'<span class="updated">Updated {esc(data["updated"])}</span>')
    parts.append('</div></header>')

    parts.append('<section class="summary" id="summary">')
    parts.append(f'<p class="logline">{esc(data["logline"])}</p>')
    parts.append(f'<p>{esc(data["overall"])}</p>')
    parts.append(f'<p class="next"><strong>Next:</strong> {esc(data["next"])}</p>')
    parts.append('</section>')

    drafts = data.get('drafts', [])
    current = drafts[-1] if drafts else None
    marks = {}
    if current:
        asset = published_asset(workspace, current['film'])
        poster_uri = None
        if asset and with_images:
            poster_seconds = None if current.get('posterFrame') is None else current['posterFrame'] / current['fps']
            poster = thumbnail(workspace, current.get('poster') or current['film'], width=720, seconds=poster_seconds, quality=80)
            poster_uri = poster[0] if poster else None
        parts.append(draft_section(current, drafts[:-1], asset, poster_uri))
        if asset:
            for segment in current['segments']:
                marks.setdefault(segment['shot'], []).append(segment['frame'])

    parts.append('<nav class="toc" aria-label="Scenes"><ul>')
    for scene in data['scenes']:
        parts.append(f'<li><a href="#scene-{esc(scene["id"])}"><span class="num">{esc(scene["number"])}</span> {esc(scene["title"])}</a></li>')
    parts.append('</ul></nav>')

    for scene in data['scenes']:
        counts[scene['status']] = counts.get(scene['status'], 0) + 1
        parts.append(f'<section class="scene" id="scene-{esc(scene["id"])}">')
        parts.append('<div class="scene-head">')
        parts.append(f'<div class="era">{esc(scene["number"])}</div>')
        parts.append(f'<div class="scene-title"><h2>{esc(scene["title"])}</h2>{chip(statuses, scene["status"])}</div>')
        parts.append('</div>')
        parts.append(f'<p class="scene-summary">{esc(scene["summary"])}</p>')
        strip = []
        seen = set()
        candidates = [(scene.get('image'), 'scene')] + [(segment.get('image'), shot_code(segment)) for segment in scene['segments']]
        for relative, caption in candidates:
            if not relative or relative in seen:
                continue
            seen.add(relative)
            thumb = thumbnail(workspace, relative) if with_images else None
            label = esc(caption if caption != 'scene' else Path(relative).stem)
            if thumb:
                images_used += 1
                uri, width, height = thumb
                strip.append(f'<figure><img src="{uri}" width="{width}" height="{height}" alt="{label}" loading="lazy">'
                             f'<figcaption>{label}</figcaption></figure>')
            else:
                strip.append(f'<figure class="pending"><div class="box"><span>pending</span></div><figcaption>{label}</figcaption></figure>')
        if strip:
            parts.append('<div class="strip">' + ''.join(strip) + '</div>')
        parts.append('<ul class="beats">')
        for segment in scene['segments']:
            counts[segment['status']] = counts.get(segment['status'], 0) + 1
            parts.append(f'<li id="seg-{esc(scene["id"])}-{esc(segment["id"])}">')
            times = ''
            if marks.get(shot_code(segment)):
                links = ''.join(f'<a href="#draft" data-seek="{frame}">{frame / current["fps"]:.3f}</a>' for frame in marks[shot_code(segment)])
                times = f'<span class="times" title="Jump the draft to this beat">{links}</span>'
            parts.append(f'<div class="beat-line"><span class="beat-title">{esc(segment["title"])}</span>{chip(statuses, segment["status"])}{times}</div>')
            if segment.get('detail'):
                parts.append(f'<p class="detail">{esc(segment["detail"])}</p>')
            parts.append('</li>')
        parts.append('</ul>')
        if scene.get('next'):
            parts.append(f'<p class="next"><strong>Next:</strong> {esc(scene["next"])}</p>')
        parts.append('</section>')

    decisions = data.get('decisions', [])
    if decisions:
        parts.append('<section class="decisions" id="decisions"><h2>Decisions for the director</h2><ol>')
        for decision in decisions:
            tone = DECISION_TONE[decision['status']]
            parts.append(f'<li id="decision-{esc(decision["id"])}"><div class="beat-line"><span class="beat-title">{esc(decision["title"])}</span>'
                         f'<span class="chip tone-{tone}">{esc(decision["status"].capitalize())}</span></div>'
                         f'<p class="detail">{esc(decision["detail"])}</p></li>')
        parts.append('</ol></section>')

    log = data.get('log', [])
    if log:
        parts.append('<section class="log" id="log"><h2>Log</h2><dl>')
        for entry in log:
            parts.append(f'<dt>{esc(entry["date"])}</dt><dd>{esc(entry["text"])}</dd>')
        parts.append('</dl></section>')

    parts.append('<section class="legend" id="legend"><details><summary>Status vocabulary</summary><dl>')
    for key, status in statuses.items():
        parts.append(f'<dt>{chip(statuses, key)}</dt><dd>{esc(status.get("description", ""))}</dd>')
    parts.append('</dl></details></section>')

    parts.append('<footer class="colophon">')
    parts.append('<p>Comment on any line to change it. Every scene, beat and decision has its own anchor link, '
                 'so a comment can point at one precisely. The agent folds comments into the status source and republishes.</p>')
    parts.append(f'<p class="fine">Built from <code>briefs/{esc(data["projectId"])}/status.json</code>. '
                 'Statuses are authored, never inferred from files on disk. No prices live on this page; the ledger is in the workspace.</p>')
    parts.append('</footer>')

    template = TEMPLATE.read_text()
    for marker in ('__TITLE__', '__BODY__'):
        if template.count(marker) != 1:
            fail(f'template must contain {marker} exactly once')
    page = template.replace('__TITLE__', esc(data['title'])).replace('__BODY__', '\n'.join(parts))
    return page, counts, images_used


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('project_id')
    parser.add_argument('--workspace', help='workspace folder (default: the production record workspace, else data/workspace/<id>-v1)')
    parser.add_argument('--out', help='output HTML (default: <workspace>/status/index.html)')
    parser.add_argument('--check', action='store_true', help='verify the output is present and fresh; write nothing')
    parser.add_argument('--no-images', action='store_true', help='render placeholders instead of inlining thumbnails')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.project_id):
        fail('project id must be lowercase letters or digits separated by single hyphens')
    folder = REPO / 'briefs' / args.project_id
    source = folder / 'status.json'
    if not source.is_file():
        fail(f'missing {source.relative_to(REPO)}')
    data = json.loads(source.read_text())
    validate(data, args.project_id)
    record_file = folder / 'production.json'
    workspace = None
    if args.workspace:
        workspace = Path(args.workspace)
    elif record_file.is_file():
        record = json.loads(record_file.read_text())
        if record.get('workspace', {}).get('path'):
            workspace = REPO / record['workspace']['path']
    if workspace is None:
        workspace = REPO / 'data' / 'workspace' / f'{args.project_id}-v1'
    if not workspace.is_absolute():
        workspace = REPO / workspace
    output = Path(args.out) if args.out else workspace / 'status' / 'index.html'
    if not output.is_absolute():
        output = REPO / output
    page, counts, images_used = render(data, workspace, not args.no_images)
    size = len(page.encode('utf-8'))
    if size > 15 * 1024 * 1024:
        fail(f'page is {size} bytes; the artifact limit is 16 MB, reduce or drop images')
    if args.check:
        if not output.is_file() or output.read_text() != page:
            raise SystemExit(f'status-page: {output} is missing or stale; rebuild it')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.tmp')
        temporary.write_text(page)
        temporary.replace(output)
    artifact = output.parent / 'artifact.json'
    published = json.loads(artifact.read_text()).get('url') if artifact.is_file() else None
    print(json.dumps({'out': str(output.relative_to(REPO)) if output.is_relative_to(REPO) else str(output),
                      'verified' if args.check else 'built': True, 'scenes': len(data['scenes']),
                      'segments': sum(len(s['segments']) for s in data['scenes']), 'statuses': counts,
                      'images': images_used, 'bytes': size, 'artifact': published,
                      'draft': data['drafts'][-1]['version'] if data.get('drafts') else None,
                      'draftVideo': bool(data.get('drafts') and published_asset(workspace, data['drafts'][-1]['film']))}, indent=2))


if __name__ == '__main__':
    main()
