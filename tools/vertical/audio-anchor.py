#!/usr/bin/env python3
"""audio-anchor — src-anchored audio re-timing + stem shaping for vertical episodes.

Encodes the audio-src-anchor doctrine: after gate trims, every audio event is
recomputed from (timeline segment, src offset) against `computed_timeline` —
never from prior edit times.

Anchor forms (on manifest vo[] / audio[] entries):
  {"seg": "S2", "occ": 0, "offset": 0.4}          seg label + occurrence + seconds into segment
  {"seg": "S8", "occ": 0, "src": 2.1}             src timestamp within the SOURCE clip
                                                  (converted via the segment's use/in window)
  captions[]: {"anchor": {"seg": "S8", "src_in": 1.2, "src_out": 4.3}}

Modes:
  --anchors     recompute vo[].t, captions[] t_in/t_out, sfx audio[].t from anchors
  --stems       build shaped stem files (LUFS-staged gains, music fade windows,
                speech ducking baked in) into <ws>/audio/stems/ and write
                audio[] `file`+`t`+`gain_db` entries for assemble-ep --stems
  --mute-base   render a copy of the picture cut with base-audio spans muted
                (his-silence rule) — pass --video/--out with it

Music windows come from audio[] entries with `windows`: [{"in": {...anchor},
"out": {...anchor}, "fade": 1.5, "gain_db": -x}]. Ducking: any stem with
"duck_db" gets that dip under every speech span (VO + dialogue captions).
"""
import argparse
import json
import os
import re
import subprocess
import sys

FPS_EPS = 0.02


def sh(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


# ---------- timeline resolution ----------

def segments(manifest):
    """computed_timeline rows + the matching timeline entries, zipped."""
    ct = manifest.get("computed_timeline")
    if not ct:
        raise SystemExit("no computed_timeline — run assemble-ep first")
    tl = manifest["timeline"]
    if len(ct) != len(tl):
        raise SystemExit("computed_timeline / timeline length mismatch — re-run assemble-ep")
    return list(zip(ct, tl))


def find_seg(manifest, label, occ=0):
    n = 0
    for row, entry in segments(manifest):
        name = entry.get("clip") or entry.get("type")
        if name == label:
            if n == occ:
                return row, entry
            n += 1
    raise SystemExit(f"anchor segment not found: {label} occ={occ}")


def seg_src_in(manifest, entry):
    """The source-clip timestamp at which this segment begins."""
    if "clip" not in entry:
        return 0.0
    shot = next(s for s in manifest["shots"] if s["id"] == entry["clip"])
    return entry.get("in", shot.get("use", [0, shot["seconds"]])[0])


def resolve_anchor(manifest, a):
    """anchor dict -> edit-time seconds."""
    row, entry = find_seg(manifest, a["seg"], a.get("occ", 0))
    if "src" in a:
        t = row["start"] + (a["src"] - seg_src_in(manifest, entry))
    else:
        t = row["start"] + a.get("offset", 0.0)
    return max(0.0, round(t, 3))


# ---------- audio measurement ----------

def duration_of(path):
    p = sh(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
            "-of", "csv=p=0", path])
    return float(p.stdout.strip())


def lufs_of(path):
    p = sh(["ffmpeg", "-i", path, "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    m = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", p.stderr)
    return float(m[-1]) if m else None


def onset_of(path, noise_db=-38):
    """First non-silent moment (s) — for aligning SFX transients to picture."""
    p = sh(["ffmpeg", "-i", path, "-af",
            f"silencedetect=noise={noise_db}dB:d=0.03", "-f", "null", "-"])
    starts = re.findall(r"silence_end:\s*([\d.]+)", p.stderr)
    first_silence = re.search(r"silence_start:\s*([\d.]+)", p.stderr)
    if first_silence and float(first_silence.group(1)) < 0.02 and starts:
        return float(starts[0])
    return 0.0


# ---------- speech spans / ducking ----------

def speech_spans(manifest, pad=0.15):
    spans = []
    for vo in manifest.get("vo", []):
        if vo.get("t") is None:
            continue
        d = vo.get("duration") or (0.8 + 0.055 * len(vo["text"]))
        spans.append((vo["t"] - pad, vo["t"] + d + pad))
    for cap in manifest.get("captions", []):
        # non-italic captions are on-camera dialogue (italic = VO, already covered above)
        if not cap.get("italic"):
            spans.append((cap["t_in"] - pad, cap["t_out"] + pad))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1] + 0.2:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([max(0, s), e])
    return merged


def duck_expr(spans, duck_db):
    """volume= expression dipping duck_db inside spans (eval=frame)."""
    if not spans:
        return None
    cond = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in spans)
    lin = 10 ** (duck_db / 20.0)
    return f"volume='if(gt({cond},0),{lin:.4f},1)':eval=frame"


# ---------- modes ----------

