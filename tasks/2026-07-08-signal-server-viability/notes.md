# Signal server self-hosting viability

Tracks scds-infra #148.

**Question:** can `signalapp/Signal-Server` be run as a genuine standalone server — our own
infra, talked to by real/official Signal clients, independent of Signal Foundation's own
servers?

**Short answer: no, not practically.** Every documented, hands-on attempt either stalls
permanently at the Contact Discovery Service's SGX-enclave requirement, or "succeeds" only by
stripping core protocol security features and requiring a custom-patched, non-official
client that no team member would actually be running day to day. There is no current,
maintained path that ends with "the official Signal app talks to a server we control."

---

## Sources checked

### 1. Official repo README — [signalapp/Signal-Server](https://github.com/signalapp/Signal-Server)

- Hard dependency on **FoundationDB** — "requires the FoundationDB client library to be
  installed on the host system."
- AGPLv3 licensed.
- No direct technical support for self-hosters: "we cannot provide direct technical
  support" — points instead to an unofficial community forum.
- Standard crypto export-control notice (ECCN 5D002.C.1) — a real compliance consideration
  for redistribution/deployment, not just boilerplate.
- A related module, `spam-filter`, points to a private, inaccessible repository — the public
  checkout doesn't build without excluding it.

### 2. Hands-on attempt — [softwaremill.com, "Can You Self-Host the Signal Server?"](https://softwaremill.com/can-you-self-host-the-signal-server/)

- Got the server process itself running, but only via a test-scope class
  (`LocalWhisperServerService`) with reduced functionality.
- To connect a client at all, had to fake TLS trust (DuckDNS + Let's Encrypt + manually
  injecting the root CA into the *app's own* trust store, since the client doesn't use the
  OS trust store) and exploit lax test-mode SMS verification (any code was accepted).
- **Hit a hard wall at Contact Discovery Service (CDS):**
  - Requires an SGX-style secure enclave.
  - Requires native libraries compiled specifically for x86 — won't build on macOS.
  - The container build step for those native libraries itself failed to complete, forcing
    a fallback to an Ubuntu VM.
  - Even after rebuilding the mobile app against a local `libsignal` and patching hardcoded
    domain configs, the client made **zero outgoing requests** — undiagnosed.
- Author explicitly gave up on true Signal-Server self-hosting at this point and pivoted to
  building an unrelated custom messaging server using the `libsignal` protocol library
  directly (not self-hosting Signal-Server itself).

### 3. Furthest-reaching community guide — [jtof-dev/signal-server](https://github.com/jtof-dev/signal-server) (archived, unmaintained)

- Works only by targeting **AWS EC2** specifically — not portable to arbitrary
  infrastructure.
- Requires a separate Redis cluster (Docker/bitnami), NGINX + Certbot, and a custom fork of
  Signal's registration service.
- **Only starts at all after manually stripping `zkgroup`** out of the codebase — a core
  libsignal protocol/security component, removed just to get the build to run.
- Never addresses FoundationDB or Contact Discovery Service — both are skipped entirely, not
  solved.
- Requires connecting via **a custom-patched fork of the Android client**
  (`jtof-dev/Signal-Android`). The official Signal app is not expected to, and does not,
  connect to it.
- Repo is archived as of mid-2025 with an active unfinished to-do list at the time it was
  shelved.

---

## Conclusion

The official Signal server is a real, open-source, buildable-in-principle codebase — but
turning it into something a team could actually use, with the app everyone already has
installed, is not realistically achievable:

- **FoundationDB** and a **private `spam-filter` submodule** are build-time blockers before
  you even reach the hard part.
- **Contact Discovery Service's SGX enclave + x86-only native build** is the wall every
  serious attempt either never gets past, or works around by disabling/stripping the feature
  entirely.
- The one guide that got furthest only works by removing core cryptographic protocol
  components (`zkgroup`) and requires a **forked, non-official client** — which means the
  team still wouldn't be using their normal Signal app, defeating the point of "reachable and
  functional for the team."
- No current, maintained project demonstrates the official Signal app connecting to a
  self-hosted server end-to-end.

This means a genuinely standalone, infrastructure-independent self-hosted Signal is **not** a
realistic option for #148. The #26 conclusion — self-hosted Matrix as the actual
infrastructure-independent backup — stands unchanged; #148 doesn't need to (and can't)
duplicate that property.

**Worth noting for completeness, not as a recommendation:** an unofficial middle ground
exists — [`signal-cli`](https://github.com/AsamK/signal-cli) /
[`signal-cli-rest-api`](https://github.com/bbernhard/signal-cli-rest-api) — which automates a
*real* Signal account through Signal's actual production servers via a REST wrapper, rather
than replacing those servers. That gives functional messaging/group chat, but explicitly does
**not** provide infrastructure independence from Signal Foundation — it's still Signal's
network underneath. Considered and set aside for this ticket, since it doesn't change the
"standalone server" answer and isn't being deployed as part of this finding.

---

## Disposition

- No deployment work done in `hpccluster` or `hpc-k8s-infra` — this ticket resolves as a
  documented finding, not an infra change.
- Draft comment prepared for scds-infra #148 (shown separately for approval before posting)
  summarizing this conclusion.

*Research date: 2026-07-08. Sources cited inline.*
