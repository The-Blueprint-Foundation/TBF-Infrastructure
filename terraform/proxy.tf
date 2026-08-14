###############################################################################
# proxy.tf – Nginx reverse proxy VM
#
# Topology:
#   Internet
#     │
#     ├── HTTP :80  /api/*  → FastAPI VM :8000
#     │
#     └── TCP  :1883        → MQTT broker VM :1883
#
# The proxy VM is the only VM with a public IP. The FastAPI and MQTT VMs
# remain private, reachable only from within the VPC or via IAP tunnel.
#
# The root path (/) is intentionally unhandled by the proxy — reserved for
# a future frontend served via CDN or other mechanism by a downstream team.
###############################################################################

# ── Static public IP ──────────────────────────────────────────────────────────

resource "google_compute_address" "proxy_static_ip" {
  name   = "${var.app_name}-proxy-ip"
  region = var.region
}

# ── Service account ───────────────────────────────────────────────────────────

resource "google_service_account" "proxy_sa" {
  account_id   = "${var.app_name}-proxy-sa"
  display_name = "Nginx reverse proxy VM service account"
}

resource "google_project_iam_member" "proxy_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.proxy_sa.email}"
}

resource "google_project_iam_member" "proxy_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.proxy_sa.email}"
}

# ── IAP tunnel access ─────────────────────────────────────────────────────────

resource "google_iap_tunnel_instance_iam_member" "proxy_tunnel_access" {
  for_each = toset(var.iap_tunnel_users)

  project  = var.project_id
  zone     = var.zone
  instance = google_compute_instance.proxy_vm.name
  role     = "roles/iap.tunnelResourceAccessor"
  member   = each.value
}

# ── Compute instance ──────────────────────────────────────────────────────────

resource "google_compute_instance" "proxy_vm" {
  name         = "${var.app_name}-proxy-${random_id.suffix.hex}"
  machine_type = var.proxy_machine_type
  zone         = var.zone
  tags         = ["proxy-vm"]

  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = var.proxy_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id

    # Proxy VM is publicly accessible — this is intentional.
    access_config {
      nat_ip = google_compute_address.proxy_static_ip.address
    }
  }

  service_account {
    email  = google_service_account.proxy_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    # Internal IPs of the backend VMs — used by Ansible to template nginx.conf.
    fastapi-internal-ip = google_compute_instance.api_vm.network_interface[0].network_ip
    mqtt-internal-ip    = google_compute_instance.mqtt_vm.network_interface[0].network_ip
    fastapi-port        = var.api_port
    mqtt-port           = var.mqtt_port
  }

  lifecycle {
    ignore_changes = [
      metadata["ssh-keys"],
    ]
  }

  depends_on = [
    google_compute_instance.api_vm,
    google_compute_instance.mqtt_vm,
  ]
}
