#!/usr/bin/env python3
"""
anchor-drift.py — pre-generation QA for Veo "book-end" frames: catch the
impossible-slide and pop-in artifacts BEFORE spending a Veo generation.

Veo produces a clip by interpolating between a FIRST anchor frame and a LAST
anchor frame. It will SLIDE, MORPH, MATERIALIZE, or POP any object whose
position / scale / count / orientation differs between the two frames it is
handed — even when that motion is physically impossible (a placed object
gliding across a table with nothing pushing it; a new object blinking into
existence). The same thing happens at a hard CUT between two shots when the
last frame of shot N and the first frame of shot N+1 disagree about what is
on screen.

Both failures are detectable from frames alone — no Veo spend required. This
tool sends a frame PAIR to Claude vision, asks which supposedly-static objects
differ between them and which differences are MOTIVATED by a visible mover
(e.g. a gripper carrying an object), and predicts the resulting artifact.

Two modes:
  --mode within-clip   (default)  A = first anchor, B = last anchor of ONE clip.
                                   Flags objects Veo will SLIDE/MORPH/MATERIALIZE.
  --mode across-cut                A = last frame of shot N, B = first frame of
                                   shot N+1 (a hard cut). Flags objects that will
                                   POP / JUMP at the cut.

Usage
  python3 tools/anchor-drift.py <frameA> <frameB> [--mode within-clip|across-cut] \\
    --static="TEXT" --motivated="TEXT" [flags]

Examples
  # within a clip: the two copies must hold position; only the gripper-carried one may move
  python3 tools/anchor-drift.py s4_a.png s4_b.png --mode=within-clip \\
    --static="every felt copy already sitting on the table (count and position)" \\
    --motivated="the grey machine gripper arm and any single copy it is holding" \\
    --fail-on=medium

  # across a cut: shot 3's last frame vs shot 4's first frame must agree on the dolls
  python3 tools/anchor-drift.py s3_last.png s4_first.png --mode=across-cut \\
    --static="the felt copies on the table (count and positions)" \\
    --motivated="the machine gripper arm" --fail-on=medium

Flags
  --mode=within-clip|across-cut   Which artifact class to predict (default within-clip).
  --static=TEXT       What must NOT change between the two frames (inert objects, placed props).
  --motivated=TEXT    What IS allowed to move and its mover (changes here are OK, not flagged).
  --labelA=TEXT       Override Image-1 label (default depends on mode).
  --labelB=TEXT       Override Image-2 label.
  --model=opus|sonnet|haiku   Claude model (default opus — most reliable for visual diffs).
  --model-id=NAME     Full Claude model id (overrides --model).
  --json              Emit JSON only.
  --config=PATH       data/config.json override (for claudeKey).
  --fail-on=LEVEL     Exit code 3 if any violation at/above LEVEL (high | medium | any). Default medium.
  --retries=N         API retries (default 3).

Exit codes
  0 — pass (no violation at/above --fail-on)
  1 — internal / API failure
  2 — usage error
  3 — violations meet --fail-on threshold
"""

import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    from PIL import Image
except ImportError:
    print(json.dumps({"error": "Missing Pillow: pip install Pillow"}))
    sys.exit(1)

MODELS = {
    "opus": "claude-opus-4-7",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}
RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}

MODE_INTRO = {
    "within-clip": (
        "These two images are the FIRST anchor frame (Image 1) and the LAST anchor frame "
        "(Image 2) of a SINGLE Veo book-end clip. Veo will interpolate between them. Any "
        "static object that differs in position, scale, count, or orientation will be SLID, "
        "MORPHED, or MATERIALIZED across the clip — with no real cause."
    ),
    "across-cut": (
        "Image 1 is the LAST frame of one shot; Image 2 is the FIRST frame of the NEXT shot, "
        "joined by a HARD CUT. For continuity, everything static should match across the cut. "
        "Any static object whose count or position differs will POP into/out of existence or "
        "JUMP position at the cut."
    ),
}
MODE_ARTIFACTS = {
    "within-clip": "slide (moved), resize-morph (resized), morph (reoriented), or materialize (appeared) — all without a real cause",
    "across-cut": "pop (appeared/disappeared), jump (moved), or a mover-payload jump (an object teleporting into a gripper/hand, or the mover snapping to a new shape) at the cut — a continuity break",
}
PAYLOAD_RULE = {
    "within-clip": (
        "PAYLOAD RULE (within a clip the mover moves SMOOTHLY): a new object that is HELD BY / GRIPPED BY / "
        "in contact with an allowed mover is OK — the mover carries it in smoothly; do NOT flag it. Only flag a "
        "new object that appears UNATTACHED on a static surface with nothing touching it. For a PLACEMENT to be "
        "motivated, the mover must be in contact with the object in BOTH frames (holding it in the first, still "
        "touching it mid-release in the last). If the last frame shows the object resting while the mover is "
        "already detached/empty, the placement is NOT motivated in the endpoints — flag it (Veo will pop/slide it)."
    ),
    "across-cut": (
        "PAYLOAD / MOVER RULE (a hard cut is INSTANTANEOUS — it carries NOTHING smoothly): flag NOT ONLY a "
        "static-surface count change, but ALSO any change in the MOVER itself across the cut. If the mover is "
        "empty-handed in one frame and holding an object in the other, the object TELEPORTS into its grip — a "
        "jarring jump. If the mover's shape/form or position changes substantially, it SNAPS — also a jump. The "
        "'a held object is OK' relaxation does NOT apply across a cut; everything must match. EXCEPTION: if the "
        "two frames are clearly at DIFFERENT camera framings (a reframe — different shot scale, distance, or "
        "angle), the cut is deliberately masking discontinuities; tag those items 'masked by reframe' and set "
        "their severity to low."
    ),
}
DEFAULT_LABELS = {
    "within-clip": ("FIRST anchor frame", "LAST anchor frame"),
    "across-cut": ("LAST frame of shot N", "FIRST frame of shot N+1"),
}

