# Notes — demo-173-opencode-proxy

- 2026-07-20: created. Source content pulled from a demo script drafted in another
  session's scratchpad (never persisted anywhere durable) and corrected against live state.
- 2026-07-20: verified pre-flight against live services — proxy and watch-inject both
  healthy, litellm service still failed (missing `litellm/` compose dir, same as source doc).
- Correction from user: LiteLLM is no longer part of the architecture — `proxy.py` now does
  the OpenAI-compat translation in-process itself. Confirmed in code
  (`~/projects/claudeStuff/gateways/opencode-go/proxy.py`, `_forward_openai_compat()`
  forwards directly to `opencode.ai/zen/go/v1/chat/completions`). Rewrote the "Known gaps"
  section accordingly: dropped "rebuild litellm compose dir" as an action item, replaced
  with "disable/remove the now-dead opencode-litellm.service" as the follow-up candidate.
