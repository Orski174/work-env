#!/usr/bin/env bash
# Driver for the pg-ha-boxman-trial lab. Meant to run on sc1.
#
#   ./run.sh up                                  boxman up (provision the 3 VMs)
#   ./run.sh setup                                ./setup.sh (docker+patroni+etcd stack)
#   ./run.sh status                               boxman ps + patronictl list
#   ./run.sh ssh <pg1|pg2|pg3>                     ssh into a node
#   ./run.sh failover-test [--switchover|--kill-leader]
#   ./run.sh backup-test
#   ./run.sh destroy                              boxman destroy
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

CONF="boxman/conf.yml"
WORKSPACE="${PG_HA_WORKSPACE:-$HOME/workspaces/boxmandev/pg-ha-boxman-trial}"

boxman() {
  if [ -n "${BOXMAN:-}" ]; then "$BOXMAN" "$@";
  elif command -v boxman >/dev/null 2>&1; then command boxman "$@";
  elif [ -x "$HOME/.conda/envs/boxman/bin/boxman" ]; then "$HOME/.conda/envs/boxman/bin/boxman" "$@";
  else python -m boxman "$@"; fi
}

ssh_config() {
  local cfg
  cfg="$(find "$WORKSPACE" -name ssh_config -type f 2>/dev/null | head -1)"
  [ -n "$cfg" ] || { echo "no ssh_config under $WORKSPACE — run './run.sh up' first" >&2; exit 1; }
  printf '%s\n' "$cfg"
}

host_for() {
  local host
  host="$(awk -v p="$2" '$1=="Host" && $2 ~ p {print $2; exit}' "$1")"
  [ -n "$host" ] || { echo "no Host matching '$2' in $1" >&2; exit 1; }
  printf '%s\n' "$host"
}

ip_for() {
  awk -v h="$2" '
    $1=="Host" { inblock = ($2==h) }
    inblock && tolower($1)=="hostname" { print $2; exit }
  ' "$1"
}

ssh_to() {
  local cfg="$1" host="$2"; shift 2
  ssh -F "$cfg" -o BatchMode=yes -o ConnectTimeout=10 "$host" "$@"
}

patronictl_list() {  # cfg alias -> raw patronictl list output
  ssh_to "$1" "$2" 'timeout 15 sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni patronictl -c /etc/patroni.yml list' 2>/dev/null
}

current_leader() {  # cfg alias -> member name currently Leader (empty if none)
  patronictl_list "$1" "$2" | awk -F'|' '
    /Leader/ { gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2; exit }
  '
}

ssh_vm() {
  local cfg host
  cfg="$(ssh_config)"
  host="$(host_for "$cfg" "$1\$")"
  shift
  exec ssh -F "$cfg" "$host" "$@"
}

do_status() {
  echo "== boxman ps =="
  boxman --conf "$CONF" ps || true
  echo
  echo "== patronictl list (via pg1) =="
  local cfg alias
  cfg="$(ssh_config)"
  alias="$(host_for "$cfg" "pg1\$")"
  patronictl_list "$cfg" "$alias" || echo "(could not reach pg1's patroni stack — has 'setup' run?)"
}

do_failover_test() {
  local mode="${1:---switchover}"
  local cfg
  cfg="$(ssh_config)"
  declare -A ALIAS
  for n in pg1 pg2 pg3; do ALIAS[$n]="$(host_for "$cfg" "$n\$")"; done

  local leader
  leader="$(current_leader "$cfg" "${ALIAS[pg1]}")"
  [ -n "$leader" ] || { echo "no current leader found — is the cluster up? run './run.sh status'" >&2; exit 1; }
  echo ">> current leader: $leader"

  local candidate=""
  for n in pg1 pg2 pg3; do [ "$n" != "$leader" ] && { candidate="$n"; break; }; done

  local start_ts
  start_ts="$(date +%s)"

  case "$mode" in
    --switchover)
      echo ">> triggering graceful switchover: $leader -> $candidate"
      ssh_to "$cfg" "${ALIAS[pg1]}" \
        "sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni patronictl -c /etc/patroni.yml switchover --leader $leader --candidate $candidate --force"
      ;;
    --kill-leader)
      echo ">> simulating hard failure: stopping patroni container on $leader (${ALIAS[$leader]})"
      ssh_to "$cfg" "${ALIAS[$leader]}" 'cd ~/patroni && sudo docker compose stop patroni'
      ;;
    *)
      echo "usage: ./run.sh failover-test [--switchover|--kill-leader]" >&2; exit 2 ;;
  esac

  echo ">> polling for a new leader..."
  local new_leader="" elapsed=0
  for i in $(seq 1 60); do
    sleep 2
    new_leader="$(current_leader "$cfg" "${ALIAS[pg2]}" 2>/dev/null || current_leader "$cfg" "${ALIAS[pg3]}" 2>/dev/null || true)"
    elapsed=$(( $(date +%s) - start_ts ))
    if [ -n "$new_leader" ] && [ "$new_leader" != "$leader" ]; then
      break
    fi
  done

  echo
  echo "=== failover-test summary ($mode) ==="
  echo "old leader: $leader"
  echo "new leader: ${new_leader:-<none observed>}"
  echo "elapsed:    ${elapsed}s"
  echo "======================================"

  if [ "$mode" = "--kill-leader" ]; then
    echo ">> restarting $leader so it can rejoin as a replica"
    ssh_to "$cfg" "${ALIAS[$leader]}" 'cd ~/patroni && sudo docker compose start patroni'
    sleep 15
    echo ">> post-rejoin state:"
    patronictl_list "$cfg" "${ALIAS[pg1]}" || patronictl_list "$cfg" "${ALIAS[pg2]}"
  fi
}

