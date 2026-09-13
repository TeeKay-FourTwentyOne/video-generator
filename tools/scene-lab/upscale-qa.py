#!/usr/bin/env python3
"""Local technical and visual QA artifacts for a frame-preserving 2x upscale."""
import argparse
import hashlib
import importlib.metadata
import json
import struct
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def run(args):
    result = subprocess.run(args, capture_output=True, check=True)
    return result


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def timestamps(path):
    data = json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_frames",
        "-show_entries", "frame=best_effort_timestamp_time,duration_time", "-of", "json", str(path),
    ]).stdout)
    return [(frame["best_effort_timestamp_time"], frame.get("duration_time")) for frame in data["frames"]]


def audio_packets(path):
    return json.loads(run([
        "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_packets",
        "-show_data_hash", "sha256", "-show_entries", "packet=pts,dts,duration,size,data_hash,side_data_list",
        "-of", "json", str(path),
    ]).stdout)["packets"]


def audio_hash(path, copy):
    return run([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
        "-c:a", "copy" if copy else "pcm_s24le", "-f", "hash", "-hash", "sha256", "-",
    ]).stdout.decode().strip().split("=", 1)[1]


def mp4_atoms(path):
    atoms = []
    with path.open("rb") as stream:
        while header := stream.read(8):
            size, kind = struct.unpack(">I4s", header)
            header_size = 8
            if size == 1:
                size = struct.unpack(">Q", stream.read(8))[0]
                header_size = 16
            atoms.append(kind.decode("ascii", errors="replace"))
            if not size:
                break
            if size < header_size:
                raise ValueError("Invalid MP4 atom size")
            stream.seek(size - header_size, 1)
    return atoms


def proxies(path):
    data = run([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
        "-vf", "scale=320:180:flags=area", "-pix_fmt", "rgb24", "-fps_mode", "passthrough",
        "-f", "rawvideo", "-",
    ]).stdout
    return np.frombuffer(data, dtype=np.uint8).reshape(-1, 180, 320, 3)


def summary(values):
    return {"mean": float(np.mean(values)), "median": float(np.median(values)),
            "p95": float(np.percentile(values, 95)), "max": float(np.max(values))}


def proxy_comparison(source, output):
    a, b = proxies(source), proxies(output)
    if a.shape != b.shape:
        raise ValueError("Proxy frame counts differ")
    spatial, residual_change, a_motion, b_motion = [], [], [], []
    previous = None
    for n in range(len(a)):
        x, y = a[n].astype(np.float32), b[n].astype(np.float32)
        residual = y - x
        spatial.append(float(np.abs(residual).mean()))
        if previous is not None:
            residual_change.append(float(np.abs(residual - previous).mean()))
            a_motion.append(float(np.abs(x - a[n - 1]).mean()))
            b_motion.append(float(np.abs(y - b[n - 1]).mean()))
        previous = residual
    motion_ratios = np.array(b_motion) / np.maximum(a_motion, .001)
    joins = [{"frame": n, "sourceDelta": a_motion[n - 1], "upscaleDelta": b_motion[n - 1],
              "ratio": float(motion_ratios[n - 1])} for n in [96, 192, 288, 384, 480]]
    return {
        "method": "Every decoded frame at 320x180 RGB; absolute differences in 0-255 units. Diagnostic only, not a proof of perceptual quality.",
        "spatialDifference": summary(spatial), "temporalResidualChange": summary(residual_change),
        "sourceAdjacentDifference": summary(a_motion), "upscaleAdjacentDifference": summary(b_motion),
        "adjacentDifferenceRatio": summary(motion_ratios), "joins": joins,
    }


def extract_frame(path, frame, output):
    run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-i", str(path),
         "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", str(output)])


