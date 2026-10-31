#!/usr/bin/env python3
"""Apply the director's frame trims, then make a texture-preserving UHD finish."""
import argparse
import hashlib
import json
import subprocess as sp
import wave
from pathlib import Path


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(command, log):
    with log.open('w') as f:
        sp.run(command, stdout=f, stderr=sp.STDOUT, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('workspace', type=Path)
    ap.add_argument('stage', choices=['native', '4k'])
    args = ap.parse_args()
    w = args.workspace
    native = args.stage == 'native'
    version = 'draft-v4' if native else '4k-v1'
    parent_version = 'draft-v3' if native else 'draft-v4'
    source_folder = w / 'final' / parent_version
    source_report = read(source_folder / 'delivery.json')
    source_movie = source_folder / 'film.mp4'
    assert sha(source_movie) == source_report['sha256']
    if not native:
        verified = read(w / 'qa' / 'draft-v4-verification.json')
        if not (verified.get('sha256') == source_report['sha256']
                and verified.get('fullDecode') is True
                and verified.get('frames') == 776
                and verified.get('audio', {}).get('dualMonoMaxDifference', 1) < 1e-5):
            raise RuntimeError('Verify the matching native cut before 4K finishing')
    folder = w / 'final' / version
    folder.mkdir(exist_ok=False)
    movie = folder / 'film.mp4'
    edit = read(w / 'edit' / f'{parent_version}.json')
    timeline = read(source_folder / 'timeline.json')
    if native:
        # Source out points are exclusive. Keep the existing gaps and tail.
        edit['segments'][5].update(inFrame=30, frames=180)
        edit['segments'][7].update(frames=134)
        at = 0
        for segment, row in zip(edit['segments'], timeline):
            row.update(frame=at, frames=segment['frames'], sourceFrame=segment['inFrame'])
            at += segment['frames']
        assert at == 776
        # Slice the uncompressed approved soundtrack at exactly the picture cuts.
        ranges = [(0, 441), (471, 791), (885, 900)]
        audio_source = w / source_report['edit']['audio']['path']
        assert sha(audio_source) == source_report['edit']['audio']['sha256']
        audio = folder / 'soundtrack.wav'
        with wave.open(str(audio_source), 'rb') as src:
            assert (src.getframerate(), src.getnchannels(), src.getsampwidth()) == (48000, 2, 2)
            params = src.getparams()
            pcm = src.readframes(src.getnframes())
        cut_pcm = b''.join(pcm[a * 1600 * 4:b * 1600 * 4] for a, b in ranges)
        assert len(cut_pcm) == 776 * 1600 * 4
        with wave.open(str(audio), 'wb') as dst:
            dst.setparams(params)
            dst.writeframes(cut_pcm)
        edit['audio'] = {'path': str(audio.relative_to(w)), 'sha256': sha(audio)}
        vf = "select='lt(n,441)+between(n,471,790)+gte(n,885)',setpts=N/(30*TB)"
        inputs = ['-i', str(source_movie), '-i', str(audio)]
        # Disable independent perceptual-noise synthesis: the authored noise is
        # mono and must decode identically in both container channels.
        audio_args = ['-map', '1:a:0', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                      '-aac_ms', '1', '-aac_is', '0', '-aac_pns', '0']
        width, height = 1080, 1920
        transform = {'method': 'integer-frame trim', 'sourceEditRanges': [
            {'startFrame': a, 'endFrameExclusive': b} for a, b in ranges],
            'audio': 'Exact matching PCM ranges; no cue relocation, fades or gain change.',
            'changes': {'C3': {'inFrame': 30, 'endFrameExclusive': 210},
                        'C4': {'inFrame': 0, 'endFrameExclusive': 134}}}
    else:
        width, height = 2160, 3840
        # The source is deliberately a cheap IR camera. Enlarge its authored
        # texture without denoising, invented detail or a cadence conversion.
        vf = ('scale=2160:3840:flags=lanczos,format=rgb24,'
              'drawbox=x=0:y=0:w=iw:h=1110:color=black:t=fill,'
              'drawbox=x=0:y=2730:w=iw:h=1110:color=black:t=fill,'
              'format=yuv420p,setsar=1')
        inputs = ['-i', str(source_movie)]
        audio_args = ['-map', '0:a:0', '-c:a', 'copy']
        transform = {'method': 'Lanczos', 'scale': 2, 'aiModel': None,
                     'reason': 'Preserve authored infrared grain, compression, faces and data strip.',
                     'audio': 'Copy the revised native AAC packets without another encode.',
                     'cameraWindow': {'x': 0, 'y': 1110, 'width': 2160, 'height': 1620}}
    vf += ',setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709'
    command = ['ffmpeg', '-hide_banner', '-nostdin', '-n', *inputs, '-map', '0:v:0',
               '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
               '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-g', '60', '-bf', '0',
               '-fps_mode', 'passthrough', '-color_range', 'tv',
               '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
               '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0',
               *audio_args, '-t', str(776 / 30), '-movflags', '+faststart', str(movie)]
    save(folder / 'transform.json', {'source': str(source_movie.relative_to(w)),
         'sourceSha256': sha(source_movie), 'transform': transform, 'command': command,
         'recipe': 'tools/motion/revise.py', 'recipeSha256': sha(__file__)})
    run(command, folder / 'encode.log')
    run(['ffmpeg', '-v', 'error', '-i', str(movie), '-f', 'null', '-'], folder / 'decode.log')
    probe = json.loads(sp.check_output(['ffprobe', '-v', 'error', '-count_frames',
                       '-show_streams', '-show_format', '-of', 'json', str(movie)]))
    v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert (v['width'], v['height'], int(v['nb_read_frames']), v['avg_frame_rate']) == (width, height, 776, '30/1')
    assert all(v[k] == 'bt709' for k in ['color_space', 'color_transfer', 'color_primaries'])
    report = {'schemaVersion': 1, 'version': version, 'title': source_report['title'],
              'output': str(movie.relative_to(w)), 'sha256': sha(movie),
              'expected': {'frames': 776, 'seconds': 776 / 30, 'width': width, 'height': height},
              'probe': probe, 'edit': edit, 'checks': {'fullDecode': True, 'frameCount': True,
              'dimensions': True, 'colourTags': True, 'sourceHashes': True},
              'parent': {'version': parent_version, 'sha256': source_report['sha256']},
              'transform': transform, 'recipe': {'path': 'tools/motion/revise.py', 'sha256': sha(__file__)},
              'directorReview': 'Draft-v3 approved subject to the two specified trims; 4K finishing explicitly authorized.',
              'audioReview': 'Matched approved source ranges; computational verification remains separate from listening.',
              'artisticApproval': False, 'publication': None}
    save(folder / 'delivery.json', report)
    save(folder / 'timeline.json', timeline)
    save(w / 'edit' / f'{version}.json', edit)
    if native:
        plan = read(w / 'edit' / 'assembly-plan-v1.json')
        for shot, segment in zip(plan['shots'], edit['segments']):
            shot['frames'] = segment['frames']
        plan['shots'][7]['beat'] = 'All eight already face the lens. Hold through source frame 133; cut at frame 134.'
        save(w / 'edit' / 'assembly-plan-v4.json', plan)
        save(w / 'film.json', plan)
    print(json.dumps({'version': version, 'frames': 776, 'seconds': 776 / 30,
                      'dimensions': [width, height], 'sha256': report['sha256']}, indent=2))


if __name__ == '__main__':
    main()
