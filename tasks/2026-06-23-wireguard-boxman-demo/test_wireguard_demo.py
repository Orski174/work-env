"""
Integration test: wireguard_server + wireguard_client Ansible roles via boxman.

Spins up two libvirt VMs (wg_server + wg_client) from conf.yml in this directory,
deploys the wireguard roles from ~/git/hpccluster, and verifies that wg_client
can reach wg_server's mgmt IP (10.1.30.10) through a split-tunnel WireGuard VPN.

Run:
    pytest -m "integration and slow" test_wireguard_demo.py -v

Requirements:
    - libvirtd running, /dev/kvm accessible
    - boxman CLI in PATH (activate ~/git/boxman-orig/.venv first, or pip install -e)
    - ~/git/hpccluster present (roles + playbooks + smoke tests)
    - ansible, ansible-playbook in PATH
    - BOXMAN_ADMIN_PASS env var optional (defaults to "boxman")

Teardown always runs even if tests fail — the finally block deprovisions the box.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import shlex

import invoke
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

TASK_DIR = Path(__file__).resolve().parent
CONF = TASK_DIR / "conf.yml"
HPCCLUSTER = Path.home() / "git" / "hpccluster"
WS = Path.home() / "workspaces" / "boxmandev" / "wireguard-boxman-demo"
SSH_CFG = WS / "ssh_config"

SERVER_HOST = "wireguard_demo_wg_server"
CLIENT_HOST = "wireguard_demo_wg_client"
SERVER_MGMT_IP = "10.1.30.10"

# ---------------------------------------------------------------------------
# Gate: skip the whole module if preconditions are not met
# ---------------------------------------------------------------------------

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_SKIP_REASON: str | None = None
if not CONF.is_file():
    _SKIP_REASON = f"conf.yml not found: {CONF}"
elif not HPCCLUSTER.is_dir():
    _SKIP_REASON = f"hpccluster repo not found: {HPCCLUSTER}"
elif not os.access("/dev/kvm", os.R_OK | os.W_OK):
    _SKIP_REASON = "/dev/kvm not accessible"

if _SKIP_REASON:
    pytestmark.append(pytest.mark.skip(reason=_SKIP_REASON))


# ---------------------------------------------------------------------------
# SSH helpers
# ---------------------------------------------------------------------------

def _ssh(host: str, cmd: str, warn: bool = False) -> invoke.runners.Result:
    result = invoke.run(
        f"ssh -F {SSH_CFG} -o BatchMode=yes -o ConnectTimeout=10 {host} {shlex.quote(cmd)}",
        hide=True, warn=warn, in_stream=False,
    )
    assert result is not None  # invoke.run only returns None with disown=True
    return result


def _wait_ssh(host: str, max_attempts: int = 30, delay: int = 5) -> None:
    for _ in range(max_attempts):
        r = _ssh(host, "hostname", warn=True)
        if r.ok and r.stdout.strip():
            return
        time.sleep(delay)
    raise RuntimeError(f"{host}: SSH not ready after {max_attempts} attempts")


def _ssh_ip_from_config(host: str) -> str:
    """Return the Hostname value from boxman's generated ssh_config for *host*."""
    text = SSH_CFG.read_text()
    # ssh_config has "Host alias1 alias2\n    Hostname <ip>" — split on Host stanzas
    for block in re.split(r'\n(?=Host )', text):
        first_line = block.split('\n')[0]
        if re.search(rf'\b{re.escape(host)}\b', first_line):
            m = re.search(r'Hostname\s+(\S+)', block, re.IGNORECASE)
            if m:
                return m.group(1)
    raise RuntimeError(f"No Hostname entry for {host!r} in {SSH_CFG}")


def _detect_mgmt_nic(host: str) -> str:
    """
    Return the name of the second ethernet NIC on *host* (the one with no IP).
    This is the mgmt adapter; it's unconfigured after clone since mgmt has no DHCP.
    """
    r = _ssh(
        host,
        "ip -o link show | awk '/: (ens|enp|eth)[0-9]/{print $2}' | tr -d ':' | tail -1",
    )
    nic = r.stdout.strip()
    if not nic:
        raise RuntimeError(f"Could not detect mgmt NIC on {host}")
    return nic


# ---------------------------------------------------------------------------
# Ansible helpers
# ---------------------------------------------------------------------------

def _ansible_playbook(
    playbook: Path,
    inventory: Path,
    extra_vars: dict | None = None,
) -> None:
    vars_blob: dict = {"ansible_user": "admin"}
    if extra_vars:
        vars_blob.update(extra_vars)
    cmd = [
        "ansible-playbook",
        str(playbook),
        "-i", str(inventory),
        f"--ssh-common-args=-F {SSH_CFG}",
        "-e", json.dumps(vars_blob),
    ]
    subprocess.run(cmd, check=True, cwd=str(HPCCLUSTER))


