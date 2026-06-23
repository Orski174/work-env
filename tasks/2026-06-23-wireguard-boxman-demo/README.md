# wireguard-boxman-demo

## Goal

Build a boxman box definition (`conf.yml`) and a pytest integration test
(`test_wireguard_demo.py`) — both living in this task dir — that demonstrate the
`wireguard_server` + `wireguard_client` Ansible roles working together in a local
libvirt environment.

Tracks: scds-infra #119. References hpccluster branch `orski/73-wireguard-clouddev01`.

---

## Task layout

```
tasks/2026-06-23-wireguard-boxman-demo/
├── conf.yml                # boxman box definition (to be written)
├── test_wireguard_demo.py  # pytest integration test (to be written)
├── README.md               # this file
├── run.sh                  # runs the pytest integration test
├── input/
└── output/
```

---

## External repos

| Repo | Path | What lives there |
|------|------|-----------------|
| boxman-orig | `~/git/boxman-orig` | boxman CLI + Python package |
| hpccluster  | `~/git/hpccluster`  | roles at `ansible/roles/wireguard_{server,client}/`, playbooks at `ansible/playbooks/wireguard_{server,client}.yml`, smoke tests at `tests/wireguard_{server,client}_smoke.yml` |

---

## Box topology — `conf.yml`

```
wg_server  ── nat1  (192.168.10.0/24, libvirt NAT)
            ── mgmt (10.1.30.0/24, libvirt isolated, no NAT)

wg_client  ── nat1  (same NAT bridge)
```

- Both VMs: Ubuntu 24.04, cloud-init provisioned.
- `wg_server` has **two NICs**; `wg_client` has **one NIC**.
- After deploying the roles, `wg_client` must reach `wg_server`'s mgmt IP
  (`10.1.30.10`) via split-tunnel WireGuard (only `10.1.30.0/24` routed through
  the tunnel).

### conf.yml authoring notes

Reference: `~/git/boxman-orig/boxes/tiny-multi-cluster-ubuntu-24.04-cloudinit/conf.yml`
(single cluster, two VMs, two networks — match its YAML structure exactly).

Key decisions:
- Single cluster named `wireguard_demo`.
- `nat1`: libvirt NAT network, `192.168.10.0/24`, DHCP `192.168.10.2–254`.
- `mgmt`: libvirt `route` mode (or `isolated`), `10.1.30.0/24`, **no NAT, no DHCP**.
- `wg_server` VM: 1 vCPU, 1 GB RAM, Ubuntu 24.04 cloud image, adapters `[nat1, mgmt]`.
  - Cloud-init network-config: `eth0` DHCP (nat1), `eth1` static `10.1.30.10/24` (mgmt).
- `wg_client` VM: 1 vCPU, 1 GB RAM, Ubuntu 24.04 cloud image, adapter `[nat1]`.
- Cloud-init user-data: admin user + qemu-guest-agent (same pattern as reference box).
- Admin password via Jinja2: `{{ env('BOXMAN_ADMIN_PASS', default='boxman') }}`.

### Role vars for wg_server

Supply these via Ansible `group_vars` embedded in the box inventory (or pass as
extra-vars in the test). The test must know wg_server's nat1 IP at runtime to set
`wireguard_server_remote_host`.

```yaml
wireguard_server_remote_host: "<wg_server's nat1 IP>"   # resolved at test runtime
wireguard_server_local_ip: "10.1.30.10"                 # static mgmt IP
wireguard_firewall_backend: iptables
wireguard_egress_interface: eth1                         # mgmt NIC
wireguard_client_default_allowed_ips: "10.1.30.0/24"    # split-tunnel
wireguard_clients:
  - name: boxman_client
```

Role defaults at:
- `~/git/hpccluster/ansible/roles/wireguard_server/defaults/main.yml`
- `~/git/hpccluster/ansible/roles/wireguard_client/defaults/main.yml`

The server role writes `/root/boxman_client.conf`; the client role reads it via
`wireguard_client_connections[0].config_src`.

---

## Pytest integration test — `test_wireguard_demo.py`

### Before writing

Read existing boxman integration tests to match the fixture/teardown pattern:
- `~/git/boxman-orig/tests/test_lifecycle_e2e.py` — module-scoped fixture,
  `BoxmanManager.provision/destroy`, try/finally teardown with `auto_accept=True`
- `~/git/boxman-orig/tests/test_provision_boxes.py` — CLI-driven variant

The test **does not** need to be added to the boxman test suite; it is self-contained
and driven from `run.sh`.

### Test steps (in order)

1. `boxman up` using this task's `conf.yml` (pass path explicitly — check
   `boxman --help` for the correct flag, e.g. `boxman --conf ./conf.yml up`).
2. Retrieve `wg_server`'s nat1 IP from boxman SSH config / inventory.
3. Run `ansible-playbook ansible/playbooks/wireguard_server.yml`
   with `-i <boxman-generated-inventory>` and extra-var
   `wireguard_server_remote_host=<nat1 IP>` (cwd: `~/git/hpccluster`).
4. Fetch `/root/boxman_client.conf` from `wg_server` → controller temp path.
5. Run `ansible-playbook ansible/playbooks/wireguard_client.yml`
   with extra-var
   `wireguard_client_connections='[{"name":"boxman_client","config_src":"<fetched-path>"}]'`.
6. Run smoke tests:
   - `ansible-playbook tests/wireguard_server_smoke.yml -i <inventory>`
   - `ansible-playbook tests/wireguard_client_smoke.yml -i <inventory>`
7. Assert `ping -c3 10.1.30.10` succeeds from `wg_client` (via SSH exec).
8. **Teardown (always)**: `boxman destroy` in `finally` block.

### Pytest markers

```python
@pytest.mark.integration
@pytest.mark.slow
```

(Run explicitly: `pytest -m integration test_wireguard_demo.py -v`)

---

## How to run

```bash
cd tasks/2026-06-23-wireguard-boxman-demo
bash run.sh          # runs the pytest integration test
# or directly:
pytest -m integration test_wireguard_demo.py -v
```

Requires: libvirtd running locally, `boxman` CLI in PATH (from `~/git/boxman-orig`
venv or editable install), `~/git/hpccluster` present, `BOXMAN_ADMIN_PASS` optionally
set (defaults to `boxman`).