PROMPT_TEMPLATE = """You are a pre-generation QA check for AI video (Veo) "book-end" generation.

{mode_intro}

You are given two images:
- IMAGE 1 = {label_a}
- IMAGE 2 = {label_b}

WHAT SHOULD BE STATIC — must NOT change position, scale, count, or orientation between the two frames:
{static}

WHAT IS ALLOWED TO MOVE, and its mover — changes to these are MOTIVATED and must NOT be flagged:
{motivated}

Compare the two images carefully and literally. Identify EVERY object or element whose position, scale, count, or orientation differs between Image 1 and Image 2. For each difference decide:
- VIOLATION: it is a should-be-static object that changed, OR a new object that appears UNATTACHED — resting on a static surface (table, floor, shelf) or floating — with NO mover holding it. Veo will artifact it.
- OK: the change is clearly caused by a visible mover listed above.

{payload_rule}

Be precise about object COUNT, counting only the objects of the static class RESTING ON THE STATIC SURFACE (do NOT count objects currently held in a mover's grip). A change in the resting-on-surface count with no mover placing the extra one is the classic artifact; a change only in what the mover is holding is NOT.

For each VIOLATION, predict the Veo artifact: {artifacts}.

Return ONLY a JSON object, no prose:
{{
  "verdict": "pass" | "flag",
  "summary": "one or two sentences describing what (if anything) will artifact",
  "counts": {{"image1": <int objects of the static class>, "image2": <int>}},
  "violations": [
    {{
      "subject": "which object",
      "change": "appeared|disappeared|moved|resized|reoriented|count_changed",
      "from": "state in Image 1",
      "to": "state in Image 2",
      "motivated_by": "name of the visible mover, or null",
      "predicted_artifact": "slide|resize-morph|morph|materialize|pop|jump|vanish",
      "severity": "low|medium|high",
      "fix": "the concrete frame fix (e.g. pin this object to its Image-1 position; only ADD new objects at empty spots; make the cut frames agree on count)"
    }}
  ],
  "ok_changes": ["short notes on motivated/allowed differences you deliberately did NOT flag"]
}}
Set verdict to "flag" if any violation has severity medium or high; otherwise "pass"."""


# ---------- config / auth ----------

def load_api_key(config_path: str) -> str:
    if not os.path.exists(config_path):
        raise SystemExit(f"config not found: {config_path}")
    with open(config_path) as f:
        cfg = json.load(f)
    key = cfg.get("claudeKey") or cfg.get("anthropicKey")
    if not key:
        raise SystemExit("claudeKey / anthropicKey not set in config")
    return key


# Anthropic messages API caps at 5MB per image; downscale with headroom for base64 (~1.33x).
MAX_B64_BYTES = int(4.6 * 1024 * 1024)


def encode_image_for_api(path: str) -> tuple[str, str]:
    if not os.path.exists(path):
        raise SystemExit(f"image not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    media_type = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif",
    }.get(ext, "image/png")
    raw = open(path, "rb").read()
    if len(raw) * 4 // 3 <= MAX_B64_BYTES:
        return base64.b64encode(raw).decode(), media_type
    # too big — downscale to JPEG, max 1568px on the long side
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    long_side = max(img.size)
    if long_side > 1568:
        scale = 1568 / long_side
        img = img.resize((int(img.size[0] * scale), int(img.size[1] * scale)))
    for q in (90, 80, 70, 60, 50):
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q)
        data = buf.getvalue()
        if len(data) * 4 // 3 <= MAX_B64_BYTES:
            return base64.b64encode(data).decode(), "image/jpeg"
    return base64.b64encode(data).decode(), "image/jpeg"


