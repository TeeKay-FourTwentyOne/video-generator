#!/usr/bin/env python3
"""Borrowed Light (Fable draft) — original local score and foley, "By Given Light".

Deterministic numpy synthesis. No samples, recordings, downloads or paid services.
Usage: python3 recipes/score.py edit/timeline.json edit/score.wav [--master-db=0]
timeline.json holds edit-time shot starts: {"S01": 0.0, ..., "T01": 32.5, "end": 35.5}.
Cues are placed relative to those shot starts, so a re-timed edit only needs a re-render.
"""
import json, math, sys, wave
import numpy as np

SR = 48000
RNG = np.random.default_rng(20261003)

def n_of(sec): return int(round(sec * SR))
def tgrid(sec): return np.arange(n_of(sec)) / SR
def noise(sec): return RNG.standard_normal(n_of(sec))

def fft_filter(sig, lo=None, hi=None, order=4):
    n = len(sig)
    if n == 0: return sig
    F = np.fft.rfft(sig); f = np.fft.rfftfreq(n, 1 / SR)
    g = np.ones_like(f)
    if lo: g = g / np.sqrt(1 + (lo / np.maximum(f, 1e-9)) ** (2 * order))
    if hi: g = g / np.sqrt(1 + (f / hi) ** (2 * order))
    return np.fft.irfft(F * g, n)

def fade(sig, a=0.0, r=0.0):
    out = sig.copy(); n = len(sig)
    na, nr = min(n, n_of(a)), min(n, n_of(r))
    if na: out[:na] *= np.linspace(0, 1, na)
    if nr: out[n - nr:] *= np.linspace(1, 0, nr)
    return out

def half_sine(sec): return np.sin(np.pi * tgrid(sec) / sec)

def piecewise(points, total):
    """Linear envelope over the whole mix from (time, level) points."""
    t = tgrid(total); xs = [p[0] for p in points]; ys = [p[1] for p in points]
    return np.interp(t, xs, ys)

# ---------- instruments ----------
def click(level=1.0):
    t = tgrid(0.03)
    burst = fft_filter(noise(0.03), 1800, 7000) * np.exp(-t / 0.004)
    ring = np.sin(2 * np.pi * 1450 * t) * np.exp(-t / 0.010)
    return (burst * 0.9 + ring * 0.5) * level

def tock(level=1.0):
    t = tgrid(0.16)
    f = 150 * np.exp(-t / 0.05) + 95
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.055)
    knock = fft_filter(noise(0.16), 300, 1500) * np.exp(-t / 0.006) * 0.5
    return fft_filter(body + knock, None, 2500) * level

def rumble(sec):
    t = tgrid(sec)
    low = fft_filter(noise(sec), 30, 140) * (1 + 0.55 * np.sin(2 * np.pi * 11.3 * t))
    grit = fft_filter(noise(sec), 240, 1100) * (1 + 0.6 * np.sin(2 * np.pi * 22.6 * t + 1.0)) * 0.22
    return fade(low + grit, 0.35, 0.45)