def _write_group_inventory(
    path: Path,
    server_nat_ip: str,
    mgmt_nic: str,
) -> None:
    """Write inventory/02-groups.yml mapping VMs to wireguard_server / wireguard_clients."""
    clients_yaml = json.dumps([{"name": "boxman_client"}])
    path.write_text(
        f"---\n"
        f"all:\n"
        f"  children:\n"
        f"    wireguard_server:\n"
        f"      hosts:\n"
        f"        {SERVER_HOST}:\n"
        f"          ansible_user: admin\n"
        f"          wireguard_server_remote_host: \"{server_nat_ip}\"\n"
        f"          wireguard_server_local_ip: \"{SERVER_MGMT_IP}\"\n"
        f"          wireguard_firewall_backend: iptables\n"
        f"          wireguard_egress_interface: {mgmt_nic}\n"
        f"          wireguard_client_default_allowed_ips: \"10.1.30.0/24\"\n"
        f"          wireguard_clients: {clients_yaml}\n"
        f"    wireguard_clients:\n"
        f"      hosts:\n"
        f"        {CLIENT_HOST}:\n"
        f"          ansible_user: admin\n"
    )


# ---------------------------------------------------------------------------
# Module-scoped fixture: provision → deploy roles → yield → deprovision
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def wg_box():
    """
    Bring up the wireguard-server-client box, deploy both WireGuard roles,
    then tear down regardless of test outcome.

    Yields a dict with runtime info (server_nat_ip, mgmt_nic) for use in tests.
    """
    try:
        # 1. Bring up the box (create-templates if needed, then provision)
        subprocess.run(
            ["boxman", "--conf", str(CONF), "up", "--force"],
            check=True,
        )

        # 2. Wait for both VMs to accept SSH
        _wait_ssh(SERVER_HOST)
        _wait_ssh(CLIENT_HOST)

        # 3. wg_server's nat1 IP — used as wireguard_server_remote_host
        #    (wg_client is on the same nat1 bridge, so nat1 IP is reachable)
        server_nat_ip = _ssh_ip_from_config(SERVER_HOST)

        # 4. Detect and statically configure the mgmt NIC on wg_server.
        #    The mgmt network has no DHCP, so eth1/ens*/enp* has no IP after clone.
        mgmt_nic = _detect_mgmt_nic(SERVER_HOST)
        _ssh(SERVER_HOST, f"sudo ip addr add {SERVER_MGMT_IP}/24 dev {mgmt_nic}", warn=True)
        _ssh(SERVER_HOST, f"sudo ip link set {mgmt_nic} up")

        # 5. Write the Ansible group inventory (02-groups.yml) in the boxman workspace
        inv_dir = WS / "inventory"
        inv_dir.mkdir(parents=True, exist_ok=True)
        _write_group_inventory(inv_dir / "02-groups.yml", server_nat_ip, mgmt_nic)

        # 6. Deploy wireguard_server role
        _ansible_playbook(
            HPCCLUSTER / "ansible" / "playbooks" / "wireguard_server.yml",
            inv_dir,
        )

        # 7. Fetch the server-generated client config to the controller.
        #    File is root-owned (600); use sudo cat over SSH instead of scp.
        with tempfile.NamedTemporaryFile(suffix=".conf", delete=False, mode="w") as tf:
            client_conf_local = tf.name
            tf.write(_ssh(SERVER_HOST, "sudo cat /root/boxman_client.conf").stdout)

        # 8. Deploy wireguard_client role
        _ansible_playbook(
            HPCCLUSTER / "ansible" / "playbooks" / "wireguard_client.yml",
            inv_dir,
            extra_vars={
                "wireguard_client_connections": [
                    {"name": "boxman_client", "config_src": client_conf_local}
                ]
            },
        )

        yield {"server_nat_ip": server_nat_ip, "mgmt_nic": mgmt_nic}

    finally:
        if not os.environ.get("KEEP_BOXES"):
            subprocess.run(
                ["boxman", "--conf", str(CONF), "deprovision"],
                input="yes\n", text=True, timeout=300,
            )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWireGuardSmoke:
    """Ansible smoke tests from hpccluster/tests/."""

    def test_server_smoke(self, wg_box):
        """wireguard_server_smoke.yml: package, config, service, port."""
        _ansible_playbook(
            HPCCLUSTER / "tests" / "wireguard_server_smoke.yml",
            WS / "inventory",
        )

    def test_client_smoke(self, wg_box):
        """wireguard_client_smoke.yml: package, config, service, peer."""
        _ansible_playbook(
            HPCCLUSTER / "tests" / "wireguard_client_smoke.yml",
            WS / "inventory",
        )


class TestSplitTunnel:
    """End-to-end tunnel connectivity."""

    def test_ping_server_mgmt_ip_from_client(self, wg_box):
        """wg_client reaches wg_server's mgmt IP (10.1.30.10) via WireGuard split-tunnel."""
        result = _ssh(CLIENT_HOST, f"ping -c3 -W5 {SERVER_MGMT_IP}", warn=True)
        assert result.ok, (
            f"ping {SERVER_MGMT_IP} from {CLIENT_HOST} failed\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "3 received" in result.stdout, (
            f"Expected '3 received' in ping output:\n{result.stdout}"
        )
