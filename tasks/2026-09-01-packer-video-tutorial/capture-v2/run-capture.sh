#!/usr/bin/env bash
set -euo pipefail

ASSETS=/admin/recording-assets
SKILL_SCRIPTS=/admin/screen-demo-recording/scripts
WORKDIR=/admin/packer-boxman-demo-v3
OUTPUT=/admin/packer-tutorial-v3-raw.mp4
ACTION_LOG=/admin/packer-v3-action.log
SCENE_LOG=/admin/packer-v3-scenes.jsonl
RECORD_LOG=/admin/packer-v3-fastgrab.log
TERMINAL_LOG=/admin/packer-v3-terminal.log
REVIEW_DIR=/admin/packer-v3-review

GO=/tmp/packer_v3_recording_go
PROMPT=/tmp/packer_v3_prompt_ready
LAST_RC=/tmp/packer_v3_last_rc
PENDING=/tmp/packer_v3_review_pending
ACK=/tmp/packer_v3_review_ack

for path in "$WORKDIR" "$OUTPUT" "$ACTION_LOG" "$SCENE_LOG" "$REVIEW_DIR"; do
  if [[ -e "$path" ]]; then
    echo "Refusing to overwrite existing v3 capture state: $path" >&2
    exit 2
  fi
done
for helper in fastgrab_record.py human_move.py human_type.py trim_recording.py; do
  if [[ ! -f "$SKILL_SCRIPTS/$helper" ]]; then
    echo "Missing screen-demo-recording helper: $SKILL_SCRIPTS/$helper" >&2
    exit 2
  fi
done

rm -f "$GO" "$PROMPT" "$LAST_RC" "$PENDING" "$ACK"
mkdir "$REVIEW_DIR"

cleanup() {
  if [[ -n "${ACTION_PID:-}" ]]; then kill "$ACTION_PID" 2>/dev/null || true; fi
  if [[ -n "${REC_PID:-}" ]]; then kill -INT "$REC_PID" 2>/dev/null || true; fi
  if [[ -n "${XTERM_PID:-}" ]]; then kill "$XTERM_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

xsetroot -solid '#101318'
xterm \
  -title 'Packer to boxman' \
  -fa 'DejaVu Sans Mono' -fs 13 \
  -bg '#101318' -fg '#e6edf3' \
  -bd '#101318' -bw 0 +sb \
  -e script -qefc "bash --noprofile --rcfile $ASSETS/packer-v2-bashrc -i" "$TERMINAL_LOG" &
XTERM_PID=$!

for _ in $(seq 1 200); do
  WINDOW="$(xdotool search --name 'Packer to boxman' 2>/dev/null | tail -1 || true)"
  [[ -n "$WINDOW" && -e "$PROMPT" ]] && break
  sleep 0.05
done
if [[ -z "${WINDOW:-}" || ! -e "$PROMPT" ]]; then
  echo 'xterm did not become ready' >&2
  exit 3
fi
xdotool windowmove "$WINDOW" 20 20
xdotool windowsize "$WINDOW" 1120 740
xdotool windowraise "$WINDOW"
xdotool windowfocus --sync "$WINDOW"

PYTHONPATH=/admin/fastgrab-gdp \
  /admin/fastgrab-venv/bin/python "$ASSETS/capture-frame.py" \
  "$REVIEW_DIR/000-preflight.png"
printf '%s\t%s\n' preflight "$REVIEW_DIR/000-preflight.png" >"$PENDING"
for _ in $(seq 1 18000); do
  if [[ -e "$ACK" && "$(cat "$ACK")" == preflight ]]; then
    rm -f "$ACK" "$PENDING"
    break
  fi
  sleep 0.1
done
if [[ -e "$PENDING" ]]; then
  echo 'preflight frame was not acknowledged' >&2
  exit 4
fi

ACTION_LOG="$ACTION_LOG" \
  /admin/fastgrab-venv/bin/python "$ASSETS/packer-v2-actions.py" \
  >/admin/packer-v3-actions.log 2>&1 &
ACTION_PID=$!

ACTION_LOG="$ACTION_LOG" PYTHONPATH=/admin/fastgrab-gdp \
  /admin/fastgrab-venv/bin/python "$ASSETS/record-raw.py" \
  "$OUTPUT" --fps 12 >"$RECORD_LOG" 2>&1 &
REC_PID=$!

for _ in $(seq 1 200); do
  grep -q ' recording_start ' "$ACTION_LOG" 2>/dev/null && break
  sleep 0.05
done
if ! grep -q ' recording_start ' "$ACTION_LOG" 2>/dev/null; then
  echo 'skill recorder did not become ready' >&2
  exit 5
fi
touch "$GO"

set +e
wait "$ACTION_PID"
ACTION_RC=$?
set -e
kill -INT "$REC_PID" 2>/dev/null || true
wait "$REC_PID"
unset REC_PID

if [[ "$ACTION_RC" -ne 0 ]]; then
  cat /admin/packer-v3-actions.log >&2
  exit 6
fi

ffprobe -v error \
  -show_entries stream=codec_name,width,height,avg_frame_rate,pix_fmt \
  -show_entries format=duration,size \
  -of default=nw=1 "$OUTPUT"

trap - EXIT
kill "$XTERM_PID" 2>/dev/null || true
