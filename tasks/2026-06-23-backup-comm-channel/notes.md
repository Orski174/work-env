# Backup Communication Channel — Comparison (rev. 2)

Tracks scds-infra #26.

**Updated context (rev. 2):**
- Current primary: **Microsoft Teams** (M365)
- Planned new primary: **Signal** (outcome of this evaluation, rev. 1)
- This revision re-evaluates backup options knowing Signal will be the main channel.

Signal drops out as a backup candidate — it can't be both primary and backup.
The backup must be independent of both M365 infrastructure and Signal Foundation servers.

---

## Why the primary matters for backup selection

**Teams reliability:** 23 incidents since Jan 2025, including a 19-hour cascading outage
in July 2025 that took down Teams, Exchange, and Azure together.
([messageware.com analysis](https://www.messageware.com/microsofts-july-2025-outage-a-19-hour-disruption/))
The backup for Teams needs to be off M365 entirely.

**Signal reliability:** Generally good for a small team. A few outages per year, mostly
25 min–3 hr range. ([isdown.app/signal](https://isdown.app/status/signal))
The backup for Signal needs to be off Signal Foundation infrastructure — i.e. self-hosted
or on a platform with no dependency on Signal's servers.

**Transition period:** While migrating from Teams → Signal, Teams can serve as a natural
fallback for Signal outages (everyone still has it, nothing to set up). Once Teams is
decommissioned, you need a permanent backup for Signal.

---

## Matrix (Element)

**Self-hosting vs. hosted / data control**
Fully self-hostable via Synapse (Python + PostgreSQL) or Conduit (Rust, lighter).
Docker Compose on a VPS is sufficient. Requires a publicly routable server and domain.
Data lives on your homeserver — fully independent of M365 and Signal Foundation.
Managed options: [etke.cc](https://etke.cc/) (no per-user charges), EMS (for orgs),
matrix.org free account (Element/Matrix controls data, shared infra).
([matrix.org hosting ecosystem](https://matrix.org/ecosystem/hosting/))

**Setup friction**
Admin: moderate. VPS + domain + Synapse config + PostgreSQL for sliding sync.
[2025 self-hosting write-up](https://blog.klein.ruhr/self-hosting-matrix-in-2025) calls it
"finally seamless" but it's still an ops task.
User onboarding: install Element X, register on your homeserver. Manageable.

**Mobile app quality**
Element X (iOS and Android). "Clunky but functional" per March 2026 Android reviews.
Improving steadily but still behind Signal in polish.
([Element X on Google Play](https://play.google.com/store/apps/details?id=io.element.android.x))

**Cost**
Self-host: ~$5–10/mo VPS + ~$10–15/yr domain. Light footprint: <350 MB RAM for a small team.
([self-hosting-matrix-in-2025](https://blog.klein.ruhr/self-hosting-matrix-in-2025))

**Reliability as a backup**
Infrastructure is entirely under your control and independent from both M365 and Signal.
A Signal outage or M365 outage has no impact on your Matrix homeserver.
No VPN required. Works on any internet connection.

**Federation / interop**
Fully federated open protocol. Matrix bridges to Teams and Signal both exist, which
could be useful during the Teams → Signal migration period.

**Verdict: good fit**
The only option that puts you in full control of both the data and the infrastructure.
Independent from both current primary (Teams/M365) and incoming primary (Signal).
Aligns with the direction of travel (moving off commercial platforms).
Admin overhead is the price — justified here because it's a permanent, long-lived backup,
not a throwaway.

---

## Discord

**Self-hosting vs. hosted / data control**
No self-hosting. Data lives on Discord Inc. servers.
Independent from M365 and Signal Foundation — an outage on either doesn't affect Discord.
No GDPR DPA or compliance tooling on the free tier; consumer ToS.

**Setup friction**
Admin: near-zero — create a server, share an invite link.
User onboarding: create a Discord account (email only, no phone required). Familiar to
most technical users.

**Mobile app quality**
Excellent. Consistently 4.4–4.6 on iOS and Android.

**Cost**
Free tier: unlimited members, unlimited message history, 8 MB uploads, calls up to 25.
([Discord pricing 2026](https://costbench.com/software/communication/discord/))
No per-seat business tier; Nitro is individual.

**Reliability as a backup**
18 incidents in the past 90 days (9 major outages, 9 minor), median ~53 min.
([statusfield.com/is-down/discord](https://statusfield.com/is-down/discord))
More outage-prone than Signal. For a backup channel you only need it when the primary
is already down — having the backup also flaky is a real risk.

**Federation / interop**
None. Closed platform.

**Verdict: acceptable, not ideal**
Easy to spin up and free, but the reliability record is the weakest of the candidates.
Fine if you need something running in the next hour with zero admin overhead. Less suitable
as the permanent backup for a team that just chose Signal over Teams for reliability reasons.

---

## Slack

**Self-hosting vs. hosted / data control**
No self-hosting. Data on Slack (Salesforce) servers.
Independent from M365 and Signal Foundation.

**Setup friction**
Admin: create a workspace. User onboarding: trivial.

**Mobile app quality**
Excellent. Best-in-class among the four.

**Cost**
Free tier: 90-day message history cap, 10 integrations, 5 GB storage, 1:1 calls only.
Pro: $7.25/user/mo.
([Slack pricing 2026](https://viewexport.com/post/slack-pricing))

**Reliability as a backup**
Infrastructure is independent of M365 and Signal. Generally reliable.
But the free tier's 90-day history cap is a real limitation — if the backup sits unused
for a few months, older context is hidden.

**Federation / interop**
None.

**Verdict: bad fit**
Costs money for a usable experience (free tier history cap degrades over time).
The team just moved off a Teams-class commercial platform — adding Slack, another
commercial tool with its own SaaS lock-in, as a backup is a step backward.
No meaningful advantage over Discord except app polish, which doesn't justify the cost.

---

## Signal (for reference — now the primary, not evaluated as backup)

Signal will be the new primary channel. It cannot serve as its own backup.
Signal's reliability as a primary is acceptable for a small team: occasional outages,
mostly <1 hr, a few times per year. Backup needs to cover those gaps.

---

## Recommendation

**Use Matrix (self-hosted) as the permanent backup.**

Once Teams is decommissioned, the backup for Signal must be independent of both M365 and
Signal Foundation infrastructure. A self-hosted Matrix homeserver on a cheap VPS is the
only option here that satisfies that requirement without ceding data control to a third party.
It also aligns with the direction already set by choosing Signal — the team is moving
toward open, independent infrastructure. The admin overhead (~1–2 hours to set up, minimal
ongoing maintenance) is a one-time cost for a long-lived backup that you fully control.

**For the transition period (while Teams is still running):** Teams already serves as a
natural backup for early Signal outages. No setup required — use it.

**If Matrix setup is not feasible in the short term:** Discord is the pragmatic fallback —
free, zero setup, independent infrastructure. Accept the reliability trade-off and revisit
once there's bandwidth to stand up the Matrix homeserver.

**Prerequisites for Matrix:**
- A VPS (any provider; ~$5–6/mo for a 1 vCPU/1 GB instance is sufficient).
- A domain name (~$12/yr).
- ~1–2 hours of admin time to deploy Synapse via Docker Compose and configure DNS.
- All team members create an Element X account on the homeserver (5 min each).
- Run a test drill before Teams is decommissioned.

---

*Research date: 2026-06-23 (rev. 2). Sources cited inline.*
