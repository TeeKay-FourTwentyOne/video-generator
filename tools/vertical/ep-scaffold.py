#!/usr/bin/env python3
"""Scaffold a vertical-series episode: workspace dirs + episode.json manifest template.

    python3 tools/vertical/ep-scaffold.py --series series/the-lodger --ep 1 \
        --title "The Stranger at Dusk"

Never overwrites an existing episode.json. See series/<series>/production-cycle.md.
"""
import argparse
import datetime
import json
import os
import sys

DIRS = ["refs", "frames", "clips", "final", "scratch"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True, help="series dir, e.g. series/the-lodger")
    ap.add_argument("--ep", type=int, required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--slug", help="workspace slug (default: <series-name>-epNN)")
    args = ap.parse_args()

    cfg_path = os.path.join(args.series, "series-config.json")
    with open(cfg_path) as f:
        cfg = json.load(f)

    name = cfg["series"].replace("the-", "")  # the-lodger -> lodger
    slug = args.slug or f"{name}-ep{args.ep:02d}"
    ws = os.path.join("data", "workspace", slug)
    for d in DIRS:
        os.makedirs(os.path.join(ws, d), exist_ok=True)

    manifest_path = os.path.join(ws, "episode.json")
    if os.path.exists(manifest_path):
        print(f"exists, not touching: {manifest_path}")
        return

    manifest = {
        "episode": args.ep,
        "slug": slug,
        "title": args.title,
        "series_config": cfg_path,
        "created": datetime.date.today().isoformat(),
        "status": "manifest-draft",
        "shots": [
            {
                "id": "S1",
                "seconds": 6,
                "use": [0.0, 4.0],
                "prompt": "<action prose; {{LOCK}} placeholders allowed; era suffix appended automatically>",
                "refs": [],
                "anchors": {"first": None, "last": None},
                "motion": False,
                "dialogue": None,
                "protected_retake": False,
                "qa_context": "<what should and should NOT be present>",
                "status": "pending",
                "job_id": None,
                "clip": None,
                "cost_usd": None,
                "verdicts": {}
            }
        ],
        "vo": [{"id": "V1", "text": "<line>", "t": 0.0, "file": None}],
        "captions": [],
        "stamps": {
            "title_lines": [cfg["display_title"], f"Episode {args.ep} — {args.title}"],
            "title_window": [4.0, 7.5],
            "end_card": {"text": "<Episode N+1 — Title>", "seconds": 1.5}
        },
        "audio": [],
        "timeline": [],
        "spend": {"veo_usd": 0, "nano_images": 0, "qa_usd": 0}
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"scaffolded {ws}")
    print(f"manifest:   {manifest_path}")


if __name__ == "__main__":
    sys.exit(main())
