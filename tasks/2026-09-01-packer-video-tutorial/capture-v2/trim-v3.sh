#!/usr/bin/env bash
set -euo pipefail

SKILL_TRIM=/admin/screen-demo-recording/scripts/trim_recording.py
RAW=/admin/packer-tutorial-v3-raw.mp4
ACTION_LOG=/admin/packer-v3-action.log
TRIMMED=/admin/packer-tutorial-v3-trimmed.mp4
RETIMED=/admin/packer-tutorial-v3-retimed.mp4
CLIPS=/admin/packer-v3-trim-clips

python3 "$SKILL_TRIM" \
  --src "$RAW" \
  --log "$ACTION_LOG" \
  --out "$TRIMMED" \
  --cap 2.0 \
  --tail-hold 20.0 \
  --clips-dir "$CLIPS"

# The action log keeps both completion shots, but their static frames would
# otherwise last only about two seconds. Hold those two proven result frames
# long enough for a viewer to read them; no workflow content is fabricated.
for clip_number in 020 033; do
  ffmpeg -loglevel error -y \
    -i "$CLIPS/clip_${clip_number}.mp4" \
    -vf 'tpad=stop_mode=clone:stop_duration=4' \
    -c:v libx264 -preset veryfast -pix_fmt yuv420p -an \
    "$CLIPS/clip_${clip_number}-held.mp4"
done

sed \
  -e 's|clip_020.mp4|clip_020-held.mp4|' \
  -e 's|clip_033.mp4|clip_033-held.mp4|' \
  "$CLIPS/concat.txt" >"$CLIPS/concat-held.txt"

ffmpeg -loglevel error -y \
  -f concat -safe 0 -i "$CLIPS/concat-held.txt" \
  -c copy "$RETIMED"

ffprobe -v error \
  -show_entries stream=codec_name,width,height,avg_frame_rate,pix_fmt \
  -show_entries format=duration,size \
  -of default=nw=1 "$RETIMED"
