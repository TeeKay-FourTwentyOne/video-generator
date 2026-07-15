#!/usr/bin/env python3
"""
clone-check.py — detect SUBJECT DUPLICATION (clone / ghost-twin / merge / extra-limb)
in a generated video clip, using motion-gated dense sampling + Claude vision.

This is the artifact clip-qa misses: during fast subject motion (standing, crossing
frame, turning) Veo-style generators briefly render a SECOND COPY of the same subject
that splits off and merges back — visible for ~0.3-0.6s, inside a motion window. Even
sampling at clip-qa's ~0.3s cadence + its motion-tolerant prompt reads it as "a person
walking" and lets it through.

Strategy that catches it:
  1. Coarse pass: one cheap ffmpeg extraction → a per-frame MOTION-ENERGY curve.
  2. Locate the high-motion window(s) — where clones actually happen.
  3. DENSE pass: re-sample those windows every ~0.12s (accurate timestamps) so a
     transient double lands in 2-3 consecutive frames, not between samples.
  4. Vision pass: a duplication-SPECIFIC, HIGH-RECALL prompt that counts the subject
     per frame and flags count>expected, with explicit reflection/blur/shadow rule-outs.

Complements clip-qa (general, high-precision) — run BOTH on every generation.

Usage
  python3 tools/clone-check.py <video> [flags]

Flags
  --expected=N         Expected count of the primary subject in frame (default: 1).
  --step=S             Dense sample interval, seconds (default: 0.12).
  --coarse-step=S      Coarse/motion-profile interval, seconds (default: 0.30).
  --motion-k=K         Sensitivity: window = energy above median + K*MAD (default: 1.0; lower = more windows).
  --window-margin=S    Seconds of padding added around each motion window (default: 0.4).
  --whole              Ignore motion gating; densely sample the ENTIRE clip.
  --max-frames=N       Cap on dense frames sent to vision per clip (default: 48; chunked into grids of 15).
  --context=TEXT       Intent context (e.g. the generation prompt). Reduces false positives.
  --context-file=PATH  Read intent context from a file.
  --model=opus|sonnet|haiku   Claude model shortcut (default: opus).
  --model-id=NAME      Full Claude model ID (overrides --model).
  --save-strip=PATH    Save the dense composite(s); default adjacent as <name>.clone-strip[-N].png.
  --no-save-strip      Don't save composites.
  --json               Emit JSON only.
  --fail-on=LEVEL      Exit 3 if any doubling at/above severity LEVEL (high | medium | any).
  --config=PATH        data/config.json override (for claudeKey).
  --retries=N          API retries on transient errors (default: 3).

Exit codes
  0 — no doublings at or above --fail-on
  1 — internal/API failure
  2 — usage error
  3 — doublings detected meeting --fail-on threshold (only if --fail-on used)
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

try:
    from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat
except ImportError:
    print(json.dumps({"error": "Missing Pillow: pip install Pillow"}))
    sys.exit(1)


MODEL_SHORTCUTS = {
    "opus": "claude-opus-4-5-20251101",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
}

CONTEXT_PREFIX = """INTENT CONTEXT — what this clip is supposed to show:
{context}

Use it to fix the EXPECTED subject count and to recognize any intended second character (which is NOT a clone).

"""

DUP_PROMPT = """{context_block}You are inspecting frames from ONE continuous video clip, in chronological order, each labeled with its timestamp (e.g. "t=2.04s"). They are sampled DENSELY (every {step:.2f}s) and concentrated on a high-motion window — on purpose, to catch a brief artifact.

## The artifact you are hunting: SUBJECT DUPLICATION
During fast motion (a subject standing up, crossing the frame, turning), AI video generators sometimes render a SECOND COPY of the SAME subject: a duplicate body or ghost twin that splits off and then MERGES back into the original, or a doubled / extra limb that appears mid-motion. It typically lasts only a few frames. In sparse sampling it is easily mistaken for normal motion — here you have dense frames specifically so you can count bodies frame by frame.

EXPECTED count of the primary subject in frame: {expected}.

## Your job
1. For the densest motion frames, count the DISTINCT instances of the primary subject in each frame.
2. Report the MAXIMUM number of distinct instances seen in any single frame (`max_count_observed`).
3. Flag every span where a second copy / ghost twin appears, splits, or merges, or where an extra duplicated limb appears.

## DISAMBIGUATE — do NOT call these duplication (rule each out explicitly):
- **Motion blur**: ONE body smeared along its direction of travel — a single head with a directional smear. A REAL clone has its OWN separate head AND separately-posed limbs in a DIFFERENT position, not a smear.
- **Reflection**: a mirrored copy on glass / mirror / water with consistent reflective geometry.
- **Cast shadow** on a wall or floor.
- **An intended second character** named in the intent context.
For each flagged span, say which of these you ruled out and what proves it is a real second BODY (separate head, separately-articulated limbs, distinct pose).

