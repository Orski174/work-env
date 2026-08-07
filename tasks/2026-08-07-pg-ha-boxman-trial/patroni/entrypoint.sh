#!/bin/sh
set -e
# Container starts as root (needed for the apt/pip install layer in Dockerfile);
# initdb refuses to run as root, so fix ownership on the mounted data volume
# (named volumes are created root-owned by default) and drop to the image's
# existing `postgres` user (uid 26) before handing off to Patroni.
mkdir -p /var/run/postgresql
chown -R postgres:postgres /var/lib/postgresql/data /var/run/postgresql
# Fresh named volumes are created 0755 root:root; chown above fixes ownership
# but not mode. Postgres 16 refuses to start (leader init AND replica
# bootstrap alike) unless the top-level data dir is exactly 0700/0750 — the
# initdb path on a first-time leader happens to set this itself, but a
# replica's basebackup-based bootstrap does not, so set it explicitly here.
chmod 0700 /var/lib/postgresql/data
# setpriv (unlike `su -`) does not reset $HOME — it stays /root, which the
# postgres user can't write to, and Patroni needs a writable home for its
# default .pgpass path. Set it explicitly to the postgres user's actual home
# (confirmed via /etc/passwd: postgres:x:26:102:...:/var/lib/postgresql:/bin/bash).
export HOME=/var/lib/postgresql
exec setpriv --reuid=postgres --regid=postgres --init-groups patroni /etc/patroni.yml
