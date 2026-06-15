# Terraform workspaces for prod vs. staging — findings (scds-infra#87)

Tech-scouting evaluation: do Terraform **CLI workspaces** let us share one codebase
across prod/staging (reducing duplication) while keeping state separated?

**Our situation (assumptions this evaluation is tuned to):** greenfield (no state yet),
target backend **AWS S3**, **one cloud account** with environments separated by
naming/tags, only **prod + staging** for now. Sources: current HashiCorp docs (June 2026)
— `terraform/cli/workspaces`, `terraform/language/state/workspaces`,
`terraform/language/backend/s3`. Hands-on run done locally on Terraform v1.14.8.

---

## 1. Concept — how workspaces work

A workspace is a **named, isolated state** for one and the same configuration. You start
in a workspace called `default` (it always exists and can't be deleted) and create more
with `terraform workspace new <name>`. Every workspace runs the *same* `.tf` code but
against its *own* state, so a `plan`/`apply` in one workspace never sees or touches another
workspace's resources — you must `terraform workspace select` to act on a given env.

**Where the state lives:**
- **Local backend:** the `default` workspace uses `./terraform.tfstate`; every other
  workspace gets `terraform.tfstate.d/<workspace>/terraform.tfstate`. (Confirmed by our
  hands-on run — see §3.)
- **Remote backends:** the workspace name is appended to the state path.
  - **S3 (our target):** `default` is stored at the configured `key`; other workspaces at
    `<workspace_key_prefix>/<workspace_name>/<key>`. The default prefix is `env:` and is
    configurable via `workspace_key_prefix`. So one bucket holds
    `env:/staging/<key>` and `env:/prod/<key>` side by side.
  - **Terraform Cloud / `remote`:** maps to TFC workspaces via `workspaces { prefix = "..." }`
    or a single named workspace.
- The **currently selected** workspace is tracked locally in `.terraform/` (not committed),
  so two people can be on different workspaces at once.

**Referencing it in config:** the `terraform.workspace` value holds the active name. Typical
use is namespacing so the shared code produces per-env names/tags:

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "scds-assets-${terraform.workspace}"   # scds-assets-staging / scds-assets-prod
  tags   = { Environment = terraform.workspace }
}
```

**Key limitation baked into the model:** the `backend` block is **static** — it cannot
reference `terraform.workspace` or vary per workspace. All workspaces of a config share
**one backend, one bucket, one credential/role configuration**. That single fact drives most
of the trade-offs below.

---

## 2. Comparison — workspaces vs. the alternatives

Three common ways to do prod/staging from shared code:

- **A. Directory-per-environment** — `environments/prod/` and `environments/staging/`, each
  a thin root module (own `backend` + `*.tfvars`) calling shared child modules.
- **B. One root module + per-env `-var-file`** — single config, `terraform apply -var-file=prod.tfvars`.
  (On its own this does **not** split state — you need workspaces or partial-backend
  `-backend-config` to avoid prod/staging sharing one state.)
- **C. Workspaces** — one config, `terraform workspace select prod`, one backend.

| Criterion | A. Dir-per-env | B. One module + per-env tfvars | C. Workspaces |
|---|---|---|---|
| **Code duplication** | Highest (root wiring repeated per env; mitigated by shared modules) | Low (one root; only var files differ) | **Lowest** (one root, one set of files) |
| **State isolation / blast radius** | **Strongest** — separate state *and* separate backend per env | Weak by default (one state) unless paired with workspaces/partial backend | Strong state isolation, but **all envs in one backend/bucket** (correlated backend risk) |
| **Per-env backend / creds differences** | **Easy** — each env can use a different bucket, account, role | Possible via `-backend-config` per env, but clunky | **Not supported** — backend block is static; same bucket + creds for all |
| **CI/CD ergonomics** | Clear: pipeline `cd environments/<env>`; hard to mix up | Must pass the right `-var-file` (and backend config) every run | Must `select` the right workspace every run; easy to script but invisible in the diff |
| **"Wrong env" mistake risk** | **Lowest** — env is the directory you're in | Medium — wrong `-var-file` flag | **Highest** — selected workspace is hidden CLI state; "apply to prod thinking you're in staging" is the classic footgun |
| **Scales to many envs** | Verbose but explicit; fine for a stable handful | OK | **Best** for many short-lived/identical envs (per-PR, per-dev, per-region) |

**One-line reading:** dir-per-env buys the strongest isolation at the cost of duplication;
workspaces buy the least duplication at the cost of a shared backend and a real "wrong
workspace" footgun; var-files sit in between but don't isolate state by themselves.

---

## 3. Hands-on — proving state isolation (run locally, no cloud cost)

Trivial config using the `hashicorp/local` provider (`local_file`) — no cloud, no cost.
Full code in `demo/main.tf`; driver in `demo/run.sh`. Exact sequence:

```bash
terraform init
terraform workspace new staging
terraform workspace new prod
terraform workspace select staging && terraform apply -auto-approve
terraform workspace select prod    && terraform apply -auto-approve
terraform workspace list
```

**What the run proved (real output, trimmed):**

```
== workspace list (asterisk marks current) ==
  default
