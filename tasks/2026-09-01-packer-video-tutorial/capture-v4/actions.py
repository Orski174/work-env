#!/usr/bin/env python3
"""Run ONE reviewed on-screen step. Never batch steps past the review gate."""
import json
import os
from pathlib import Path
import subprocess as sp
import sys
import time

os.environ.update(DISPLAY=':94', ACTION_LOG='/admin/packer-v4-action.log',
                  PYTHONPATH='/admin/fastgrab-gdp')
PYTHON = '/admin/fastgrab-venv/bin/python'
SKILL = '/admin/screen-demo-recording/scripts/'
LOG = Path(os.environ['ACTION_LOG'])
SCENES = Path('/admin/packer-v4-scenes.jsonl')
PENDING = Path('/admin/packer-v4-review-pending')
PROMPT = Path('/tmp/packer_v4_prompt_ready')
RC = Path('/tmp/packer_v4_last_rc')
START = next(float(x.split()[0]) for x in LOG.read_text().splitlines()
             if ' recording_start' in x)


def log(event):
    with LOG.open('a') as f:
        f.write(f'{time.time():.6f} {event}\n')


def mark(label, phase, **extra):
    with SCENES.open('a') as f:
        f.write(json.dumps(dict(time=time.time()-START, label=label,
                               phase=phase, **extra)) + '\n')


def helper(name, *args):
    sp.run([PYTHON, SKILL+name+'.py', *map(str, args)], check=True)


def key(*keys):
    log('type_start keys:'+' '.join(keys))
    sp.run(['xdotool', 'key', '--clearmodifiers', *keys], check=True)
    time.sleep(.3)
    log('type_end')


def park():
    helper('human_move', 1890, 460)


def focus_editor():
    helper('human_move', 1450, 250, 'click')
    park()


def focus_terminal():
    helper('human_move', 450, 420, 'click')
    park()


def wait_prompt(timeout=60):
    deadline = time.monotonic()+timeout
    while not PROMPT.exists() and time.monotonic()<deadline:
        time.sleep(.1)
    if not PROMPT.exists():
        raise TimeoutError('terminal prompt did not return')
    if int(RC.read_text()) != 0:
        raise RuntimeError('terminal command failed; inspect the screenshot')


def command(text, timeout=60, wait=True):
    focus_terminal()
    PROMPT.unlink(missing_ok=True)
    helper('human_type', text)
    key('Return')
    mark(label, 'submitted', command=text)
    if wait:
        wait_prompt(timeout)


def open_file(path):
    focus_editor()
    key('ctrl+o')
    time.sleep(.5)
    key('ctrl+a')
    helper('human_type', path)
    key('Return')
    time.sleep(.8)


def hold(seconds):
    log('read_start')
    time.sleep(seconds)
    log('read_end')


def screenshot(name):
    path = f'/admin/packer-v4-review/{name}.png'
    sp.run([PYTHON, '/admin/recording-v4/frame.py', path], check=True)
    print(path, flush=True)
    return path


if sys.argv[1] == 'ack':
    assert PENDING.read_text().strip() == sys.argv[2]
    mark(sys.argv[2], 'reviewed')
    PENDING.unlink()
    sys.exit(0)
if sys.argv[1] == 'snapshot':
    screenshot(sys.argv[2])
    sys.exit(0)
if PENDING.exists():
    raise SystemExit('First LOOK at the prior screenshot, then ack '+PENDING.read_text())
label = sys.argv[1]
mark(label, 'start')
try:
    if label == '01-desktop':
        park()
    elif label == '02-terminal':
        helper('human_move', 53, 18, 'click')
        time.sleep(1.5)
        park()
    elif label == '03-values':
        helper('human_move', 91, 18, 'click')
        time.sleep(1.5)
        park()
    elif label == '04-side-by-side':
        helper('human_drag', 1450, 51, 1468, 79)
        park()
    elif label == '05-workspace':
        command('mkdir packer-demo && cd packer-demo')
    elif label == '06-copy-templates':
        command('cp -R ~/packer-tutorial/. .')
    elif label == '07-template':
        open_file('/admin/packer-demo/template.pkr.hcl')
    elif label == '08-provisioning':
        key('ctrl+End')
    elif label == '09-values-again':
        helper('human_move', 1240, 138, 'click')
        park()
    elif label == '10-values-copy':
        key('ctrl+a', 'ctrl+c')
        copied = sp.check_output(['xclip', '-selection', 'clipboard', '-o'])
        assert copied == Path('/admin/packer-tutorial/packer-values.txt').read_bytes()
    elif label == '11-values-paste':
        command('cat > demo.env', wait=False)
        key('ctrl+shift+v')
        time.sleep(.6)
        key('ctrl+d')
        wait_prompt()
        assert Path('/admin/packer-demo/demo.env').read_bytes() == Path('/admin/packer-tutorial/packer-values.txt').read_bytes()
    elif label == '12-prepare':
        command('clear')
        command('./prepare.sh', 180)
    elif label == '13-build-script':
        open_file('/admin/packer-demo/build.sh')
    elif label == '14-build':
        command('./build.sh', 900)
    elif label == '15-boot-script':
        open_file('/admin/packer-demo/boot.sh')
    elif label == '16-boot':
        command('clear')
        command('./boot.sh', 600)
    elif label == '17-proof-script':
        open_file('/admin/packer-demo/verify.sh')
    elif label == '18-proof':
        command('clear')
        command('./verify.sh', 120)
    elif label == '19-finish':
        park()
    else:
        raise ValueError('unknown step '+label)
    mark(label, 'completed')
    hold(4 if label in ('08-provisioning', '14-build', '16-boot', '18-proof', '19-finish') else 2)
finally:
    path = screenshot(label)
    mark(label, 'review', path=path)
    PENDING.write_text(label)
