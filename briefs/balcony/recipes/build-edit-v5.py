#!/usr/bin/env python3
"""Build edit/<ver>.json and edit/mix-<ver>.json for Balcony v5+ (re-blocked coverage) from one segment table,
so picture and sound frame addresses can never disagree.
usage: python3 recipes/build-edit-v5.py VER TABLE_JSON [--no-aside]
TABLE_JSON: {"segments": [{"shot","src","inFrame","frames","gainDb"|null,"decision","fadeInFrames"?,"fadeOutFrames"?,"audioExtraFrames"?}],
             "click": "SHOT", "click2": "SHOT"|null, "luteReturnAfterS07": 24, "s08Lines": [12,84,130,182]}
Clip IDs come from the sha256 in each Veo take's qa decision file; local segments (src "local") are hashed from the file.
Native audio for a take is clips/<src>-v1.native.wav (extracted from the clip master). The mix is rendered with
tools/production/mix.mjs; S08 must already be rendered."""
import argparse, json, hashlib, subprocess
ap = argparse.ArgumentParser(); ap.add_argument('ver'); ap.add_argument('table'); ap.add_argument('--no-aside', action='store_true')
a = ap.parse_args()
W = 'data/workspace/balcony-v1'
T = json.load(open(f'{W}/{a.table}'))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
def clip_id(decision):
    s = json.load(open(f'{W}/{decision}'))['sha256']
    return s if s.startswith('clip_') else 'clip_' + s
segments, tracks, at = [], [], {}
f = 0
for row in T['segments']:
    shot, src, inF, fr = row['shot'], row['src'], row['inFrame'], row['frames']
    at[shot] = f
    seg = {"shotId": shot, "inFrame": inF, "frames": fr, "decisionFile": row['decision']}
    if src == 'local':
        seg.update(source=row['path'], sha256=sha(f"{W}/{row['path']}"))
    else:
        seg["clipId"] = clip_id(row['decision'])
    for k in ('fadeInFrames', 'fadeOutFrames'):
        if k in row: seg[k] = row[k]
    segments.append(seg)
    if row.get('gainDb') is not None:
        tr = {"id": f"{shot}-native", "source": f"clips/{src}-v1.native.wav", "inFrame": inF, "frames": fr + row.get('audioExtraFrames', 0),
              "atFrame": f, "gainDb": row['gainDb'], "highpassHz": 60, "fadeInFrames": row.get('audioFadeIn', 4), "fadeOutFrames": row.get('audioFadeOut', 4)}
        tracks.append(tr)
    f += fr
total = f
for x in T.get('extraTracks', []):
    x = dict(x); x['atFrame'] = at[x.pop('atShot')]; tracks.append(x)
click_at = at[T['click']]; s07 = at['S07B']; s08 = at['S08']
lute_b_at = s07 + T.get('luteReturnAfterS07', 24)
tracks += [
 {"id": "bed", "source": "audio/night-bed-60s.wav", "inFrame": 0, "frames": total, "atFrame": 0, "gainDb": 7.0, "highpassHz": 80, "fadeInFrames": 24, "fadeOutFrames": 60},
 {"id": "lute-a", "source": "audio/lute.wav", "inFrame": 0, "frames": click_at, "atFrame": 0, "gainDb": -17.0, "fadeInFrames": 36, "fadeOutFrames": 2},
 {"id": "click", "source": "audio/earbud-click.loud.wav", "inFrame": 0, "frames": 36, "atFrame": click_at, "gainDb": -4.0},
 {"id": "lute-b-speaker", "source": "audio/lute.speaker.wav", "inFrame": 480, "frames": total - lute_b_at, "atFrame": lute_b_at, "gainDb": -10.0, "fadeInFrames": 48, "fadeOutFrames": 60},
]
if T.get('click2'):
    tracks.append({"id": "click2", "source": "audio/earbud-click.loud.wav", "inFrame": 0, "frames": 36, "atFrame": at[T['click2']], "gainDb": T.get('click2GainDb', -12.0)})
lines = [("phone-1", "audio/phone-1-his-v2.speaker.wav", 63, 9.0), ("phone-2", "audio/phone-2-her.speaker.wav", 42, 5.0),
         ("phone-3", "audio/phone-3-his.speaker.wav", 46, 7.0), ("phone-4", "audio/phone-4-her.speaker.wav", 29, 2.0)]
for (id_, src, fr, g), off in zip(lines, T.get('s08Lines', [12, 84, 130, 182])):
    tracks.append({"id": id_, "source": src, "inFrame": 0, "frames": fr, "atFrame": s08 + off, "gainDb": g})
if not a.no_aside:
    s07_in = next(r['inFrame'] for r in T['segments'] if r['shot'] == 'S07B')
    tracks.append({"id": "aside-1", "source": "audio/aside-1-his.speaker.wav", "inFrame": 0, "frames": 28, "atFrame": s07 + 134 - s07_in, "gainDb": 6.0})
    tracks.append({"id": "aside-2", "source": "audio/aside-2-her.speaker.wav", "inFrame": 0, "frames": 21, "atFrame": s07 + 166 - s07_in, "gainDb": 5.0})
json.dump({"schemaVersion": 1, "fps": 24, "frames": total, "master": {"targetLufs": -16, "truePeakDbtp": -1.5}, "tracks": tracks}, open(f'{W}/edit/mix-{a.ver}.json', 'w'), indent=2)
r = subprocess.run(['node', 'tools/production/mix.mjs', W, f'edit/mix-{a.ver}.json', f'edit/mix-{a.ver}.wav', f'--report=edit/mix-{a.ver}-report.json'], capture_output=True, text=True)
if r.returncode: raise SystemExit(r.stderr[-1500:])
rep = json.load(open(f'{W}/edit/mix-{a.ver}-report.json'))
json.dump({"schemaVersion": 1, "segments": segments, "audio": {"path": f"edit/mix-{a.ver}.wav", "sha256": sha(f'{W}/edit/mix-{a.ver}.wav')}}, open(f'{W}/edit/{a.ver}.json', 'w'), indent=2)
print(json.dumps({"version": a.ver, "frames": total, "seconds": round(total / 24, 2), "segmentsAt": at, "mix": {"gainDb": rep["gainDb"], "after": rep["after"]}}))
