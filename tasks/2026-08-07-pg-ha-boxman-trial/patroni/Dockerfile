# Patroni supervising Postgres inside CNPG's own Postgres image (PID 1 = patroni,
# which forks/execs postgres itself) — not Patroni-on-host managing a separate
# container. See ../README.md "Why not CNPG/k8s directly" for the reasoning.
FROM ghcr.io/cloudnative-pg/postgresql:16

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv \
    && pip install --break-system-packages "patroni[etcd3]" \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
