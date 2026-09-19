# MPI tech-scouting — findings (scds#236)

Tech-scouting pass on MPI (Message Passing Interface) for potential multi-node
parallel workloads on sc1. Covers core concepts, fit against the current/planned
sc1 stack, and a hands-on multi-node "hello world" proof-of-concept run on sc1
itself. Sources: kubeflow/mpi-operator + Kubeflow Trainer docs, Open MPI's
"Launching with Slurm" docs, SchedMD's Slurm MPI Users Guide, and this repo's
own `hpccluster`/`hpc-k8s-infra`/`scds-infra` repos (checked 2026-08-24).

---

## 1. Core concepts

**MPI** is a standardized API (not a single implementation) for message-passing
parallel programs — the dominant model for tightly-coupled HPC workloads
(simulation, numerical solvers) and, increasingly, multi-node ML training.

- **Process launch.** An MPI job is a fixed set of ranked processes started
  together by a launcher — `mpirun`/`mpiexec` (implementation-provided) or a
  scheduler's own launch path (e.g. Slurm's `srun` with the PMIx plugin). The
  launcher distributes ranks across nodes per a **hostfile** (`node slots=N`)
  or the scheduler's allocation, and needs either passwordless SSH between
  nodes (plain `mpirun`) or direct scheduler integration (`srun`/PMIx) to start
  remote processes.
- **Point-to-point vs. collective.** Two communication styles sit on top of a
  **communicator** (`MPI_COMM_WORLD` = all ranks): point-to-point
  (`MPI_Send`/`MPI_Recv`, one rank to another) and collective operations
  (`MPI_Bcast`, `MPI_Reduce`, `MPI_Allreduce`, `MPI_Barrier`, ...) involving
  every rank in the communicator at once, each with algorithm variants MPI
  picks dynamically by message size/topology.
- **Implementations.** **OpenMPI** and **MPICH** are the two mainstream
  open-source implementations (Intel MPI and Cray MPICH are downstream/vendor
  variants). Recent 2025/2026 benchmarking (SC'25 workshop, AMD MI300A) found
  MPICH-family stacks edging out OpenMPI on point-to-point latency and
  bandwidth on modern hardware, though results are hardware- and
  message-size-dependent — not a reason on its own to prefer one over the
  other for a first deployment. OpenMPI's tooling/docs and Slurm integration
  are the more mature/common default, which is what this scouting pass used.
- **Scheduler integration (PMIx).** Under Slurm, `mpirun` run inside a Slurm
  allocation automatically uses Slurm's launch infrastructure (no
  `--hostfile`/`--host` needed); Slurm's own `srun` can also direct-launch MPI
  processes if Slurm was built with the **PMIx** plugin. Per current Open MPI
  docs, `mpirun` is now the recommended path either way — direct `srun` launch
  is no longer meaningfully faster (Open MPI ≥ 5.0.x).

---

## 2. Fit against the sc1 stack

sc1 currently has **two separate infra tracks**, both boxman-provisioned VMs on
the same physical host (scds001):

| | `hpccluster` (Ansible/VMs) | `hpc-k8s-infra` (sc1-talos, k8s) |
|---|---|---|
| **What it is** | Traditional HPC stack: `service01/02`, `node01/02`... | FluxCD GitOps Talos k8s cluster (3 control + 3 worker + mgmt) |
| **Batch scheduler** | **Slurm — in progress.** `docs/slurm.md`: `slurm_controller` role → service02, `slurm_compute` → nodes. RPMs built with `slurm_build_features: [pmix, hwloc, lua, mysql, pam]` — **PMIx (Slurm↔MPI integration) is already a build flag.** Tracked by **#249** (open, sprint-012), split from **#223** (deploy hpccluster on sc1, open). | **None.** Infra-layer only today (cert-manager, metallb, storage, monitoring). Repo-wide grep for mpi/pmix/openmpi/mpich/slurm: zero hits. |
| **MPI today** | Not deployed, but the natural next layer once #249 lands | Would need net-new tooling — no MPI/batch operator present |

Three real options for running MPI workloads on sc1:

- **(a) Bare-metal/VM direct** — OpenMPI + SSH across boxman-provisioned VMs,
  no scheduler. Simplest to stand up (this is exactly what the hands-on POC
  below did), but no job queueing/accounting/multi-tenant fairness — fine for
  a single team's ad-hoc runs, not for shared/scheduled capacity.
- **(b) Slurm-paired** — `mpirun` inside a Slurm allocation on `hpccluster`,
  once #249 lands. **This is the natural fit**: PMIx is already staged in the
  RPM build, meaning whoever specced #249 already anticipated MPI-under-Slurm.
  Gets queueing, accounting, and fair-share scheduling essentially for free —
  the standard HPC pattern this session's research confirms is still the
  default recommendation (Open MPI's own docs assume Slurm as the common
  case).
