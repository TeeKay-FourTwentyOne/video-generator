#!/usr/bin/env python3
"""Write cue data for the maintained local score synthesizer. No provider calls."""
import argparse
import json
from pathlib import Path


def cues():
    events=[]
    def add(at,length,midi,amp,voice='bell',pan=0):
        events.append(dict(at=at,length=min(length,38-at),midi=midi,amp=amp,voice=voice,pan=pan))
    # Same two-note motif, changed harmonic company.
    for at,root in [(0,50),(4.1,46)]:
        add(at,4.9,root,.10,'pad',-.15)
        add(at,4.9,root+7,.055,'pad',.15)
    for i in range(14):
        add(.18+i*.625,1.0,[74,69,74,81][i%4],.09 if i%2==0 else .055,'bell',(-1)**i*.3)
    add(4.1,1.8,62,.045,'servo')
    add(9.75,1.5,74,.12)
    add(11.8,1.7,69,.07,'bell',-.2)
    add(13.45,2,62,.09,'bell',.2)
    # The wheel's five-second period equals eight beats at 96 bpm.
    for note,level,pan in [(50,.09,-.2),(57,.055,.2),(64,.035,0)]:
        add(14,6.3,note,level,'pad',pan)
    for i in range(8):
        add(14.35+i*.11,1.1,[62,69,74,78,81,86,90,93][i],.035,'bell',-.45+i*.9/7)
    for i in range(8):
        add(15.625+i*.625,1.5,[74,78,81,86,81,78,76,69][i],.07,'bell',(-1)**i*.22)
    # Guide reveal strips the bed to sparse, dry events.
    for at in [20.25,22.75,25.25]:
        add(at,.12,74,.045,'tick')
        add(at,1.0,74,.08)
    add(23.4,3.4,50,.045,'pad')
    for i in range(8):
        add(23.4+i*.3125,.9,[62,69,74,78,81,78,74,69][i],.028,'bell',-.3+i*.6/7)
    # Return of the gestalt: fuller version of the same pitch material.
    for note,level,pan in [(50,.09,-.2),(57,.045,.2),(62,.04,0),(66,.025,.1)]:
        add(27,8.7,note,level,'pad',pan)
    for i in range(13):
        add(27.1+i*.625,1.6,[74,78,81,86,81,78,76,69][i%8],.077,'bell',(-1)**i*.3)
    for note,amp in [(50,.10),(57,.07),(62,.06),(66,.035),(74,.045)]:
        add(35,3,note,amp,'pad')
    add(35.1,2.9,86,.08)
    return {'duration':38,'events':sorted(events,key=lambda e:e['at'])}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('workspace',type=Path)
    args=parser.parse_args()
    output=args.workspace/'audio/cues-v1.json'
    with output.open('x') as f:json.dump(cues(),f,indent=2);f.write('\n')
    # The mixer supports a 30 fps timebase. The single, precomposed WAV starts
    # at zero and has exactly 38 seconds; this does not resample picture timing.
    mix={'schemaVersion':1,'fps':30,'frames':1140,'tracks':[{'id':'score','source':'audio/score-v1.wav','inFrame':0,'frames':1140,'atFrame':0,'highpassHz':55,'lowpassHz':12000}],'master':{'targetLufs':-19,'truePeakDbtp':-2}}
    with (args.workspace/'audio/mix-v1.json').open('x') as f:json.dump(mix,f,indent=2);f.write('\n')
    print(json.dumps({'cues':len(cues()['events']),'duration':38,'paidRequests':0}))
