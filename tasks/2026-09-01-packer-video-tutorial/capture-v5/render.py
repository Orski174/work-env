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

ROOT = Path('/var/lib/scds-recording/v5')
RAW = ROOT / 'packer-tutorial-v5-raw.mp4'
LOG = ROOT / 'packer-v5-action.log'
SCENES = ROOT / 'packer-v5-scenes.jsonl'
CUT = ROOT / 'packer-tutorial-v5-trimmed.mp4'
FINAL = ROOT / 'packer-tutorial-v5-final.mp4'
WORK = ROOT / 'packer-v5-render'
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
    assert len(begins) == len(ends) == 20
    assert {r['label'] for r in scenes if r['phase'] == 'reviewed'} == set(begins)
    duration = skill.probe_duration(RAW)
    raw_frames = int(sp.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                     '-show_entries', 'stream=nb_frames', '-of', 'csv=p=0', str(RAW)]))
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
    frame_ranges = skill.merge([(math.floor(s*FPS), min(raw_frames, math.ceil(e*FPS))) for s, e in kept])
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
    texts = {
        '01-desktop': 'Build a Rocky Linux image with Packer.',
        '02-terminal': 'Open a terminal. Packer, KVM and boxman are installed.',
        '03-values': 'Open the values sheet beside the terminal.',
        '04-side-by-side': 'Keep values visible; copy long content.',
        '05-workspace': 'Create an empty build directory.',
        '06-copy-templates': 'Copy the supplied templates and scripts.',
        '07-template': 'The HCL stays unchanged; demo.env supplies its values.',
        '08-provisioning': 'Use host CPU; clean cloud-init last.',
        '09-values-again': 'Return to the values sheet.',
        '10-values-copy': 'Copy all: Ctrl+A, Ctrl+C.',
        '11-values-paste': 'Paste: Ctrl+Shift+V. Save: Ctrl+D.',
        '12-prepare': 'Generate credentials, then fmt and validate. Formatting is a no-op.',
        '12b-private-files': 'Ignore rendered passwords, private logs, seeds and caches.',
        '13-build-script': 'build.sh loads the values and runs Packer.',
        '14-build': 'Run the real Packer build.',
        '15-boot-script': 'boot.sh starts boxman, then sets the configured hostname.',
        '16-boot': 'Boot the built image. Password-bearing logs stay private.',
        '17-proof-script': 'One SSH proof from the actual clone.',
        '18-proof': 'demo-node: Rocky 9.8, baked packages, guest agent and cloud-init.',
        '19-finish': 'Done: reusable image and working clone. Templates included.',
    }
    labels = list(begins)
    captions = []
    skips = []
    boundary = lambda value: round(mapped(value)*FPS)/FPS
    for i, label in enumerate(labels):
        start = boundary(begins[label]) if i else 0
        end = boundary(begins[labels[i+1]]) if i+1 < len(labels) else total
        caption_end = end
        if label in ('14-build', '16-boot'):
            gaps = [(b['raw_first']-a['raw_last'], b) for a,b in zip(edit, edit[1:])
                    if a['raw_last']/FPS >= submitted[label]
                    and b['raw_first']/FPS <= ends[label]]
            gap, following = max(gaps, key=lambda pair: pair[0])
            assert gap/FPS > 5, 'expected a genuine build/boot wait to cut'
            caption_end = following['out_first']/FPS
            assert boundary(submitted[label]) < caption_end < end
            text = 'TIME SKIP: '+('build' if label == '14-build' else 'boot')+' wait cut.'
            skips.append(dict(label=label, at=caption_end, removed_seconds=gap/FPS,
                              submitted=boundary(submitted[label])))
            captions.append(dict(label=label+'-skip', start=caption_end, end=end, text=text))
        captions.append(dict(label=label, start=start, end=caption_end, text=texts[label]))
    captions.sort(key=lambda caption: caption['start'])
    for c in captions:
        c['chars_per_second'] = len(c['text'])/(c['end']-c['start'])
        assert c['chars_per_second'] <= 15, c
    filters = []
    font = ImageFont.truetype(FONT, 30)
    for i, c in enumerate(captions):
        start, end = c['start'], c['end']
        wrapped = '\n'.join(textwrap.wrap(c['text'], width=102))
        assert len(wrapped.splitlines()) <= 3
        assert max(font.getlength(line) for line in wrapped.splitlines()) <= 1840
        textfile = WORK / f'caption-{i:02d}.txt'
        textfile.write_text(wrapped)
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
                    duration=total, edit=edit, captions=captions, skips=skips,
                    actions=[dict(raw_start=s, raw_end=e, kind=k,
                                  start=mapped(s), end=mapped(e)) for s,e,k in actions],
                    scenes=[dict(label=label, start=mapped(begins[label]),
                                 completed=mapped(ends[label])) for label in labels])
    (WORK/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Wrote {FINAL}: {total:.3f}s, {cursor} frames', flush=True)


if __name__ == '__main__':
    main()
