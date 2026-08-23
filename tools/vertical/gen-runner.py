#!/usr/bin/env python3
"""gen-runner — Veo generation orchestration for vertical-series episodes.

Veo submission happens through the MCP tool `submit_veo_generation` (agent-side;
there is deliberately no direct-submit path here). This tool does everything
around that: expands prompts, enforces doctrine, polls, downloads, records.

Modes (in build order):
  --plan                   Expand every runnable shot; print prompt/anchors/cost + budget check. No side effects.
  --specs                  Write scratch/submit-specs.json — exact MCP args per shot for the agent to submit.
  --record S7=projects/... Stamp operation names onto shots (repeatable; = pairs).
  --poll                   Poll all submitted shots (tools/gcp/poll-veo-ops.cjs), download DONE clips
                           (tools/gcp/dl.cjs) to <ws>/clips/<shot>_RAW.mp4, stamp status + cost.
  --shot ID                Restrict --plan/--specs to one shot.
  --retake ID              Allow re-spec of a non-pending shot. Requires protected_retake:true on the
                           shot, or --override "<reason>" (logged). Encodes the no-auto-reroll doctrine.

Doctrine encoded: one generation per shot (a shot with a job_id is not re-specced
without --retake); every submission attempt is costed (veo-bills-attempts).
"""
import argparse
import json
import os
import re
import subprocess
import sys

VEO_USD_PER_SEC = 0.10


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def ws_dir(manifest_path):
    return os.path.dirname(os.path.abspath(manifest_path))


def expand_prompt(shot, cfg):
    p = shot["prompt"]
    for key, text in cfg.get("locks", {}).items():
        p = p.replace("{{" + key + "}}", text)
    missing = re.findall(r"{{([A-Z_]+)}}", p)
    if missing:
        raise SystemExit(f"{shot['id']}: unresolved placeholders {missing}")
    suffix = cfg.get("era_suffix", "").strip()
    if suffix and suffix.lower()[:20] not in p.lower():
        p = p.rstrip() + " " + suffix
    return p


def runnable(shots, shot_id, retake, override):
    for s in shots:
        if s.get("type", "veo") != "veo":
            continue
        if shot_id and s["id"] != shot_id:
            continue
        if s.get("job_id") and s["id"] != retake:
            continue
        if s["id"] == retake:
            if not (s.get("protected_retake") or override):
                raise SystemExit(
                    f"{s['id']}: retake refused — not protected_retake and no --override reason "
                    "(no-auto-reroll doctrine)")
            s.setdefault("retake_log", []).append(override or "protected retake")
        yield s


def mcp_args(shot, cfg, ws):
    veo = cfg.get("veo", {})
    args = {
        "prompt": expand_prompt(shot, cfg),
        "model": veo.get("model", "veo-3.1-prod"),
        "durationSeconds": shot["seconds"],
        "aspectRatio": veo.get("aspect", "9:16"),
        "generateAudio": veo.get("generate_audio", True),
    }
    resolution = shot.get("resolution") or veo.get("resolution")
    if resolution:
        args["resolution"] = resolution
    anchors = shot.get("anchors") or {}
    for key, mcp_key in (("first", "firstFramePath"), ("last", "lastFramePath")):
        if anchors.get(key):
            path = anchors[key] if os.path.exists(anchors[key]) else os.path.join(ws, anchors[key])
            if not os.path.exists(path):
                raise SystemExit(f"{shot['id']}: anchor missing: {anchors[key]}")
            args[mcp_key] = os.path.abspath(path)
    return args


def cmd_plan(cfg, manifest, args):
    total_s, n = 0, 0
    for s in runnable(manifest["shots"], args.shot, args.retake, args.override):
        a = mcp_args(s, cfg, ws_dir(args.manifest))
        n += 1
        total_s += s["seconds"]
        print(f"\n=== {s['id']}  ({s['seconds']}s, use {s.get('use')})  "
              f"motion={s.get('motion')} dialogue={'yes' if s.get('dialogue') else 'no'}")
        for k in ("firstFramePath", "lastFramePath"):
            if k in a:
                print(f"  {k}: {a[k]}")
        print(f"  prompt: {a['prompt']}")
    overhead = cfg["budget"].get("veo_overhead", 1.3)
    est = total_s * VEO_USD_PER_SEC * overhead
    spent = manifest.get("spend", {}).get("veo_usd", 0)
    cap = cfg["budget"]["per_episode_usd"]
    print(f"\n{n} shots, {total_s} Veo-s → est ${est:.2f} (x{overhead} overhead); "
          f"already spent ${spent:.2f}; cap ${cap}")
    if spent + est > cap:
        print(f"!! projected ${spent + est:.2f} EXCEEDS cap ${cap}")


