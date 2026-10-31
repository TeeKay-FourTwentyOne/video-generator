#!/usr/bin/env python3
"""Verify a GENERATION native draft against its saved integer-frame recipe."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import wave

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--scale", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    root = args.workspace.resolve()
    scale = args.scale
    width, height, top, bottom = 1080 * scale, 1920 * scale, 555 * scale, 1365 * scale
    cfg = json.loads((root / "edit/render.json").read_text())
    movie = root / "final" / args.version / "film.mp4"
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames",
        "-show_streams", "-show_format", "-of", "json", str(movie)]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    assert (video["width"], video["height"], video["r_frame_rate"], video["pix_fmt"],
            video["profile"], int(video["nb_read_frames"])) == (width, height, "30/1", "yuv420p", "High", cfg["frames"])
    assert all(video.get(k) == "bt709" for k in ["color_space", "color_transfer", "color_primaries"])
    assert video.get("color_range") == "tv"
    assert audio["codec_name"] == "aac" and audio["sample_rate"] == "48000" and audio["channels"] == 2
    assert abs(float(probe["format"]["duration"]) - cfg["frames"] / 30) < .001
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-i", str(movie),
        "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], stdout=subprocess.PIPE)
    frame_bytes = width * height * 3
    outside_max, count, osd_errors = 0, 0, []
    blue = []
    # Interior samples from the P's top and stem, and the L's stem and foot.
    points = [(54, 26), (58, 26), (62, 26), (54, 34), (54, 42),
              (78, 26), (78, 34), (78, 42), (82, 50), (86, 50)]
    while True:
        raw = proc.stdout.read(frame_bytes)
        if not raw:
            break
        assert len(raw) == frame_bytes, "Partial decoded frame"
        x = np.frombuffer(raw, np.uint8).reshape(height, width, 3)
        outside_max = max(outside_max, int(x[:top].max()), int(x[bottom:].max()))
        item = next(i for i in cfg["timeline"] if i["frame"] <= count < i["frame"] + i["frames"])
        if item["kind"] == "copy":
            white = np.mean([np.min(x[top + round(y * 810 * scale / 480), round(px * width / 640)]) > 230
                             for px, y in points])
            expected = count - item["frame"] < 60
            if (white >= .8) != expected:
                osd_errors.append({"frame": count, "expected": expected, "whiteFraction": float(white)})
        elif item["kind"] == "blue":
            blue.append(x[height // 2, width // 2].tolist())
        count += 1
    assert proc.wait() == 0
    assert count == cfg["frames"] and outside_max == 0
    assert not osd_errors, f"PLAY timing mismatches: {osd_errors[:4]}"
    assert max(abs(v - target) for pixel in blue for v, target in zip(pixel, [26, 26, 168])) <= 5
    with wave.open(str(root / "audio/master.wav")) as wav:
        assert wav.getnchannels() == 2 and wav.getframerate() == 48000
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), "<i2").reshape(-1, 2)
    assert len(pcm) == cfg["frames"] * 1600 and np.array_equal(pcm[:, 0], pcm[:, 1])
    for item in cfg["timeline"]:
        if item["kind"] == "blue":
            assert not np.any(pcm[item["frame"] * 1600:(item["frame"] + item["frames"]) * 1600])
    encoded = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(movie),
        "-vn", "-f", "f32le", "-ac", "2", "pipe:1"])
    channels = np.frombuffer(encoded, "<f4").reshape(-1, 2)
    assert np.max(np.abs(channels[:, 0] - channels[:, 1])) < 1e-6
    result = {"schemaVersion": 1, "sha256": hashlib.sha256(movie.read_bytes()).hexdigest(),
        "frames": count, "fps": 30, "seconds": count / 30, "dimensions": [width, height],
        "fullDecode": True, "outsideBlackMax": outside_max, "playTimingErrors": osd_errors,
        "blueDecodedCenter": blue[0], "blueColorTolerance": 5,
        "pcmSamples": len(pcm), "pcmBlueDigitalZero": True, "dualMonoPcmAndAac": True,
        "audioListening": "not-claimed", "artisticApproval": False,
        "note": "AAC may have boundary ringing; blue is exact digital zero in the PCM master. Color tolerance reflects lossy YUV encoding."}
    (root / "qa" / f"{args.version}-technical.json").write_text(json.dumps(result, indent=2) + "\n")
    (root / "qa" / f"{args.version}-probe.json").write_text(json.dumps(probe, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
