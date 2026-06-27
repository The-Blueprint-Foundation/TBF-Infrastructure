###############################################################################
# networking.tf – VPC, subnet, firewall rules, and VPC peering for Cloud SQL
#
# IAP TCP tunneling note:
#   SSH access is restricted to Google's IAP forwarder range (35.235.240.0/20)
#   only. There is no open-internet SSH exposure. Local access to FastAPI,
#   Cloud SQL, and the MQTT broker is handled via SSH port-forwarding through
#   the IAP tunnel — see scripts/tunnel.sh for the helper command.
#
# External access note:
#   Firewall rules for public internet access to FastAPI and the MQTT broker
#   are present below but commented out. Uncomment when ready to demo/expose.
###############################################################################

# ── VPC & subnet ──────────────────────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "${var.app_name}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${var.app_name}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = var.vpc_cidr

  # Required for Private Google Access (metadata, APIs, etc.)
  private_ip_google_access = true
}

# ── Cloud NAT – lets the VM pull packages without a public IP ─────────────────

resource "google_compute_router" "router" {
  name    = "${var.app_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${var.app_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# ── Firewall rules ────────────────────────────────────────────────────────────

# SSH via IAP — covers both the FastAPI VM and the MQTT broker VM.
# var.ssh_source_ranges defaults to the IAP forwarder range only.
resource "google_compute_firewall" "allow_ssh_iap" {
  name    = "${var.app_name}-allow-ssh-iap"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["fastapi-vm", "mqtt-vm"]
}

# ── FastAPI server – internal VPC access ────────────────────────────────────────
# Allows any resource in the VPC subnet to reach FastAPI on the value of `var.api_port`.
resource "google_compute_firewall" "allow_fastapi_internal" {
  name    = "${var.app_name}-allow-fastapi-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = [tostring(var.api_port)]
  }

  source_ranges = [var.vpc_cidr]
  target_tags   = ["fastapi-vm"]
}

# ── MQTT broker – internal VPC access ────────────────────────────────────────
# Allows any resource in the VPC subnet to reach Mosquitto on the value of `var.mqtt_port`.
# This covers the subscriber process writing sensor data to Cloud SQL.
resource "google_compute_firewall" "allow_mqtt_internal" {
  name    = "${var.app_name}-allow-mqtt-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = [tostring(var.mqtt_port)]
  }

  source_ranges = [var.vpc_cidr]
  target_tags   = ["mqtt-vm"]
}

# ── External access (commented out – uncomment when ready to demo) ────────────
#
# FastAPI – exposes the web server to the public internet.
# resource "google_compute_firewall" "allow_fastapi_external" {
#   name    = "${var.app_name}-allow-fastapi-external"
#   network = google_compute_network.vpc.name
#
#   allow {
#     protocol = "tcp"
#     ports    = [tostring(var.fastapi_port)]
#   }
#
#   source_ranges = ["0.0.0.0/0"]
#   target_tags   = ["fastapi-vm"]
# }
#
# MQTT – exposes Mosquitto to external IoT devices.
# Port 1883 is plain MQTT; 8883 is MQTT over TLS (recommended for production).
# resource "google_compute_firewall" "allow_mqtt_external" {
#   name    = "${var.app_name}-allow-mqtt-external"
#   network = google_compute_network.vpc.name
#
#   allow {
#     protocol = "tcp"
#     ports    = ["1883", "8883"]
#   }
#
#   source_ranges = ["0.0.0.0/0"]
#   target_tags   = ["mqtt-vm"]
# }
#
# NOTE: When enabling external MQTT access, also assign a static external IP
# to the broker VM so IoT devices have a stable address to point to. Add
# an access_config {} block inside the network_interface in mqtt.tf and
# provision a google_compute_address resource.

resource "google_compute_firewall" "allow_internal" {
  name    = "${var.app_name}-allow-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = [var.vpc_cidr]
}

# ── Private Services Access (VPC peering for Cloud SQL private IP) ────────────

resource "google_compute_global_address" "private_sql_range" {
  name          = "${var.app_name}-sql-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_sql_range.name]
}
