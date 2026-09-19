# Notes — mpi-tech-scout

- 2026-08-24: created. Tracks scds-infra#236 (Vikunja Work #411), due 2026-08-28.
  Follows the tech-scouting shape of terraform-workspaces-eval / saltstack-lab.

## Sources (general MPI concepts, checked 2026-08-24)
- kubeflow/mpi-operator README + Kubeflow Trainer docs — https://github.com/kubeflow/mpi-operator,
  https://trainer.kubeflow.org/en/latest/legacy-v1/user-guides/mpi.html
- Open MPI docs, "Launching with Slurm" — https://docs.open-mpi.org/en/v5.0.x/launching-apps/slurm.html
- SchedMD Slurm MPI Users Guide — https://slurm.schedmd.com/mpi_guide.html
- SC'25 workshop MPI stack comparison (MI300A) — https://dl.acm.org/doi/10.1145/3731599.3767462

## Infra scoping (checked via a research fork + direct SSH to sc1, 2026-08-24)
- `hpc-k8s-infra` (sc1-talos, FluxCD k8s): infra-layer only today, zero
  mpi/pmix/openmpi/mpich/slurm hits repo-wide. GitLab #143.
- `hpccluster` (Ansible/VMs): `docs/slurm.md` — Slurm controller (service02) +
  compute (node01/02) roles, RPMs built with `slurm_build_features:
  [pmix, hwloc, lua, mysql, pam]`. Tracked by #249 (open, sprint-012), split
  from #223 (open). PMIx already staged = Slurm-MPI integration is planned.
- scds#236 itself: "learn about mpi", labels backlog/doing/infra/tech-scouting,
  sprint-012, investigate list matches the task brief verbatim.
- sc1 (scds001) resource check before provisioning: 88Gi mem free / 124Gi
  total, 347G disk free. Existing libvirt networks checked to avoid subnet
  collision (salt-lab has 192.168.77.0/24, derboukagpt 192.168.78.0/24,
  clouddev01-small/sc1-talos/etc use others) — picked 192.168.79.0/24, free.

## Hands-on run (sc1, 2026-08-24 ~18:42–18:47 UTC)
- `./run.sh up`: both VMs got leased IPs in ~15s (192.168.79.192 / .194),
  boxman's guest-agent IP probe took a few retries (normal — same pattern as
  saltstack-lab), ssh-copy-id succeeded first try on both.
- First `boxman up` attempt failed with `jinja2.exceptions.TemplateSyntaxError:
  unexpected char '\\' at 2841` — I'd over-escaped the nested quotes in the
  `admin_pass`/`chpasswd` runcmd line when copying it from
  `saltstack-lab/boxman/conf.yml`. Fixed by matching that file's exact
  (unescaped) syntax — boxman's config loader has its own Jinja2
  preprocessing quirks around that line, don't "clean up" the escaping.
- `./setup-mpi.sh`: apt install of `openmpi-bin libopenmpi-dev` pulled in
  gcc/gfortran toolchains (~ a minute), everything else (SSH keygen/trust,
  compile, hostfile) was fast. No errors.
- First `mpirun --hostfile hosts -np 4 ./hello` run: succeeded, but all 4
  ranks printed the same hostname (`mpi-base`) — cloud-init's `hostname:`
  directive only applies when the template itself boots; clones inherit the
  disk without re-running cloud-init, so every clone keeps the template's
  hostname. (Exact same finding is implicit in saltstack-lab, which sidesteps
  it by not printing hostnames.) This looked like "all ranks ran on node1" at
  first glance — verified it wasn't:
  - `mpirun --display-map hostname` showed the real JOB MAP: 2 procs on node
    "mpi-base" (=node1, since mpirun resolves its own hostfile entry that
    matches the local hostname) and 2 procs explicitly on `192.168.79.194`
    (node2) — correct placement.
  - A quick inline `bash -c "echo $(hostname -I ...)"` test through 2 SSH hops
    hit nested-quoting hell (command substitution ran locally before ever
    reaching mpirun) and printed the same IP 4x — a shell-escaping bug in my
    test, not a real result. Fixed by writing a real script file
    (`whereami.sh`) and scp'ing it to both nodes instead of trying to inline
    quote through ssh→ssh→mpirun. That gave the clean per-rank IP proof used
    in findings.md §3.
- `./run.sh destroy`: needs an interactive `y` confirmation (piped `echo y`
  since this ran non-interactively over SSH) — same pattern as boxman's other
  destroy prompts. One non-fatal error in the log: `Failed to remove storage
  volume 'vda' ... unsupported flags (0x2) in function
  virStorageBackendVolDeleteLocal` — libvirt couldn't delete the qcow2 via its
  storage API, but boxman's `_force_rmtree()` step afterward removed the whole
  `~/workspaces/mpi-lab` directory at the OS level regardless, so the disk
  file was gone either way. Verified clean: `virsh list --all` / `virsh
  net-list --all` show no mpi-lab entries, `~/workspaces/mpi-lab` doesn't
  exist, `df -h /` back to 346G free (was 347G before — noise).

