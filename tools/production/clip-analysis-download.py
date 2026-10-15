"""Explicit setup only: download the selected public model revisions into ignored storage.

Never imported or invoked by analysis. Packages and compilers are provisioned separately.
Existing files require a matching receipt; failed downloads retain their partial files.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MODELS = {
    "qwen": ("mlx-community/Qwen3-VL-4B-Instruct-4bit", "2fd8dacbdb8f1e54b8c005f081ec5bf79c56376b", [
        "README.md", "added_tokens.json", "chat_template.jinja", "chat_template.json", "config.json",
        "generation_config.json", "merges.txt", "model.safetensors", "model.safetensors.index.json",
        "preprocessor_config.json", "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json",
        "video_preprocessor_config.json", "vocab.json"]),
    "clip": ("laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "1a25a446712ba5ee05982a381eed697ef9b435cf", [
        "open_clip_model.safetensors", "open_clip_config.json", "README.md"]),
    "whisper-model": ("ggerganov/whisper.cpp", "5359861c739e955e79d9a303bcbc70fb988958b1", ["ggml-small.bin", "README.md"]),
    "vad-model": ("ggml-org/whisper-vad", "9ffd54a1e1ee413ddf265af9913beaf518d1639b", ["ggml-silero-v6.2.0.bin", "README.md"]),
}


def identity(file):
    with file.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    return {"sha256": digest, "bytes": file.stat().st_size}


def main(destination):
    repo = Path(__file__).resolve().parents[2]
    root = Path(destination).resolve()
    if not root.is_relative_to(repo / "data"):
        raise ValueError("Model downloads belong in ignored repository data storage")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt = root / "downloads.json"
    records = json.loads(receipt.read_text()) if receipt.exists() else {}
    for key, (model, revision, files) in MODELS.items():
        folder = root / key
        folder.mkdir(exist_ok=True, mode=0o700)
        for name in files:
            file = folder / name
            url = f"https://huggingface.co/{model}/resolve/{revision}/{name}"
            record_key = f"{key}/{name}"
            if file.exists():
                if records.get(record_key) != {"url": url, **identity(file)}:
                    raise ValueError(f"Existing unverified download: {record_key}")
                continue
            partial = file.with_name(file.name + ".partial")
            print(f"Downloading {record_key}", flush=True)
            subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--retry", "2",
                            "--connect-timeout", "30", "--max-time", "1800", "--continue-at", "-",
                            "--output", str(partial), url], check=True)
            partial.rename(file)
            records[record_key] = {"url": url, **identity(file)}
            temporary = receipt.with_suffix(".tmp")
            temporary.write_text(json.dumps(records, indent=2) + "\n")
            temporary.replace(receipt)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 tools/production/clip-analysis-download.py data/tools/INSTALL/models")
    main(sys.argv[1])
