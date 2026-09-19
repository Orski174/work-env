# Demo — OpenCode Go models in Claude Code's /model picker (scds#173)

Repo: `~/projects/claudeStuff/gateways/opencode-go`.

## Pre-flight (checked 2026-07-20)
- `opencode-proxy.service` — **active/running** ✅ (routing proxy, port 4000)
- `opencode-watch-inject.service` — **active/running** ✅ (inotify watcher on `~/.claude.json`)
- `opencode-litellm.service` — **failed** ❌ — but this is now **expected and fine**, not a
  gap to fix. See "Architecture correction" below.
- **Correction to the ticket text**: only **3** systemd units exist, not 4 — `opencode-proxy`,
  `opencode-litellm`, `opencode-watch-inject`. "injector" (`inject-models.py`) is a plain
  script invoked by the watcher on file events, not its own unit. Say 3, not 4.
- **Correction to the ticket text**: `/model` picker currently shows **22** injected entries
  (verified live in `~/.claude.json`'s `additionalModelOptionsCache`), not 14 — the provider
  set has grown since the ticket was filed.
- **Architecture correction (found during prep)**: the ticket/original doc frames the
  LiteLLM bridge as a live dependency that's "down, needs the compose dir rebuilt." That's
  stale — `proxy.py` now does the Anthropic↔OpenAI translation **in-process** itself
  (`_forward_openai_compat()`, forwards directly to `opencode.ai/zen/go/v1/chat/completions`).
  LiteLLM is no longer part of the request path for any model. `opencode-litellm.service`
  is a stale leftover unit, not a component the demo depends on.

## Script

1. **Architecture** — `proxy.py` (port 4000, confirmed listening) routes by model ID:
   - Anthropic-compat direct path (Qwen/MiniMax) → forwarded as-is to
     `https://opencode.ai/zen/go/v1/messages`
   - OpenAI-compat path (GLM/Kimi/DeepSeek/MiMo) → translated Anthropic→OpenAI **in-process**
     by `proxy.py` itself, forwarded to `opencode.ai/zen/go/v1/chat/completions`, response
     translated back. (No LiteLLM bridge involved — that dependency has been removed from
     the architecture.)
   - Unregistered model IDs → passthrough to `api.anthropic.com` using existing Claude Code auth
   - All driven by `providers.json` — no code changes needed to add a provider (show the
     "Adding a provider" section in `gateways/opencode-go/README.md`)
2. **Units** — `systemctl --user status opencode-proxy opencode-watch-inject` (both green).
   Explain the watcher: Claude Code overwrites `additionalModelOptionsCache` in `~/.claude.json`
   on every bootstrap; `watch-inject.sh` (inotifywait on `close_write`/`moved_to` for
   `.claude.json`) re-runs `inject-models.py`, which is idempotent (no-ops if entries already
   present).
3. **Live: /model picker** — open Claude Code, show the 22 OpenCode entries in `/model`,
   switch to a Qwen or MiniMax model (direct path, known-good), run a real prompt to prove
   round-trip.
   ```
   claude --model qwen3.7-max
   ```
   Optionally also demo a GLM/Kimi/DeepSeek/MiMo model to prove the in-process OpenAI-compat
   translation path directly — no LiteLLM dependency, no known gap here anymore.
4. **Live: watcher resilience** — trigger a fresh bootstrap (new `claude` session, or switch
   model again) to force Claude Code to overwrite the cache, then show
   `journalctl --user -u opencode-watch-inject -f` catching the overwrite and re-injecting
   within ~0.3s (the script's debounce sleep).
5. **Known gaps, stated plainly**:
   - MITM-proxy follow-up (unscoped)
   - Model ID staleness risk if OpenCode Go renames/retires an ID
   - `opencode-litellm.service` is a dead/obsolete unit left over from a prior architecture —
     candidate for cleanup (disable/remove), not a functional gap
   - `ANTHROPIC_BASE_URL` override is scoped to fish shell only — bash/zsh sessions don't
     get the proxy automatically.

## Close-out
- [ ] Demo delivered
- [ ] Follow-up items from Known gaps triaged into new tickets if still worth pursuing —
  strong candidate: disable/remove `opencode-litellm.service` now that it's unused.
- Comment the outcome on scds-infra#173 (mirrors to Vikunja Work #127 per the
  resolution-documentation convention) and check both Outcome boxes before closing.
