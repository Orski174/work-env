#!/usr/bin/env python3
"""Decode every final frame and extract whole-cut + scene + command evidence."""
import json
from pathlib import Path
import subprocess as sp

from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/var/lib/scds-recording/v5/packer-v5-render')
manifest = json.loads((ROOT/'manifest.json').read_text())
video = manifest['final']
evidence = ROOT/'evidence'
evidence.mkdir(exist_ok=False)
sp.run(['ffmpeg', '-v', 'error', '-xerror', '-i', video, '-f', 'null', '-'], check=True)
probe = json.loads(sp.check_output(['ffprobe', '-v', 'error', '-count_frames',
    '-select_streams', 'v:0', '-show_entries',
    'stream=width,height,nb_read_frames,r_frame_rate,pix_fmt:format=duration,size',
    '-of', 'json', video]))
stream = probe['streams'][0]
assert (stream['width'], stream['height']) == (1920, 1080)
assert int(stream['nb_read_frames']) == manifest['frames']
assert float(probe['format']['duration']) <= 240
(ROOT/'decode-report.json').write_text(json.dumps(probe, indent=2)+'\n')


def extract(time, name):
    path = evidence/(name+'.png')
    sp.run(['ffmpeg', '-v', 'error', '-ss', str(time), '-i', video,
            '-frames:v', '1', str(path)], check=True)
    return path


def sheets(items, prefix):
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    for start in range(0, len(items), 12):
        sheet = Image.new('RGB', (1920, 3*294), '#26323d')
        draw = ImageDraw.Draw(sheet)
        for j, (path, label) in enumerate(items[start:start+12]):
            x, y = (j%4)*480, (j//4)*294
            with Image.open(path) as im:
                sheet.paste(im.resize((480,270)), (x,y))
            draw.text((x+6,y+272), label, font=font, fill='white')
        sheet.save(evidence/f'{prefix}-{start//12:02d}.png')


whole = []
for t in range(0, int(manifest['duration']), 2):
    whole.append((extract(t, f'whole-{t:03d}'), f'{t:03d}s'))
whole.append((extract(manifest['duration']-1/12, 'closing'), 'last frame'))
sheets(whole, 'whole-sheet')
scenes = []
for scene in manifest['scenes']:
    t = min(scene['completed']+.5, manifest['duration']-1/12)
    path = extract(t, 'scene-'+scene['label'])
    scenes.append((path, scene['label']))
sheets(scenes, 'scene-sheet')

# Adjacent frames prove the TIME SKIP label begins on the actual edit boundary.
for skip in manifest['skips']:
    extract(skip['at']-1/manifest['fps'], skip['label']+'-skip-before')
    extract(skip['at'], skip['label']+'-skip-at')


def mapped(time):
    for c in manifest['edit']:
        if time*12 < c['raw_first']:
            return c['out_first']/12
        if time*12 < c['raw_last']:
            return (c['out_first']+time*12-c['raw_first'])/12
    return manifest['duration']


# Native human_type text, not the keyboard-shortcut markers. Three samples per
# typed string (first characters, midpoint, full text), plus scene outcomes.
lines = Path('/var/lib/scds-recording/v5/packer-v5-action.log').read_text().splitlines()
epoch = next(float(line.split()[0]) for line in lines if ' recording_start' in line)
pending, commands = None, []
for line in lines:
    fields = line.split(' ', 2)
    if fields[1] == 'type_start':
        pending = (float(fields[0])-epoch, fields[2])
    elif fields[1] == 'type_end' and pending:
        start, text = pending
        end = float(fields[0])-epoch
        pending = None
        if text.startswith('keys:'):
            continue
        index = len(commands)
        frames = []
        for part, time in [('start', start+.15), ('mid', (start+end)/2), ('full', end-.05)]:
            frames.append((extract(mapped(time), f'command-{index:02d}-{part}'),
                           f'{index:02d} {part}: {text[:42]}'))
        commands.append(dict(command=text, raw_start=start, raw_end=end,
                             frames=[str(p) for p,_ in frames]))
        if index == 0:
            command_tiles = []
        command_tiles += frames
sheets(command_tiles, 'command-sheet')
(ROOT/'command-review.json').write_text(json.dumps(commands, indent=2)+'\n')
# Inspect the entire short dialog interval, including its initial listing
# before a filename is typed. This specifically catches rig-folder flashes.
dialog_start, dialogs, dialog_tiles = None, [], []
for line in lines:
    fields = line.split(' ', 2)
    if len(fields) < 3 or fields[1] != 'type_start':
        continue
    if fields[2] == 'keys:ctrl+o':
        assert dialog_start is None
        dialog_start = float(fields[0])-epoch
    elif fields[2] == 'keys:Return' and dialog_start is not None:
        end = float(fields[0])-epoch
        index = len(dialogs)
        start_out, end_out = mapped(dialog_start), mapped(end)
        samples = []
        t = start_out
        while t <= end_out:
            path = extract(t, f'dialog-{index:02d}-{len(samples):02d}')
            samples.append(dict(time=t, path=str(path)))
            dialog_tiles.append((path, f'dialog {index+1}: {t:.2f}s'))
            t += .25
        dialogs.append(dict(start=start_out, end=end_out, samples=samples))
        dialog_start = None
assert dialog_start is None
assert len(dialogs) == 5
sheets(dialog_tiles, 'dialog-sheet')
(ROOT/'dialog-review.json').write_text(json.dumps(dialogs, indent=2)+'\n')
print(json.dumps(dict(duration=manifest['duration'], decoded_frames=manifest['frames'],
                     scenes=len(scenes), typed_strings=len(commands),
                     whole_cut_samples=len(whole)), indent=2))