* prod
  staging

== PROOF 1: separate state file per workspace ==
terraform.tfstate.d/prod/terraform.tfstate
terraform.tfstate.d/staging/terraform.tfstate

== PROOF 2: each workspace manages its OWN artifact (contents differ) ==
--- env-staging.txt ---
workspace = staging
generated for the staging environment
--- env-prod.txt ---
workspace = prod
generated for the prod environment

== PROOF 3: select staging => plan reports no changes (prod state untouched) ==
No changes. Your infrastructure matches the configuration.
```

Isolation is demonstrated three ways: (1) Terraform created a **separate state file per
workspace** under `terraform.tfstate.d/`; (2) the same code managed a **different file in
each workspace** (`env-staging.txt` vs `env-prod.txt`, with `terraform.workspace` resolving
to `staging` vs `prod`), and each workspace only knows about its own file; (3) after applying
both, re-selecting `staging` reported **no changes**, confirming the prod apply did not leak
into staging's state. On an S3 backend the same proof appears as two objects:
`env:/staging/<key>` and `env:/prod/<key>`.

---

## 4. Recommendation (paste-ready, ~5 bullets)

- **Adopt workspaces — conditionally yes for our case.** With a single AWS account and
  envs separated by naming/tags, the main argument *against* workspaces (HashiCorp:
  *"not suitable for deployments requiring separate credentials and access controls"*)
  **does not apply to us today**. Workspaces give us the lowest code duplication and clean
  per-env state on one S3 backend.
- **Guardrail the footgun.** The real risk is "applied to prod while selected on staging."
  Mitigate: always echo `terraform workspace show` before apply, make the **GitLab CI job
  select the workspace explicitly** (one job per env, env name not hand-typed), and protect
  the prod job with a manual approval + protected branch — never rely on whatever workspace a
  laptop happens to be on.
- **Namespace everything by `terraform.workspace`.** Bake `${terraform.workspace}` into
  resource names/tags and set S3 `workspace_key_prefix` so state objects are clearly
  `env:/prod/...` vs `env:/staging/...`. This prevents name collisions in the shared account.
- **Know the hard limit and the escape hatch.** Workspaces **cannot** give prod and staging
  different backends, buckets, or credentials/roles. The day we want prod in a separate
  account (stronger blast-radius isolation, separate IAM) we should **migrate prod to a
  directory-per-environment** root with its own backend — plan for that as the likely
  end-state if this graduates from "share an account" to "isolate accounts."
- **Net:** start with workspaces for prod+staging to move fast with minimal duplication;
  treat dir-per-env as the upgrade path once environments need real credential/account
  separation. (If we expect separate accounts *soon*, skip workspaces and go dir-per-env now.)
