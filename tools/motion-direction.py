#!/usr/bin/env python3
"""
motion-direction.py — per-region MOTION-DIRECTION digest for a clip.

Catches the "right action, WRONG DIRECTION" failure class that glitch detectors
(clip-qa) and holistic VLM "find the weirdness" passes miss: a car window that
rolls UP instead of down, a pour that runs backward, a door that closes when it
should open, a level that drains when it should fill. Direction is a measurable
physical signal — dense optical flow — not a perception you have to coax from a
model, so we measure it with OpenCV and only OPTIONALLY ask a VLM to name the
object and judge plausibility.

Pipeline (each stage is the lesson from the failed holistic attempts):
  1. LOCALIZE   — dense Farneback flow per frame pair; accumulate energy map.
  2. SEPARATE   — estimate global camera motion (pan + zoom); residual = object motion.
  3. DIRECTION  — per grid cell, ENERGY-WEIGHTED mean flow (a thin moving edge is
                  not diluted by the static background in its cell).
  4. DIGEST     — rank independent movers, label UP/DOWN/LEFT/RIGHT/EXPAND, write
                  JSON + console table + an annotated frame (arrows). This is the
                  human-attention-direction artifact.
  5. (--vlm)    — crop the top regions (first vs last, full res), tell the model the
                  MEASURED direction, BRACKET the intentional premise, ask "what is
                  this object and is that direction plausible here?". Perception is
                  done by CV; the model only does naming + world-knowledge judgment.

Usage
  python3 tools/motion-direction.py <video> [flags]

Flags
  --n=24            frames to sample
  --width=480       analysis width (flow computed at this scale)
  --grid=RxC        cell grid (default 8x14)
  --top=6           max regions to report
  --min-speed=0.15  min energy-weighted speed (px/frame at --width) to call a cell a mover
  --annotate=PATH   write an annotated frame (default: <video>.motion.png)
  --json            print JSON only
  --vlm             add the naming/plausibility layer (Claude vision; ~$0.02-0.05)
  --premise="..."   what is INTENTIONALLY stylized — ignore it (kills premise false-positives)
  --context="..."   one-line real-world situation for the plausibility rule

Exit: 0 always (diagnostic). JSON has the machine-readable digest.
"""
import argparse, json, os, subprocess, tempfile, base64, urllib.request
import numpy as np, cv2


def ffprobe_dur(v):
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", v]).decode().strip())


def grab(v, t, width, tmp, tag):
    p = os.path.join(tmp, f"{tag}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", v,
                    "-frames:v", "1"] + (["-vf", f"scale={width}:-1"] if width else []) + [p], check=True)
    return p