def cmd_anchors(manifest, path):
    for vo in manifest.get("vo", []):
        if vo.get("anchor"):
            vo["t"] = resolve_anchor(manifest, vo["anchor"])
    # collision pass: keep >=0.3s gap between consecutive VO lines
    prev_end = None
    for vo in sorted([v for v in manifest.get("vo", []) if v.get("t") is not None],
                     key=lambda v: v["t"]):
        d = vo.get("duration") or (0.8 + 0.055 * len(vo["text"]))
        if prev_end is not None and vo["t"] < prev_end + 0.3:
            vo["t"] = round(prev_end + 0.3, 3)
        prev_end = vo["t"] + d
    for cap in manifest.get("captions", []):
        a = cap.get("anchor")
        if not a:
            continue
        row, entry = find_seg(manifest, a["seg"], a.get("occ", 0))
        src0 = seg_src_in(manifest, entry)
        cap["t_in"] = round(max(row["start"], row["start"] + a["src_in"] - src0), 3)
        cap["t_out"] = round(min(row["end"], row["start"] + a["src_out"] - src0), 3)
        cap["timing"] = "src-anchored"
    for a in manifest.get("audio", []):
        if a.get("anchor"):
            t = resolve_anchor(manifest, a["anchor"])
            t -= a.get("onset_trim", 0.0)
            a["t"] = max(0.0, round(t, 3))
    save(path, manifest)
    print("anchors resolved:",
          {v["id"]: v.get("t") for v in manifest.get("vo", [])},
          {a["id"]: a.get("t") for a in manifest.get("audio", []) if a.get("anchor")})


def build_music_stem(a, spans, stems_dir, total):
    """Cut/fade the music source per windows[]; bake ducking; one stem per window."""
    out_entries = []
    src = a["source_file"]
    for wi, w in enumerate(a.get("windows", [])):
        t_in, t_out = w["t_in"], w["t_out"]
        dur = round(t_out - t_in, 3)
        fade_in = w.get("fade_in", 1.5)
        fade_out = w.get("fade_out", 2.0)
        src_from = w.get("src_from", 0.0)
        out = os.path.join(stems_dir, f"{a['id']}_w{wi}.m4a")
        af = [f"atrim=start={src_from}:end={src_from + dur}", "asetpts=PTS-STARTPTS",
              f"afade=t=in:st=0:d={fade_in}",
              f"afade=t=out:st={max(0, dur - fade_out)}:d={fade_out}"]
        duck = w.get("duck_db", a.get("duck_db"))
        if duck:
            local = [(max(0, s - t_in), max(0, e - t_in)) for s, e in spans
                     if e > t_in and s < t_out]
            expr = duck_expr(local, duck)
            if expr:
                af.append(expr)
        r = sh(["ffmpeg", "-y", "-i", src, "-af", ",".join(af),
                "-c:a", "aac", "-b:a", "192k", out])
        if r.returncode:
            raise SystemExit(f"music stem failed: {r.stderr[-400:]}")
        out_entries.append({"file": out, "t": t_in, "gain_db": w.get("gain_db", 0)})
    return out_entries


def cmd_stems(manifest, path, targets):
    ws = os.path.dirname(os.path.abspath(path))
    stems_dir = os.path.join(ws, "audio", "stems")
    os.makedirs(stems_dir, exist_ok=True)
    total = manifest["computed_timeline"][-1]["end"]
    spans = speech_spans(manifest)
    print("speech spans:", [[round(s, 2), round(e, 2)] for s, e in spans])

    stems = []
    # VO stems: LUFS-staged to target
    for vo in manifest.get("vo", []):
        if not (vo.get("file") and vo.get("t") is not None):
            continue
        lufs = lufs_of(vo["file"])
        gain = round(targets["vo"] - lufs, 1) if lufs is not None else 0
        stems.append({"file": vo["file"], "t": vo["t"], "gain_db": gain, "role": "vo",
                      "id": vo["id"]})
    for a in manifest.get("audio", []):
        if not a.get("source_file"):
            continue
        role = a.get("role") or ("music" if a["type"] == "music" else "sfx")
        if a.get("windows"):
            for st in build_music_stem(a, spans, stems_dir, total):
                lufs = lufs_of(st["file"])
                base_gain = targets.get(role, 0) - lufs if lufs is not None else 0
                st["gain_db"] = round(base_gain + st.get("gain_db", 0), 1)
                st.update(role=role, id=a["id"])
                stems.append(st)
            continue
        if a.get("t") is None:
            print(f"  skip {a['id']} (no t)")
            continue
        stem_file = a["source_file"]
        # bed with ducking baked in
        if a.get("duck_db"):
            out = os.path.join(stems_dir, f"{a['id']}_duck.m4a")
            expr = duck_expr(spans, a["duck_db"])
            af = expr or "anull"
            end = a.get("end")
            if end:
                af = f"atrim=start=0:end={end - a['t']},asetpts=PTS-STARTPTS," + af
                af += f",afade=t=out:st={max(0, end - a['t'] - 2)}:d=2"
            r = sh(["ffmpeg", "-y", "-i", stem_file, "-af", af,
                    "-c:a", "aac", "-b:a", "192k", out])
            if r.returncode:
                raise SystemExit(f"bed stem failed: {r.stderr[-400:]}")
            stem_file = out
        lufs = lufs_of(stem_file)
        tgt = a.get("target_lufs", targets.get(role, targets["sfx"]))
        gain = round(tgt - lufs, 1) if lufs is not None else 0
        gain += a.get("gain_trim_db", 0)
        stems.append({"file": stem_file, "t": a["t"], "gain_db": round(gain, 1),
                      "role": role, "id": a["id"]})

    manifest["stems"] = stems
    manifest["audio_mix"] = [{"file": s["file"], "t": s["t"], "gain_db": s["gain_db"]}
                             for s in stems]
    save(path, manifest)
    print(f"built {len(stems)} stems:")
    for s in stems:
        print(f"  {s['id']:>16} t={s['t']:>7.2f} gain={s['gain_db']:>6.1f}  {os.path.basename(s['file'])}")