def servo(sec, f0, f1, level=1.0):
    t = tgrid(sec)
    f = f0 + (f1 - f0) * (t / sec) ** 0.7
    f = f * (1 + 0.012 * np.sin(2 * np.pi * 6.2 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    s = s + 0.18 * fft_filter(noise(sec), 900, 3200)
    return fft_filter(s * half_sine(sec), None, 5200) * level

def scrape(sec, level=1.0):
    t = tgrid(sec)
    s = fft_filter(noise(sec), 1400, 5200) * half_sine(sec)
    squeak = np.sin(2 * np.pi * (2100 + 180 * np.sin(2 * np.pi * 1.7 * t)) * t) * half_sine(sec) ** 2 * 0.35
    return (s + squeak) * level

def bell(freq, sec=3.2, level=1.0):
    t = tgrid(sec)
    parts = [(1.0, 1.0, 2.1), (2.0, 0.22, 1.0), (2.98, 0.33, 0.8), (4.21, 0.13, 0.45), (5.4, 0.07, 0.3)]
    s = np.zeros_like(t)
    for ratio, amp, tau in parts:
        det = 1 + RNG.normal(0, 0.0008)
        s += amp * np.sin(2 * np.pi * freq * ratio * det * t) * np.exp(-t / tau)
    s *= (1 - np.exp(-t / 0.004))
    return fade(s, 0, 0.05) * level

def pad(freqs, sec, attack, release, dark_hz, bright_hz, level=1.0):
    t = tgrid(sec); s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.0035, 0.0, 0.0035):
            ph = 2 * np.pi * f * (1 + det) * t + 0.4 * np.sin(2 * np.pi * 0.11 * t + f)
            v = np.zeros_like(t)
            for k in range(1, 9): v += np.sin(k * ph) / k ** 1.3
            s += v / 3
    dark = fft_filter(s, None, dark_hz); bright = fft_filter(s, None, bright_hz)
    w = np.clip(t / sec, 0, 1) ** 0.8
    s = dark * (1 - w) + bright * w
    env = np.minimum(1, t / max(attack, 1e-3)) * np.minimum(1, (sec - t) / max(release, 1e-3))
    return s * env * level / len(freqs)

def hum(sec, level=1.0):
    t = tgrid(sec)
    s = (0.6 * np.sin(2 * np.pi * 55 * t) + 0.4 * np.sin(2 * np.pi * 110 * t + 0.3)
         + 0.15 * np.sin(2 * np.pi * 165 * t) + 0.08 * np.sin(2 * np.pi * 220 * t))
    s *= 1 + 0.12 * np.sin(2 * np.pi * 0.31 * t)
    return s * level

def crackle(sec, per_second, level=1.0):
    n = n_of(sec); s = np.zeros(n)
    for _ in range(int(RNG.poisson(per_second * sec))):
        i = int(RNG.integers(0, n)); length = int(RNG.integers(60, 220))
        burst = RNG.standard_normal(length) * np.exp(-np.arange(length) / (length / 3)) * RNG.uniform(0.3, 1)
        s[i:i + length] += burst[:n - i]
    return fft_filter(s, 2200, 7500) * level

def wind(sec, level=1.0):
    t = tgrid(sec)
    body = fft_filter(noise(sec), 110, 900)
    am = 0.55 + 0.45 * (0.6 * np.sin(2 * np.pi * 0.07 * t) + 0.4 * np.sin(2 * np.pi * 0.19 * t + 2))
    whistle = (np.sin(2 * np.pi * (820 + 160 * np.sin(2 * np.pi * 0.05 * t)) * t)
               * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t)) ** 3 * 0.06)
    return (body * am + whistle) * level

def heartbeat(level=1.0):
    def thump(amp):
        t = tgrid(0.22)
        f = 78 * np.exp(-t / 0.07) + 52
        ph = 2 * np.pi * np.cumsum(f) / SR
        return fft_filter(np.sin(ph) * np.exp(-t / 0.075) * amp, None, 220)
    a = thump(1.0); b = thump(0.65)
    out = np.zeros(n_of(0.45)); out[:len(a)] += a; i = n_of(0.17); out[i:i + len(b)] += b
    return out * level

def room_tone(sec, level=1.0): return fft_filter(noise(sec), 60, 400) * level

def shimmer(sec, level=1.0):
    t = tgrid(sec)
    return fft_filter(noise(sec), 3800, 9000) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t)) * level

# ---------- reverb ----------
def reverb_ir(sec=2.6, damp_hz=3200):
    t = tgrid(sec)
    def chan():
        ir = fft_filter(noise(sec), None, damp_hz) * np.exp(-t * 6.91 / sec)
        for ms, g in ((11, 0.5), (23, 0.38), (37, 0.3), (53, 0.22), (71, 0.16)):
            ir[n_of(ms / 1000)] += g
        return ir / np.sqrt(np.sum(ir ** 2))
    return chan(), chan()

