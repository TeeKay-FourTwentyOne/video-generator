#!/usr/bin/env python3
"""Offline music planning measurements. Requires FFmpeg, NumPy, SciPy, Matplotlib.

No service calls, model downloads, or changes to the input audio. Section-change
peaks and pulse candidates are measurements to audition, not semantic labels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from scipy import ndimage, optimize, signal


def run(args):
    return subprocess.run(args, check=True, capture_output=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def normalized(x):
    return (x - np.mean(x)) / (np.std(x) + 1e-9)


def tempo_candidates(envelope, dt):
    x = envelope - np.mean(envelope)
    ac = signal.correlate(x, x, mode="full", method="fft")[len(x)-1:]
    ac /= np.maximum(1, np.arange(len(x), 0, -1))
    ac /= max(float(ac[0]), 1e-9)
    lo, hi = int(60 / 210 / dt), int(60 / 45 / dt)
    peaks, _ = signal.find_peaks(ac[lo:hi], distance=3)
    peaks += lo
    order = sorted(peaks, key=lambda p: ac[p], reverse=True)[:8]
    return [{"bpm": round(60 / (p * dt), 3),
             "autocorrelation": round(float(ac[p]), 4)} for p in order]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--title", default="Song")
    args = ap.parse_args()
    src, out = args.input.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original_hash, original_stat = sha(src), src.stat()
    dest = out / ("source" + src.suffix.lower())
    if src == dest:
        raise SystemExit("Input must be outside the analysis output.")
    if dest.exists() and sha(dest) != original_hash:
        raise SystemExit("Refusing to replace a different analysis source.")
    if not dest.exists():
        shutil.copy2(src, dest)
    info = json.loads(run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                          "-show_entries", "stream=codec_name,sample_rate,channels,duration,bit_rate",
                          "-of", "json", str(dest)]).stdout)["streams"][0]
    rate = int(info["sample_rate"])
    channels = int(info["channels"])
    raw = run(["ffmpeg", "-v", "error", "-i", str(dest), "-map", "0:a:0",
               "-f", "f32le", "-acodec", "pcm_f32le", "-"]).stdout
    stereo = np.frombuffer(raw, dtype="<f4").reshape(-1, channels)
    duration = len(stereo) / rate
    # Exact playback sample origin: decoded first sample is t=0; do not add the
    # MP3 packet start timestamp or encoder delay to any generated cue.
    sr = 22050
    from math import gcd
    divisor = gcd(rate, sr)
    y = signal.resample_poly(stereo.mean(axis=1), sr // divisor, rate // divisor)
    hop, fft_size = 220, 2048
    f, t, spec = signal.stft(y, sr, nperseg=fft_size, noverlap=fft_size-hop,
                             boundary="zeros", padded=True)
    mag, power = abs(spec), abs(spec)**2
    dt = hop / sr
    mel = lambda hz: 2595 * np.log10(1 + hz / 700)
    hz = lambda m: 700 * (10**(m / 2595)-1)
    edges = hz(np.linspace(mel(35), mel(10000), 50))
    filters = np.array([np.maximum(0, np.minimum((f-a)/(b-a), (c-f)/(c-b)))
                        for a, b, c in zip(edges[:-2], edges[1:-1], edges[2:])])
    mel_power = filters @ power
    logmel = np.log1p(100000 * mel_power)
    flux = np.mean(np.maximum(0, np.diff(logmel, axis=1, prepend=logmel[:, :1])), axis=0)
    envelope = np.maximum(0, flux - ndimage.median_filter(flux, size=51))
    envelope /= max(float(np.max(envelope)), 1e-9)
    tempos = tempo_candidates(envelope, dt)
    local_tempos = []
    for start in np.arange(4, duration - 18, 12):
        selected = (t >= start) & (t < start+18)
        local_tempos.append({"start": float(start), "end": float(start+18),
                             "candidates": tempo_candidates(envelope[selected], dt)[:4]})
    # A periodic grid is only exported if a measurable pulse exists. This does
    # not infer the downbeat, meter, swing, or a quarter-note interpretation.
    pulse = None
    if tempos and tempos[0]["autocorrelation"] > 0.02:
        seed = tempos[0]["bpm"]
        mask = (t >= 5) & (t < duration-8)
        tt, ee = t[mask], envelope[mask]
        def strength(bpm):
            return abs(np.sum(ee * np.exp(-2j*np.pi*tt*bpm/60))) / max(ee.sum(), 1e-9)
        trial = np.linspace(seed-3, seed+3, 601)
        best = float(trial[np.argmax([strength(b) for b in trial])])
        fit = optimize.minimize_scalar(lambda b: -strength(b), bounds=(best-.02, best+.02), method="bounded")
        bpm = float(fit.x)
        phase = float((-np.angle(np.sum(ee*np.exp(-2j*np.pi*tt*bpm/60))) / (2*np.pi)) % 1)
        offset, period = phase * 60/bpm, 60/bpm
        beats = np.arange(offset, duration, period)
        pulse = {"bpm": round(bpm, 5), "seconds_per_pulse": round(period, 6),
                 "offset_seconds": round(offset, 6), "phase_concentration": round(strength(bpm), 4),
                 "meaning": "Provisional periodic pulse; not confirmed beats or downbeats",
                 "times": np.round(beats, 6).tolist()}
    peaks, props = signal.find_peaks(envelope, distance=round(.13/dt), prominence=.065)
    onsets = [{"time": round(float(t[p]), 4), "strength": round(float(envelope[p]), 4)}
              for p in peaks if t[p] < duration]
    bins = np.arange(0, duration, .1)
    rms = np.array([np.sqrt(np.mean(stereo[int(b*rate):min(len(stereo), int((b+.1)*rate))]**2)) for b in bins])
    rms_db = 20*np.log10(np.maximum(rms, 1e-9))
    centroid = (f[:, None]*power).sum(axis=0)/np.maximum(power.sum(axis=0), 1e-12)
    bass = power[f < 180].sum(axis=0)/np.maximum(power.sum(axis=0), 1e-12)
    # One-second timbre cells. Separate level from normalized spectral shape.
    seconds = np.arange(0, int(np.ceil(duration)))
    features = np.array([np.mean(logmel[:, (t >= s) & (t < s+1)], axis=1) for s in seconds]).T
    shape = features / np.maximum(np.linalg.norm(features, axis=0), 1e-9)
    similarity = shape.T @ shape
    # Symmetric 4-second timbre contrast plus level and transient changes.
    z = (features - features.mean(axis=1, keepdims=True))/(features.std(axis=1, keepdims=True)+.1)
    nov = np.zeros(len(seconds))
    for i in range(4, len(seconds)-4):
        nov[i] = np.linalg.norm(z[:, i-4:i].mean(axis=1)-z[:, i:i+4].mean(axis=1)) / np.sqrt(len(z))
    boundary_ids, _ = signal.find_peaks(nov, distance=6, prominence=.15)
    changes = [{"time": int(p), "contrast": round(float(nov[p]), 4)} for p in boundary_ids]
    # Loudness measurement is read-only; the MP3 is not normalized.
    meter = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(dest), "-map", "0:a:0",
                 "-af", "loudnorm=I=-16:TP=-1:LRA=11:print_format=json", "-f", "null", "-"]).stderr.decode()
    meter = json.loads(meter[meter.rfind("{"):meter.rfind("}")+1])
    loudness = {k: float(v) for k, v in meter.items() if k.startswith("input_")}
    windows = []
    for start in range(0, int(duration), 5):
        a = (bins >= start) & (bins < start+5)
        b = (t >= start) & (t < start+5)
        windows.append({"start": start, "end": round(min(start+5, duration), 3),
                        "rms_dbfs": round(float(20*np.log10(np.sqrt(np.mean(rms[a]**2)))), 2),
                        "bass_power_fraction": round(float(np.mean(bass[b])), 3),
                        "power_centroid_hz": round(float(np.mean(centroid[b])), 1),
                        "onsets_per_second": round(sum(start <= x['time'] < min(start+5, duration) for x in onsets)/min(5, duration-start), 2)})
    report = {
        "title": args.title,
        "analysis_kind": "Offline signal measurements; no listening or transcription",
        "source": {"filename": src.name, "sha256": original_hash, "bytes": original_stat.st_size,
                   "copy_sha256": sha(dest), "audio": info},
        "decoded_duration_seconds": duration, "decoded_samples_per_channel": len(stereo),
        "sample_peak_dbfs": float(20*np.log10(np.max(abs(stereo)))),
        "loudness": loudness, "tempo_candidates": tempos, "local_tempos": local_tempos,
        "pulse_grid": pulse, "texture_change_candidates": changes, "five_second_windows": windows,
        "limitations": ["No semantic verse/chorus labeling", "No verified lyrics or instrument recognition",
                        "No confirmed key or meter", "RMS and spectral density are not emotional intensity",
                        "Change times are approximate; audition before editing", "Periodic pulse is not a verified downbeat grid"],
        "cost": {"external_api_calls": 0, "analysis_spend_usd": 0, "analysis_ceiling_usd": 10}}
    dump(out/"analysis.json", report)
    dump(out/"onsets.json", onsets)
    dump(out/"pulse-grid.json", pulse)
    # Compact arrays for a local player; embeds without fetch so file:// works.
    dump(out/"plot-data.json", {"duration": duration, "times": np.round(bins, 2).tolist(),
                              "rms_dbfs": np.round(rms_db, 2).tolist(),
                              "texture_change_candidates": changes})
    np.savez_compressed(out/"features.npz", seconds=seconds, similarity=similarity,
                        novelty=nov, t=t, envelope=envelope, bass=bass, centroid=centroid)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4, 1, figsize=(15, 11), gridspec_kw={"height_ratios": [1, 1, 1, 2.7]})
    fig.suptitle(args.title + " | local signal map\nChange candidates require listening; loudness does not establish mood", fontsize=15)
    axes[0].plot(bins, rms_db, color="#187d8c", lw=.6)
    axes[0].plot(bins, ndimage.uniform_filter1d(rms_db, size=20), color="#134655", lw=1.5)
    axes[0].set(ylabel="RMS dBFS", xlim=(0, duration), ylim=(-55, 0))
    axes[1].plot(t, ndimage.uniform_filter1d(bass, size=200), label="Bass power fraction (<180 Hz)", color="#987521")
    axes[1].plot(t, ndimage.uniform_filter1d(envelope, size=200), label="Mean transient strength", color="#7046a5")
    axes[1].legend(loc="upper right", fontsize=8)
    axes[1].set(xlim=(0, duration), ylim=(0, 1))
    axes[2].plot(seconds, nov, color="#bd5043")
    for change in changes:
        for ax in axes[:3]: ax.axvline(change['time'], color="#aaa", alpha=.35, lw=.6)
        axes[2].annotate(str(change['time']), (change['time'], change['contrast']), fontsize=8)
    axes[2].set(ylabel="Texture contrast", xlim=(0, duration), xlabel="Seconds from decoded audio start")
    im = axes[3].imshow(similarity, origin="lower", extent=(0, len(seconds), 0, len(seconds)),
                        aspect="auto", vmin=.55, vmax=1, cmap="magma")
    axes[3].set(xlabel="Seconds", ylabel="Seconds", title="Timbre similarity (bright = similar spectral balance; does not prove a repeated melody)")
    fig.colorbar(im, ax=axes[3], fraction=.02)
    fig.tight_layout(rect=(0, 0, 1, .95))
    fig.savefig(out/"signal-map.png", dpi=140)
    plt.close(fig)
    final_hash = sha(src)
    assert final_hash == original_hash == sha(dest)
    assert src.stat().st_mtime_ns == original_stat.st_mtime_ns
    dump(out/"verification.json", {"source_hash_before": original_hash,
                                  "source_hash_after": final_hash, "source_mtime_unchanged": True,
                                  "copy_matches_original": True, "all_cues_within_track": all(0 <= x['time'] < duration for x in onsets),
                                  "network_calls": 0})
    print(json.dumps({"duration": duration, "tempo_candidates": tempos,
                      "pulse": {k:v for k,v in (pulse or {}).items() if k != 'times'},
                      "changes": changes, "loudness": loudness}, indent=2))


if __name__ == "__main__":
    main()
