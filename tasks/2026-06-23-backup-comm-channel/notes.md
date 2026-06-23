# Backup Communication Channel — Comparison

Tracks scds-infra #26. Evaluating Matrix, Discord, Slack, and Signal as a backup channel
for a small technical team (~5–10 people, some non-technical) whose primary tool (Slack-like)
goes down.

---

## Matrix (Element)

**Self-hosting vs. hosted / data control**
Fully self-hostable via Synapse (Python + PostgreSQL) or the lighter Conduit (Rust).
Docker Compose + Traefik is sufficient; no Kubernetes required.
Requires a publicly routable server and a domain name.
Data lives on your homeserver — you own it entirely.
Managed alternatives: matrix.org free account (shared infra, Element/Matrix controls data),
[etke.cc](https://etke.cc/) (no per-user charges, FOSS-based), Element Matrix Services (EMS,
for organisations). ([matrix.org hosting ecosystem](https://matrix.org/ecosystem/hosting/))

**Setup friction**
Admin: moderate — needs a VPS, domain, DNS records, and Synapse config.
Getting sliding sync (required for Element X) needs PostgreSQL specifically.
[2025 self-hosting write-up](https://blog.klein.ruhr/self-hosting-matrix-in-2025) describes it
as finally seamless but still a real ops task.
User onboarding: once the homeserver is up, users install Element X and register — straightforward.

**Mobile app quality**
Element X (iOS and Android) is the current recommended app; Element Classic is legacy.
User reviews describe it as "clunky but functional" (Google Play, March 2026).
Improved significantly over 2024–2025 but still lags behind Slack/Signal in polish.
([Element X on Google Play](https://play.google.com/store/apps/details?id=io.element.android.x))

**Cost**
Self-hosting: ~$5–10/mo VPS + ~$10–15/yr domain.
Resource footprint is light for small teams: <350 MB RAM, <1% CPU on a single-user instance.
etke.cc: no per-user fees; pricing on their site.
matrix.org free account: £0, but shared infrastructure.

**Reliability as a backup**
If self-hosted on the same infra as your primary tool, it goes down together — defeats the purpose.
Self-host on an external VPS, or use a managed provider, and it's independent.
No VPN required. Federation means you can always fall back to matrix.org as a bridge.

**Federation / interop**
Fully federated open protocol — users on different homeservers can join the same room.
Strong interop story: Matrix bridges to Slack, Discord, IRC, etc. exist.

**Verdict: conditional fit**
Best option if you already run a homeserver or have a sysadmin willing to set one up.
Overkill admin overhead for a pure backup channel if starting from scratch.
The data-sovereignty story is the strongest of the four.

---

## Discord

**Self-hosting vs. hosted / data control**
No self-hosting. All data lives on Discord's (Discord Inc.) servers.
ToS is consumer-oriented — no DPA, no GDPR data processing agreement for free tier,
no audit logs, no SSO. Not designed for business compliance.

**Setup friction**
Admin: near-zero — create a server in two minutes, share an invite link.
User onboarding: create a Discord account (email only, no phone required). Very familiar to
most people under 40; non-technical users typically know it from gaming/communities.

**Mobile app quality**
Excellent. One of the most polished consumer messaging apps; fast, reliable, well-designed.
Consistently 4.4–4.6 on iOS and Android.

**Cost**
Free tier: unlimited members, unlimited message history, 100 servers, 8MB upload limit,
video calls up to 25 participants.
Nitro ($2.99–$9.99/mo) is personal — no team billing tier.
([Discord pricing 2026](https://costbench.com/software/communication/discord/))

**Reliability as a backup**
18 incidents in the past 90 days (9 major outages, 9 minor), median outage duration ~53 min.
([statusfield.com/is-down/discord](https://statusfield.com/is-down/discord))
Reliability is decent but not enterprise-grade. An outage during an incident where you need
your backup is plausible.
No VPN required.

**Federation / interop**
None. Closed platform. No interop with other tools.

**Verdict: weak fit**
Fine informally if the team already uses Discord personally.
The reliability record (frequent minor outages) is a concern for a backup channel — you don't
want the backup down when you need it. ToS is consumer-focused which may matter for sensitive comms.

---

## Slack

**Self-hosting vs. hosted / data control**
No self-hosting. Data lives on Slack (Salesforce) servers.
Enterprise Key Management (EKM) available only on Enterprise Grid (large organisations).

**Setup friction**
Admin: create a workspace (2 min). Users join via invite link.
User onboarding: trivial for anyone who has used Slack.

**Mobile app quality**
Excellent. Best-in-class mobile experience among the four.

**Cost**
Free tier: 90-day message history (older messages hidden, not deleted), 10 app integrations,
5 GB file storage total, 1:1 calls only.
Pro: $7.25/user/mo; Business+: $12.50/user/mo.
([Slack pricing 2026](https://viewexport.com/post/slack-pricing),
[free tier limits](https://slack.com/help/articles/27204752526611-Feature-limitations-on-the-free-version-of-Slack))

**Reliability as a backup**
**Fatal flaw**: if your primary channel is Slack, a Slack outage takes out both simultaneously.
Even if your primary is something else, Slack's free tier lacks persistent history and call
features — it's a degraded experience as a backup.

**Federation / interop**
None. Closed platform.

**Verdict: bad fit**
Using Slack as a backup for Slack is a non-starter.
Using Slack as a backup for another tool: the 90-day history cap and 1:1-only calls
on the free tier make it a weak secondary option. Pay-to-fix, and you're paying per seat.

---

## Signal

**Self-hosting vs. hosted / data control**
No self-hosting in practice. Source code is open, but the production infrastructure runs
on Signal Foundation's servers — you cannot federate or run your own instance.
([Can you self-host Signal?](https://softwaremill.com/can-you-self-host-the-signal-server/))
Data is end-to-end encrypted; Signal Foundation has minimal metadata access by design.

**Setup friction**
Admin: zero — create a group, add members, done. No server to provision.
User onboarding: install app, verify phone number. Requires a mobile phone number (no
email-only accounts). Minor friction for users without a personal mobile they want to
register; non-issue for most.

**Mobile app quality**
Excellent. Consistently 4.8 on iOS, 4.5+ on Android. Clean, fast, minimal UI.
Desktop: dramatically improved in 2025–2026 — full multi-device sync without requiring
the phone to be online. ([Signal 2026 features](https://aboutsignal.com/news/whats-next-for-signal-in-2026-these-handy-features-are-coming-soon/))

**Cost**
Free. Nonprofit (Signal Foundation). No paid tiers.

**Reliability as a backup**
Runs on infrastructure entirely independent from your team's stack.
Signal Foundation servers are rarely down — significantly better uptime than Discord.
No VPN required. Works over any internet connection.
Groups: up to 1,000 members. Calls: up to 75 participants (raised Feb 2026).
([call limit announcement](https://aboutsignal.com/news/signal-raises-limit-for-audio-and-video-calls-to-75-participants/))

**Federation / interop**
None. Centralized, closed protocol. No bridges or interop.

**Verdict: good fit**
Ideal backup channel for a small team. Completely independent infrastructure, free, minimal
setup, excellent mobile app. The phone number requirement is the only friction, and for a
5–10 person team it's not a blocker.

---

## Recommendation

**Use Signal.**

Signal is the right choice for a small team's backup communication channel. Its infrastructure
is entirely independent of your team's stack (and of any commercial SaaS your team might use),
so it stays up when your primary tool goes down. Setup takes under ten minutes: create a Signal
group and add every team member. The mobile app is the most polished of the four, and the
desktop client now works properly without a phone present. It's free, end-to-end encrypted
by default, and run by a nonprofit — no licensing, no seat costs, no ToS concerns for a 5-person group.

Matrix is the only alternative worth considering if data sovereignty is a hard requirement
(e.g., sensitive comms that can't touch a US commercial server), but it brings real admin
overhead that isn't justified for a backup channel unless you already run the homeserver.

**Prerequisites:**
- Every team member creates a Signal account (requires a mobile phone number).
- One person creates a Signal group and adds all members.
- Test the group once with a drill message — confirm everyone receives it before you need it.

---

*Research date: 2026-06-23. Sources cited inline.*
