#!/usr/bin/env python3
"""gate-runner — clip acceptance gate for vertical-series episodes.

Per generated clip (status "generated"), in order:
  1. normalize check   tools/normalize-clip.cjs --detect-only (rewrite only if bars > 2px)
  2. probe             ffprobe duration/fps vs shot seconds
  3. clip-qa           tools/clip-qa.py  --context=<shot.qa_context> --fail-on=medium
  4. clone-check       tools/clone-check.py (only shots with motion:true) --expected=N
  5. dialogue          marked "pending-mcp" — transcribe via MCP at build (no local whisper)

Writes verdicts into the manifest and emits <ws>/gate-report.md: per clip, the
flags + strips + a recommended treatment on the keep / edit-around / reroll
ladder. THE GATE NEVER REROLLS — recommendations only (no-auto-reroll doctrine).

Flags: --shot ID (one clip) · --no-api (skip 3+4: plumbing test) · --fail-on=LEVEL
"""
import argparse
import json
import os
import subprocess
import sys

QA_LADDER = """Recommended ladder: keep (cosmetic/low, doesn't block the beat) ->
edit-around (flag confined to a clip end: trim to clean range / cut early / mask) ->
reroll (mid-essential-action, untrimmable; change what CAUSES the artifact)."""


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    p = sh(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
            "-show_streams", path])
    try:
        j = json.loads(p.stdout)
        dur = float(j["format"]["duration"])
        v = next(s for s in j["streams"] if s["codec_type"] == "video")
        return {"duration": round(dur, 2), "w": v["width"], "h": v["height"],
                "r_frame_rate": v.get("r_frame_rate"),
                "has_audio": any(s["codec_type"] == "audio" for s in j["streams"])}
    except Exception as e:
        return {"error": str(e)}


def gate_shot(s, ws, args, report):
    clip = os.path.join(ws, s["clip"])
    v = s.setdefault("verdicts", {})
    report.append(f"\n## {s['id']} — `{s['clip']}`")

    # 1. normalize (detect; rewrite only if real bars)
    n = sh(["node", "tools/normalize-clip.cjs", clip, "--detect-only"])
    try:
        det = json.loads(n.stdout)
    except Exception:
        det = {"raw": n.stdout[-400:], "stderr": n.stderr[-400:]}
    v["normalize"] = det
    bars = det.get("bars") or det.get("barPx") or {}
    max_bar = max(bars.values()) if isinstance(bars, dict) and bars else 0
    if max_bar > 2:
        fixed = clip.replace("_RAW", "_NORM")
        sh(["node", "tools/normalize-clip.cjs", clip, fixed])
        s["clip"] = os.path.relpath(fixed, ws)
        report.append(f"- normalize: bars {bars} -> rewrote `{s['clip']}`")
    else:
        report.append("- normalize: clean")

    # 2. probe
    pr = probe(os.path.join(ws, s["clip"]))
    v["probe"] = pr
    report.append(f"- probe: {pr}")
    if "duration" in pr and abs(pr["duration"] - s["seconds"]) > 1.0:
        report.append(f"  - !! duration {pr['duration']} vs requested {s['seconds']}")

    if args.no_api:
        s["status"] = "gated-noapi"
        report.append("- clip-qa / clone-check: SKIPPED (--no-api)")
        return

    # 3. clip-qa
    ctx = s.get("qa_context", "")
    q = sh(["python3", "tools/clip-qa.py", os.path.join(ws, s["clip"]),
            f"--context={ctx}", f"--fail-on={args.fail_on}", "--json"])
    v["clip_qa"] = {"exit": q.returncode, "out": q.stdout[-2000:]}
    report.append(f"- clip-qa: exit {q.returncode}"
                  + (" (FLAGGED — see strip)" if q.returncode == 3 else ""))

    # 4. clone-check on motion shots
    if s.get("motion"):
        c = sh(["python3", "tools/clone-check.py", os.path.join(ws, s["clip"]),
                f"--expected={s.get('expected_subjects', 1)}",
                f"--context={ctx}", f"--fail-on={args.fail_on}", "--json"])
        v["clone_check"] = {"exit": c.returncode, "out": c.stdout[-2000:]}
        report.append(f"- clone-check: exit {c.returncode}"
                      + (" (FLAGGED — full-res frames are the arbiter)" if c.returncode == 3 else ""))

    # 5. dialogue
    if s.get("dialogue"):
        v["dialogue_check"] = "pending-mcp"
        report.append(f"- dialogue: transcribe via MCP against: \"{s['dialogue']['text']}\"")

    flagged = v["clip_qa"]["exit"] == 3 or v.get("clone_check", {}).get("exit") == 3
    s["status"] = "flagged" if flagged else "gated-pass"
    report.append(f"- **status: {s['status']}**")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--shot")
    ap.add_argument("--no-api", action="store_true")
    ap.add_argument("--fail-on", default="medium")
    args = ap.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)
    ws = os.path.dirname(os.path.abspath(args.manifest))

    report = [f"# Gate report — {manifest['slug']}", QA_LADDER]
    todo = [s for s in manifest["shots"]
            if s.get("clip") and s.get("status") in ("generated", "flagged", "gated-noapi")
            and (not args.shot or s["id"] == args.shot)]
    if not todo:
        print("no generated clips to gate")
        return
    for s in todo:
        print(f"gating {s['id']} ...")
        gate_shot(s, ws, args, report)

    with open(args.manifest + ".tmp", "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(args.manifest + ".tmp", args.manifest)
    rp = os.path.join(ws, "gate-report.md")
    with open(rp, "w") as f:
        f.write("\n".join(report) + "\n")
    print(f"wrote {rp}")


if __name__ == "__main__":
    sys.exit(main())