def convolve(sig, ir):
    n = len(sig) + len(ir) - 1; m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(sig, m) * np.fft.rfft(ir, m), m)[:len(sig)]

class Mix:
    def __init__(self, sec):
        self.n = n_of(sec)
        self.dry = [np.zeros(self.n), np.zeros(self.n)]
        self.send = [np.zeros(self.n), np.zeros(self.n)]
        self.events = []
    def add(self, sig, at, pan=0.0, gain=1.0, wet=0.3, label=None):
        i0 = n_of(at)
        if i0 >= self.n or i0 < 0: return
        seg = sig[:self.n - i0]
        lg, rg = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        for buf, w in ((self.dry, 1.0), (self.send, wet)):
            buf[0][i0:i0 + len(seg)] += seg * gain * lg * w
            buf[1][i0:i0 + len(seg)] += seg * gain * rg * w
        if label: self.events.append({"at": round(at, 3), "label": label, "gain": gain, "pan": pan})

NOTE = {'D2': 73.42, 'A2': 110.0, 'D3': 146.83, 'F#3': 185.0, 'A3': 220.0, 'B3': 246.94, 'D4': 293.66, 'E4': 329.63,
        'F#4': 369.99, 'A4': 440.0, 'B4': 493.88, 'D5': 587.33, 'E5': 659.25, 'F#5': 739.99, 'A5': 880.0}

