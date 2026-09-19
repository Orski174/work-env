#!/usr/bin/env bash
# Post-provision: install k3s, Helm, cert-manager, and Rancher on the single
# throwaway VM (rancher01). Two-phase pattern (cloud-init stays minimal,
# heavy lifting happens here over SSH) mirrors saltstack-lab/setup-salt.sh
# and pg-ha-boxman-trial/setup.sh, for the same reason: boxman's ~120s
# cloud-init done-marker poll can't tolerate a slow install baked into the
# template.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

WORKSPACE="${RANCHER_WORKSPACE:-$HOME/workspaces/boxmandev/rancher_scouting_trial}"
RANCHER_HOSTNAME="${RANCHER_HOSTNAME:-rancher01.local}"
BOOTSTRAP_PASS="${RANCHER_BOOTSTRAP_PASS:-scouting-trial-pass}"

ssh_config() {
  local cfg
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  printf '%s\n' "$cfg"
}

host_for() {  # cfg pattern -> boxman Host alias
  local host
  host="$(awk -v p="$2" '$1=="Host" && $2 ~ p {print $2; exit}' "$1")"
  [ -n "$host" ] || { echo "no Host matching '$2' in $1" >&2; exit 1; }
  printf '%s\n' "$host"
}

ssh_to() {  # cfg host_alias cmd...
  local cfg="$1" host="$2"; shift 2
  ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=10 "$host" "$@"
}

CFG="$(ssh_config)"
HOST="$(host_for "$CFG" "rancher01\$")"
echo ">> target: $HOST"

echo "== installing k3s =="
ssh_to "$CFG" "$HOST" 'command -v k3s >/dev/null 2>&1 || curl -sfL https://get.k3s.io | sudo sh -'
ssh_to "$CFG" "$HOST" 'sudo k3s kubectl wait --for=condition=Ready node --all --timeout=120s'

echo "== installing Helm =="
ssh_to "$CFG" "$HOST" 'command -v helm >/dev/null 2>&1 || (curl -fsSL -o /tmp/get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && chmod +x /tmp/get_helm.sh && sudo /tmp/get_helm.sh)'

# k3s writes its kubeconfig root-only 0600 at /etc/rancher/k3s/k3s.yaml.
# `VAR=val sudo cmd` does NOT reliably propagate through sudo's env_reset
# (that idiom only works if sudoers grants SETENV), so rather than depend on
# that, copy the file into the ssh user's own ~/.kube/config once — every
# helm/kubectl call after this needs no sudo at all.
ssh_to "$CFG" "$HOST" '[ -f ~/.kube/config ] || { mkdir -p ~/.kube && sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && sudo chown $(id -u):$(id -g) ~/.kube/config && chmod 600 ~/.kube/config; }'

echo "== installing cert-manager (Rancher's documented TLS prerequisite) =="
ssh_to "$CFG" "$HOST" "helm repo add jetstack https://charts.jetstack.io >/dev/null 2>&1 || true"
ssh_to "$CFG" "$HOST" "helm repo update >/dev/null"
ssh_to "$CFG" "$HOST" "helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true --wait --timeout 5m"

echo "== installing Rancher (single-node, self-signed TLS — trial only) =="
ssh_to "$CFG" "$HOST" "helm repo add rancher-latest https://releases.rancher.com/server-charts/latest >/dev/null 2>&1 || true"
ssh_to "$CFG" "$HOST" "helm repo update >/dev/null"
ssh_to "$CFG" "$HOST" "helm upgrade --install rancher rancher-latest/rancher \
  --namespace cattle-system --create-namespace \
  --set hostname=$RANCHER_HOSTNAME \
  --set bootstrapPassword=$BOOTSTRAP_PASS \
  --set replicas=1 \
  --wait --timeout 10m"

echo "== waiting for the Rancher deployment rollout =="
# k3s's bundled `kubectl` (a symlink into the k3s multicall binary) defaults
# its own --kubeconfig to /etc/rancher/k3s/k3s.yaml directly, NOT
# ~/.kube/config like upstream kubectl — so the ~/.kube/config copy above
# doesn't help here unless KUBECONFIG is set explicitly. (helm's `--wait`
# above already confirmed the rollout; this is just an explicit readback.)
ssh_to "$CFG" "$HOST" "KUBECONFIG=\$HOME/.kube/config kubectl -n cattle-system rollout status deploy/rancher --timeout=300s"

echo
echo "Rancher up. bootstrap password: $BOOTSTRAP_PASS"
echo "UI: run './run.sh ui' for the SSH tunnel command, then browse https://localhost:8443 (accept the self-signed cert)."
