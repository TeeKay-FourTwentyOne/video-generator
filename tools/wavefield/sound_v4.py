#!/usr/bin/env python3
"""A dry mechanical detector tick; retain the original quiet field-air bed."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, resample_poly, sosfilt

SR = 48000
SECONDS = 24
ONSETS = (2, 6, 10, 14, 18, 22)
SEED = 2026111404


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def filtered(signal, hz, kind='lowpass'):
    return sosfilt(butter(4, hz, btype=kind, fs=SR, output='sos'), signal, axis=0)


def event_metrics(signal):
    energy = np.mean(signal.astype(np.float64) ** 2, axis=1)
    cumulative = np.cumsum(energy)
    spectrum = np.fft.rfft(signal, axis=0)
    power = np.mean(np.abs(spectrum) ** 2, axis=1)
    power[1:-1] *= 2
    frequency = np.fft.rfftfreq(len(signal), 1 / SR)
    low = float(power[frequency < 250].sum() / len(signal))
    return {
        'peakDbFS': float(20 * np.log10(max(np.max(np.abs(signal)), 1e-12))),
        'rmsDbFS': float(10 * np.log10(max(energy.mean(), 1e-24))),
        'energy95Ms': float(np.searchsorted(cumulative, .95 * cumulative[-1]) / SR * 1000),
        'energy99Ms': float(np.searchsorted(cumulative, .99 * cumulative[-1]) / SR * 1000),
        'energyBelow250Hz': low,
        'fractionBelow250Hz': float(low / max(energy.sum(), 1e-24)),
        'spectralCentroidHz': float(np.sum(frequency * power) / np.sum(power)),
    }


def build(workspace):
    root = Path(workspace)
    out = root / 'audio'
    names = ['detector-source-tick-v4.wav', 'clicks-v4.wav', 'resonance-v4.wav', 'mix-v4.wav']
    for name in names:
        if (out / name).exists():
            raise ValueError(f'Preserve existing output: {name}')
    report_path = root / 'qa/audio-synthesis-v4.json'
    if report_path.exists():
        raise ValueError('Preserve existing synthesis report.')
    rng = np.random.default_rng(SEED)
    ct = np.arange(round(SR * .055)) / SR
    attack = 1 - np.exp(-ct / .000075)
    contact = filtered(rng.normal(size=len(ct)), 1100, 'highpass')
    tick = (.38 * contact * np.exp(-ct / .0011)
            + .95 * np.sin(2 * np.pi * 2450 * ct) * np.exp(-ct / .0022)
            + .40 * np.sin(2 * np.pi * 4720 * ct + .35) * np.exp(-ct / .0015)) * attack
    # A tiny second contact gives the escapement its tactile character.
    delay = round(.0035 * SR)
    tick[delay:] += .20 * tick[:-delay].copy()
    tick = filtered(filtered(tick, 650, 'highpass'), 12500)
    tick /= np.max(np.abs(tick))
    wavfile.write(out / names[0], SR, tick.astype(np.float32))

    samples = SR * SECONDS
    clicks = np.zeros((samples, 2), np.float64)
    resonance = np.zeros_like(clicks)
    gains = (.025, .050, .105, .20, .34, .60)
    cutoffs = (1100, 1900, 3000, 4800, 7800, 12500)
    for j, seconds in enumerate(ONSETS):
        start = seconds * SR
        direct = filtered(tick, cutoffs[j]) * gains[j]
        clicks[start:start + len(tick)] += direct[:, None]
        # Only short, faint spatial reflections, becoming completely dry at the detector.
        wet = .18 * (1 - j / 5) ** 1.5
        for k, echo_delay in enumerate((.014, .027, .046)):
            echo = filtered(direct, max(900, cutoffs[j] / (1 + .35 * k)))
            echo *= wet * np.exp(-k * .6)
            for channel in (0, 1):
                at = start + round((echo_delay + channel * .0015) * SR)
                resonance[at:at + len(tick), channel] += echo
    detector = clicks + resonance
    true_peak = float(np.max(np.abs(resample_poly(detector, 4, 1, axis=0))))
    gain = 10 ** (-5 / 20) / true_peak
    clicks *= gain
    resonance *= gain
    detector = clicks + resonance

    sr, bed = wavfile.read(out / 'field-air-v1.wav')
    assert sr == SR and bed.shape == (samples, 2)
    mix = detector + bed.astype(np.float64)
    for name, signal in [('clicks-v4.wav', clicks), ('resonance-v4.wav', resonance), ('mix-v4.wav', mix)]:
        wavfile.write(out / name, SR, signal.astype(np.float32))
    baseline = np.zeros_like(detector)
    for name in ['clicks-v1.wav', 'body-v1.wav', 'resonance-v1.wav']:
        sr, stem = wavfile.read(out / name)
        assert sr == SR and stem.shape == baseline.shape
        baseline += stem
    events = []
    for j, seconds in enumerate(ONSETS):
        start = seconds * SR
        revised = event_metrics(detector[start:start + SR])
        previous = event_metrics(baseline[start:start + SR])
        events.append({'number': j + 1, 'seconds': seconds, 'sample': start, 'frame': seconds * 30,
                       'gain': gains[j], 'lowpassHz': cutoffs[j], 'revisedDetector': revised,
                       'previousDetector': previous,
                       'lowBandEnergyChangeDb': float(10 * np.log10(
                           revised['energyBelow250Hz'] / previous['energyBelow250Hz']))})
    peak = float(np.max(np.abs(resample_poly(mix, 4, 1, axis=0))))
    assert peak < 10 ** (-4 / 20)
    assert events[-1]['revisedDetector']['energy95Ms'] < 12
    assert events[-1]['lowBandEnergyChangeDb'] < -30
    assert all(events[j + 1]['revisedDetector']['rmsDbFS'] > events[j]['revisedDetector']['rmsDbFS']
               for j in range(5))
    assert np.max(np.abs(mix[round(22.34 * SR):])) == 0
    report = {
        'schemaVersion': 1, 'version': 'v4', 'method': 'Local deterministic mechanical-tick synthesis',
        'sampleRate': SR, 'samples': samples, 'durationSeconds': SECONDS, 'channels': 2, 'seed': SEED,
        'events': events, 'globalDetectorGain': gain, 'truePeakDbTP': float(20 * np.log10(peak)),
        'intervalSamples': [4 * SR] * 5, 'monotonicDetectorRms': True,
        'bodyStemIncluded': False, 'finalDetectorReflections': False,
        'fieldAir': {'path': 'audio/field-air-v1.wav', 'sha256': sha(out / 'field-air-v1.wav'),
                     'samplesPreserved': True},
        'silentAfterSeconds': 22.34, 'endingSilenceMaxAbs': 0,
        'sourceHashes': {name: sha(out / name) for name in names},
        'mixSha256': sha(out / 'mix-v4.wav'), 'recipeSha256': sha(__file__),
        'listening': 'Signal measurements establish timing and spectral changes; full human listening pending.',
    }
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'mixSha256': report['mixSha256'], 'truePeakDbTP': report['truePeakDbTP'],
                      'lastDetector': events[-1], 'originalFieldAirPreserved': True}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default='data/workspace/wavefield-v1')
    build(parser.parse_args().workspace)
