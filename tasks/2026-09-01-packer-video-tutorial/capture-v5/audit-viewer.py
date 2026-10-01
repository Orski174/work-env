#!/usr/bin/env python3
"""Post-run audit. Report secret-bearing PATHS only, never secret values."""
import hashlib
import json
from pathlib import Path
import subprocess as sp

root = Path('/admin/packer-demo')
bundle = Path('/admin/packer-tutorial')
rig = Path('/var/lib/scds-recording/v5')
assert not list(root.rglob('__pycache__'))
assert not list(bundle.rglob('__pycache__'))
assert not list(bundle.rglob('*.pyc'))
assert (root/'template.pkr.hcl').read_bytes() == (bundle/'template.pkr.hcl').read_bytes()
result = sp.run(['packer', 'fmt', '-check', '-diff', str(root/'template.pkr.hcl')],
                check=True, capture_output=True)
assert not result.stdout, 'fmt must be silent and leave the template unchanged'
assert (root/'demo.env').read_bytes() == (bundle/'packer-values.txt').read_bytes()

# A disposable Git database tests the real working-tree ignore rules without
# adding .git or any audit artifacts to the viewer's directory.
audit = rig/'audit-git'
sp.run(['git', 'init', '-q', str(audit)], check=True)
git = ['git', '--git-dir='+str(audit/'.git'), '--work-tree='+str(root)]
password = (root/'.demo-password').read_bytes().strip()
secret_paths = []
for path in root.rglob('*'):
    if not path.is_file() or path.stat().st_size > 8*1024*1024:
        continue
    data = path.read_bytes()
    if password in data or b'-----BEGIN OPENSSH PRIVATE KEY-----' in data:
        relative = str(path.relative_to(root))
        sp.run(git+['check-ignore', '--no-index', '-q', relative], cwd=root, check=True)
        secret_paths.append(relative)
assert 'boxman.rendered.yml' in secret_paths
for relative in ['boxman.rendered.yml', '.boxman-up.log', '.boxman-templates/probe',
                 'workspace/probe', 'http/probe', '__pycache__/probe.pyc']:
    sp.run(git+['check-ignore', '--no-index', '-q', relative], cwd=root, check=True)
for relative in ['.demo-password', 'id_ed25519_packer', 'boxman.rendered.yml', '.boxman-up.log']:
    assert (root/relative).stat().st_mode & 0o077 == 0, relative
report = dict(template_sha256=hashlib.sha256((root/'template.pkr.hcl').read_bytes()).hexdigest(),
              fmt_silent=True, values_match=True, bytecode_absent=True,
              all_detected_secret_files_ignored=True,
              secret_paths=sorted(secret_paths), source_files=sorted(p.name for p in bundle.iterdir()))
(rig/'viewer-audit.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
