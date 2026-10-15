/** Build a draft from an explicitly provisioned semantic-v1 layout. No downloads. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { REPO, readJson } from './clip-library.mjs';
import { assert, privateJson, configFor, BASELINE } from './clip-analysis-store.mjs';

export function semanticProfile(root, ocrConfig, repo = REPO) {
  root = path.resolve(root);
  const site = path.join(root, 'python/lib/python3.12/site-packages'), models = path.join(root, 'models');
  const script = path.join(REPO, 'tools/production/clip-analysis-model.py'), bridgeSource = path.join(REPO, 'tools/production/clip-analysis-whisper.cpp');
  const python = path.join(root, 'python/bin/python3.12'), requirements = path.join(REPO, 'tools/production/clip-analysis-requirements.txt');
  const runtimeFiles = [path.join(site, 'mlx_vlm/__init__.py'), path.join(site, 'open_clip/__init__.py')];
  for (const f of [python, requirements, script, ...runtimeFiles]) assert(fs.lstatSync(f).isFile(), 'Provision the documented Python environment with --copies first');
  const normalize = s => s.toLowerCase().replaceAll(/[-_.]+/g, '-');
  const installed = new Map(fs.readdirSync(site).filter(n => n.endsWith('.dist-info')).map(n => {
    const metadata = fs.readFileSync(path.join(site, n, 'METADATA'), 'utf8');
    return [normalize(metadata.match(/^Name: (.+)$/m)?.[1] ?? ''), metadata.match(/^Version: (.+)$/m)?.[1]];
  }));
  for (const line of fs.readFileSync(requirements, 'utf8').trim().split('\n')) {
    const [name, version] = line.split('==');
    assert(version && installed.get(normalize(name)) === version, 'Installed packages disagree with the qualified dependency lock');
  }
  const pythonFiles = [site, path.join(root, 'python/pyvenv.cfg'), requirements, script];
  const common = { executable: python, files: pythonFiles, settings: { script, runtimeFiles, runtimeRoots: [site] } };
  const transcript = { kind: 'whisper.cpp', executable: path.join(root, 'bridge/clip-analysis-whisper'),
    files: [bridgeSource, path.join(REPO, 'tools/production/clip-analysis-whisper/CMakeLists.txt'),
      path.join(root, 'whisper.cpp/include/whisper.h'), path.join(root, 'whisper.cpp/src/whisper.cpp'), path.join(root, 'whisper.cpp/LICENSE'),
      path.join(models, 'whisper-model'), path.join(models, 'vad-model')],
    identity: { runtimeRevision: 'whisper.cpp v1.9.5 d1be6fde11ac6e0407606b4e42fe72d34add8037; static CPU build; original-time bridge v1',
      model: 'Whisper small multilingual / Silero VAD v6.2.0', license: 'Whisper MIT; Silero MIT', quantization: 'GGML F16 weights',
      preprocessing: 'Timestamp-preserving mono float32 16 kHz; integrated VAD; original-audio segment/token getters; uncalibrated language auto-detection' },
    settings: { bridgeSource, modelFile: path.join(models, 'whisper-model/ggml-small.bin'), vadModelFile: path.join(models, 'vad-model/ggml-silero-v6.2.0.bin'),
      timestampContract: 'whisper.cpp-original-time-v1', language: 'auto', vadThreshold: .5, vadMinSpeechMs: 250, vadMinSilenceMs: 100, vadPadMs: 30, vadOverlapSeconds: .1 } };
  return configFor({ profile: 'semantic-local-v1', required: [...BASELINE, 'ocr', 'transcript', 'observations', 'embeddings'], threads: 2,
    adapters: { ocr: readJson(ocrConfig).adapters.ocr, transcript,
      observations: { ...common, kind: 'mlx-vlm', files: [...pythonFiles, path.join(models, 'qwen')],
        identity: { runtimeRevision: 'mlx-vlm 0.7.8 / mlx 0.32.4 / transformers 5.19.0; exact dependency lock and runtime files pinned',
          model: 'mlx-community/Qwen3-VL-4B-Instruct-4bit@2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b', license: 'Apache-2.0', quantization: '4 bit, group size 64',
          preprocessing: 'Ordered SDR RGB frames, 336x336 resize bound; four-frame windows, one-frame overlap; prompt blind; temperature 0; seed 0' },
        settings: { ...common.settings, modelPath: path.join(models, 'qwen'), windowFrames: 4, imageSide: 336, maxTokens: 200, seed: 0 } },
      embeddings: { ...common, kind: 'openclip', files: [...pythonFiles, path.join(models, 'clip')],
        identity: { runtimeRevision: 'open-clip-torch 3.3.0 / torch 2.14.1; exact dependency lock and runtime files pinned',
          model: 'laion/CLIP-ViT-B-32-laion2B-s34B-b79K@1a25a446712ba5ee05982a381eed697ef9b435cf', license: 'MIT', quantization: 'FP32 CPU',
          preprocessing: '224 RGB bicubic shortest-side resize and center crop; model-config mean/std; pinned SimpleTokenizer BPE, context 77; L2 normalized 512 dimensions' },
        settings: { ...common.settings, architecture: 'ViT-B-32', vectorDimensions: 512, weights: path.join(models, 'clip/open_clip_model.safetensors'),
          modelConfig: path.join(models, 'clip/open_clip_config.json'), tokenizerFile: path.join(site, 'open_clip/bpe_simple_vocab_16e6.txt.gz') } } } });
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [root, ocr, output] = process.argv.slice(2);
  assert(root && ocr && output && process.argv.length === 5, 'Usage: node tools/production/clip-analysis-profile.mjs INSTALL_ROOT OCR_CONFIG PRIVATE_OUTPUT');
  const target = path.resolve(output);
  assert(target.startsWith(path.join(REPO, 'data') + path.sep) && !fs.existsSync(target), 'Use a new ignored output path');
  privateJson(target, semanticProfile(root, ocr), true);
  console.log(JSON.stringify({ profile: path.relative(REPO, target), pinned: false, network: false }));
}