## Severity
- **high** — a clearly doubled body a normal viewer would see on playback.
- **medium** — a brief ghost / extra limb / partial twin noticeable on a careful watch.
- **low** — faint, would likely go unnoticed.

## Recommendation
- `use_as_is` — no real duplication.
- `trim_before:<t>` — duplication sits early; everything from <t> on is clean (give the cut point).
- `trim_after:<t>` — duplication sits late; everything up to <t> is clean.
- `regenerate` — duplication is in the middle of essential action and cannot be trimmed around.

Return ONLY a JSON object, no prose, no markdown fences:
{{
  "subject": "<the primary subject, one phrase>",
  "expected_count": {expected},
  "max_count_observed": <int>,
  "doublings": [
    {{"timestamp_range": [<start_t>, <end_t>], "peak_count": <int>, "kind": "clone_body|ghost_twin|merge|extra_limb", "severity": "low|medium|high", "confidence": <0..1>, "ruled_out": "<what you eliminated and why it is a real second body>", "description": "<what is seen>"}}
  ],
  "clean_ranges": [{{"start": <t>, "end": <t>}}],
  "recommendation": "use_as_is|trim_before:<t>|trim_after:<t>|regenerate"
}}"""


# ---------- ffmpeg ----------

def probe_duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path]
    )
    return float(out.decode().strip())


def extract_at(video: str, t: float, out: str, width: int):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", video,
         "-frames:v", "1", "-vf", f"scale={width}:-1", out, "-y"],
        check=True,
    )


# ---------- motion profile ----------

def motion_curve(video: str, dur: float, coarse_step: float, tmpdir: str):
    """Return list of (t, energy) where energy = mean abs pixel diff vs previous coarse frame."""
    ts = []
    t = coarse_step / 2.0
    while t < dur:
        ts.append(round(t, 3))
        t += coarse_step
    prev = None
    curve = []
    for i, t in enumerate(ts):
        fp = os.path.join(tmpdir, f"c_{i:03d}.png")
        extract_at(video, t, fp, 160)
        img = Image.open(fp).convert("L")
        if prev is not None:
            diff = ImageChops.difference(prev, img)
            energy = ImageStat.Stat(diff).mean[0]
            curve.append((t, energy))
        prev = img
    return curve


def find_motion_windows(curve, k: float, margin: float, dur: float):
    """Threshold the motion curve at median + k*MAD; merge contiguous hot samples into windows."""
    if not curve:
        return []
    energies = sorted(e for _, e in curve)
    n = len(energies)
    median = energies[n // 2]
    mad = sorted(abs(e - median) for _, e in curve)[n // 2] or 1e-6
    thresh = median + k * mad
    hot = [t for t, e in curve if e >= thresh]
    if not hot:
        return []
    # merge hot timestamps within 2*coarse spacing into windows
    spacing = (curve[1][0] - curve[0][0]) if len(curve) > 1 else 0.3
    windows = []
    start = prev = hot[0]
    for t in hot[1:]:
        if t - prev <= spacing * 2.5:
            prev = t
        else:
            windows.append((start, prev))
            start = prev = t
    windows.append((start, prev))
    # pad + clamp
    out = []
    for a, b in windows:
        out.append((max(0.0, a - margin), min(dur, b + margin)))
    # merge overlaps after padding
    merged = [out[0]]
    for a, b in out[1:]:
        la, lb = merged[-1]
        if a <= lb:
            merged[-1] = (la, max(lb, b))
        else:
            merged.append((a, b))
    return merged


def dense_timestamps(windows, step: float, dur: float, whole: bool):
    ts = []
    spans = [(0.0, dur)] if whole or not windows else windows
    # keep timestamps clear of the very last frame: ffmpeg -ss within ~1 frame of
    # EOF can exit 0 yet write no image. dur-0.08 is a safe margin at >=12fps.
    last = max(0.0, dur - 0.08)
    for a, b in spans:
        t = a
        while t <= b + 1e-6:
            if t <= last:
                ts.append(round(t, 3))
            t += step
    # dedupe + sort
    return sorted(set(ts))


# ---------- strip ----------

def make_strip(frames, out_path: str, cols: int = 5):
    imgs = [Image.open(f["path"]) for f in frames]
    sw, sh = imgs[0].size
    scale = 260 / sw
    tw, th = int(sw * scale), int(sh * scale)
    lh = 22
    rows = (len(imgs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tw, rows * (th + lh)), (18, 18, 18))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    except Exception:
        font = ImageFont.load_default()
    for i, (img, f) in enumerate(zip(imgs, frames)):
        r, c = divmod(i, cols)
        x, y = c * tw, r * (th + lh)
        canvas.paste(img.resize((tw, th), Image.LANCZOS), (x, y))
        draw.text((x + 4, y + th + 3), f"t={f['t']}s", fill=(255, 255, 255), font=font)
    canvas.save(out_path)
    return canvas.size


# ---------- config / auth ----------

def load_api_key(config_path: str):
    if not os.path.exists(config_path):
        raise SystemExit(f"config not found: {config_path}")
    with open(config_path) as f:
        cfg = json.load(f)
    key = cfg.get("claudeKey") or cfg.get("anthropicKey")
    if not key:
        raise SystemExit("claudeKey / anthropicKey not set in config")
    return key


RETRYABLE = {408, 429, 500, 502, 503, 504, 529}


def call_claude(strip_path, api_key, model, step, expected, context, retries=3):
    with open(strip_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ctx_block = CONTEXT_PREFIX.format(context=context.strip()) if context else ""
    prompt = DUP_PROMPT.format(context_block=ctx_block, step=step, expected=expected)
    payload = {
        "model": model,
        "max_tokens": 2000,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    }
    body = json.dumps(payload).encode()
    data = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body,
            headers={"Content-Type": "application/json", "x-api-key": api_key,
                     "anthropic-version": "2023-06-01"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE and attempt < retries:
                delay = min(30, 2 ** attempt)
                sys.stderr.write(f"[clone-check] HTTP {e.code} (try {attempt+1}); retry {delay}s\n")
                time.sleep(delay); continue
            raise SystemExit(f"Claude API error {e.code}: {e.read().decode()[:300]}")
        except urllib.error.URLError as e:
            if attempt < retries:
                delay = min(30, 2 ** attempt)
                sys.stderr.write(f"[clone-check] net error (try {attempt+1}); retry {delay}s\n")
                time.sleep(delay); continue
            raise SystemExit(f"Network error: {e}")
    try:
        import costlog
        costlog.log_call("clone-check", data, strip_path)
    except Exception:
        pass
    parts = data.get("content", [])
    text = next((p.get("text") for p in parts if p.get("type") == "text"), None)
    if not text:
        raise SystemExit(f"No text in Claude response: {json.dumps(data)[:400]}")
    return text


def extract_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    s, e = t.find("{"), t.rfind("}")
    if s < 0 or e < 0:
        raise SystemExit(f"No JSON in response:\n{text[:800]}")
    return json.loads(t[s:e + 1])


SEV = {"low": 1, "medium": 2, "high": 3}


def meets(doublings, level):
    if level == "any":
        return bool(doublings)
    thr = SEV.get(level)
    return thr is not None and any(SEV.get(d.get("severity", "low"), 1) >= thr for d in doublings)


def merge_results(results):
    """Merge per-grid vision results into one report."""
    out = {"subject": "", "expected_count": None, "max_count_observed": 0,
           "doublings": [], "clean_ranges": [], "recommendation": "use_as_is"}
    recs = []
    for r in results:
        out["subject"] = out["subject"] or r.get("subject", "")
        out["expected_count"] = r.get("expected_count", out["expected_count"])
        out["max_count_observed"] = max(out["max_count_observed"], int(r.get("max_count_observed", 0) or 0))
        out["doublings"].extend(r.get("doublings", []) or [])
        out["clean_ranges"].extend(r.get("clean_ranges", []) or [])
        recs.append(r.get("recommendation", "use_as_is"))
    # strongest recommendation wins
    if any(x == "regenerate" for x in recs):
        out["recommendation"] = "regenerate"
    elif any(str(x).startswith("trim_") for x in recs):
        out["recommendation"] = next(x for x in recs if str(x).startswith("trim_"))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--expected", type=int, default=1)
    p.add_argument("--step", type=float, default=0.12)
    p.add_argument("--coarse-step", type=float, default=0.30)
    p.add_argument("--motion-k", type=float, default=1.0)
    p.add_argument("--window-margin", type=float, default=0.4)
    p.add_argument("--whole", action="store_true")
    p.add_argument("--max-frames", type=int, default=48)
    p.add_argument("--context", default=None)
    p.add_argument("--context-file", default=None)
    p.add_argument("--model", default="opus", choices=list(MODEL_SHORTCUTS.keys()))
    p.add_argument("--model-id", default=None)
    p.add_argument("--save-strip", default=None)
    p.add_argument("--no-save-strip", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--fail-on", default=None, choices=["high", "medium", "any"])
    p.add_argument("--config", default="data/config.json")
    p.add_argument("--retries", type=int, default=3)
    args = p.parse_args()

    if not os.path.exists(args.video):
        raise SystemExit(f"video not found: {args.video}")
    context = args.context
    if args.context_file:
        with open(args.context_file) as f:
            context = f.read()

    api_key = load_api_key(args.config)
    dur = probe_duration(args.video)
    model = args.model_id or MODEL_SHORTCUTS[args.model]

    with tempfile.TemporaryDirectory() as tmp:
        # 1) motion profile + windows
        curve = motion_curve(args.video, dur, args.coarse_step, tmp)
        windows = [] if args.whole else find_motion_windows(curve, args.motion_k, args.window_margin, dur)
        peak = max(curve, key=lambda x: x[1]) if curve else (0, 0)
        sys.stderr.write(
            f"[clone-check] {args.video} ({dur:.2f}s): motion peak {peak[1]:.1f} @ t={peak[0]}s; "
            f"{'WHOLE clip' if args.whole or not windows else str(len(windows))+' window(s): '+str([(round(a,2),round(b,2)) for a,b in windows])}\n")

        # 2) dense timestamps (cap)
        ts = dense_timestamps(windows, args.step, dur, args.whole)
        if len(ts) > args.max_frames:
            # keep densest coverage of the hottest window: prioritize frames nearest the peak
            ts = sorted(sorted(ts, key=lambda t: abs(t - peak[0]))[:args.max_frames])
        sys.stderr.write(f"[clone-check] dense frames: {len(ts)} @ step {args.step}s, model={model}\n")

        # 3) extract dense frames
        frames = []
        for i, t in enumerate(ts):
            fp = os.path.join(tmp, f"d_{i:03d}.png")
            try:
                extract_at(args.video, t, fp, 360)
            except subprocess.CalledProcessError:
                pass
            if os.path.exists(fp):  # ffmpeg can exit 0 near EOF yet write nothing
                frames.append({"t": t, "path": fp})
        if not frames:
            raise SystemExit("no frames could be extracted from the dense window")

        # 4) chunk into grids of <=15, run vision on each
        base = os.path.splitext(args.video)[0]
        chunks = [frames[i:i + 15] for i in range(0, len(frames), 15)]
        results, strip_paths = [], []
        for ci, chunk in enumerate(chunks):
            if args.no_save_strip:
                sp = os.path.join(tmp, f"strip_{ci}.png")
            elif args.save_strip:
                sp = args.save_strip if len(chunks) == 1 else f"{os.path.splitext(args.save_strip)[0]}-{ci}.png"
            else:
                sp = f"{base}.clone-strip.png" if len(chunks) == 1 else f"{base}.clone-strip-{ci}.png"
            w, h = make_strip(chunk, sp)
            if not args.no_save_strip:
                strip_paths.append(sp)
            sys.stderr.write(f"[clone-check] grid {ci+1}/{len(chunks)} {w}x{h} ({len(chunk)} frames) → {sp}\n")
            resp = call_claude(sp, api_key, model, args.step, args.expected, context, retries=args.retries)
            results.append(extract_json(resp))

    parsed = merge_results(results)
    parsed["_meta"] = {
        "video": args.video, "duration": round(dur, 2),
        "motion_peak_t": peak[0], "windows": [[round(a, 2), round(b, 2)] for a, b in windows] or "whole",
        "dense_frames": len(ts), "step": args.step, "model": model,
        "strips": strip_paths, "context_provided": bool(context),
    }
    doublings = parsed.get("doublings") or []

    print(json.dumps(parsed, indent=2))
    if not args.json:
        print()
        if doublings:
            by = {}
            for d in doublings:
                by[d.get("severity", "low")] = by.get(d.get("severity", "low"), 0) + 1
            print(f"⚠ {len(doublings)} doubling(s) — " + ", ".join(f"{k}={v}" for k, v in by.items()))
            for d in doublings:
                tr = d.get("timestamp_range", [0, 0])
                print(f"   [{tr[0]}–{tr[1]}s] {d.get('severity','?')} {d.get('kind','?')} "
                      f"(peak {d.get('peak_count','?')}, conf {d.get('confidence','?')}): {d.get('description','')[:90]}")
        else:
            print(f"✓ No duplication detected (max bodies seen: {parsed.get('max_count_observed','?')}, expected {args.expected})")
        print(f"  recommendation: {parsed.get('recommendation','?')}")
        for sp in strip_paths:
            print(f"  strip: {sp}")

    if args.fail_on and meets(doublings, args.fail_on):
        sys.exit(3)


if __name__ == "__main__":
    main()
