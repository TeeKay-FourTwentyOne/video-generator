---
name: upscale
description: AI upscale video to 4K using Real-ESRGAN. Use when upscaling videos, improving resolution, or preparing final exports at higher quality. Requires realesrgan-ncnn-py (pip install realesrgan-ncnn-py).
allowed-tools: Bash, Read, Glob
---

# Upscale Video

AI-powered video upscaling using Real-ESRGAN on Apple Silicon (Metal GPU).

## Tool

`python3 tools/upscale.py <input.mp4> [output.mp4] [--scale 2|3|4] [--model 0|1]`

## Quick Usage

```bash
# Default: 4x upscale (720p -> 4K) with general model
python3 tools/upscale.py data/workspace/my_video.mp4

# Explicit output path
python3 tools/upscale.py data/workspace/my_video.mp4 data/workspace/my_video_4k.mp4

# 2x only (faster, no lanczos pass)
python3 tools/upscale.py data/workspace/my_video.mp4 --scale 2

# Anime/animation model
python3 tools/upscale.py data/workspace/my_video.mp4 --model 1
```

## Models

| Model | Flag | Notes |
|-------|------|-------|
| realesr-animevideov3-x2 | `--model 1` (default) | Native 2x, about 1-2 s per 1080p frame. This is the model behind every 2026 4K master (August, September, Can-Can, Church Grim): until 2026-09-12 the CLI's "model 0" was passed straight to the ncnn wrapper, where ID 0 is this model |
| realesrgan-x4plus | `--model 0` | The true general model. Renders 4x natively, then resizes; about 30x slower (30-50 s per 1080p frame, roughly six hours for a 33 s film). **Disabled on this MacBook by the director (2026-10-03); the tool refuses it on macOS.** Only a machine where that cost is accepted may set `VIDEO_ALLOW_X4PLUS=1` |

## How It Works

1. Extracts all frames from video using ffmpeg
2. Upscales each frame 2x using Real-ESRGAN AI model on GPU (Metal)
3. If target scale > 2x, applies lanczos interpolation for remaining upscale
4. Reassembles frames into video with libx264 (crf 18, slow preset)
5. Copies audio from original

## Performance

- Default model: about 1.6 s per 1080p frame on an M3 Pro on battery (faster on mains); a 33 s 1080p vertical takes about 25 minutes including encodes
- x4plus: about 30-50 s per 1080p frame; measure before committing
- Temp PNG frames need about 20 GB for a 35 s 1080p vertical; the tool measures the first frame and refuses when the disk is short. Upscale per assembled segment and concatenate when space is tight
- The ncnn library prints a percentage per frame tile; progress is the `[i/N] s/frame, ETA` lines
- Check `pmset -g batt`: on battery the GPU is throttled and a long run can outlive the charge

## Prerequisites

```bash
pip install realesrgan-ncnn-py
```

This package bundles the ncnn-vulkan binary and model weights (~51MB). Works on macOS Apple Silicon via Metal.

## Steps (when invoked as skill)

1. **Identify the video** — Confirm input path and desired output resolution with user.
2. **Check dependency** — Verify `realesrgan-ncnn-py` is installed: `python3 -c "import realesrgan_ncnn_py"`.
   If missing: `pip install realesrgan-ncnn-py`.
3. **Run upscale** — Execute the tool. For long videos, run in background.
4. **Verify output** — Check output file exists, confirm resolution with ffprobe, report file size.
