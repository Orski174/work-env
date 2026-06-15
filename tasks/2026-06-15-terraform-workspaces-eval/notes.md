# Notes — terraform-workspaces-eval

- 2026-06-15: created. Evaluating Terraform workspaces for prod/staging (scds-infra#87).

## User-confirmed context
- No current state (greenfield); recommended target backend = AWS S3.
- Same cloud account, envs separated by naming/tags (not separate creds/accounts).
- Only prod + staging for now.
- Demo to be run for real and output captured.

## Doc sources (current HashiCorp docs, fetched via context7, June 2026)
- terraform/cli/workspaces — workspace model, default workspace, `.terraform/` tracking.
- terraform/language/state/workspaces — "not suitable for ... separate credentials and
  access controls."
- terraform/language/backend/s3 — `<workspace_key_prefix>/<workspace_name>/<key>`, default
  prefix `env:`.
- terraform/language/expressions/references — `terraform.workspace` interpolation.

## Hands-on
- Tool: terraform v1.14.8, local backend, `hashicorp/local` provider v2.9.0.
- Re-run 2026-06-15: provider registry reachable, so the demo uses the real `local_file`
  resource (writes `env-<workspace>.txt`). (An earlier offline pass used the built-in
  `terraform_data` resource when the registry was unreachable — same proof, less tangible.)
- `demo/run.sh` output proved isolation 3 ways:
  1. separate state files: `terraform.tfstate.d/{staging,prod}/terraform.tfstate`
  2. each workspace managed its own file: `env-staging.txt` vs `env-prod.txt`, contents
     differing via `terraform.workspace`
  3. after both applies, `select staging` + `plan` => "No changes" (prod apply didn't leak)
- `terraform workspace list` showed `default`, `staging`, `* prod`.

## Outcome
- Recommendation: conditional yes — workspaces are defensible here (single account), with
  guardrails for the "wrong workspace" footgun; escape hatch to dir-per-env if envs ever
  need separate accounts/credentials. Full write-up in `findings.md`.
