#!/usr/bin/env bash
#
# videofx.sh — small ffmpeg toolkit for compositing/modifying videos.
#
# Commands:
#   flicker   Alternate (strobe) between two video segments where they overlap,
#             then let the longer segment play out normally.
#
# Run `videofx.sh <command> --help` for command-specific usage.
#
set -euo pipefail

PROG=$(basename "$0")

die()  { printf 'error: %s\n' "$*" >&2; exit 1; }
warn() { printf 'warning: %s\n' "$*" >&2; }

# Convert a timecode to seconds (float). Accepts SS(.mmm), MM:SS(.mmm), HH:MM:SS(.mmm).
to_seconds() {
  awk -v t="$1" 'BEGIN{
    n = split(t, a, ":");
    if (n == 1)      printf "%.6f", a[1] + 0;
    else if (n == 2) printf "%.6f", a[1]*60 + a[2];
    else if (n == 3) printf "%.6f", a[1]*3600 + a[2]*60 + a[3];
    else             exit 1;
  }' || die "could not parse time: $1"
}

# Float helpers (awk so we are not at the mercy of the shell's integer math).
fsub() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.6f", a-b}'; }
fgt()  { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>b)}'; }   # exit 0 if a>b
fge()  { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>=b)}'; }  # exit 0 if a>=b

has_audio() {
  [ -n "$(ffprobe -v error -select_streams a:0 -show_entries stream=index \
            -of csv=p=0 "$1" 2>/dev/null)" ]
}

usage() {
  cat >&2 <<EOF
$PROG — ffmpeg video toolkit

Usage:
  $PROG <command> [options]

Commands:
  flicker   Strobe/alternate between two clips over their overlap, then play
            the longer clip out normally.

Run "$PROG <command> --help" for details.
EOF
}

# ---------------------------------------------------------------------------
# flicker
# ---------------------------------------------------------------------------
flicker_usage() {
  cat >&2 <<EOF
Usage:
  $PROG flicker [options] VIDEO_A START_A END_A VIDEO_B START_B END_B OUTPUT

Takes a segment from each video (START..END, inclusive of START). Over the
period where the two segments overlap (= the shorter of the two segment
lengths) the output rapidly alternates between them to create a flicker/strobe.
After the overlap ends, the longer segment continues playing normally.

  Example: A = [0:30 .. 1:00] (30s), B = [0:00 .. 0:15] (15s)
           -> 15s of A/B flicker, then 15s of A alone. Output = 30s.

Times accept SS, MM:SS, or HH:MM:SS (decimals allowed).

Options:
  -f, --flicker-frames N   Frames shown from one source before switching to the
                           other. Smaller = faster strobe. (default: 2)
  -F, --flash MODE         Insert a flash frame at every switch boundary.
                           MODE = black | white. (default: none)
  -a, --audio MODE         Audio for the output:
                             main  audio of the longer clip (default)
                             a     always video A's audio
                             b     always video B's audio
                             mix   blend both (amix)
                             none  silent
      --crf N              x264 quality, lower = better. (default: 18)
      --preset NAME        x264 preset. (default: medium)
  -h, --help               This help.
EOF
}