def label_dir(dx, dy):
    parts = []
    if abs(dy) >= abs(dx) * 0.5:
        parts.append("UP" if dy < 0 else "DOWN")
    if abs(dx) >= abs(dy) * 0.5:
        parts.append("LEFT" if dx < 0 else "RIGHT")
    return "+".join(parts) or "still"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--width", type=int, default=480)
    ap.add_argument("--grid", default="8x14")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--min-speed", type=float, default=0.15)
    ap.add_argument("--annotate", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--vlm", action="store_true")
    ap.add_argument("--premise", default="")
    ap.add_argument("--context", default="a video clip")
    a = ap.parse_args()

    rows, cols = (int(x) for x in a.grid.lower().split("x"))
    dur = ffprobe_dur(a.video)
    times = [dur * (i + 0.5) / a.n for i in range(a.n)]
    tmp = tempfile.mkdtemp()
    grays = [cv2.cvtColor(cv2.imread(grab(a.video, t, a.width, tmp, f"f{i}")), cv2.COLOR_BGR2GRAY)
             for i, t in enumerate(times)]
    H, W = grays[0].shape

    # 1+2: accumulate flow & energy
    net = np.zeros((H, W, 2), np.float32)     # summed flow (for camera estimate)
    wsum = np.zeros((rows, cols), np.float64)            # per-cell energy
    wvx = np.zeros((rows, cols), np.float64)             # per-cell energy-weighted dx
    wvy = np.zeros((rows, cols), np.float64)
    ch, cw = H // rows, W // cols
    npairs = len(grays) - 1
    for i in range(npairs):
        fl = cv2.calcOpticalFlowFarneback(grays[i], grays[i + 1], None,
                                          0.5, 3, 21, 3, 5, 1.2, 0)
        net += fl
        mag = np.linalg.norm(fl, axis=2)
        for r in range(rows):
            for c in range(cols):
                ys, xs = r * ch, c * cw
                m = mag[ys:ys + ch, xs:xs + cw]
                fx = fl[ys:ys + ch, xs:xs + cw, 0]
                fy = fl[ys:ys + ch, xs:xs + cw, 1]
                w = float(m.sum())
                wsum[r, c] += w
                wvx[r, c] += float((fx * m).sum())
                wvy[r, c] += float((fy * m).sum())

    # global camera translation = spatial median of net flow (background dominates)
    gdx = float(np.median(net[..., 0])) / npairs
    gdy = float(np.median(net[..., 1])) / npairs
    # zoom: mean radial component of net flow (>0 push-in / expand)
    yy, xx = np.mgrid[0:H, 0:W]
    rx, ry = xx - W / 2, yy - H / 2
    rn = np.hypot(rx, ry) + 1e-6
    zoom = float(np.mean((net[..., 0] * rx + net[..., 1] * ry) / rn)) / npairs

    cells = []
    for r in range(rows):
        for c in range(cols):
            if wsum[r, c] < 1e-6:
                continue
            dx = wvx[r, c] / wsum[r, c]      # energy-weighted mean velocity (px/frame)
            dy = wvy[r, c] / wsum[r, c]
            speed = float(np.hypot(dx, dy))
            rdx, rdy = dx - gdx, dy - gdy     # residual vs camera
            rspeed = float(np.hypot(rdx, rdy))
            cells.append(dict(r=r, c=c, dx=dx, dy=dy, speed=speed,
                              rdx=rdx, rdy=rdy, rspeed=rspeed,
                              energy=wsum[r, c] / npairs,
                              cx=(c + 0.5) / cols, cy=(r + 0.5) / rows))

    movers = sorted([c for c in cells if c["rspeed"] >= a.min_speed],
                    key=lambda d: -d["rspeed"] * d["energy"] ** 0.5)[:a.top]
    for m in movers:
        m["direction"] = label_dir(m["dx"], m["dy"])
        m["direction_vs_camera"] = label_dir(m["rdx"], m["rdy"])

    cam = {"pan": label_dir(gdx, gdy), "pan_px_per_frame": [round(gdx, 3), round(gdy, 3)],
           "zoom": "push-in/expand" if zoom > 0.05 else ("pull-out/contract" if zoom < -0.05 else "none"),
           "zoom_score": round(zoom, 3)}

    digest = {
        "video": a.video, "duration": round(dur, 2), "frames": a.n, "grid": a.grid,
        "camera": cam,
        "movers": [{"at_xy": [round(m["cx"], 2), round(m["cy"], 2)],
                    "direction": m["direction"],
                    "direction_vs_camera": m["direction_vs_camera"],
                    "speed_px_per_frame": round(m["speed"], 2),
                    "independent_speed": round(m["rspeed"], 2)} for m in movers],
    }

    # 5: annotate a mid-frame
    out_annot = a.annotate or (a.video + ".motion.png")
    midp = grab(a.video, dur / 2, 0, tmp, "mid")       # full-res mid frame
    mid = cv2.imread(midp)
    MH, MW = mid.shape[:2]
    sx, sy = MW / W, MH / H
    for m in movers:
        x = int(m["cx"] * MW); y = int(m["cy"] * MH)
        ex = int(x + m["dx"] * sx * 18); ey = int(y + m["dy"] * sy * 18)
        cv2.arrowedLine(mid, (x, y), (ex, ey), (0, 0, 255), 6, tipLength=0.35)
        cv2.putText(mid, m["direction"], (x + 8, y - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    1.1, (0, 255, 255), 3, cv2.LINE_AA)
    cv2.imwrite(out_annot, mid)
    digest["annotated"] = out_annot

    # optional VLM naming + plausibility judgment (CV did the perception)
    if a.vlm and movers:
        cfg = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "config.json")))
        key = cfg.get("claudeKey") or cfg.get("anthropicKey")
        firstp = grab(a.video, 0.1, 0, tmp, "first")
        lastp = grab(a.video, max(0.0, dur - 0.1), 0, tmp, "last")
        fimg, limg = cv2.imread(firstp), cv2.imread(lastp)
        verdicts = []
        for m in movers[:4]:
            # crop a generous context window (>=32% of frame) centred on the mover,
            # so the object is identifiable rather than an ambiguous tile
            half_w = max(int(0.16 * MW), int(0.6 / cols * MW))
            half_h = max(int(0.16 * MH), int(0.6 / rows * MH))
            cxp, cyp = int(m["cx"] * MW), int(m["cy"] * MH)
            x0, y0 = max(0, cxp - half_w), max(0, cyp - half_h)
            x1, y1 = min(MW, cxp + half_w), min(MH, cyp + half_h)
            def enc(im):
                crop = im[y0:y1, x0:x1]
                ok, buf = cv2.imencode(".jpg", crop)
                return base64.b64encode(buf).decode()
            prompt = (
                f"Two crops of the SAME region of a video frame: FIRST frame then LAST frame "
                f"(the region between them changed). Context: {a.context}. "
                + (f"NOTE — intentionally stylized, mark plausible=true ONLY if the moving thing IS this: {a.premise}. " if a.premise else "")
                + f"Optical flow measured the moving thing here going {m['direction']} (independent of camera). "
                "Identify the single object that actually moved between FIRST and LAST. "
                "If it is a kind of object with a CONVENTIONAL direction for this situation "
                "(a car window rolls DOWN to interact at a drive-thru; a door opens to enter; a cup fills when served; "
                "a person leans toward what they address), STATE that expected direction, then say whether the measured "
                f"direction ({m['direction']}) MATCHES or CONTRADICTS it. Set plausible=false on any contradiction; "
                "do NOT invent an alternate explanation to make it plausible. "
                'Return STRICT JSON {"object":str,"measured":str,"expected_direction":str,"plausible":bool,"why":str,"confidence":"low|med|high"}.')
            content = [{"type": "text", "text": prompt},
                       {"type": "text", "text": "FIRST:"},
                       {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": enc(fimg)}},
                       {"type": "text", "text": "LAST:"},
                       {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": enc(limg)}}]
            req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                data=json.dumps({"model": "claude-opus-4-5-20251101", "max_tokens": 400,
                                 "messages": [{"role": "user", "content": content}]}).encode(),
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            try:
                txt = json.load(urllib.request.urlopen(req))["content"][0]["text"]
                v = json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
            except Exception as e:
                v = {"error": str(e)}
            v["at_xy"] = [round(m["cx"], 2), round(m["cy"], 2)]
            v["measured_direction"] = m["direction"]
            verdicts.append(v)
        digest["vlm"] = verdicts

    if a.json:
        print(json.dumps(digest, indent=2))
        return
    print(f"\n  motion-direction · {os.path.basename(a.video)} · {dur:.1f}s")
    print(f"  camera: pan {cam['pan']} {cam['pan_px_per_frame']}  zoom {cam['zoom']} ({cam['zoom_score']})")
    if not movers:
        print("  no independent movers above threshold")
    for m in movers:
        print(f"   • ({m['cx']:.2f},{m['cy']:.2f})  {m['direction']:<10} "
              f"speed {m['speed']:.2f}px/f  indep {m['rspeed']:.2f}  vs-cam {m['direction_vs_camera']}")
    if digest.get("vlm"):
        print("  VLM:")
        for v in digest["vlm"]:
            if "error" in v:
                print(f"   ! {v['error']}")
            else:
                flag = "OK " if v.get("plausible") else "ODD"
                print(f"   [{flag}] {v.get('object','?')} moving {v.get('direction','?')} — {v.get('why','')[:90]}")
    print(f"  annotated → {out_annot}\n")


if __name__ == "__main__":
    main()
