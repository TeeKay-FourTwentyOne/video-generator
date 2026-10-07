/** Extract a continuation anchor by decoded frame index, preserving join provenance.
 * Local only. The preceding take ends one frame BEFORE this anchor; its endFrameExclusive
 * is the selected frame index. This avoids repeating a held frame at a generated join.
 */
import fs from 'node:fs';
import { command, hashFile, localPath, probe } from './film.mjs';

export function joinAnchor(root, source, frame, output) {
  if (!Number.isSafeInteger(frame) || frame < 1)
    throw new Error('Continuation frame must be a positive integer with a preceding frame');
  if (typeof output !== 'string' || !output.endsWith('.png'))
    throw new Error('Continuation output must be a PNG');
  const input = localPath(root, source), out = localPath(root, output);
  const recordPath = out + '.json';
  if (fs.existsSync(out) || fs.existsSync(recordPath))
    throw new Error('Refusing to overwrite a continuation anchor or its record');
  const stream = probe(input).streams.find(s => s.codec_type === 'video');
  if (!stream) throw new Error('Continuation source has no video');
  const counted = JSON.parse(command('ffprobe', ['-v', 'error', '-select_streams', 'v:0',
    '-count_frames', '-show_entries', 'stream=nb_read_frames', '-of', 'json', input]));
  const frames = Number(counted.streams[0]?.nb_read_frames);
  if (!Number.isSafeInteger(frames) || frame >= frames)
    throw new Error('Continuation frame is outside the decoded source range');
  const sourceSha256 = hashFile(input);
  command('ffmpeg', ['-v', 'error', '-n', '-i', input, '-map', '0:v:0',
    '-vf', `select=eq(n\\,${frame})`, '-frames:v', '1', '-fps_mode', 'vfr', out]);
  const record = { schemaVersion: 1, source, sourceSha256, sourceFrames: frames,
    frame, width: stream.width, height: stream.height, frameRate: stream.avg_frame_rate,
    output, sha256: hashFile(out),
    precedingSegment: { endFrameExclusive: frame, lastFrame: frame - 1 },
    continuationSegment: { suggestedInFrame: 0 },
    note: 'Choose a moving frame by visual review. Run seam-check on the actual generated pair; this record does not certify the join.' };
  fs.writeFileSync(recordPath, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' });
  return record;
}
