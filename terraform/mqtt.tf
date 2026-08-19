###############################################################################
# mqtt.tf – Mosquitto MQTT broker VM
#
# Topology:
#   IoT sensors ──(1883)──► MQTT broker VM (Mosquitto)
#                                │
#                         subscriber process
#                         (written by hand)
#                                │
#                           Cloud SQL
#                                │
#                           FastAPI VM
#
# The broker has no public IP. During dev, reach it via the IAP tunnel
# (scripts/tunnel.sh). Uncomment the external firewall rule in networking.tf
# when ready to expose it to real IoT devices.
###############################################################################

# ── Service account ───────────────────────────────────────────────────────────

resource "google_service_account" "mqtt_sa" {
  account_id   = "${var.app_name}-mqtt-sa"
  display_name = "MQTT broker VM service account"
}

resource "google_project_iam_member" "mqtt_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.mqtt_sa.email}"
}

resource "google_project_iam_member" "mqtt_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.mqtt_sa.email}"
}

# ── IAP tunnel access ─────────────────────────────────────────────────────────

resource "google_iap_tunnel_instance_iam_member" "mqtt_tunnel_access" {
  for_each = toset(var.iap_tunnel_users)

  project  = var.project_id
  zone     = var.zone
  instance = google_compute_instance.mqtt_vm.name
  role     = "roles/iap.tunnelResourceAccessor"
  member   = each.value
}

# ── Compute instance ──────────────────────────────────────────────────────────

resource "google_compute_instance" "mqtt_vm" {
  name         = "${var.app_name}-mqtt-vm-${random_id.suffix.hex}"
  machine_type = var.mqtt_machine_type
  zone         = var.zone
  tags         = ["mqtt-vm"]

  lifecycle {
    ignore_changes = [
      metadata["ssh-keys"],
    ]
  }
  
  boot_disk {
    initialize_params {
      image = var.vm_image
      size  = var.mqtt_disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
  }

  service_account {
    email  = google_service_account.mqtt_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    # DB connection info available for the subscriber process you'll write.
    db-host     = google_sql_database_instance.postgres.private_ip_address
    db-name     = var.db_name
    db-user     = var.db_user
    db-password = var.db_password
  }

  depends_on = [
    google_sql_database_instance.postgres,
    google_service_networking_connection.private_vpc_connection,
  ]
}