def visual_artifacts(source, output, folder):
    indices = [0, 60, 110, 150, 190, 225, 265, 285, 305, 335, 370, 400, 440, 480, 530, 575]
    selection = "+".join(f"eq(n\\,{n})" for n in indices)
    run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-i", str(output),
         "-vf", f"select={selection},scale=480:270:flags=lanczos,tile=4x4", "-frames:v", "1",
         str(folder / "full-tour-contact.png")])
    extract_frame(output, 0, folder.parent / "poster-4k.png")
    for frame, name in [(150, "library"), (335, "return-pan"), (530, "orrery")]:
        src_png, out_png = folder / f"{name}-1080.png", folder / f"{name}-4k.png"
        extract_frame(source, frame, src_png)
        extract_frame(output, frame, out_png)
        src = Image.open(src_png).convert("RGB").resize((3840, 2160), Image.Resampling.LANCZOS)
        out = Image.open(out_png).convert("RGB")
        board = Image.new("RGB", (1920, 1120), "#141821")
        draw = ImageDraw.Draw(board)
        for column, (image, label) in enumerate([(src, "1080p / Lanczos reference"), (out, "4K / native AI 2x")]):
            draw.text((column * 960 + 20, 12), f"{label} / frame {frame}", fill="white", font_size=22)
            board.paste(image.crop((1440, 540, 2400, 1620)), (column * 960, 40))
        board.save(folder / f"{name}-native-crop-comparison.png")
    # Dense native-pixel crops during two camera moves, including book spines and rings.
    for start, name, x, y in [(332, "bookshelf-motion", 1760, 500), (523, "orrery-motion", 1760, 600)]:
        run(["ffmpeg", "-v", "error", "-nostdin", "-n", "-i", str(output),
             "-vf", f"select=between(n\\,{start}\\,{start+7}),crop=640:480:{x}:{y},tile=4x2",
             "-frames:v", "1", str(folder / f"{name}.png")])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    folder = output.parent / "qa"
    folder.mkdir(exist_ok=True)
    source_info, output_info = probe(source), probe(output)
    v = next(s for s in output_info["streams"] if s["codec_type"] == "video")
    a = next(s for s in output_info["streams"] if s["codec_type"] == "audio")
    source_sha = digest(source)
    checks = {"approvedSourceHash": source_sha == "bd325ccef807f0b50a6d1d4fae1d9e6d6e2f6f63df6cdc781ef213384734e356",
              "uhd2160p": (v["width"], v["height"]) == (3840, 2160),
              "576frames": v["nb_frames"] == "576", "24fps": v["avg_frame_rate"] == "24/1",
              "24seconds": float(v["duration"]) == 24 and float(a["duration"]) == 24,
              "audio48kStereo": a["sample_rate"] == "48000" and a["channels"] == 2,
              "frameTimestampsUnchanged": timestamps(source) == timestamps(output),
              "audioPacketsAndTimestampsUnchanged": audio_packets(source) == audio_packets(output),
              "audioBitstreamUnchanged": audio_hash(source, True) == audio_hash(output, True),
              "decodedAudioUnchanged": audio_hash(source, False) == audio_hash(output, False)}
    atoms = mp4_atoms(output)
    checks["faststart"] = atoms.index("moov") < atoms.index("mdat")
    print(json.dumps(checks, indent=2), flush=True)
    scan = run([
        "ffmpeg", "-hide_banner", "-i", str(output),
        "-vf", "blackdetect=d=0.08:pix_th=0.1,freezedetect=n=-50dB:d=0.5",
        "-f", "null", "-",
    ]).stderr.decode()
    with (folder / "decode-scan.log").open("x") as stream:
        stream.write(scan)
    detections = [line for line in scan.splitlines() if any(word in line for word in ["black_start", "freeze_start", "freeze_duration"])]
    checks["noBlackOrFrozenSegments"] = not detections
    diagnostics = proxy_comparison(source, output)
    visual_artifacts(source, output, folder)
    report = {
        "status": "technical-qa-complete; visual inspection pending", "technicalPass": all(checks.values()),
        "source": str(source), "sourceSHA256": source_sha, "output": str(output), "outputSHA256": digest(output),
        "sourceProbe": source_info, "outputProbe": output_info, "checks": checks,
        "model": {"name": "realesr-animevideov3-x2", "wrapperModelID": 0, "cliModelID": 1,
                  "nativeScale": 2, "tile": 256, "tta": False},
        "encoding": {"codec": "libx264", "crf": 16, "preset": "slow", "pixelFormat": "yuv420p", "audio": "copy", "faststart": True},
        "dependencies": {name: importlib.metadata.version(name) for name in ["realesrgan-ncnn-py", "pillow", "numpy", "opencv-python"]},
        "diagnostics": diagnostics, "blackFreezeDetections": detections,
        "audioSHA256": audio_hash(output, True), "decodedAudioSHA256": audio_hash(output, False),
        "paidRequests": 0, "additionalGenerationCostUSD": 0, "footageUploaded": False,
        "publication": {"baseCutApprovedByUser": True, "published": False},
    }
    write_json(output.parent / "manifest.json", report)
    print(json.dumps({"technicalPass": report["technicalPass"], "output": str(output), "bytes": output.stat().st_size, "diagnostics": diagnostics}, indent=2))
    if not report["technicalPass"]:
        raise SystemExit("Technical QA failed; inspect manifest before delivery")


if __name__ == "__main__":
    main()
