#!/usr/bin/env python3
"""Original sparse plucks, air and cloth for Washing Day. NumPy, no downloaded samples.

Usage: python washing-day-score.py WORKSPACE EDIT_JSON NEW_STEM_DIRECTORY
The cue timing follows the final integer-frame edit, not the intended take lengths.
"""
import json
import math
import sys
import wave
from pathlib import Path

import numpy as np


def render(workspace, edit_file, directory):
    root = Path(workspace).resolve()
    edit = json.loads((root / edit_file).read_text())
    fps = json.loads((root / "film.json").read_text())["fps"]
    starts, lengths, frame = {}, {}, 0
    for segment in edit["segments"]:
        starts[segment["shotId"]] = frame / fps
        lengths[segment["shotId"]] = segment["frames"] / fps
        frame += segment["frames"]
    rate, duration = 48000, frame / fps
    # The local pin insert cuts from held linen to the empty peg at frame 42.
    # Keep its near-silence tied to the visible event, not the next shot boundary.
    release = starts['S03'] + 42 / fps
    n = round(rate * duration)
    score = np.zeros((n, 2), np.float64)
    air = np.zeros_like(score)
    foley = np.zeros_like(score)
    rng = np.random.default_rng(421)
    events = []

    def place(target, x, at, amp, pan=0):
        begin = round(at * rate)
        end = min(n, begin + len(x))
        if begin < 0 or end <= begin:
            return
        target[begin:end, 0] += x[:end-begin] * amp * math.cos((pan+1)*math.pi/4)
        target[begin:end, 1] += x[:end-begin] * amp * math.sin((pan+1)*math.pi/4)

    def pluck(at, midi, amp=.036, length=2.7, pan=0):
        t = np.arange(round(length*rate)) / rate
        f = 440*2**((midi-69)/12)
        x = np.zeros_like(t)
        for h in range(1, 13):
            # Slightly inharmonic short string; upper partials die first.
            x += np.sin(2*np.pi*f*h*(1+.000045*h*h)*t) * np.exp(-t*(.72+.44*h)) / h**1.35
        x *= (1-np.exp(-t/.0018)) * np.minimum(1, (length-t)/.14)
        place(score, x, at, amp, pan)
        events.append({"at":at,"type":"pluck","midi":midi,"amp":amp})

    def band_noise(length, low, high):
        count = round(length*rate)
        freq = np.fft.rfftfreq(count, 1/rate)
        raw = np.fft.rfft(rng.normal(0, 1, count))
        shape = (1/(1+(low/np.maximum(freq,1))**6)) * np.exp(-(freq/high)**4)
        x = np.fft.irfft(raw*shape, n=count)
        return x/max(float(np.std(x)), .0001)

    def cloth(at, length, amp, pan):
        t = np.arange(round(length*rate))/rate
        x = band_noise(length, 550, 7000)
        envelope = np.sin(np.pi*t/length)**2 * (.72+.28*np.sin(2*np.pi*8*t)**2)
        place(foley, x*envelope, at, amp, pan)
        events.append({"at":at,"type":"cloth","length":length,"amp":amp})

    def peg(at, amp=.045, pan=-.3):
        t = np.arange(round(.09*rate))/rate
        x = (rng.normal(0,.28,len(t))+np.sin(2*np.pi*1650*t)*.6+np.sin(2*np.pi*2810*t)*.22)*np.exp(-t/.008)
        place(foley, x, at, amp, pan)
        events.append({"at":at,"type":"wooden peg","amp":amp})

    # No regular pulse and no sentimental cadence: a few answered intervals.
    for at, midi, amp, pan in [
        (.9,74,.037,-.35),(2.6,81,.026,.3),
        (starts['S02']+.9,76,.03,.15),
        (starts['S04']+1.1,86,.026,.5),
        (starts['S05']+.9,81,.022,-.15),
        (starts['S06']+2.7,74,.03,-.3),
        (starts['S07']+1.2,83,.034,.2),
        (starts['S07']+3.8,88,.023,-.4),
        (starts['S07']+5.5,81,.016,.3),
    ]:
        if at < starts['T01']-.5: pluck(at,midi,amp,pan=pan)

    t = np.arange(n)/rate
    # Correlated low air, independent fine turbulence, opening into stereo after release.
    base = band_noise(duration, 65, 1200)
    fine = band_noise(duration, 300, 3200)
    level = .0035 + .003*np.sin(t*.37)**2
    level += .009/(1+np.exp(-(t-starts['S04'])*2))
    level *= 1 - .97*np.exp(-((t-release)/.31)**2)
    level *= np.minimum(1,t/.6)*np.clip((starts['T01']+.35-t)/1.6,0,1)
    air[:,0]=(base+fine*.23)*level
    air[:,1]=(np.roll(base,173)+fine*.18)*level

    peg(1.05,.020)
    peg(starts['S02']+.65,.023)
    peg(release,.042,.1)
    peg(starts['S06']+2.60,.030,-.3)
    cloth(starts['S02']+1.4,1.7,.007,-.1)
    cloth(starts['S03']+.25,min(1.2,lengths['S03']-.5),.011,.15)
    cloth(starts['S04']+.08,1.55,.025,-.15)
    cloth(starts['S04']+2.65,1.7,.012,.4)
    cloth(starts['S05']+.9,1.5,.010,.3)
    cloth(starts['S06']+2.7,1.1,.018,-.3)
    cloth(starts['S07']+.6,2.0,.009,.2)

    # Small airy reflections on the instrument only, no score under the decisive break.
    for offset,gain in [(.137,.10),(.283,.055),(.461,.028)]:
        delay=round(offset*rate)
        score[delay:,0] += score[:-delay,1].copy()*gain
        score[delay:,1] += score[:-delay,0].copy()*gain
    duck=1-.98*np.exp(-((t-release)/.45)**4)
    score*=duck[:,None]
    fade=np.clip((starts['T01']+1.0-t)/1.8,0,1)
    score*=fade[:,None]

    folder=root/directory
    folder.mkdir(parents=True,exist_ok=False)
    result={"sampleRate":rate,"frames":frame,"samples":n,"duration":duration,"events":events,"stems":{}}
    for name,data in [('score',score),('air',air),('foley',foley)]:
        peak=float(np.max(np.abs(data)))
        if peak>.8: raise ValueError('Stem exceeds headroom')
        with wave.open(str(folder/(name+'.wav')),'wb') as file:
            file.setnchannels(2);file.setsampwidth(2);file.setframerate(rate)
            file.writeframes((data*32767).astype('<i2').tobytes())
        result['stems'][name]={"peak":peak,"path":str((folder/(name+'.wav')).relative_to(root))}
    (folder/'cues.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    render(*sys.argv[1:])
