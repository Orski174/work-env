#!/usr/bin/env python3
"""Fill the provided seeds and boxman configuration from demo.env."""
import os
from pathlib import Path

root = Path.cwd()
name = os.environ["DEMO_NAME"]
key = Path("id_ed25519_packer.pub").read_text().strip()
Path("http").mkdir()
Path("http/meta-data").write_text(f"instance-id: {name}-build-001\nlocal-hostname: packer-build\n")
seed = Path("user-data.in").read_text().replace("__SSH_PUBLIC_KEY__", key)
Path("http/user-data").write_text(seed)
values = {
    "__PROJECT__": name,
    "__TEMPLATE_NAME__": f"{name}-template",
    "__TEMPLATE_WORKDIR__": str(root / ".boxman-templates"),
    "__IMAGE_ENV__": "PACKER_IMAGE_PATH",
    "__TEMPLATE_HOSTNAME__": "packer-template",
    "__WORKSPACE_PATH__": str(root / "workspace"),
    "__NETWORK_PREFIX__": os.environ["DEMO_SUBNET"],
    "__VM_HOSTNAME__": os.environ["DEMO_HOSTNAME"],
}
config = Path("boxman.yml.in").read_text()
for placeholder, value in values.items():
    config = config.replace(placeholder, value)
Path("boxman.yml").write_text(config)
print("Generated temporary SSH key, NoCloud seed and boxman.yml.")
print("Image inputs: demo.env | Credentials: .demo-password (private)")
