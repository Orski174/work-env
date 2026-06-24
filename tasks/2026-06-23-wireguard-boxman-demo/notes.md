# Notes — wireguard-boxman-demo

## 2026-06-23 — created

Scaffolded the task. Same authoring-here / executing-on-sc1 pattern as saltstack-lab.

## 2026-06-24 — sc1 execution setup

Added sc1 run instructions to README and updated `run.sh` to prepend
`~/.conda/envs/boxman/bin` to PATH (so `subprocess.run(["boxman"])` inside the pytest
test finds the right binary without requiring manual `conda activate`).

**One-time setup on sc1 (not yet verified):**
```bash
conda activate boxman
pip install pytest invoke ansible ansible-core
# confirm hpccluster is present at ~/git/hpccluster
```

**Run workflow:**
```bash
# workstation
git push
# sc1
cd ~/git/work-env && git pull
cd tasks/2026-06-23-wireguard-boxman-demo
conda activate boxman
bash run.sh
```