def compose(T):
    end = T['end']; m = Mix(end)
    # --- ambience: cold wind through broken panes; thins at the transfer, settles warmer after
    wind_env = piecewise([(0, 0.0), (0.6, 0.11), (T['S03'], 0.09), (T['S03'] + 1.8, 0.05), (T['S04'] + 1.0, 0.035),
                          (T['S05'], 0.045), (T['S06'], 0.05), (T['T01'], 0.04), (end - 0.2, 0.0), (end, 0.0)], end)
    m.add(wind(end) * wind_env, 0, 0, 1.0, wet=0.5, label='wind')
    m.add(room_tone(end, 0.022) * piecewise([(0, 0), (0.4, 1), (end - 1.0, 1), (end, 0)], end), 0, 0, 1.0, wet=0.2)
    # cold drone under the first half (D2 + faint A2), gone by the transfer
    drone_env = piecewise([(0, 0), (1.5, 1), (T['S03'], 1), (T['S03'] + 1.6, 0)], end)
    m.add(fft_filter(np.sin(2 * np.pi * 73.42 * tgrid(end)) + 0.35 * np.sin(2 * np.pi * 110.0 * tgrid(end) + 1), None, 400) * drone_env, 0, 0, 0.05, wet=0.6, label='cold drone')
    # --- the machine: regular pulse, tracks, servos (S01–S03)
    beat = 0.64; t = T['S01'] + 0.45
    s03_stop = T['S03'] + 1.75
    while t < s03_stop:
        if t < T['S02']:
            frac = (t - T['S01']) / max(T['S02'] - T['S01'], 1e-3); gain, wet, pan = 0.22 + 0.2 * frac, 0.65, 0.0
        elif t < T['S03']:
            frac = (t - T['S02']) / max(T['S03'] - T['S02'], 1e-3); gain, wet, pan = 0.55, 0.3, 0.45 - 0.25 * min(1, frac * 3)
        else:
            gain, wet, pan = 0.6, 0.15, 0.15
        m.add(click(0.55), t, pan, gain, wet); m.add(tock(0.8), t, pan, gain, wet)
        if t >= T['S03']: beat += 0.085   # the pulse slows as the gripper takes hold
        t += beat
    m.events.append({"at": T['S01'] + 0.45, "label": "mechanical pulse begins", "until": s03_stop})
    m.add(rumble(T['S02'] - T['S01'] + 0.3), T['S01'] + 0.1, 0.0, 0.3, 0.55, 'tracks (far)')
    m.add(rumble(1.1), T['S02'] - 0.05, 0.35, 0.42, 0.3, 'tracks stop just after the cut')
    m.add(servo(1.1, 700, 1050, 0.27), T['S02'] + 1.8, 0.25, 1.0, 0.3, 'arm rises')
    m.add(servo(1.7, 1000, 1180, 0.2), T['S02'] + 3.2, 0.2, 1.0, 0.3, 'arm reaches to the socket')
    m.add(click(0.35), T['S02'] + 5.6, 0.2, 0.6, 0.3, 'arm settles, hovering')
    m.add(servo(0.7, 900, 760, 0.22), T['S03'] + 0.05, 0.1, 1.0, 0.15, 'gripper arrives')
    m.add(click(0.5), T['S03'] + 1.3, 0.1, 0.8, 0.15, 'gripper closes'); m.add(click(0.4), T['S03'] + 1.37, 0.1, 0.8, 0.15)
    m.add(servo(0.55, 520, 640, 0.18), T['S03'] + 1.4, 0.1, 1.0, 0.15, 'quarter turn')
    m.add(scrape(0.55, 0.13), T['S03'] + 1.4, 0.1, 1.0, 0.2, 'brass on brass')
    # --- near-silence across the cut; then the lamp wakes (S04)
    m.add(crackle(1.1, 22, 0.32), T['S04'] + 1.1, 0.0, 1.0, 0.25, 'filament crackle')
    hum_env = piecewise([(T['S04'] + 1.3, 0), (T['S04'] + 2.8, 1), (T['T01'], 1), (T['T01'] + 1.8, 0)], end)
    m.add(hum(end, 0.16) * hum_env, 0, 0, 1.0, 0.25, 'lamp hum')
    # imperfect warm rhythm: a heartbeat with human jitter and the occasional held breath
    t = T['S04'] + 2.2; count = 0
    while t < T['T01'] + 1.0:
        gain = 0.42 if t < T['S05'] else (0.5 if t < T['S06'] else 0.55)
        m.add(heartbeat(), t, 0.0, gain, 0.2)
        count += 1
        gap = 0.86 + RNG.normal(0, 0.075)
        if count % 7 == 0: gap += 0.35   # a held breath
        t += max(0.6, gap)
    m.events.append({"at": T['S04'] + 2.2, "label": "imperfect warm rhythm begins", "until": T['T01'] + 1.0})
    # --- bells: light enters the roots, then climbs (S05), then settles (S06)
    m.add(bell(NOTE['D3'], 3.5), T['S04'] + 3.0, -0.1, 0.4, 0.5, 'bell D3 (roots)')
    m.add(bell(NOTE['A3'], 3.5), T['S04'] + 4.05, 0.1, 0.34, 0.5, 'bell A3')
    m.add(bell(NOTE['F#3'], 3.5), T['S04'] + 5.0, -0.05, 0.3, 0.5, 'bell F#3 (trunk)')
    climb = ['D4', 'E4', 'F#4', 'A4', 'B4', 'D5', 'E5', 'F#5', 'A5']
    span = max(T['S06'] - T['S05'] - 0.3, 2.0)
    at = [0.2 + span * (i / 8) ** 1.25 for i in range(9)]   # bells accelerate as the light climbs
    for i, (n, a) in enumerate(zip(climb, at)):
        m.add(bell(NOTE[n]), T['S05'] + a, (-0.3 if i % 2 else 0.3) * (0.4 + i / 12), 0.42 - 0.012 * i, 0.55, f'bell {n} (climb)')
    for n, a, g in (('F#5', 1.6, 0.24), ('B4', 3.4, 0.24), ('D5', 5.5, 0.22), ('A4', 7.0, 0.2)):
        m.add(bell(NOTE[n]), T['S06'] + a, 0.0, g, 0.6, f'bell {n} (settle)')
    m.add(bell(NOTE['D4'], 4.0), T['T01'] + 0.5, 0.0, 0.32, 0.6, 'bell D4 (title)')
    # --- pad: D major add9, opening from dark to bright as the light climbs
    pad_len = end - (T['S04'] + 1.5)
    chord = [NOTE['D2'], NOTE['A2'], NOTE['D3'], NOTE['F#3'], NOTE['A3'], NOTE['E4']]
    p = pad(chord, pad_len, 6.0, 2.6, 420, 2600)
    pad_env = piecewise([(T['S04'] + 1.5, 0.0), (T['S04'] + 4.0, 0.09), (T['S05'], 0.12), (T['S05'] + 6, 0.2),
                         (T['S06'], 0.24), (T['T01'], 0.22), (T['T01'] + 1.5, 0.12), (end - 0.3, 0.0), (end, 0)], end)
    full = np.zeros(m.n); i0 = n_of(T['S04'] + 1.5); full[i0:i0 + len(p)] = p[:m.n - i0]
    m.add(full * pad_env, 0, 0, 1.0, 0.45, 'pad D add9')
    m.add(shimmer(T['T01'] - T['S06'] + 1.0, 0.02) * piecewise([(0, 0), (1.5, 1), (T['T01'] - T['S06'] + 0.5, 1), (T['T01'] - T['S06'] + 1.0, 0)], T['T01'] - T['S06'] + 1.0), T['S06'], 0, 1.0, 0.5, 'light shimmer')
    return m