cmd_flicker() {
  local flicker_frames=2 flash="" audio_mode="main" crf=18 preset="medium"
  local pos=()

  while [ $# -gt 0 ]; do
    case "$1" in
      -f|--flicker-frames) flicker_frames="${2:?}"; shift 2;;
      -F|--flash)          flash="${2:?}"; shift 2;;
      -a|--audio)          audio_mode="${2:?}"; shift 2;;
      --crf)               crf="${2:?}"; shift 2;;
      --preset)            preset="${2:?}"; shift 2;;
      -h|--help)           flicker_usage; exit 0;;
      --)                  shift; while [ $# -gt 0 ]; do pos+=("$1"); shift; done;;
      -*)                  die "unknown option: $1 (see '$PROG flicker --help')";;
      *)                   pos+=("$1"); shift;;
    esac
  done

  [ "${#pos[@]}" -eq 7 ] || { flicker_usage; die "expected 7 positional args, got ${#pos[@]}"; }

  local A="${pos[0]}" sa="${pos[1]}" ea="${pos[2]}"
  local B="${pos[3]}" sb="${pos[4]}" eb="${pos[5]}"
  local OUT="${pos[6]}"

  [ -f "$A" ] || die "video A not found: $A"
  [ -f "$B" ] || die "video B not found: $B"
  case "$flicker_frames" in *[!0-9]*|'') die "--flicker-frames must be a positive integer";; esac
  [ "$flicker_frames" -ge 1 ] || die "--flicker-frames must be >= 1"
  case "$flash" in ''|black|white) ;; *) die "--flash must be black or white";; esac
  case "$audio_mode" in main|a|b|mix|none) ;; *) die "--audio must be main|a|b|mix|none";; esac

  # Resolve times -> durations.
  local start_a end_a start_b end_b dur_a dur_b
  start_a=$(to_seconds "$sa"); end_a=$(to_seconds "$ea")
  start_b=$(to_seconds "$sb"); end_b=$(to_seconds "$eb")
  dur_a=$(fsub "$end_a" "$start_a")
  dur_b=$(fsub "$end_b" "$start_b")
  fgt "$dur_a" 0 || die "video A segment length must be > 0 (got $dur_a s)"
  fgt "$dur_b" 0 || die "video B segment length must be > 0 (got $dur_b s)"

  # The background of the overlay must be the LONGER segment so it survives the
  # tail (eof_action=pass keeps the background once the shorter one ends).
  # A is always input 0, B is always input 1.
  local bg_v ov_v bg_file
  if fge "$dur_a" "$dur_b"; then
    bg_v="v0"; ov_v="v1"; bg_file="$A"
  else
    bg_v="v1"; ov_v="v0"; bg_file="$B"
  fi

  # Geometry/fps come from the background clip; the other is scaled to match.
  local W H FPS
  IFS=',' read -r W H <<<"$(ffprobe -v error -select_streams v:0 \
      -show_entries stream=width,height -of csv=p=0 "$bg_file")"
  [ -n "$W" ] && [ -n "$H" ] || die "could not read dimensions of $bg_file"
  FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate \
      -of csv=p=0 "$bg_file")
  case "$FPS" in ''|0/0) FPS=30;; esac

  local F="$flicker_frames" twoF=$((flicker_frames*2))

  # --- video graph ---
  local parts=()
  parts+=("[0:v]setpts=PTS-STARTPTS,fps=${FPS},scale=${W}:${H}:flags=bicubic,setsar=1[v0]")
  parts+=("[1:v]setpts=PTS-STARTPTS,fps=${FPS},scale=${W}:${H}:flags=bicubic,setsar=1[v1]")
  # Show the overlay (top) for F frames, hide it (show background) for the next F.
  parts+=("[${bg_v}][${ov_v}]overlay=enable='lt(mod(n,${twoF}),${F})':eof_action=pass[vmix]")

  local vlabel="vmix"
  if [ -n "$flash" ]; then
    local lut
    case "$flash" in
      black) lut="lutyuv=y=16:u=128:v=128";;
      white) lut="lutyuv=y=235:u=128:v=128";;
    esac
    # One flash frame at the start of every switch block.
    parts+=("[vmix]${lut}:enable='eq(mod(n,${F}),0)'[vflash]")
    vlabel="vflash"
  fi

  # --- audio graph ---
  local a_has b_has want="$audio_mode" alabel=""
  a_has=$(has_audio "$A" && echo 1 || echo 0)
  b_has=$(has_audio "$B" && echo 1 || echo 0)

  if [ "$want" = "main" ]; then
    if fge "$dur_a" "$dur_b"; then want="a"; else want="b"; fi
  fi

  case "$want" in
    a)
      if [ "$a_has" = 1 ]; then
        parts+=("[0:a]asetpts=PTS-STARTPTS[aout]"); alabel="aout"
      else warn "video A has no audio track; output will be silent"; fi
      ;;
    b)
      if [ "$b_has" = 1 ]; then
        parts+=("[1:a]asetpts=PTS-STARTPTS[aout]"); alabel="aout"
      else warn "video B has no audio track; output will be silent"; fi
      ;;
    mix)
      if [ "$a_has" = 1 ] && [ "$b_has" = 1 ]; then
        parts+=("[0:a]asetpts=PTS-STARTPTS[a0]")
        parts+=("[1:a]asetpts=PTS-STARTPTS[a1]")
        parts+=("[a0][a1]amix=inputs=2:duration=longest:dropout_transition=0[aout]")
        alabel="aout"
      elif [ "$a_has" = 1 ]; then
        warn "video B has no audio; using video A only"
        parts+=("[0:a]asetpts=PTS-STARTPTS[aout]"); alabel="aout"
      elif [ "$b_has" = 1 ]; then
        warn "video A has no audio; using video B only"
        parts+=("[1:a]asetpts=PTS-STARTPTS[aout]"); alabel="aout"
      else warn "neither clip has audio; output will be silent"; fi
      ;;
    none) ;;
  esac

  # --- assemble filtergraph (join parts with ';') ---
  local filter
  filter=$(printf '%s;' "${parts[@]}"); filter="${filter%;}"

  # --- maps + encode ---
  local maps=(-map "[${vlabel}]")
  local acodec=()
  if [ -n "$alabel" ]; then
    maps+=(-map "[${alabel}]")
    acodec=(-c:a aac -b:a 192k)
  fi

  printf '>> flicker: A[%ss..%ss=%.2fs] B[%ss..%ss=%.2fs] -> %s\n' \
    "$start_a" "$end_a" "$dur_a" "$start_b" "$end_b" "$dur_b" "$OUT" >&2
  printf '   overlay base=%s  %dx%d @ %s fps  switch every %d frame(s)%s\n' \
    "$([ "$bg_v" = v0 ] && echo A || echo B)" "$W" "$H" "$FPS" "$F" \
    "$([ -n "$flash" ] && echo "  flash=$flash" || true)" >&2

  ffmpeg -y -hide_banner \
    -ss "$start_a" -t "$dur_a" -i "$A" \
    -ss "$start_b" -t "$dur_b" -i "$B" \
    -filter_complex "$filter" \
    "${maps[@]}" \
    -c:v libx264 -crf "$crf" -preset "$preset" -pix_fmt yuv420p -r "$FPS" \
    "${acodec[@]}" \
    -movflags +faststart \
    "$OUT"

  printf '>> done: %s\n' "$OUT" >&2
}

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
[ $# -ge 1 ] || { usage; exit 1; }
cmd="$1"; shift
case "$cmd" in
  flicker)        cmd_flicker "$@";;
  -h|--help|help) usage;;
  *)              usage; die "unknown command: $cmd";;
esac
