#!/usr/bin/env python3
"""Double the approved tape image without interpreting or restoring its noise."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repair_color(output):
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(output)]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    if all(video.get(k) == "bt709" for k in ["color_space", "color_transfer", "color_primaries"]):
        return {"needed": False}
    candidate = output.with_name("film-color-candidate.mp4")
    if candidate.exists():
        raise FileExistsError(candidate)
    output.rename(candidate)
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(candidate),
        "-map", "0", "-c", "copy", "-bsf:v",
        "h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1:video_full_range_flag=0",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-color_range", "tv", "-movflags", "+faststart", str(output)], check=True)
    hashes = [subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(file),
        "-map", "0:v:0", "-f", "hash", "-hash", "sha256", "-"]).decode().strip()
        for file in [candidate, output]]
    assert hashes[0] == hashes[1], "Metadata repair changed decoded picture"
    return {"needed": True, "method": "H.264 and container BT.709 metadata only",
            "decodedPictureHashBefore": hashes[0], "decodedPictureHashAfter": hashes[1]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--source-version", default="v1")
    parser.add_argument("--version", default="4k-v1")
    args = parser.parse_args()
    for name in [args.source_version, args.version]:
        if not name.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Invalid version")
    root = args.workspace.resolve()
    source = root / "final" / args.source_version / "film.mp4"
    folder = root / "final" / args.version
    folder.mkdir(exist_ok=False)
    output = folder / "film.mp4"
    source_hash = sha(source)
    filters = ("scale=2160:3840:flags=bilinear,"
        "geq=lum='if(between(Y,1110,2729),p(X,Y),0)'"
        ":cb='if(between(Y,555,1364),p(X,Y),128)'"
        ":cr='if(between(Y,555,1364),p(X,Y),128)',"
        "addroi=x=0:y=1104:w=2160:h=16:qoffset=-1,"
        "addroi=x=0:y=2720:w=2160:h=16:qoffset=-1")
    command = ["ffmpeg", "-v", "error", "-nostdin", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a:0", "-vf", filters,
        "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-c:a", "copy",
        "-movflags", "+faststart", str(output)]
    subprocess.run(command, check=True)
    color_repair = repair_color(output)
    assert sha(source) == source_hash, "Approved source changed"
    packets = []
    for file in [source, output]:
        probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error",
            "-select_streams", "a:0", "-show_packets", "-show_data_hash", "sha256",
            "-of", "json", str(file)]))
        packets.append([{k: p.get(k) for k in ["pts", "dts", "duration", "size", "data_hash", "side_data_list"]}
                        for p in probe["packets"]])
    assert packets[0] == packets[1], "Audio packet content or timing changed"
    report = {"schemaVersion": 1, "source": str(source.relative_to(root)),
        "sourceSha256": source_hash, "output": str(output.relative_to(root)),
        "sha256": sha(output), "method": "bilinear 2x of approved native picture",
        "rationale": "Preserve authored tape degradation, grain and clean playback lettering",
        "dimensions": [2160, 3840], "window": [0, 1110, 2160, 1620],
        "fps": 30, "frames": 1290, "audioPacketsIdentical": True,
        "audioPacketCount": len(packets[0]), "filter": filters,
        "colorRepair": color_repair,
        "encoder": {"codec": "libx264", "profile": "high", "crf": 16, "preset": "fast"}}
    (folder / "finish.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["output", "sha256", "audioPacketsIdentical"]}, indent=2))


if __name__ == "__main__":
    main()
