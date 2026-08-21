#!/usr/bin/env python3
"""ep-report — status + spend rollup for a vertical-series episode manifest.

Prints a markdown report (shots table, gate verdicts, spend vs cap) and, with
--write, saves it as <ws>/ep-report.md. BQ reconciliation note included —
manifest costs are planned/attempt-counted; billing truth arrives via
tools/gcp/bq.cjs ~24h later.
"""
import argparse
import json
import os
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    with open(os.path.join(args.series, "series-config.json")) as f:
        cfg = json.load(f)
    with open(args.manifest) as f:
        m = json.load(f)

    lines = [f"# {cfg['display_title']} — Ep {m['episode']} report ({m['slug']})", ""]
    lines += ["| shot | sec | status | qa | clone | dialogue | cost |",
              "|---|---|---|---|---|---|---|"]
    for s in m["shots"]:
        v = s.get("verdicts", {})
        qa = v.get("clip_qa", {}).get("exit", "—")
        cl = v.get("clone_check", {}).get("exit", "—") if s.get("motion") else "n/a"
        dg = v.get("dialogue_check", "n/a") if s.get("dialogue") else "n/a"
        cost = f"${s['cost_usd']:.2f}" if s.get("cost_usd") else "—"
        lines.append(f"| {s['id']} | {s.get('seconds', '—')} | {s.get('status')} "
                     f"| {qa} | {cl} | {dg} | {cost} |")

    spend = m.get("spend", {})
    cap = cfg["budget"]["per_episode_usd"]
    veo = spend.get("veo_usd", 0)
    lines += ["", f"**Spend:** Veo ${veo:.2f} (attempt-counted) · nano {spend.get('nano_images', 0)} imgs "
                  f"(≈${spend.get('nano_images', 0) * 0.15:.2f}) · QA ≈${spend.get('qa_usd', 0):.2f} "
                  f"· **cap ${cap}**",
              "", "_Manifest costs are planned; reconcile with tools/gcp/bq.cjs (~24h lag) "
                  "and tools/cost-report.cjs at wrap._"]
    if m.get("computed_timeline"):
        total = m["computed_timeline"][-1]["end"]
        lines += ["", f"**Cut length:** {total:.2f}s "
                      f"(contract {cfg['format']['target_seconds']})"]
    report = "\n".join(lines)
    print(report)
    if args.write:
        ws = os.path.dirname(os.path.abspath(args.manifest))
        with open(os.path.join(ws, "ep-report.md"), "w") as f:
            f.write(report + "\n")
        print(f"\nwrote {os.path.join(ws, 'ep-report.md')}")


if __name__ == "__main__":
    sys.exit(main())
