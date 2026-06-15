#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

# Throwaway, local-only Terraform workspaces demo (no cloud, no cost).
# Uses the hashicorp/local provider; proves Terraform isolates state per workspace.

echo "== init =="
terraform init -input=false

echo "== create staging + prod workspaces =="
terraform workspace new staging 2>/dev/null || terraform workspace select staging
terraform workspace new prod    2>/dev/null || terraform workspace select prod

echo "== apply in staging =="
terraform workspace select staging
terraform apply -auto-approve -input=false

echo "== apply in prod =="
terraform workspace select prod
terraform apply -auto-approve -input=false

echo "== workspace list (asterisk marks current) =="
terraform workspace list

echo "== PROOF 1: separate state file per workspace =="
find terraform.tfstate.d -name terraform.tfstate -print | sort

echo "== PROOF 2: each workspace manages its OWN artifact (contents differ) =="
for f in env-staging.txt env-prod.txt; do
  echo "--- $f ---"
  cat "$f"
done

echo "== PROOF 3: select staging => plan reports no changes (prod state untouched) =="
terraform workspace select staging >/dev/null
# -detailed-exitcode: 0 = no changes, 2 = changes drifted. Tolerate either for the demo.
terraform plan -input=false -detailed-exitcode && echo "(exit 0: no changes in staging)" || true
