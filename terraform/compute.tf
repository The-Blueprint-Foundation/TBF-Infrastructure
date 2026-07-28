###############################################################################
# compute.tf – Service account and FastAPI VM
###############################################################################

# ── Service account for the VM ────────────────────────────────────────────────

resource "google_service_account" "api_sa" {
  account_id   = "${var.app_name}-api-sa"
  display_name = "FastAPI VM service account"
}

# Allows the VM to write logs and metrics to Cloud Operations (Stackdriver).
resource "google_project_iam_member" "api_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

# ── IAP tunnel access ─────────────────────────────────────────────────────────
# Grants each identity in var.iap_tunnel_users the ability to open an IAP TCP
# tunnel to this specific VM instance. This is the minimum required permission
# — it does not grant any broader project access.

resource "google_project_iam_custom_role" "tunnel_user" {
  role_id     = "tunnelUser"
  title       = "IAP Tunnel User"
  description = "Minimal permissions for gcloud IAP SSH tunnel access"
  permissions = [
    "resourcemanager.projects.get",
    "resourcemanager.projects.getIamPolicy",
  ]
}

resource "google_iap_tunnel_instance_iam_member" "api_tunnel_access" {
  for_each = toset(var.iap_tunnel_users)

  project  = var.project_id
  zone     = var.zone
  instance = google_compute_instance.api_vm.name
  role     = "roles/iap.tunnelResourceAccessor"
  member   = each.value
}

resource "google_project_iam_member" "team_compute_viewer" {
  for_each = toset(var.iap_tunnel_users)

  project = var.project_id
  role    = "roles/compute.viewer"
  member  = each.value
}

resource "google_project_iam_member" "team_tunnel_user" {
  for_each = toset(var.iap_tunnel_users)

  project = var.project_id
  role    = google_project_iam_custom_role.tunnel_user.id
  member  = each.value
}

# ── Compute instance ──────────────────────────────────────────────────────────

resource "google_compute_instance" "api_vm" {
  name         = "${var.app_name}-api-vm-${random_id.suffix.hex}"
  machine_type = var.api_machine_type
  zone         = var.zone
  tags         = ["fastapi-vm"]

  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = var.api_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    # No access_config block -> no public IP; traffic exits via Cloud NAT.
    #
    # When ready for external access, uncomment the block below and provision
    # a google_compute_address resource for a stable public IP:
    #
    # resource "google_compute_address" "api_static_ip" {
    #   name   = "${var.app_name}-api-ip"
    #   region = var.region
    # }
    #
    # access_config {
    #   nat_ip = google_compute_address.api_static_ip.address
    # }
    #
    # NOTE: Also uncomment the allow_api_external firewall rule in
    # networking.tf, and update the web app team's API base URL to point
    # at this static IP.
  }

  service_account {
    email  = google_service_account.api_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    # Passes DB connection info as instance metadata for the startup script to read.
    db-host     = google_sql_database_instance.postgres.private_ip_address
    db-name     = var.db_name
    db-user     = var.db_user
    db-password = var.db_password
  }

  metadata_startup_script = templatefile("${path.module}/scripts/api_startup.sh", {
    api_port = tostring(var.api_port)
  })

  # Ensure SQL instance is ready before the VM boots so the startup script
  # can reach the database during first-run setup.
  depends_on = [
    google_sql_database_instance.postgres,
    google_service_networking_connection.private_vpc_connection,
  ]
}
