#!/usr/bin/env python3
"""Soundtrack for the Borrowed Light comparison, aware of the freeze holds in cards.json.

Plan (film seconds): the left film's score plays from 0 to 13.9 (fade-out 0.4 s from 13.5), the
right film's from 13.5 (fade-in 0.4 s) to its end; the left film's 21.0-32.5 plays under the outro.
Both composers wrote a near-silence at the lamp transfer, so the handoff hides inside it.
During each hold the picture is frozen, the scores pause, and a faint air bed (-48 dBFS) fills the gap.
Usage: python3 recipes/mix.py cards.json LEFT.mp4 RIGHT.mp4 out.wav
"""
import json, subprocess, sys, wave
import numpy as np
SR = 48000
cards, left, right, out = sys.argv[1:5]
lay = json.load(open(cards))['layout']; fs = lay['film_start']; dur = lay['duration']
holds = sorted(lay.get('holds', []), key=lambda h: h['film_t'])

def pcm(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)
L = pcm(left); R = pcm(right); lenL = len(L) / SR; lenR = len(R) / SR
mix = np.zeros((int(round(dur * SR)), 2))

def vtime(t):
    """film seconds -> video seconds (holds that start at or before t have elapsed)."""
    return fs + t + sum(h['duration'] for h in holds if h['film_t'] <= t)

def n(sec): return int(round(sec * SR))
def ramp(k, up=True):
    r = np.linspace(0, 1, k) if up else np.linspace(1, 0, k); return r * r * (3 - 2 * r)
def place(seg, at):
    a = n(at); b = min(len(mix), a + len(seg)); mix[a:b] += seg[:b - a]

def play(src, f0, f1, fade_in=0.0, fade_out=0.0, edge=0.25):
    """Play src film audio from f0 to f1 (film s) on the video timeline, pausing across holds."""
    cuts = [f0] + [h['film_t'] for h in holds if f0 < h['film_t'] < f1] + [f1]
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        seg = src[n(a):n(b)].copy()
        fi = fade_in if i == 0 else edge; fo = fade_out if i == len(cuts) - 2 else edge
        if fi: k = min(len(seg), n(fi)); seg[:k] *= ramp(k)[:, None]
        if fo: k = min(len(seg), n(fo)); seg[-k:] *= ramp(k, False)[:, None]
        place(seg, vtime(a) if i == 0 else vtime(a) )  # a == hold film_t => after that hold
        print(f'  {"L" if src is L else "R"} film {a:6.2f}-{b:6.2f} -> video {vtime(a) if i==0 else vtime(a):6.2f}', file=sys.stderr)

print('placing scores', file=sys.stderr)
play(L, 0.0, 13.9, fade_out=0.4)
play(R, 13.5, lenR, fade_in=0.4)
# air bed under each hold
rng = np.random.default_rng(7)
for h in holds:
    at = fs + h['film_t'] + sum(x['duration'] for x in holds if x['film_t'] < h['film_t'])
    k = n(h['duration']); t = np.arange(k) / SR
    noise = rng.standard_normal((k, 2))
    F = np.fft.rfft(noise, axis=0); f = np.fft.rfftfreq(k, 1 / SR)[:, None]
    g = 1 / np.sqrt(1 + (f / 500.0) ** 4) * 1 / np.sqrt(1 + (60.0 / np.maximum(f, 1e-6)) ** 4)
    bed = np.fft.irfft(F * g, k, axis=0); bed *= 10 ** (-48 / 20) / np.sqrt(np.mean(bed ** 2))
    bed *= (1 + 0.15 * np.sin(2 * np.pi * 0.11 * t))[:, None]
    e = n(1.5); bed[:e] *= ramp(e)[:, None]; bed[-e:] *= ramp(e, False)[:, None]
    place(bed, at); print(f'  hold bed video {at:6.2f}-{at + h["duration"]:6.2f}', file=sys.stderr)
# outro: left film's second half under the cards
films_end = fs + lenR + sum(h['duration'] for h in holds); outro_at = round((films_end + 0.58) * 24) / 24  # snap to a frame
seg = L[n(21.0):n(32.5)].copy(); k = n(1.0); seg[:k] *= ramp(k)[:, None]; place(seg, outro_at)
print(f'  outro L film 21.00-32.50 -> video {outro_at:6.2f}', file=sys.stderr)
peak = np.max(np.abs(mix)); print(f'peak {20*np.log10(peak):.2f} dBFS, films_end {films_end:.3f}, duration {dur}', file=sys.stderr)
assert peak < 1.0
pcm16 = np.clip(mix * 32767, -32768, 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm16.tobytes())
print('wrote', out, file=sys.stderr)
