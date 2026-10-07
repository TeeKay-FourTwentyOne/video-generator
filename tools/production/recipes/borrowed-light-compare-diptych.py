#!/usr/bin/env python3
"""Borrowed Light comparison: 16:9 diptych (Astra left, Claude right) with a text spine.

The text/base layer is rendered locally with PIL and streamed raw to FFmpeg, which
scales the two portrait films into their panels, pads them in time and overlays them.
Usage:
  python3 recipes/build.py cards.json out.mp4 --left ASTRA.mp4 --right CLAUDE.mp4 --audio mix.wav
         [--scale 1.0] [--crf 17] [--preset medium]
All geometry and font sizes in cards.json are stated at 3840x2160; --scale 0.5 renders a
1920x1080 proof from the native 1080x1920 films. Elements: start/end/fade_in/fade_out in seconds.
layout.holds = [{film_t, duration}]: both films freeze on the frame at film_t for duration seconds
(frame-exact: trim/loop/concat), so cards can sit over a paused picture. Element times are video seconds.
"""
import argparse, json, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    'serif': ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 0),
    'serif-italic': ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 2),
    'serif-semibold': ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 4),
    'sans': ('/System/Library/Fonts/Avenir Next.ttc', 7),
    'sans-medium': ('/System/Library/Fonts/Avenir Next.ttc', 5),
    'sans-demi': ('/System/Library/Fonts/Avenir Next.ttc', 2),
}
COLORS = {'amber': (232, 184, 116), 'ink': (232, 228, 220), 'grey': (150, 150, 146),
          'dim': (105, 105, 101), 'black': (0, 0, 0)}
_fc = {}

def font(name, size):
    key = (name, size)
    if key not in _fc:
        path, idx = FONTS[name]; _fc[key] = ImageFont.truetype(path, max(1, int(round(size))), index=idx)
    return _fc[key]

def wrap(draw, text, f, width):
    lines = []
    for para in text.split('\n'):
        if not para.strip():
            lines.append(''); continue
        cur = ''
        for w in para.split():
            t = (cur + ' ' + w).strip()
            if draw.textlength(t, font=f) <= width: cur = t
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def tracked_width(draw, text, f, track):
    return sum(draw.textlength(c, font=f) for c in text) + track * max(0, len(text) - 1)

def draw_line(draw, text, x, y, f, fill, track=0, align='left', width=0):
    tw = tracked_width(draw, text, f, track)
    if align == 'center': x = x + (width - tw) / 2
    elif align == 'right': x = x + width - tw
    if track == 0:
        draw.text((x, y), text, font=f, fill=fill); return
    for c in text:
        draw.text((x, y), c, font=f, fill=fill); x += draw.textlength(c, font=f) + track

