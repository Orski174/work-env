# Notes — demo-172-sc1-talos

- 2026-07-20: created. Source content pulled from a demo script drafted in another
  session's scratchpad (never persisted anywhere durable) and corrected against live state.
- 2026-07-20: verified pre-flight against live sc1 — nodes still 6/6 Ready, but flux
  `kustomization/infrastructure` is now failing (new since the source doc was written).
  Root cause: commit `16035f3` in `hpc-k8s-infra` added a `CephBlockPool` manifest without
  the Rook-Ceph operator/CRDs being installed first. Flux revision drifted from
  `main@sha1:5f451a33` (doc's snapshot) to `main@sha1:411b437b` (current).
- Decision: flag the blocker in `demo-script.md`, don't fix the cluster or hide the issue —
  demo proceeds as planned, blocker called out as a known in-progress item if it comes up.
