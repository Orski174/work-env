terraform {
  required_version = ">= 1.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }

  # No backend block => default "local" backend.
  # With the local backend, non-default workspaces store state under
  # terraform.tfstate.d/<workspace>/terraform.tfstate (the default workspace
  # uses ./terraform.tfstate). In real prod/staging use this would be an S3
  # backend instead; see ../findings.md for the S3 workspace_key_prefix layout.
}

# Trivial, no-cost resource. Its filename and content embed the active
# workspace name, so each workspace manages a *different* file and gets a
# *separate* state entry -- this is what proves isolation. Because each
# workspace only knows about its own file, switching workspaces leaves the
# other env's artifact untouched.
resource "local_file" "env_marker" {
  filename = "${path.module}/env-${terraform.workspace}.txt"
  content  = "workspace = ${terraform.workspace}\ngenerated for the ${terraform.workspace} environment\n"
}

output "active_workspace" {
  value = terraform.workspace
}

output "marker_file" {
  value = local_file.env_marker.filename
}