def master(m, master_db=0.0, T=None):
    irL, irR = reverb_ir()
    L = m.dry[0] + 0.9 * convolve(m.send[0], irL)
    R = m.dry[1] + 0.9 * convolve(m.send[1], irR)
    L = fft_filter(L, 28, 18000, 2); R = fft_filter(R, 28, 18000, 2)
    g = 10 ** (master_db / 20)
    if T:  # section balance: lift the quiet mechanical half so it survives phone speakers
        lift = piecewise([(0, 10 ** (2.5 / 20)), (T['S04'] + 0.5, 10 ** (2.5 / 20)), (T['S04'] + 2.5, 1.0), (T['end'], 1.0)], T['end'])
        L, R = L * lift[:len(L)], R * lift[:len(R)]
    L, R = L * g, R * g
    k = 1.25
    L, R = np.tanh(L * k) / k, np.tanh(R * k) / k
    n = len(L); head, tail = n_of(0.5), n_of(1.4)
    for ch in (L, R):
        ch[:head] *= np.linspace(0, 1, head); ch[n - tail:] *= np.linspace(1, 0, tail)
    return L, R

def write_wav(path, L, R):
    tpdf = (RNG.random(len(L)) + RNG.random(len(L)) - 1) / 32768
    data = np.empty(len(L) * 2); data[0::2] = L + tpdf; data[1::2] = R + tpdf
    pcm = np.clip(np.round(data * 32767), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == '__main__':
    timeline, out = sys.argv[1], sys.argv[2]
    master_db = float(next((a.split('=')[1] for a in sys.argv[3:] if a.startswith('--master-db=')), '0'))
    T = json.load(open(timeline))
    m = compose(T)
    L, R = master(m, master_db, T)
    write_wav(out, L, R)
    peak = float(max(np.abs(L).max(), np.abs(R).max())); rms = float(np.sqrt((np.mean(L ** 2) + np.mean(R ** 2)) / 2))
    meta = {"title": "By Given Light", "film": "Borrowed Light (Fable draft)", "origin": "Original local numpy synthesis; no samples, recordings or generation services",
            "composer": "Claude (Fable 5.1)", "durationSeconds": T['end'], "sampleRate": SR, "timeline": T, "masterDb": master_db,
            "peak": peak, "peakDbfs": 20 * math.log10(max(peak, 1e-9)), "rmsDbfs": 20 * math.log10(max(rms, 1e-9)), "events": m.events, "paidRequests": 0}
    json.dump(meta, open(out.rsplit('.', 1)[0] + '.json', 'w'), indent=2)
    print(json.dumps({k: meta[k] for k in ('title', 'durationSeconds', 'peakDbfs', 'rmsDbfs', 'paidRequests')}))
