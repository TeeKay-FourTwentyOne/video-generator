#!/usr/bin/env python3
"""veo-budget.py — pre-flight HARD STOP for all Veo generation spend.
Modelled on the MAX_COST gate in tools/study-audio.cjs.

ONE POT PER AUTHORIZATION, selected with --project (default seamless-joins):
    seamless-joins  $10.00  data/veo-budget.tsv
        The research project. Lifetime cap, Stephen 2026-08-16 — not per
        cycle, not re-interpretable.
    personal-best   $50.00  data/veo-budget-personal-best.tsv
        The film. "30-60s, 9:16, $25 max budget", Stephen 2026-08-18.
        RAISED to $50.00, Stephen 2026-08-19 (review round, seg5+seg6
        body-consistency regen): "Push the cap to $50. Don't need to use
        it all but there's room if you need it."
Caps are NOT fungible. An exhausted pot is never topped up from another one;
a new pot needs a new PROJECTS entry and the sentence that authorized it.
Anthropic-billed QA calls (clip-qa/frame-qa) are a SEPARATE ledger entirely
and do not count against any of these.

Ledger: appended BEFORE any submission so a crash
over-reports rather than under-reports. Every submission counts — Veo bills
RAI-filtered and hung operations too, at the SNAPPED duration (a 7s request
bills as 8s), so only durations {4,6,8} are accepted.

Rates ($/REQUESTED second — from the GCP billing export; PRICING.md's cheap
tiers were wrong until 2026-08-17):
    fast  720p  silent  0.08        quality (any res) silent 0.20
    fast  1080p silent  0.10        quality (any res) audio  0.40
    fast  720p  audio   0.10
    fast  1080p audio   0.12

This gate covers ALL THREE live submission doors — none of them gate
themselves, and a bare call defaults to quality/8s ($1.60-$3.20):
    1. MCP submit_veo_generation
    2. MCP create_job (mcp/video-generator/src/services/jobs.ts)
    3. data/workspace/mine-too/scratch/shot.cjs
Procedure: run `preflight` immediately before EVERY submission through any
door; submit only on exit 0. Model alias note: use veo-3.1-fast-prod /
veo-3.1-prod — bare 'veo-3.1-fast' maps to a dead preview model.

Usage:
    veo-budget.py status
    veo-budget.py preflight --model fast|quality --seconds 4|6|8 \
        --resolution 720p|1080p --audio yes|no --note "what this buys"
    veo-budget.py log --usd 0.12 --note "reconcile vs BQ export"   # +/- adj.

Exit codes: 0 ok / within cap, 2 usage error, 3 HARD STOP (would exceed cap;
nothing appended, do NOT submit).
"""
import argparse
import datetime
import os
import sys

VALID_SECONDS = (4, 6, 8)
HEADER = "date\tmodel\tseconds\tresolution\taudio\tusd\tnote\n"

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# One pot per authorization. Caps are NOT fungible: each is a separate thing
# Stephen said yes to, so an exhausted pot is never topped up from another and
# a new pot needs a new line here plus the sentence that authorized it.
PROJECTS = {
    # The research project. Hard lifetime cap, Stephen 2026-08-16.
    "seamless-joins": (10.00, os.path.join(_DATA, "veo-budget.tsv")),
    # The film. "30-60s, 9:16, $25 max budget" — Stephen 2026-08-18.
    "personal-best": (50.00, os.path.join(_DATA, "veo-budget-personal-best.tsv")),
    # AUGUST, monthly etymology series. "about 70s max ... the full budget
    # including any necessary re-shoots is $50" — Stephen 2026-08-27.
    # Pot covers Veo only; NBP/EL/QA tracked separately, all-in target <=$50.
    "august": (42.00, os.path.join(_DATA, "veo-budget-august.tsv")),
    # SEPTEMBER, monthly series ("THE COPY"). No explicit dollar quote yet:
    # "Roll with THE COPY... complete a complete first draft" — Stephen 2026-09-01.
    # PROVISIONAL conservative pot under the series' ~$50/month all-in norm;
    # flagged for ratification in the v1 flag queue. Veo only; NBP/EL/QA separate.
    "september": (30.00, os.path.join(_DATA, "veo-budget-september.tsv")),
    # FLOSS (working title): balloon-animal clown + cotton-candy heckler short.
    # "$25 cap like last time" proposed in scoping 2026-09-11; Stephen answered
    # with the three build decisions and no objection. PROVISIONAL — ratify at
    # review. Veo only; NBP/EL/QA tracked separately.
    "floss": (25.00, os.path.join(_DATA, "veo-budget-floss.tsv")),
    # SPIDER ARREST: man arrested in an alley, offers wrists, cuffed, then
    # unfolds extra spider-style legs and scurries off tittering. "30s max.
    # 9:16, social... Budget $30." — Stephen 2026-09-12. Veo pot $25 of the
    # $30 all-in; nano/QA ~$5 tracked separately.
    "spider-arrest": (25.00, os.path.join(_DATA, "veo-budget-spider-arrest.tsv")),
}
DEFAULT_PROJECT = "seamless-joins"