def cmd_mute_base(manifest, video, out):
    """Base-audio treatment: full mutes (mute_native_audio) and partial ducks
    (duck_native: {"src_span": [a, b], "db": -8}) mapped to edit time."""
    filters = []
    for row, entry in segments(manifest):
        sid = entry.get("clip")
        if not sid:
            continue
        shot = next(s for s in manifest["shots"] if s["id"] == sid)
        src0 = seg_src_in(manifest, entry)
        if shot.get("mute_native_audio"):
            e = duck_expr([(row["start"], row["end"])], -60)
            filters.append(e)
        dn = shot.get("duck_native")
        if dn:
            a = row["start"] + max(0, dn["src_span"][0] - src0)
            b = min(row["end"], row["start"] + dn["src_span"][1] - src0)
            if b > a:
                filters.append(duck_expr([(a, b)], dn.get("db", -8)))
    if not filters:
        print("no base-audio treatments; nothing to do")
        return
    r = sh(["ffmpeg", "-y", "-i", video, "-af", ",".join(filters), "-c:v", "copy",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", out])
    if r.returncode:
        raise SystemExit(r.stderr[-400:])
    print(f"base audio treated ({len(filters)} spans) -> {out}")


def cmd_mix(manifest, video, out):
    """Overlay manifest audio_mix stems (from --stems) onto the video's audio."""
    stems = manifest.get("audio_mix") or []
    if not stems:
        raise SystemExit("no audio_mix in manifest — run --stems first")
    cmd = ["ffmpeg", "-y", "-i", video]
    for st in stems:
        cmd += ["-i", st["file"]]
    parts, labels = [], []
    for i, st in enumerate(stems, start=1):
        ms = int(st.get("t", 0) * 1000)
        parts.append(f"[{i}:a]adelay={ms}|{ms},volume={st.get('gain_db', 0)}dB[st{i}]")
        labels.append(f"[st{i}]")
    parts.append(f"[0:a]{''.join(labels)}amix=inputs={len(stems) + 1}:"
                 f"duration=first:normalize=0[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2", out]
    r = sh(cmd)
    if r.returncode:
        raise SystemExit(r.stderr[-500:])
    lufs = lufs_of(out)
    print(f"mixed {len(stems)} stems -> {out}  (integrated {lufs} LUFS)")


DEFAULT_TARGETS = {"vo": -15.0, "music": -26.0, "bed": -30.0, "sfx": -20.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--anchors", action="store_true")
    ap.add_argument("--stems", action="store_true")
    ap.add_argument("--mute-base", action="store_true")
    ap.add_argument("--mix", action="store_true")
    ap.add_argument("--video")
    ap.add_argument("--out")
    args = ap.parse_args()
    cfg = load(os.path.join(args.series, "series-config.json"))
    manifest = load(args.manifest)
    targets = dict(DEFAULT_TARGETS, **cfg.get("audio", {}).get("mix_targets", {}))
    if args.anchors:
        cmd_anchors(manifest, args.manifest)
    elif args.stems:
        cmd_stems(manifest, args.manifest, targets)
    elif args.mute_base:
        if not (args.video and args.out):
            ap.error("--mute-base needs --video and --out")
        cmd_mute_base(manifest, args.video, args.out)
    elif args.mix:
        if not (args.video and args.out):
            ap.error("--mix needs --video and --out")
        cmd_mix(manifest, args.video, args.out)
    else:
        ap.error("pick a mode: --anchors / --stems / --mute-base / --mix")


if __name__ == "__main__":
    sys.exit(main())
