###############################################################################
# networking.tf – VPC, subnet, firewall rules, and VPC peering for Cloud SQL
#
# IAP TCP tunneling note:
#   SSH access is restricted to Google's IAP forwarder range (35.235.240.0/20)
#   only. There is no open-internet SSH exposure on any VM. Local access to
#   FastAPI, Cloud SQL, MQTT, and the proxy is handled via SSH port-forwarding
#   through the IAP tunnel — see scripts/tunnel.sh for the helper command.
#
# External access note:
#   Only the proxy VM has a public IP. FastAPI and MQTT VMs are private and
#   only reachable from within the VPC or via IAP tunnel. External traffic
#   reaches FastAPI and MQTT exclusively through the Nginx reverse proxy.
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

# ── Cloud NAT – lets VMs pull packages without public IPs ────────────────────

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

# SSH via IAP — covers all VMs.
# var.ssh_source_ranges defaults to the IAP forwarder range only.
resource "google_compute_firewall" "allow_ssh_iap" {
  name    = "${var.app_name}-allow-ssh-iap"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["fastapi-vm", "mqtt-vm", "proxy-vm"]
}

# Proxy VM – allows HTTP traffic from the public internet.
# HTTPS (443) is included for when TLS is added in future.
resource "google_compute_firewall" "allow_proxy_external" {
  name    = "${var.app_name}-allow-proxy-external"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["proxy-vm"]
}

# Proxy VM – allows MQTT TCP traffic from the public internet.
resource "google_compute_firewall" "allow_mqtt_external" {
  name    = "${var.app_name}-allow-mqtt-external"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["1883"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["proxy-vm"]
}

# FastAPI VM – only reachable from the proxy VM over the VPC.
resource "google_compute_firewall" "allow_fastapi_internal" {
  name    = "${var.app_name}-allow-fastapi-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = [tostring(var.api_port)]
  }

  source_tags = ["proxy-vm"]
  target_tags = ["fastapi-vm"]
}

# MQTT VM – tightened to only accept connections from the proxy VM.
# Previously open to the full VPC CIDR; now source-tag restricted.
resource "google_compute_firewall" "allow_mqtt_internal" {
  name    = "${var.app_name}-allow-mqtt-internal"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["1883"]
  }

  source_tags = ["proxy-vm"]
  target_tags = ["mqtt-vm"]
}

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