class Renderer:
    def __init__(self, cfg, scale):
        self.s = scale
        self.W = int(round(cfg['layout']['canvas'][0] * scale)); self.H = int(round(cfg['layout']['canvas'][1] * scale))
    def px(self, v): return v * self.s

    def render(self, el):
        img = Image.new('RGB', (self.W, self.H), (0, 0, 0)); d = ImageDraw.Draw(img)
        if el['type'] == 'block': self._block(d, el)
        elif el['type'] == 'table': self._table(d, el)
        else: raise SystemExit('unknown element type ' + el['type'])
        return np.asarray(img, dtype=np.uint8)

    def _layout_parts(self, d, parts, width):
        """Returns [(part, font, lines, line_h)] and the total height (canvas px)."""
        out = []; total = 0
        for p in parts:
            f = font(p.get('font', 'serif'), self.px(p.get('size', 50)))
            text = p['text'].upper() if p.get('upper') else p['text']
            track = self.px(p.get('track', 0))
            lh = self.px(p.get('leading', p.get('size', 50) * 1.35))
            if track:
                lines = [ln for ln in text.split('\n')]
            else:
                lines = wrap(d, text, f, width)
            h = 0
            for ln in lines: h += lh * (0.5 if ln == '' else 1.0)
            total += h + self.px(p.get('gap', 0))
            out.append((p, f, lines, lh, track))
        return out, total

    def _block(self, d, el):
        x = self.px(el['x']); width = self.px(el['width'])
        parts, total = self._layout_parts(d, el['parts'], width)
        y = self.px(el['y']) - (total / 2 if el.get('anchor', 'center') == 'center' else 0)
        for p, f, lines, lh, track in parts:
            fill = COLORS[p.get('color', 'ink')]; align = p.get('align', el.get('align', 'left'))
            for ln in lines:
                if ln == '': y += lh * 0.5; continue
                draw_line(d, ln, x, y, f, fill, track=track, align=align, width=width); y += lh
            y += self.px(p.get('gap', 0))

    def _table(self, d, el):
        cols = el['cols']; rows = el['rows']; lead = self.px(el.get('leading', 78))
        title_f = font('sans-demi', self.px(el.get('title_size', 38))); head_f = font('sans-demi', self.px(el.get('head_size', 36)))
        lab_f = font('serif', self.px(el.get('label_size', 46))); val_f = font('sans', self.px(el.get('value_size', 44)))
        foot_f = font('sans', self.px(el.get('foot_size', 32)))
        n = len(rows); total = lead * (n + 1) + self.px(110) + (self.px(90) if el.get('foot') else 0)
        y = self.px(el['y']) - total / 2
        x0 = self.px(cols[0]['x']); xe = self.px(cols[-1]['x'] + cols[-1]['width'])
        draw_line(d, el['title'], x0, y, title_f, COLORS['amber'], track=self.px(6), align='center', width=xe - x0); y += self.px(110)
        for ci, c in enumerate(cols):
            h = el['header'][ci]
            if h: draw_line(d, h, self.px(c['x']), y, head_f, COLORS['amber'], track=self.px(4), align=c.get('align', 'left'), width=self.px(c['width']))
        y += lead
        for r in rows:
            for ci, c in enumerate(cols):
                f = lab_f if ci == 0 else val_f; fill = COLORS['grey'] if ci == 0 else COLORS['ink']
                draw_line(d, r[ci], self.px(c['x']), y, f, fill, align=c.get('align', 'left'), width=self.px(c['width']))
            y += lead
        if el.get('foot'):
            y += self.px(30)
            draw_line(d, el['foot'], x0, y, foot_f, COLORS['dim'], align='center', width=xe - x0)

