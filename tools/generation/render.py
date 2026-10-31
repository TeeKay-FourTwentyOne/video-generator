#!/usr/bin/env python3
"""GENERATION: frame-addressed camcorder preparation and literal dub passes.

Run with the already provisioned Pillow/NumPy/SciPy/OpenCV Python environment.
All inputs, outputs and intermediate generations live in the named workspace.
Nothing submits a provider request. Earlier renders are never overwritten.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, signal


FPS, RATE = 30, 48000
SIZE = (640, 480)
OUT = (1080, 1920)
WINDOW = (1080, 810)
Y = 555


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace")[-4000:])
    return result.stdout


def json_write(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def encoder(path, width=640, height=480, dub=False):
    if path.exists():
        raise FileExistsError(path)
    flags = (["-b:v", "1200k", "-g", "15", "-bf", "0"] if dub else
             ["-crf", "16", "-g", "30"])
    conversion = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"
    if (width, height) == OUT:
        # An odd vertical window edge shares a 4:2:0 chroma cell with black.
        # Neutralize that boundary cell and retain black footroom outside the
        # window so decoded margins remain black after H.264 quantization.
        conversion += (",geq=lum='if(between(Y,555,1364),p(X,Y),0)'"
                       ":cb='if(between(Y,278,681),p(X,Y),128)'"
                       ":cr='if(between(Y,278,681),p(X,Y),128)'")
    return subprocess.Popen([
        "ffmpeg", "-v", "error", "-nostdin", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(FPS), "-i", "pipe:0", "-an",
        "-vf", conversion, "-c:v", "libx264", "-preset", "fast", "-profile:v", "high", *flags,
        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-color_range", "tv", "-movflags", "+faststart", str(path)
    ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def finish(proc):
    if proc.stdin:
        proc.stdin.close()
    error = proc.stderr.read() if proc.stderr else b""
    if proc.wait():
        raise RuntimeError(error.decode(errors="replace")[-4000:])


def frames(path, count, start=0, prepared=False, transform_log=None, wide_registration=False):
    filters = f"trim=start={start},setpts=PTS-STARTPTS,fps={FPS}"
    width, height = (640, 480) if prepared else (960, 540)
    if not prepared:
        filters += ",scale=960:540:flags=bilinear"
    proc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-vf", filters,
        "-frames:v", str(count), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    reference = None
    orb = cv2.ORB_create(nfeatures=1600, fastThreshold=12)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    background = np.zeros((540, 960), np.uint8)
    background[:150] = 255
    background[:, :105] = 255
    background[:, 855:] = 255
    try:
        for index in range(count):
            raw = proc.stdout.read(width * height * 3)
            if len(raw) != width * height * 3:
                raise RuntimeError(f"Short decode at frame {index}: {path}")
            frame = np.frombuffer(raw, np.uint8).reshape(height, width, 3).copy()
            if not prepared:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                if reference is None:
                    reference = frame.copy()
                    reference_keypoints, reference_descriptors = orb.detectAndCompute(gray, background)
                matrix = np.array([[1., 0., 0.], [0., 1., 0.]])
                inliers = 0
                keypoints, descriptors = orb.detectAndCompute(gray, background)
                if descriptors is not None and reference_descriptors is not None:
                    pairs = matcher.knnMatch(descriptors, reference_descriptors, k=2)
                    matches = [p[0] for p in pairs if len(p) == 2 and p[0].distance < .72 * p[1].distance]
                    if len(matches) >= 14:
                        current = np.float32([keypoints[m.queryIdx].pt for m in matches])
                        fixed = np.float32([reference_keypoints[m.trainIdx].pt for m in matches])
                        estimated, mask = cv2.estimateAffinePartial2D(current, fixed,
                            method=cv2.RANSAC, ransacReprojThreshold=1.8)
                        if estimated is not None and int(mask.sum()) >= 12:
                            scale = float(np.hypot(estimated[0, 0], estimated[0, 1]))
                            limits = (.65, 1.5, 260) if wide_registration else (.90, 1.10, 70)
                            if limits[0] < scale < limits[1] and np.max(np.abs(estimated[:, 2])) < limits[2]:
                                matrix, inliers = estimated, int(mask.sum())
                aligned = cv2.warpAffine(frame, matrix, (960, 540), flags=cv2.INTER_LINEAR)
                valid = cv2.warpAffine(np.full((540, 960), 255, np.uint8), matrix,
                                      (960, 540), flags=cv2.INTER_NEAREST)
                aligned[valid == 0] = reference[valid == 0]
                if transform_log is not None:
                    transform_log.append({"frame": index, "matrix": matrix.tolist(), "inliers": inliers})
                frame = cv2.resize(aligned[:, 120:840], SIZE, interpolation=cv2.INTER_LINEAR)
            yield frame
        error = proc.stderr.read()
        if proc.wait():
            raise RuntimeError(error.decode(errors="replace"))
    finally:
        proc.stdout.close()
        if proc.poll() is None:
            proc.terminate()
            proc.wait()


def camera_base(frame):
    x = frame.astype(np.float32)
    luma = x @ np.array([.299, .587, .114], np.float32)
    streak = ndimage.gaussian_filter1d(np.maximum(luma - 240, 0), 6, axis=0)
    x += streak[:, :, None] * .4
    x *= np.array([1.012, 1.002, .982], np.float32)
    yy, xx = np.mgrid[-1:1:480j, -1:1:640j]
    x *= (1 - .045 * (xx * xx + yy * yy))[:, :, None]
    return np.clip(cv2.GaussianBlur(x, (0, 0), .4), 0, 255).astype(np.uint8)


def dub_frame(frame, n, rng, constants):
    x = cv2.cvtColor(frame.astype(np.float32) / 255, cv2.COLOR_RGB2YCrCb)
    x[:, :, 0] = ndimage.gaussian_filter1d(x[:, :, 0], constants["lumaBlur"], axis=1)
    for channel in (1, 2):
        x[:, :, channel] = np.roll(ndimage.gaussian_filter1d(
            x[:, :, channel], constants["chromaBlur"], axis=1), 1, axis=1)
    x[:, :, 0] = np.clip(x[:, :, 0], 0, 1) ** (1 / 1.03)
    x[:, :, 0] = x[:, :, 0] * (247 / 255) + 3 / 255
    x = cv2.cvtColor(x, cv2.COLOR_YCrCb2RGB)
    offsets = rng.normal(0, constants["jitter"] * 1.5 ** (n - 1), 480).astype(np.float32)
    maps_x = np.broadcast_to(np.arange(640, dtype=np.float32), (480, 640)).copy()
    maps_x += offsets[:, None]
    maps_y = np.broadcast_to(np.arange(480, dtype=np.float32)[:, None], (480, 640))
    x = cv2.remap(x, maps_x, maps_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    x += rng.normal(0, constants["noiseSigma"] * constants.get("noiseGrowth", 1.4) ** (n - 1) / 255,
                    (480, 640, 1)).astype(np.float32)
    for _ in range(3 + 2 * n):
        row, col = rng.integers(0, 478), rng.integers(0, 620)
        length = int(rng.integers(6, 38))
        x[row:row + int(rng.integers(1, 3)), col:col + length] += rng.uniform(.12, .45)
    for row in range(472, 480):
        x[row] = np.roll(x[row], int(rng.integers(2, 11)) * n, axis=0)
    return np.clip(x * 255, 0, 255).astype(np.uint8)


def play_mask():
    """Authored 5-by-7 block letters, 28 pixels high, with a two-pixel edge."""
    glyphs = {"P": [30, 17, 17, 30, 16, 16, 16],
              "L": [16, 16, 16, 16, 16, 16, 31],
              "A": [14, 17, 17, 31, 17, 17, 17],
              "Y": [17, 17, 10, 4, 4, 4, 4]}
    mask = Image.new("L", SIZE)
    draw = ImageDraw.Draw(mask)
    draw.polygon([(28, 30), (28, 46), (44, 38)], fill=255)
    for i, char in enumerate("PLAY"):
        for row, bits in enumerate(glyphs[char]):
            for col in range(5):
                if bits & (1 << (4 - col)):
                    x, y = 52 + i * 24 + col * 4, 24 + row * 4
                    draw.rectangle((x, y, x + 3, y + 3), fill=255)
    white = np.array(mask) > 0
    edge = ndimage.maximum_filter(white, size=5)
    return white, edge


PLAY, EDGE = play_mask()


def pad(frame, osd=False):
    if osd:
        frame[EDGE] = 0
        frame[PLAY] = 255
    canvas = np.zeros((OUT[1], OUT[0], 3), np.uint8)
    canvas[Y:Y + WINDOW[1]] = cv2.resize(frame, WINDOW, interpolation=cv2.INTER_LINEAR)
    return canvas


def prepare_video(root, shot, constants):
    name, count = shot["id"], shot["frames"]
    outdir = root / "renders" / name
    outdir.mkdir(parents=True, exist_ok=True)
    base = outdir / "base.mp4"
    if not base.exists():
        transforms = []
        enc = encoder(base)
        for frame in frames(root / shot["source"], count, shot.get("startSeconds", 0),
                            transform_log=transforms,
                            wide_registration=shot.get("wideRegistration", False)):
            enc.stdin.write(camera_base(frame).tobytes())
        finish(enc)
        json_write(outdir / "stabilization.json", {"method": "background ORB affine registration to first frame",
                   "trackingRaster": [960, 540], "transforms": transforms})
    previous = base
    chain = [{"pass": 0, "path": str(base.relative_to(root)), "sha256": digest(base)}]
    for n in range(1, shot["dubPasses"] + 1):
        output = outdir / f"dub-{n}.mp4"
        if not output.exists():
            rng = np.random.default_rng(1983000 + int(name[1:]) * 100 + n)
            enc = encoder(output, dub=True)
            for frame in frames(previous, count, prepared=True):
                enc.stdin.write(dub_frame(frame, n, rng, constants).tobytes())
            finish(enc)
        chain.append({"pass": n, "inputSha256": digest(previous),
                      "path": str(output.relative_to(root)), "sha256": digest(output)})
        previous = output
    result = outdir / "portrait.mp4"
    if not result.exists():
        enc = encoder(result, *OUT)
        playback_rng = np.random.default_rng(831980 + int(name[1:]))
        for index, frame in enumerate(frames(previous, count, prepared=True)):
            if shot["dubPasses"] and constants.get("playbackNoiseSigma", 0):
                # Playback electronics are downstream of the dubbed recording.
                # Add their fine noise before the clean deck OSD, so low-rate
                # intermediate coding does not turn every speck into a block.
                n = shot["dubPasses"]
                contrast = 1 - .1 * (n - 1)
                x = (frame.astype(np.float32) - 128) * contrast + 128
                sigma = constants["playbackNoiseSigma"] * 2 ** (n - 1)
                grain = playback_rng.normal(0, sigma, (480, 640, 1))
                rows = playback_rng.normal(0, sigma * .12, (480, 1, 1))
                frame = np.clip(x + grain + rows, 0, 255).astype(np.uint8)
            enc.stdin.write(pad(frame, index < 60).tobytes())
        finish(enc)
    json_write(outdir / "chain.json", {"source": shot, "constants": constants,
               "passes": chain, "portraitSha256": digest(result)})
    return result


def graphic(root, item):
    output = root / "renders" / (item["id"] + ".mp4")
    if output.exists():
        return output
    enc = encoder(output, *OUT)
    rng = np.random.default_rng(831983 + item["frame"])
    for i in range(item["frames"]):
        if item["kind"] == "blue":
            frame = np.full((480, 640, 3), (26, 26, 168), np.uint8)
        else:
            noise = rng.integers(0, 256, (480, 640), dtype=np.uint8)
            row = (130 + i * 5) % 460
            noise[row:row + 14] = np.roll(noise[row:row + 14], 33 + i * 2, axis=1)
            frame = np.repeat(noise[:, :, None], 3, axis=2)
        enc.stdin.write(pad(frame).tobytes())
    finish(enc)
    return output


def write_wav(path, data):
    if path.exists():
        raise FileExistsError(path)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        pcm = np.rint(np.clip(data, -1, 1) * 32767).astype("<i2")
        wav.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


def loudness(data, root, label):
    path = root / "audio" / (label + ".wav")
    write_wav(path, data)
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-af", "loudnorm=I=-23:TP=-1:LRA=20:print_format=json", "-f", "null", "-"],
        capture_output=True)
    log = result.stderr.decode(errors="replace")
    if result.returncode:
        raise RuntimeError(log[-2000:])
    report = json.loads(log[log.rfind("{"):log.rfind("}") + 1])
    json_write(root / "audio" / (label + ".measurement.json"), report)
    return float(report["input_i"])


def audio_shot(root, shot):
    n = round(shot["frames"] / FPS * RATE)
    data = run(["ffmpeg", "-v", "error", "-nostdin", "-ss", str(shot.get("startSeconds", 0)),
        "-i", str(root / shot["source"]), "-t", str(shot["frames"] / FPS),
        "-vn", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "pipe:1"])
    x = np.frombuffer(data, "<f4").astype(np.float64)
    if len(x) < n:
        raise ValueError("Source audio is shorter than the selected window")
    x = x[:n].copy()
    x = signal.sosfilt(signal.butter(3, [100, 8000], btype="bandpass", fs=RATE, output="sos"), x)
    # Gentle compression before any dub passes; it does not normalize the film.
    envelope = np.sqrt(ndimage.uniform_filter1d(x * x, size=960, mode="nearest") + 1e-12)
    x *= np.minimum(1, (.1 / np.maximum(envelope, 1e-8)) ** .35)
    measured = loudness(x, root, shot["id"] + "-camera")
    if not math.isfinite(measured):
        raise ValueError("Unexpected silent source audio")
    x *= 10 ** ((-23 - measured) / 20)
    rng = np.random.default_rng(198300 + int(shot["id"][1:]))
    for p in range(1, shot["dubPasses"] + 1):
        top = max(3800, 8000 - p * 700)
        x = signal.sosfilt(signal.butter(3, [100, top], btype="bandpass", fs=RATE, output="sos"), x)
        t = np.arange(n) / RATE
        # Integrate sinusoidal speed variation to make a small analog wow.
        depth = 2 ** (.06 * (1 + .2 * (p - 1)) / 12) - 1
        indices = np.arange(n) + depth * RATE / (2 * np.pi * .3) * np.sin(2 * np.pi * .3 * t)
        x = np.interp(np.clip(indices, 0, n - 1), np.arange(n), x)
        x = np.tanh(x * 1.03) / 1.03
        hiss = rng.normal(size=n)
        hiss = signal.sosfilt(signal.butter(1, 6000, fs=RATE, output="sos"), hiss)
        hiss /= np.sqrt(np.mean(hiss * hiss))
        x += hiss * 10 ** ((-48 + 4 * (p - 1)) / 20)
    if shot.get("voiceGainDb"):
        x *= 10 ** (shot["voiceGainDb"] / 20)
    # Catch isolated source transients on each copy, leaving the rising tape
    # floor and the relative program levels intact. No automatic makeup gain.
    limited = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "f64le",
        "-ar", str(RATE), "-ac", "1", "-i", "pipe:0", "-af",
        "alimiter=limit=0.79:attack=5:release=50:level=false:latency=true",
        "-f", "f64le", "pipe:1"], input=x.astype("<f8").tobytes(), capture_output=True)
    if limited.returncode:
        raise RuntimeError(limited.stderr.decode(errors="replace"))
    x = np.frombuffer(limited.stdout, "<f8").copy()
    if len(x) != n:
        raise ValueError("Limiter changed the stem duration")
    return x


def assemble(root, cfg, version):
    """Join portraits and protect the black boundary in the final encode."""
    folder = root / "final" / version
    folder.mkdir(parents=True, exist_ok=False)
    inputs = [root / "renders" / (item["shot"] + "/portrait.mp4" if item["kind"] == "copy"
                                  else item["id"] + ".mp4") for item in cfg["timeline"]]
    listing = folder / "concat.txt"
    listing.write_text("".join("file '" + str(p).replace("'", "'\\''") + "'\n" for p in inputs))
    boundary = ("geq=lum='if(between(Y,555,1364),p(X,Y),0)'"
                ":cb='if(between(Y,278,681),p(X,Y),128)'"
                ":cr='if(between(Y,278,681),p(X,Y),128)',"
                "addroi=x=0:y=544:w=1080:h=16:qoffset=-1,"
                "addroi=x=0:y=1360:w=1080:h=16:qoffset=-1")
    run(["ffmpeg", "-v", "error", "-nostdin", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-i", str(root / "audio/master.wav"),
         "-map", "0:v:0", "-map", "1:a:0", "-vf", boundary,
         "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-profile:v", "high",
         "-pix_fmt", "yuv420p", "-c:a", "aac",
         "-b:a", "192k", "-ar", "48000", "-ac", "2", "-aac_pns", "0",
         "-aac_is", "0", "-aac_ms", "1", "-aac_tns", "0", "-t", str(cfg["frames"] / FPS),
         "-movflags", "+faststart", str(folder / "film.mp4")])
    json_write(folder / "assembly.json", {"method": "CRF-16 concat with protected boundary macroblocks",
        "recipeSha256": digest(root / "edit/render.json"), "audioSha256": digest(root / "audio/master.wav"),
        "inputs": [{"path": str(p.relative_to(root)), "sha256": digest(p)} for p in inputs],
        "sha256": digest(folder / "film.mp4")})
    print(folder / "film.mp4", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("mode", choices=["video", "audio", "graphics", "assemble"])
    parser.add_argument("--shot")
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    root = args.workspace.resolve()
    cfg = json.loads((root / "edit/render.json").read_text())
    if args.mode == "video":
        for shot in cfg["shots"]:
            if args.shot and args.shot != shot["id"]:
                continue
            print(prepare_video(root, shot, cfg["dub"]), flush=True)
    elif args.mode == "graphics":
        for item in cfg["timeline"]:
            if item["kind"] != "copy":
                print(graphic(root, item), flush=True)
    elif args.mode == "assemble":
        if not args.version.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid version")
        assemble(root, cfg, args.version)
    else:
        track = np.zeros(round(cfg["frames"] / FPS * RATE), np.float64)
        shots = {s["id"]: s for s in cfg["shots"]}
        for item in cfg["timeline"]:
            start, count = item["frame"] * RATE // FPS, item["frames"] * RATE // FPS
            if item["kind"] == "copy":
                x = audio_shot(root, shots[item["shot"]])
            elif item["kind"] == "snow":
                rng = np.random.default_rng(1983 + item["frame"])
                x = rng.uniform(-1, 1, count)
                x *= .1 / np.sqrt(np.mean(x * x))
            else:
                x = np.zeros(count)
            write_wav(root / "audio" / (item["id"] + "-edit.wav"), x)
            track[start:start + count] = x
        # A ceiling only: no program-wide loudness normalization.
        ceiling = 10 ** (-1.2 / 20)
        peak = float(np.max(np.abs(track)))
        if peak > ceiling:
            raise ValueError(f"Peak {peak} exceeds ceiling; adjust the responsible stem")
        write_wav(root / "audio/master.wav", track)
        json_write(root / "audio/assembly.json", {"frames": cfg["frames"], "fps": FPS,
            "samples": len(track), "channels": 2, "dualMono": True, "samplePeak": peak,
            "globalNormalization": False, "listening": "not-claimed",
            "sha256": digest(root / "audio/master.wav")})


if __name__ == "__main__":
    main()
