#!/bin/sh
set -e
# Container starts as root (needed for the apt/pip install layer in Dockerfile);
# initdb refuses to run as root, so fix ownership on the mounted data volume
# (named volumes are created root-owned by default) and drop to the image's
# existing `postgres` user (uid 26) before handing off to Patroni.
mkdir -p /var/run/postgresql
chown -R postgres:postgres /var/lib/postgresql/data /var/run/postgresql
exec setpriv --reuid=postgres --regid=postgres --init-groups patroni /etc/patroni.yml