def alpha(el, t):
    s, e = el['start'], el['end']
    if t < s or t >= e: return 0.0
    fi = el.get('fade_in', 0.4); fo = el.get('fade_out', 0.4)
    a = 1.0
    if fi > 0: a = min(a, (t - s) / fi)
    if fo > 0: a = min(a, (e - t) / fo)
    a = max(0.0, min(1.0, a))
    return a * a * (3 - 2 * a)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cards'); ap.add_argument('out')
    ap.add_argument('--left', required=True); ap.add_argument('--right', required=True); ap.add_argument('--audio', required=True)
    ap.add_argument('--scale', type=float, default=1.0); ap.add_argument('--crf', default='17'); ap.add_argument('--preset', default='medium')
    ap.add_argument('--frames', type=int, default=0, help='render only the first N frames (proofing)')
    a = ap.parse_args()
    cfg = json.load(open(a.cards)); lay = cfg['layout']; fps = lay['fps']; dur = lay['duration']
    R = Renderer(cfg, a.scale); W, H = R.W, R.H
    N = int(round(dur * fps)) if not a.frames else a.frames
    layers = {el['id']: R.render(el) for el in cfg['elements']}
    p = lay['panel']; s = a.scale
    def px(v): return int(round(v * s))
    pw, ph = px(p['w']), px(p['h'])
    fs = lay['film_start']
    lenL = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.left]).strip())
    lenR = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.right]).strip())
    holds = sorted(lay.get('holds', []), key=lambda h: h['film_t'])
    hold_total = sum(h['duration'] for h in holds)
    padL = max(0.0, dur - fs - lenL - hold_total); padR = max(0.0, dur - fs - lenR - hold_total)
    def film_chain(idx, tag):
        """scale, then freeze-frame holds via frame-exact trim/loop/concat."""
        if not holds:
            return f"[{idx}:v]scale={pw}:{ph}:flags=lanczos[{tag}s];", f"[{tag}s]"
        n = len(holds); M = 2 * n + 1
        parts = [f"[{idx}:v]scale={pw}:{ph}:flags=lanczos,split={M}" + ''.join(f"[{tag}{i}]" for i in range(M)) + ";"]
        labels = []; prev_f = 0
        for i, h in enumerate(holds):
            F = int(round(h['film_t'] * fps)); N = int(round(h['duration'] * fps))
            parts.append(f"[{tag}{2*i}]trim=start_frame={prev_f}:end_frame={F},setpts=PTS-STARTPTS[{tag}a{i}];")
            parts.append(f"[{tag}{2*i+1}]trim=start_frame={F}:end_frame={F+1},setpts=PTS-STARTPTS,loop=loop={N-1}:size=1:start=0,setpts=N/({fps}*TB)[{tag}h{i}];")
            labels += [f"[{tag}a{i}]", f"[{tag}h{i}]"]; prev_f = F
        parts.append(f"[{tag}{M-1}]trim=start_frame={prev_f},setpts=PTS-STARTPTS[{tag}z];"); labels.append(f"[{tag}z]")
        parts.append(''.join(labels) + f"concat=n={M}:v=1:a=0[{tag}s];")
        return ''.join(parts), f"[{tag}s]"
    cL, lL = film_chain(1, 'L'); cR, lR = film_chain(2, 'R')
    fc = (f"[0:v]scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[base];" + cL + cR +
          f"{lL}tpad=start_duration={fs}:stop_duration={padL:.4f}:color=black[L];"
          f"{lR}tpad=start_duration={fs}:stop_duration={padR:.4f}:color=black[R];"
          f"[base][L]overlay={px(p['left_x'])}:{px(p['y'])}:enable='between(t,{fs},{fs+lenL+hold_total:.4f})'[b1];"
          f"[b1][R]overlay={px(p['right_x'])}:{px(p['y'])}:enable='between(t,{fs},{fs+lenR+hold_total:.4f})'[v]")
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', 'pipe:0',
           '-i', a.left, '-i', a.right, '-i', a.audio, '-filter_complex', fc, '-map', '[v]', '-map', '3:a:0',
           '-c:v', 'libx264', '-preset', a.preset, '-crf', a.crf, '-pix_fmt', 'yuv420p',
           '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-r', str(fps),
           '-c:a', 'aac', '-b:a', '256k', '-frames:v', str(N), '-movflags', '+faststart', a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev_key = None; prev = None; t0 = time.time()
    for i in range(N):
        t = i / fps
        vis = tuple((el['id'], round(alpha(el, t), 3)) for el in cfg['elements'] if alpha(el, t) > 0)
        if vis != prev_key:
            acc = np.zeros((H, W, 3), np.uint8)
            for eid, av in vis:
                L = layers[eid]
                if av >= 0.999: np.maximum(acc, L, out=acc)
                else:
                    k = int(av * 256); np.maximum(acc, ((L.astype(np.uint16) * k) >> 8).astype(np.uint8), out=acc)
            prev = acc.tobytes(); prev_key = vis
        proc.stdin.write(prev)
        if i % 240 == 0: print(f'frame {i}/{N} t={t:.2f}s elapsed={time.time()-t0:.0f}s', file=sys.stderr)
    proc.stdin.close(); rc = proc.wait()
    print('ffmpeg exit', rc, a.out, file=sys.stderr)
    if rc == 0:
        got = int(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', a.out]).strip())
        print(f'frames written {got} expected {N}', file=sys.stderr)
        if got != N: sys.exit(3)
    sys.exit(rc)

if __name__ == '__main__': main()
