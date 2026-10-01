#!/usr/bin/env python3
"""Evidence-based skill trim, exact frame map, and a hard-separated caption band.

Run --dry-run first. All typing, clipboard keys, mouse actions and explicit
reading holds survive at 1x. Only gaps are cut; there are no excluded actions.
The edit map uses integer frames, so captions/review frames cannot drift from
the action log because of per-clip rounding.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import subprocess as sp
import textwrap

from PIL import ImageFont

ROOT = Path('/admin')
RAW = ROOT / 'packer-tutorial-v4-raw.mp4'
LOG = ROOT / 'packer-v4-action.log'
SCENES = ROOT / 'packer-v4-scenes.jsonl'
CUT = ROOT / 'packer-tutorial-v4-trimmed.mp4'
FINAL = ROOT / 'packer-tutorial-v4-final.mp4'
WORK = ROOT / 'packer-v4-render'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FPS = 12
spec = importlib.util.spec_from_file_location('skill_trim', '/admin/screen-demo-recording/scripts/trim_recording.py')
skill = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill)


def run(argv):
    sp.run(argv, check=True, stdout=sp.DEVNULL)


def parse_holds(epoch):
    holds, start = [], None
    for line in LOG.read_text().splitlines():
        fields = line.split(' ', 2)
        if fields[1] == 'read_start':
            start = float(fields[0])-epoch
        elif fields[1] == 'read_end':
            assert start is not None
            holds.append((start, float(fields[0])-epoch, 'read'))
            start = None
    assert start is None
    return holds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--captions-only', action='store_true',
                    help='reuse the verified cut; preserve/rename the old final MP4 first')
    args = ap.parse_args()
    epoch, actions = skill.load_actions(LOG)
    scenes = [json.loads(line) for line in SCENES.read_text().splitlines()]
    begins = {r['label']: r['time'] for r in scenes if r['phase'] == 'start'}
    ends = {r['label']: r['time'] for r in scenes if r['phase'] == 'completed'}
    submitted = {r['label']: r['time'] for r in scenes if r['phase'] == 'submitted'}
    assert len(begins) == len(ends) == 19
    assert {r['label'] for r in scenes if r['phase'] == 'reviewed'} == set(begins)
    duration = skill.probe_duration(RAW)
    assert max(r['time'] for r in scenes) < duration, 'raw recording is truncated'
    holds = parse_holds(epoch)
    # The reviewed completed frames are explicit ground-truth read holds.
    active = skill.active_segments(RAW, duration)
    kept = skill.build_kept(actions + holds, active, duration, cap=.4,
                            tail_hold=3, excludes=[], no_filler=[])
    for label in ('14-build', '16-boot'):
        kept += [(submitted[label], submitted[label]+5), (ends[label]-2, ends[label]+4)]
    kept = skill.merge(kept)
    # Round OUTWARDS so no logged action loses even one frame.
    frame_ranges = skill.merge([(math.floor(s*FPS), math.ceil(min(e, duration)*FPS)) for s, e in kept])
    edit, cursor = [], 0
    for first, last in frame_ranges:
        edit.append(dict(raw_first=first, raw_last=last, out_first=cursor, frames=last-first))
        cursor += last-first
    total = cursor/FPS
    assert total <= 240, f'cut exceeds four minutes: {total:.3f}s'
    for start, end, _ in actions + holds:
        assert any(c['raw_first']/FPS <= start and c['raw_last']/FPS >= end for c in edit), (start, end)
    print(json.dumps(dict(raw_duration=duration, final_duration=total,
                          kept_actions=len(actions), read_holds=len(holds),
                          segments=len(edit), frames=cursor), indent=2), flush=True)
    for clip in edit:
        print(clip, flush=True)
    if args.dry_run:
        return
    if args.captions_only:
        previous = json.loads((WORK/'manifest.json').read_text())
        assert previous['edit'] == edit and previous['frames'] == cursor
        assert abs(skill.probe_duration(CUT)-total) < 1/FPS
    else:
        WORK.mkdir(exist_ok=False)

    def mapped(raw_time):
        frame = raw_time*FPS
        for c in edit:
            if frame < c['raw_first']:
                return c['out_first']/FPS
            if frame < c['raw_last']:
                return (c['out_first']+frame-c['raw_first'])/FPS
        return total

    paths = []
    for i, c in enumerate(edit):
        if args.captions_only:
            break
        path = WORK / f'clip-{i:03d}.mp4'
        run(['ffmpeg', '-v', 'error', '-ss', str(c['raw_first']/FPS), '-i', str(RAW),
             '-frames:v', str(c['frames']), '-vf', 'setpts=PTS-STARTPTS', '-r', str(FPS),
             '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-threads', '2',
             '-pix_fmt', 'yuv420p', '-an', str(path)])
        frames = int(sp.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                     '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', str(path)]))
        assert frames == c['frames']
        paths.append(path)
    if not args.captions_only:
        listing = WORK / 'concat.txt'
        listing.write_text(''.join(f"file '{p}'\n" for p in paths))
        run(['ffmpeg', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(listing),
             '-c', 'copy', '-movflags', '+faststart', str(CUT)])
    # The submit marker is written just after Enter, not at the shell's exact
    # process start. Label rounded marker-based durations as approximate.
    wait = lambda label: f"about {round(ends[label]-submitted[label])//60}:{round(ends[label]-submitted[label])%60:02d}"
    texts = {
        '01-desktop': 'Packer to boxman: build a reusable Rocky Linux image, then boot one clone.',
        '02-terminal': 'Start on a clean desktop. Packer, KVM and boxman are already installed.',
        '03-values': 'Open packer-values.txt beside the terminal: pinned image, checksum, names and subnet.',
        '04-side-by-side': 'Keep the values sheet visible. Long values will be copied, not retyped.',
        '05-workspace': 'Create an empty work directory for this build.',
        '06-copy-templates': 'Copy the supplied viewer-files bundle (staged here as ~/packer-tutorial).',
        '07-template': 'The HCL stays unchanged: demo.env supplies the image URL, SHA-256, name and output directory.',
        '08-provisioning': 'Use the host CPU; bake in the packages once. Cloud-init cleanup is the final provisioner step.',
        '09-values-again': 'Return to the values sheet. Keep the pinned image URL and checksum together.',
        '10-values-copy': 'Select all and copy (Ctrl+A, Ctrl+C). The sheet contains only demo values and comments.',
        '11-values-paste': 'Paste into demo.env (Ctrl+Shift+V), then Ctrl+D to save. No long content is typed.',
        '12-prepare': 'prepare.sh generates disposable credentials and NoCloud data, then initializes and validates Packer.',
        '13-build-script': 'The supplied build.sh loads demo.env and runs packer build. Its complete source is visible.',
        '14-build': f'TIME SKIP — build wait shortened (real run: {wait("14-build")}). The real build produces the qcow2.',
        '15-boot-script': 'boot.sh passes the built image path to boxman and loads the private, generated demo password.',
        '16-boot': f'TIME SKIP — boot wait shortened (real run: {wait("16-boot")}). Boxman creates the template and clone.',
        '17-proof-script': 'One final proof: the supplied verify.sh connects to the clone with boxman’s SSH config.',
        '18-proof': 'The real guest reports Rocky 9.8, the baked packages, an active guest agent and completed cloud-init.',
        '19-finish': 'Done: one reusable image and a working boxman clone. Viewer templates and scripts accompany the video.',
    }
    labels = list(begins)
    captions = []
    filters = []
    font = ImageFont.truetype(FONT, 30)
    for i, label in enumerate(labels):
        start = mapped(begins[label]) if i else 0
        end = mapped(begins[labels[i+1]]) if i+1 < len(labels) else total
        wrapped = '\n'.join(textwrap.wrap(texts[label], width=102))
        assert len(wrapped.splitlines()) <= 3
        assert max(font.getlength(line) for line in wrapped.splitlines()) <= 1840
        textfile = WORK / f'caption-{i:02d}.txt'
        textfile.write_text(wrapped)
        captions.append(dict(label=label, start=start, end=end, text=texts[label]))
        filters.append(f"drawtext=fontfile={FONT}:textfile={textfile}:fontcolor=white:fontsize=30:line_spacing=8:x=(w-text_w)/2:y=(h-text_h)/2:enable='gte(t,{start})*lt(t,{end})'")
    # Draw on a SEPARATE 1920x180 video, then stack BELOW the intact screen.
    # Even oversized captions cannot modify a single terminal/editor pixel.
    graph = '[1:v]'+','.join(filters)+'[band];[0:v][band]vstack=inputs=2:shortest=1[out]'
    run(['ffmpeg', '-v', 'error', '-i', str(CUT), '-f', 'lavfi', '-i',
         f'color=c=0x101318:s=1920x180:r={FPS}', '-filter_complex', graph,
         '-map', '[out]', '-frames:v', str(cursor), '-an', '-c:v', 'libx264',
         '-crf', '18', '-preset', 'medium', '-threads', '2', '-pix_fmt', 'yuv420p',
         '-movflags', '+faststart', str(FINAL)])
    manifest = dict(raw=str(RAW), final=str(FINAL), fps=FPS, frames=cursor,
                    duration=total, edit=edit, captions=captions,
                    actions=[dict(raw_start=s, raw_end=e, kind=k,
                                  start=mapped(s), end=mapped(e)) for s,e,k in actions],
                    scenes=[dict(label=label, start=mapped(begins[label]),
                                 completed=mapped(ends[label])) for label in labels])
    (WORK/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Wrote {FINAL}: {total:.3f}s, {cursor} frames', flush=True)


if __name__ == '__main__':
    main()