CAP_USD, LEDGER = PROJECTS[DEFAULT_PROJECT]

RATES = {  # (model, resolution, audio) -> $/requested-second
    ("fast", "720p", False): 0.08,
    ("fast", "1080p", False): 0.10,
    ("fast", "720p", True): 0.10,
    ("fast", "1080p", True): 0.12,
    ("quality", "720p", False): 0.20,
    ("quality", "1080p", False): 0.20,
    ("quality", "720p", True): 0.40,
    ("quality", "1080p", True): 0.40,
}


def die(msg, code=2):
    print(f"veo-budget: {msg}", file=sys.stderr)
    sys.exit(code)


def read_spent():
    if not os.path.exists(LEDGER):
        return 0.0, 0
    total, n = 0.0, 0
    with open(LEDGER) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if not line.strip() or parts[0] == "date":
                continue
            try:
                total += float(parts[5])
                n += 1
            except (IndexError, ValueError):
                die(f"malformed ledger line: {line!r} — fix {LEDGER} by hand")
    return total, n


def append(model, seconds, resolution, audio, usd, note):
    new = not os.path.exists(LEDGER)
    with open(LEDGER, "a") as f:
        if new:
            f.write(HEADER)
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"{date}\t{model}\t{seconds}\t{resolution}\t{audio}\t"
                f"{usd:.2f}\t{note}\n")
        f.flush()
        os.fsync(f.fileno())


def cmd_status():
    spent, n = read_spent()
    print(f"Veo generation spend: ${spent:.2f} of ${CAP_USD:.2f} cap "
          f"({n} ledger entries)  —  ${CAP_USD - spent:.2f} remaining")
    print(f"ledger: {os.path.normpath(LEDGER)}")
    return 0


def cmd_preflight(args):
    if args.seconds not in VALID_SECONDS:
        die(f"duration {args.seconds}s rejected: the API snaps to {{4,6,8}} by a "
            f"floor rule and BILLS THE SNAPPED VALUE. Request 4, 6 or 8 only.")
    audio = {"yes": True, "no": False}[args.audio]
    rate = RATES[(args.model, args.resolution, audio)]
    cost = rate * args.seconds
    spent, _ = read_spent()
    if spent + cost > CAP_USD:
        print(f"HARD STOP: ${spent:.2f} spent + ${cost:.2f} intended = "
              f"${spent + cost:.2f} > ${CAP_USD:.2f} cap. NOT logged. "
              f"DO NOT SUBMIT.", file=sys.stderr)
        sys.exit(3)
    # Append BEFORE the caller submits: a crash after this point over-reports.
    append(args.model, args.seconds, args.resolution, args.audio, cost, args.note)
    print(f"OK: ${cost:.2f} pre-logged ({args.model}/{args.resolution}/"
          f"audio={args.audio}/{args.seconds}s). "
          f"${spent + cost:.2f} of ${CAP_USD:.2f} now committed. Submit now; "
          f"pass model/durationSeconds/generateAudio/resolution EXPLICITLY.")
    return 0


def cmd_log(args):
    append("adjust", 0, "-", "-", args.usd, args.note)
    spent, _ = read_spent()
    print(f"logged ${args.usd:+.2f} ({args.note}). Total ${spent:.2f} of "
          f"${CAP_USD:.2f}.")
    return 0


def select_project(name):
    """Point the module-level CAP_USD/LEDGER at one authorization's pot."""
    global CAP_USD, LEDGER
    if name not in PROJECTS:
        die(f"unknown project {name!r}; known: {', '.join(sorted(PROJECTS))}")
    CAP_USD, LEDGER = PROJECTS[name]


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_project_flag(p):
        p.add_argument("--project", default=DEFAULT_PROJECT, choices=sorted(PROJECTS),
                       help=f"which authorization's pot to charge (default {DEFAULT_PROJECT}). "
                            f"Pots are separate and never fungible.")
        return p

    add_project_flag(sub.add_parser("status"))
    pf = add_project_flag(sub.add_parser("preflight"))
    pf.add_argument("--model", choices=["fast", "quality"], required=True)
    pf.add_argument("--seconds", type=int, required=True)
    pf.add_argument("--resolution", choices=["720p", "1080p"], required=True)
    pf.add_argument("--audio", choices=["yes", "no"], required=True)
    pf.add_argument("--note", required=True,
                    help="what this generation buys (goes in the ledger)")
    lg = add_project_flag(sub.add_parser("log"))
    lg.add_argument("--usd", type=float, required=True,
                    help="adjustment in USD (may be negative for BQ reconcile)")
    lg.add_argument("--note", required=True)
    args = ap.parse_args()
    select_project(args.project)
    if args.cmd == "status":
        sys.exit(cmd_status())
    if args.cmd == "preflight":
        sys.exit(cmd_preflight(args))
    if args.cmd == "log":
        sys.exit(cmd_log(args))


if __name__ == "__main__":
    main()