def image_block(path: str):
    data, media_type = encode_image_for_api(path)
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


def call_claude(frame_a, frame_b, prompt, api_key, model, retries=3) -> str:
    content = [
        {"type": "text", "text": "IMAGE 1:"}, image_block(frame_a),
        {"type": "text", "text": "IMAGE 2:"}, image_block(frame_b),
        {"type": "text", "text": prompt},
    ]
    body = json.dumps({"model": model, "max_tokens": 2000,
                       "messages": [{"role": "user", "content": content}]}).encode()
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
            if e.code in RETRYABLE_STATUS and attempt < retries:
                delay = min(30, 2 ** attempt)
                sys.stderr.write(f"[anchor-drift] HTTP {e.code} (attempt {attempt+1}); retry in {delay}s\n")
                time.sleep(delay)
                continue
            raise SystemExit(f"Claude API error {e.code}: {e.read().decode()[:300]}")
        except urllib.error.URLError as e:
            if attempt < retries:
                time.sleep(min(30, 2 ** attempt))
                continue
            raise SystemExit(f"Network error contacting Claude: {e}")
    try:
        import costlog
        costlog.log_call("anchor-drift", data, f"{frame_a}|{frame_b}")
    except Exception:
        pass
    parts = data.get("content", []) if data else []
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
        raise SystemExit(f"Could not locate JSON in Claude response:\n{text[:800]}")
    return json.loads(t[s:e + 1])


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}


def meets_fail_threshold(violations, level: str) -> bool:
    if level == "any":
        return bool(violations)
    thr = SEVERITY_ORDER.get(level)
    return thr is not None and any(
        SEVERITY_ORDER.get(v.get("severity", "low"), 1) >= thr for v in violations)


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("frame_a")
    p.add_argument("frame_b")
    p.add_argument("--mode", choices=["within-clip", "across-cut"], default="within-clip")
    p.add_argument("--static", default="all inert objects, placed props, and background figures (their count and positions)")
    p.add_argument("--motivated", default="(none specified — flag any unexplained object motion or appearance)")
    p.add_argument("--labelA")
    p.add_argument("--labelB")
    p.add_argument("--model", choices=list(MODELS), default="opus")
    p.add_argument("--model-id")
    p.add_argument("--json", action="store_true")
    p.add_argument("--config", default="data/config.json")
    p.add_argument("--fail-on", default="medium")
    p.add_argument("--retries", type=int, default=3)
    a = p.parse_args()

    label_a = a.labelA or DEFAULT_LABELS[a.mode][0]
    label_b = a.labelB or DEFAULT_LABELS[a.mode][1]
    prompt = PROMPT_TEMPLATE.format(
        mode_intro=MODE_INTRO[a.mode], label_a=label_a, label_b=label_b,
        static=a.static.strip(), motivated=a.motivated.strip(),
        payload_rule=PAYLOAD_RULE[a.mode], artifacts=MODE_ARTIFACTS[a.mode])

    model = a.model_id or MODELS[a.model]
    api_key = load_api_key(a.config)
    text = call_claude(a.frame_a, a.frame_b, prompt, api_key, model, a.retries)
    result = extract_json(text)
    result.setdefault("mode", a.mode)
    violations = result.get("violations", [])

    if a.json:
        print(json.dumps(result, indent=2))
    else:
        verdict = result.get("verdict", "?").upper()
        mark = "✅" if verdict == "PASS" else "🚩"
        print(f"{mark} anchor-drift [{a.mode}]: {verdict}")
        c = result.get("counts") or {}
        if c:
            print(f"   static-object count: image1={c.get('image1')}  image2={c.get('image2')}")
        print(f"   {result.get('summary','')}")
        for v in violations:
            sev = v.get("severity", "?").upper()
            print(f"   [{sev}] {v.get('subject')}: {v.get('change')} "
                  f"({v.get('from')} -> {v.get('to')}) "
                  f"=> {v.get('predicted_artifact')}"
                  + (f" [motivated by {v['motivated_by']}]" if v.get("motivated_by") else ""))
            if v.get("fix"):
                print(f"        fix: {v['fix']}")
        for ok in result.get("ok_changes", []) or []:
            print(f"   · ok: {ok}")

    if meets_fail_threshold(violations, a.__dict__["fail_on"]):
        sys.exit(3)


if __name__ == "__main__":
    main()
