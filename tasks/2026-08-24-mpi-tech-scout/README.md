# mpi-tech-scout

Created: 2026-08-24 — GitLab issue **scds-infra#236** (Vikunja Work #411)

## Goal
Tech-scouting evaluation of MPI (Message Passing Interface) for potential
multi-node parallel workloads on the sc1 HPC cluster: core concepts, fit
against the current/planned sc1 stack, and a hands-on multi-node "hello
world" proof-of-concept. The deliverable is **`findings.md`** — written to be
pasted directly into the ticket.

## Layout
- `findings.md` — the evaluation: concepts, fit analysis, hands-on proof, recommendation.
- `boxman/conf.yml` — throwaway 2-VM lab definition (mirrors `../2026-06-11-saltstack-lab/boxman/conf.yml`'s shape).
- `setup-mpi.sh` — post-provision: installs OpenMPI, wires SSH trust node1→node2, compiles `src/hello.c`.
- `src/hello.c` — minimal MPI program: rank/hostname print, one send/recv, one `MPI_Reduce`.
- `run.sh` — thin driver (`up` / `setup` / `mpitest` / `ssh <vm>` / `status` / `destroy`).
- `notes.md` — running log + raw command output + doc sources.

## External repos / dependencies
- **boxman** — `$REPOS_ROOT/boxman` on sc1 (`~/git/boxman`), run from the
  `boxman` conda env (`~/.conda/envs/boxman/bin/boxman`). Provisions the 2 lab
  VMs, same tool/pattern as `saltstack-lab` and `pg-ha-boxman-trial`.
- **hpccluster** (`$REPOS_ROOT/hpccluster`) and **hpc-k8s-infra**
  (`$REPOS_ROOT/hpc-k8s-infra`) — referenced read-only for the fit analysis in
  `findings.md` §2 (Slurm deployment status, sc1-talos cluster contents). Not
  touched or modified.

## Where this runs
Authored on the workstation, **executed on `sc1` (scds001)** — same workflow
as `saltstack-lab`: edit here → sync to sc1 → run boxman + the scripts on sc1.
This session had direct SSH access to sc1 (`ssh sc1`) and ran everything from
there directly; a clean sync is `rsync -az` (or `git push`/`pull` once this
task folder is committed) rather than in-place edits on sc1.

## How to run (on sc1)
```bash
cd ~/git/work-env/tasks/2026-08-24-mpi-tech-scout
BOXMAN=~/.conda/envs/boxman/bin/boxman ./run.sh up       # build template + clone the 2 VMs
./run.sh setup                                            # install OpenMPI, wire SSH, compile hello.c
./run.sh mpitest                                          # mpirun hello-world across both nodes
./run.sh destroy                                          # tear the lab down
```

## Inputs
None external — `src/hello.c` is the only input, written for this task.

## Outputs
VMs live briefly in libvirt on sc1 (`~/workspaces/mpi-lab`); torn down
immediately after the hands-on run — nothing persists on sc1. Command output
captured in `notes.md` and `findings.md` §3. Nothing large is committed here.