- **(c) Kubernetes-native (Talos)** — an MPI operator (kubeflow/mpi-operator,
  or the newer Kubeflow Trainer with its Flux Framework/MPI runtime support
  added in Kubeflow Trainer v2.2, March 2026) would let MPI jobs run as
  `MPIJob` CRDs on `sc1-talos`, managing launcher/worker pods, SSH key
  distribution, and hostfile generation automatically, with gang-scheduling.
  Viable, and this is where the ML-training-adjacent MPI use cases (Horovod/
  DeepSpeed-style multi-GPU training) tend to live in 2026 — but it's **net-new
  tooling** on a cluster that currently has nothing like it, competing with
  #143's infra-layer scope.

---

## 3. Hands-on proof — multi-node MPI on sc1

Ran on sc1 itself (scds001), a throwaway 2-VM boxman lab
(`tasks/2026-08-24-mpi-tech-scout/`, same shape as the earlier `saltstack-lab`
task) — independent of both #249's in-flight Slurm work and the live Talos
cluster, so nothing shared was touched. Ubuntu 24.04 VMs, OpenMPI installed
post-provision (`apt install openmpi-bin libopenmpi-dev`), passwordless SSH
from node1 → node2, a trivial C program (`src/hello.c`: prints rank/hostname,
one `MPI_Send`/`MPI_Recv` pair, an `MPI_Reduce` collective).

```
$ mpirun --hostfile hosts -np 4 ./hello
hello from rank 0/4 on mpi-base
hello from rank 1/4 on mpi-base
hello from rank 2/4 on mpi-base
hello from rank 3/4 on mpi-base
[rank 0 on mpi-base] sent 42 to rank 3
[rank 3 on mpi-base] received 42 from rank 0
[rank 0] MPI_Reduce sum of ranks 0..3 = 6
```

(All 4 ranks print the same hostname `mpi-base` — a boxman quirk: cloud-init's
`hostname:` only applies at template build time, and VM clones inherit the
disk without re-running it, so both clones keep the template's hostname. Not
an MPI issue — `notes.md` has the same finding from the `saltstack-lab` task.)

**Real cross-node placement**, confirmed two ways since hostname couldn't be
used:

```
$ mpirun --hostfile hosts -np 4 --display-map hostname
 Data for node: mpi-base           Num slots: 2   Num procs: 2   [ranks 0, 1]
 Data for node: 192.168.79.194     Num slots: 2   Num procs: 2   [ranks 2, 3]

$ mpirun --hostfile hosts -np 4 --tag-output ./whereami.sh   # prints hostname -I
[1,0]<stdout>:192.168.79.192
[1,1]<stdout>:192.168.79.192
[1,2]<stdout>:192.168.79.194
[1,3]<stdout>:192.168.79.194
```

Ranks 0–1 landed on node1 (192.168.79.192), ranks 2–3 on node2
(192.168.79.194) — a real 2-node MPI job, launched via `mpirun`'s SSH-based
rsh launcher and a plain hostfile, with a successful point-to-point send/recv
crossing the two VMs and a working collective reduce. Lab torn down
immediately after (`./run.sh destroy`) — no VMs, networks, or disk left behind
on sc1 (verified via `virsh list --all` / `virsh net-list --all` / `df -h`
post-destroy).

---

## 4. Recommendation

- **MPI itself is proven to work on sc1's infra today** — the hands-on POC
  above ran a real 2-node job with no scheduler, in under 15 minutes of setup,
  using only `apt install openmpi-bin` and a hostfile.
- **Don't build a standalone MPI deployment now — pair it with #249.** The
  Slurm controller work already has PMIx staged in its RPM build, which means
  Slurm-launched MPI (`mpirun` inside an `salloc`/`sbatch` allocation) is
  already the intended path for `hpccluster`. Land #249, then a short
  follow-up validates the same hello-world job under Slurm instead of a raw
  hostfile — that gets queueing/accounting/fair-share essentially for free
  and avoids maintaining two separate "how do I run MPI on sc1" answers.
  **Recommended default for HPC-style MPI workloads.**
- **Kubernetes-native (kubeflow/mpi-operator on sc1-talos) is a distinct,
  separate track — pursue only if the actual driver is multi-node ML
  training** (Horovod/DeepSpeed-style), not general HPC MPI. It requires
  net-new operator tooling on a cluster that currently has none, and
  duplicates what #249 already gets for free on the Ansible side. Don't stand
  this up speculatively; revisit if/when a concrete GPU-training workload
  needs it.
- **Net:** treat this ticket as closing out with "MPI works, pair it with the
  in-flight Slurm deployment (#249) rather than building a separate path" —
  no new standalone MPI infra work needed right now.