def cmd_specs(cfg, manifest, args):
    ws = ws_dir(args.manifest)
    specs = []
    for s in runnable(manifest["shots"], args.shot, args.retake, args.override):
        specs.append({"shot": s["id"], "mcp_tool": "submit_veo_generation",
                      "args": mcp_args(s, cfg, ws)})
    out = os.path.join(ws, "scratch", "submit-specs.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    save(out, specs)
    save(args.manifest, manifest)  # persists retake_log if any
    print(f"wrote {out} ({len(specs)} shots)")
    print("Submit each via MCP submit_veo_generation, then: "
          "gen-runner --record SHOT=<operationName> ...")


def cmd_record(cfg, manifest, args):
    overhead = cfg["budget"].get("veo_overhead", 1.3)
    by_id = {s["id"]: s for s in manifest["shots"]}
    for pair in args.record:
        sid, op = pair.split("=", 1)
        s = by_id[sid]
        s["job_id"] = op
        s["status"] = "submitted"
        # every attempt bills (veo-bills-attempts): cost on record, not on success
        s["cost_usd"] = round((s.get("cost_usd") or 0) +
                              s["seconds"] * VEO_USD_PER_SEC * overhead, 2)
        manifest["spend"]["veo_usd"] = round(
            manifest["spend"].get("veo_usd", 0) + s["seconds"] * VEO_USD_PER_SEC * overhead, 2)
        print(f"{sid} <- {op}")
    save(args.manifest, manifest)


def cmd_poll(cfg, manifest, args):
    ws = ws_dir(args.manifest)
    pending = [s for s in manifest["shots"] if s.get("status") == "submitted"]
    if not pending:
        print("nothing submitted")
        return
    pairs = [f"{s['id']}={s['job_id']}" for s in pending]
    proc = subprocess.run(["node", "tools/gcp/poll-veo-ops.cjs"] + pairs,
                          capture_output=True, text=True)
    print(proc.stdout)
    by_id = {s["id"]: s for s in pending}
    for line in proc.stdout.splitlines():
        m = re.match(r"DONE (\S+) uri=(\S+)", line)
        if m and m.group(1) in by_id:
            s = by_id[m.group(1)]
            clip = os.path.join(ws, "clips", f"{s['id']}_RAW.mp4")
            dl = subprocess.run(["node", "tools/gcp/dl.cjs", m.group(2), clip],
                                capture_output=True, text=True)
            print(dl.stdout.strip() or dl.stderr.strip())
            if dl.returncode == 0:
                s["clip"] = os.path.relpath(clip, ws)
                s["status"] = "generated"
        m = re.match(r"(FILTERED|ERROR) (\S+)", line)
        if m and m.group(2) in by_id:
            by_id[m.group(2)]["status"] = m.group(1).lower()
            by_id[m.group(2)]["verdicts"]["submit"] = line
    save(args.manifest, manifest)
    print("manifest updated")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--specs", action="store_true")
    ap.add_argument("--record", nargs="+", metavar="SHOT=OP")
    ap.add_argument("--poll", action="store_true")
    ap.add_argument("--shot")
    ap.add_argument("--retake")
    ap.add_argument("--override")
    args = ap.parse_args()
    cfg = load(os.path.join(args.series, "series-config.json"))
    manifest = load(args.manifest)
    if args.plan:
        cmd_plan(cfg, manifest, args)
    elif args.specs:
        cmd_specs(cfg, manifest, args)
    elif args.record:
        cmd_record(cfg, manifest, args)
    elif args.poll:
        cmd_poll(cfg, manifest, args)
    else:
        ap.error("pick a mode: --plan / --specs / --record / --poll")


if __name__ == "__main__":
    sys.exit(main())
