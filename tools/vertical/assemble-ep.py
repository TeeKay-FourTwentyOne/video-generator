#!/usr/bin/env python3
"""assemble-ep — timeline → picture-locked master for vertical-series episodes.

Reads the manifest `timeline[]`, renders every entry to a normalized mezzanine
segment (WxH @ fps, stereo 48k, frame-accurate re-encode), then joins them with
the concat FILTER (never the demuxer — repo ffmpeg doctrine) in one pass.

Timeline entry forms:
  {"clip": "S7", "in": 2.0, "out": 5.5}            excerpt of a shot's gated clip
  {"clip": "S1"}                                   shot's `use` window
  {"type": "still", "source": "path.png", "seconds": 3.0, "zoom": 0.04}
  {"type": "black", "seconds": 1.5}

Audio stems (VO/SFX/music) from manifest `audio[]` entries that have a `file`:
  {"file": "audio/tts/v1.mp3", "t": 0.0, "gain_db": 0}
are laid over the concat'd native audio in a second pass (amix). Entries without
`file` are ignored here (they're generation notes for build day).

Writes back `computed_timeline` (per-segment [start,end]) and, if the last
entry is the end card, `stamps.end_card.window` — which text-pass consumes.

Usage:
  assemble-ep.py --series series/the-lodger --manifest .../episode.json \
      --out final/ep01_picture.mp4 [--stems] [--debug]
"""
import argparse
import json
import os
import subprocess
import sys


def sh(cmd, **kw):
    print("+ " + " ".join(str(c) for c in cmd))
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def seg_filters(w, h, fps):
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},settb=AVTB,setsar=1")


def render_segment(entry, i, manifest, cfg, ws, segdir):
    w, h, fps = cfg["format"]["w"], cfg["format"]["h"], cfg["format"]["fps"]
    out = os.path.join(segdir, f"seg{i:02d}.mp4")
    vf = seg_filters(w, h, fps)
    af = "aformat=sample_rates=48000:channel_layouts=stereo"

    if entry.get("type") == "black":
        d = entry["seconds"]
        sh(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}:d={d}",
            "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={d}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", out], capture_output=True)
        return out, entry["seconds"]

    if entry.get("type") == "still":
        d, zoom = entry["seconds"], entry.get("zoom", 0.04)
        frames = int(d * fps)
        src = entry["source"] if os.path.exists(entry["source"]) else os.path.join(ws, entry["source"])
        # zoompan: slow push-in at `zoom` scale-fraction per second, centered
        zexpr = f"min(1+{zoom}*on/{fps},2)"
        sh(["ffmpeg", "-y", "-loop", "1", "-i", src,
            "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={d}",
            "-vf",
            (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,"
             f"crop={w * 2}:{h * 2},"
             f"zoompan=z='{zexpr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
             f":d={frames}:s={w}x{h}:fps={fps},settb=AVTB,setsar=1"),
            "-t", str(d), "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out], capture_output=True)
        return out, d

    # clip excerpt
    shot = next(s for s in manifest["shots"] if s["id"] == entry["clip"])
    clip = shot["clip"] if os.path.exists(shot.get("clip", "")) else os.path.join(ws, shot["clip"])
    t_in = entry.get("in", shot.get("use", [0, shot["seconds"]])[0])
    t_out = entry.get("out", shot.get("use", [0, shot["seconds"]])[1])
    sh(["ffmpeg", "-y", "-ss", str(t_in), "-to", str(t_out), "-i", clip,
        "-vf", vf, "-af", af,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", out], capture_output=True)
    return out, round(t_out - t_in, 3)


def concat(segs, out, fps):
    n = len(segs)
    cmd = ["ffmpeg", "-y"]
    for s in segs:
        cmd += ["-i", s]
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-r", str(fps), out]
    sh(cmd, capture_output=True)


def mix_stems(base, stems, out):
    """Overlay audio stems (delayed, gained) onto the base video's audio."""
    cmd = ["ffmpeg", "-y", "-i", base]
    for st in stems:
        cmd += ["-i", st["file"]]
    parts, labels = [], []
    for i, st in enumerate(stems, start=1):
        ms = int(st.get("t", 0) * 1000)
        gain = st.get("gain_db", 0)
        parts.append(f"[{i}:a]adelay={ms}|{ms},volume={gain}dB[st{i}]")
        labels.append(f"[st{i}]")
    parts.append(f"[0:a]{''.join(labels)}amix=inputs={len(stems) + 1}:"
                 f"duration=first:normalize=0[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-ac", "2", out]
    sh(cmd, capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True, help="output path relative to workspace")
    ap.add_argument("--stems", action="store_true", help="mix manifest audio[] stems over the cut")
    ap.add_argument("--debug", action="store_true", help="also write add-timestamp debug copy")
    args = ap.parse_args()

    with open(os.path.join(args.series, "series-config.json")) as f:
        cfg = json.load(f)
    with open(args.manifest) as f:
        manifest = json.load(f)
    ws = os.path.dirname(os.path.abspath(args.manifest))
    segdir = os.path.join(ws, "scratch", "segments")
    os.makedirs(segdir, exist_ok=True)

    segs, t, computed = [], 0.0, []
    for i, entry in enumerate(manifest["timeline"]):
        seg, dur = render_segment(entry, i, manifest, cfg, ws, segdir)
        segs.append(seg)
        computed.append({"entry": entry.get("clip") or entry.get("type"),
                         "start": round(t, 3), "end": round(t + dur, 3)})
        t += dur
    out = args.out if os.path.isabs(args.out) else os.path.join(ws, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    concat(segs, out, cfg["format"]["fps"])

    manifest["computed_timeline"] = computed
    last = computed[-1]
    if manifest["timeline"][-1].get("type") == "black" and manifest.get("stamps", {}).get("end_card"):
        manifest["stamps"]["end_card"]["window"] = [last["start"], last["end"]]
    with open(args.manifest + ".tmp", "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(args.manifest + ".tmp", args.manifest)

    print(f"picture lock: {out}  ({t:.2f}s, {len(segs)} segments)")

    stems = [dict(st, file=st["file"] if os.path.isabs(st["file"]) else
                  os.path.join(os.getcwd(), st["file"]))
             for st in manifest.get("audio", []) if st.get("file")]
    if args.stems and stems:
        mixed = out.replace(".mp4", "_mix.mp4")
        mix_stems(out, stems, mixed)
        print(f"stem mix: {mixed}")
        out = mixed
    if args.debug:
        sh(["python3", "tools/add-timestamp.py", out], capture_output=True)
        print(f"debug copy: {out.replace('.mp4', '_debug.mp4')}")


if __name__ == "__main__":
    sys.exit(main())
