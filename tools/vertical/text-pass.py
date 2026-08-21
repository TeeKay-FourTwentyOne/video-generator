#!/usr/bin/env python3
"""Text pass for vertical-series episodes: captions + title/end stamps.

All text is rendered as full-frame transparent PNG sprites via PIL (local ffmpeg
has no drawtext), then overlaid in a single ffmpeg run with exclusive-bound
enable windows: enable='gte(t,IN)*lt(t,OUT)'.

Modes:
  # Validate the title style on a still (recreates the canon title treatment):
  python3 tools/vertical/text-pass.py --series series/the-lodger \
      --demo-stamp series/the-lodger/canon/env_house_ext_dusk_rain.png out.png \
      --ep 1 --ep-title "The Stranger at Dusk"

  # Validate caption styles (dialogue + VO) on a still:
  python3 tools/vertical/text-pass.py --series series/the-lodger \
      --demo-captions series/the-lodger/canon/env_entry_hall.png out.png

  # Burn a picture-locked video from a manifest:
  python3 tools/vertical/text-pass.py --series series/the-lodger \
      --manifest data/workspace/lodger-ep01/episode.json \
      --video picture_lock.mp4 --out captioned.mp4

Caption events come from manifest `captions[]` (explicit t_in/t_out win). VO
entries without explicit captions are auto-derived from `vo[]` (italic, duration
from a reading-speed heuristic). Dialogue captions must be listed explicitly in
`captions[]` (timed from transcribe data at gate time).
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ---------- font handling ----------

def load_face(path, size, want_italic=False):
    """Load a font face from a TTF/TTC; for TTCs, hunt the italic face by name."""
    if not want_italic:
        return ImageFont.truetype(path, size)
    for idx in range(8):
        try:
            f = ImageFont.truetype(path, size, index=idx)
        except OSError:
            break
        name = " ".join(f.getname()).lower()
        if "italic" in name and "black" not in name:
            return f
    return ImageFont.truetype(path, size)  # fallback: regular


# ---------- sprite rendering ----------

def _draw_soft(layer_draw, shadow_draw, pos, text, font, fill, shadow):
    x, y = pos
    shadow_draw.text((x + shadow["dx"], y + shadow["dy"]), text, font=font,
                     fill=(0, 0, 0, shadow["alpha"]))
    layer_draw.text((x, y), text, font=font, fill=tuple(fill) + (255,))


def _center_x(draw, text, font, W, tracking=0):
    if tracking:
        widths = [draw.textbbox((0, 0), c, font=font)[2] for c in text]
        return (W - (sum(widths) + tracking * (len(text) - 1))) / 2, widths
    bb = draw.textbbox((0, 0), text, font=font)
    return (W - (bb[2] - bb[0])) / 2 - bb[0], None


def _tracked_text(layer_draw, shadow_draw, x, y, text, font, fill, shadow, tracking, widths):
    cx = x
    for ch, w in zip(text, widths):
        _draw_soft(layer_draw, shadow_draw, (cx, y), ch, font, fill, shadow)
        cx += w + tracking


def wrap_text(text, max_chars):
    words, lines, cur = text.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_text_sprite(size, lines, font, style, y_center):
    """Full-frame RGBA sprite with soft-shadowed centered text lines."""
    W, H = size
    sh = style["shadow"]
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    ld, sd = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    asc, desc = font.getmetrics()
    line_h = asc + desc + int(H * style.get("line_spacing_frac", 0.012))
    total_h = line_h * len(lines)
    y = y_center - total_h / 2
    for line in lines:
        x, _ = _center_x(ld, line, font, W)
        _draw_soft(ld, sd, (x, y), line, font, style["fill"], sh)
        y += line_h
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sh["blur"])))
    out.alpha_composite(layer)
    return out


def render_title_sprite(size, cfg, title_lines):
    """Series title stamp sprite (main + sub line), per locked treatment."""
    W, H = size
    ts = cfg["title_style"]
    sh = cfg["caption_style"]["shadow"]
    main_font = load_face(ts["font"], int(H * ts["main_size_frac"]))
    sub_font = load_face(ts["font"], int(H * ts["sub_size_frac"]))
    tracking = int(H * ts["tracking_frac"])
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", size, (0, 0, 0, 0))
    ld, sd = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)

    main, sub = title_lines[0], title_lines[1] if len(title_lines) > 1 else None
    for text, font, yfrac, trk in ((main, main_font, ts["y_main_frac"], tracking),
                                   (sub, sub_font, ts["y_sub_frac"], 0)):
        if not text:
            continue
        asc, desc = font.getmetrics()
        y = int(H * yfrac) - (asc + desc) / 2
        x, widths = _center_x(ld, text, font, W, trk)
        if widths:
            _tracked_text(ld, sd, x, y, text, font, ts["fill"], sh, trk, widths)
        else:
            _draw_soft(ld, sd, (x, y), text, font, ts["fill"], sh)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(sh["blur"])))
    out.alpha_composite(layer)
    return out


def render_caption_sprite(size, text, cfg, italic):
    cs = cfg["caption_style"]
    H = size[1]
    font = load_face(cs["font"], int(H * cs["size_frac"]), want_italic=italic and cs["vo_italic"])
    lines = wrap_text(text, cs["max_chars"])
    return render_text_sprite(size, lines, font, cs, int(H * cs["y_center_frac"]))


# ---------- caption event derivation ----------

def vo_duration(text):
    """Reading-speed heuristic, seconds."""
    return max(1.4, min(4.5, 0.8 + 0.055 * len(text)))


def caption_events(manifest):
    """[{text, t_in, t_out, italic}] — explicit captions win; VO auto-derived.

    VO caption length prefers the measured audio duration (manifest vo[].duration)
    over the reading-speed heuristic. All captions share one band, so a final
    collision pass clamps each event to end before the next one begins."""
    events = list(manifest.get("captions", []))
    covered = {e.get("source") for e in events if e.get("source")}
    for vo in manifest.get("vo", []):
        if vo["id"] in covered or vo.get("t") is None:
            continue
        dur = (vo["duration"] + 0.25) if vo.get("duration") else vo_duration(vo["text"])
        events.append({"text": vo["text"], "t_in": vo["t"],
                       "t_out": round(vo["t"] + dur, 2),
                       "italic": True, "source": vo["id"]})
    events.sort(key=lambda e: e["t_in"])
    for a, b in zip(events, events[1:]):
        if a["t_out"] > b["t_in"]:
            a["t_out"] = round(max(a["t_in"] + 0.6, b["t_in"] - 0.04), 2)
    return events


# ---------- modes ----------

def demo_stamp(cfg, plate, out, ep, ep_title):
    im = Image.open(plate).convert("RGBA")
    lines = [cfg["display_title"], f"Episode {ep_num_words(ep)} — {ep_title}" if ep_title else None]
    im.alpha_composite(render_title_sprite(im.size, cfg, lines))
    im.convert("RGB").save(out, quality=92)
    print("wrote", out)


def ep_num_words(n):
    words = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
             8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen",
             14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
             19: "Nineteen", 20: "Twenty"}
    return words.get(n, str(n))


def demo_captions(cfg, plate, out):
    im = Image.open(plate).convert("RGBA")
    im.alpha_composite(render_caption_sprite(
        im.size, "One condition. No one enters my room.", cfg, italic=False))
    im.convert("RGB").save(out, quality=92)
    print("wrote", out, "(dialogue style)")
    base, ext = os.path.splitext(out)
    im2 = Image.open(plate).convert("RGBA")
    im2.alpha_composite(render_caption_sprite(
        im2.size, "Nobody pays in gold.", cfg, italic=True))
    im2.convert("RGB").save(base + "_vo" + ext, quality=92)
    print("wrote", base + "_vo" + ext, "(VO italic style)")


def burn_video(cfg, manifest, video, out):
    W, H = cfg["format"]["w"], cfg["format"]["h"]
    scratch = os.path.join(os.path.dirname(os.path.abspath(
        manifest["_path"])), "scratch", "text-pass")
    os.makedirs(scratch, exist_ok=True)

    evs = caption_events(manifest)
    tw = (manifest.get("stamps") or {}).get("title_window")
    if tw:
        for ev in evs:
            # auto-derived VO captions share the band with the title stamp —
            # clamp them out of its window (explicit captions are left alone)
            if str(ev.get("source", "")).startswith("V") and \
                    ev["t_in"] < tw[1] and ev["t_out"] > tw[0]:
                if ev["t_in"] < tw[0]:
                    ev["t_out"] = max(ev["t_in"] + 0.6, tw[0])
                else:
                    ev["t_in"] = tw[1]
                    ev["t_out"] = max(ev["t_out"], tw[1] + 0.8)

    overlays = []  # (png_path, t_in, t_out)
    for i, ev in enumerate(evs):
        sp = os.path.join(scratch, f"cap{i:03d}.png")
        render_caption_sprite((W, H), ev["text"], cfg, ev.get("italic", False)).save(sp)
        overlays.append((sp, ev["t_in"], ev["t_out"]))

    stamps = manifest.get("stamps", {})
    if stamps.get("title_window"):
        sp = os.path.join(scratch, "title.png")
        render_title_sprite((W, H), cfg, stamps["title_lines"]).save(sp)
        overlays.append((sp, stamps["title_window"][0], stamps["title_window"][1]))

    ec = stamps.get("end_card") or {}
    if ec.get("text") and ec.get("window"):
        ts = cfg["title_style"]
        font = load_face(ts["font"], int(H * ts["sub_size_frac"] * 1.5))
        sty = dict(cfg["caption_style"], fill=ts["fill"])
        sp = os.path.join(scratch, "endcard.png")
        render_text_sprite((W, H), wrap_text(ec["text"], 34), font, sty,
                           int(H * 0.5)).save(sp)
        overlays.append((sp, ec["window"][0], ec["window"][1]))

    if not overlays:
        print("no text events; nothing to do")
        return

    cmd = ["ffmpeg", "-y", "-i", video]
    for sp, _, _ in overlays:
        cmd += ["-i", sp]
    parts, cur = [], "0:v"
    for i, (_, t_in, t_out) in enumerate(overlays):
        nxt = f"v{i+1}"
        parts.append(f"[{cur}][{i+1}:v]overlay=0:0:enable='gte(t,{t_in})*lt(t,{t_out})'[{nxt}]")
        cur = nxt
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{cur}]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", out]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print("wrote", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--demo-stamp", nargs=2, metavar=("PLATE", "OUT"))
    ap.add_argument("--demo-captions", nargs=2, metavar=("PLATE", "OUT"))
    ap.add_argument("--ep", type=int, default=1)
    ap.add_argument("--ep-title", default=None)
    ap.add_argument("--manifest")
    ap.add_argument("--video")
    ap.add_argument("--out")
    args = ap.parse_args()

    with open(os.path.join(args.series, "series-config.json")) as f:
        cfg = json.load(f)

    if args.demo_stamp:
        demo_stamp(cfg, *args.demo_stamp, ep=args.ep, ep_title=args.ep_title)
    elif args.demo_captions:
        demo_captions(cfg, *args.demo_captions)
    elif args.manifest and args.video and args.out:
        with open(args.manifest) as f:
            manifest = json.load(f)
        manifest["_path"] = os.path.abspath(args.manifest)
        burn_video(cfg, manifest, args.video, args.out)
    else:
        ap.error("pick a mode: --demo-stamp / --demo-captions / --manifest+--video+--out")


if __name__ == "__main__":
    sys.exit(main())