do_backup_test() {
  local cfg
  cfg="$(ssh_config)"
  declare -A ALIAS
  for n in pg1 pg2 pg3; do ALIAS[$n]="$(host_for "$cfg" "$n\$")"; done

  local leader
  leader="$(current_leader "$cfg" "${ALIAS[pg1]}")"
  [ -n "$leader" ] || { echo "no current leader found — is the cluster up?" >&2; exit 1; }
  echo ">> current leader: $leader (${ALIAS[$leader]})"

  echo ">> seeding testdb with a trivial table"
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres -c "DROP DATABASE IF EXISTS testdb;" -c "CREATE DATABASE testdb;"'
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres -d testdb -c "CREATE TABLE t (id serial primary key, v text); INSERT INTO t (v) SELECT '"'"'row'"'"' || g FROM generate_series(1,50) g;"'

  echo ">> pg_dump -> restore round-trip"
  local t0 t1
  t0="$(date +%s)"
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni pg_dump -U postgres testdb > /tmp/backup.sql'
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres -c "DROP DATABASE IF EXISTS restoretest;" -c "CREATE DATABASE restoretest;"'
  # NOTE: redirect at this level (VM host shell, same as the pg_dump `>`
  # above), not nested inside a container-side `sh -c "... < file"` — the
  # dump landed on the VM host's /tmp, not inside the container's own
  # filesystem, so a nested redirect would look in the wrong place. Letting
  # `<` apply to the `docker compose exec -T` invocation itself means the
  # VM host redirects the file as stdin, and -T forwards that stdin straight
  # into the container's psql process.
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres restoretest < /tmp/backup.sql'
  t1="$(date +%s)"

  echo ">> verifying row counts match"
  local orig_count restore_count
  orig_count="$(ssh_to "$cfg" "${ALIAS[$leader]}" 'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres -d testdb -tAc "SELECT count(*) FROM t;"')"
  restore_count="$(ssh_to "$cfg" "${ALIAS[$leader]}" 'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni psql -U postgres -d restoretest -tAc "SELECT count(*) FROM t;"')"

  echo ">> pg_basebackup sanity check (replication auth path)"
  local pb_ok="yes"
  ssh_to "$cfg" "${ALIAS[$leader]}" \
    'sudo docker compose -f ~/patroni/docker-compose.yml exec -T patroni sh -c "rm -rf /tmp/basebackup && PGPASSWORD=$(grep -A2 replication /etc/patroni.yml | grep password | awk \"{print \\\$2}\") pg_basebackup -h 127.0.0.1 -U replicator -D /tmp/basebackup -Fp -Xs -P"' \
    || pb_ok="no"

  echo
  echo "=== backup-test summary ==="
  echo "dump+restore elapsed: $((t1-t0))s"
  echo "original row count:   $orig_count"
  echo "restored row count:   $restore_count"
  echo "row counts match:     $([ "$orig_count" = "$restore_count" ] && echo yes || echo NO)"
  echo "pg_basebackup ok:      $pb_ok"
  echo "==========================="
  echo "NOTE: this restores pg_dump output into a fresh DATABASE on an existing"
  echo "node — it does NOT exercise restoring into a brand-new Patroni-bootstrapped"
  echo "node, and this trial did not evaluate continuous WAL-archiving"
  echo "(Barman/pgBackRest). Flag both as known gaps in notes.md."
}

cmd="${1:-}"; shift || true
case "$cmd" in
  up)              boxman --conf "$CONF" up "$@" ;;
  setup)           ./setup.sh "$@" ;;
  status)          do_status ;;
  ssh)             ssh_vm "${1:-pg1}" "${@:2}" ;;
  failover-test)   do_failover_test "${1:---switchover}" ;;
  backup-test)     do_backup_test ;;
  destroy)         boxman --conf "$CONF" destroy "$@" ;;
  *) echo "usage: ./run.sh {up|setup|status|ssh <pg1|pg2|pg3>|failover-test [--switchover|--kill-leader]|backup-test|destroy}" >&2; exit 2 ;;
esac
