###############################################################################
# variables.tf
###############################################################################

variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Default GCP region."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Default GCP zone."
  type        = string
  default     = "us-central1-a"
}

variable "app_name" {
  description = "Short application name used as a prefix on resources."
  type        = string
}

# ── Networking ────────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR for the primary subnet."
  type        = string
  default     = "10.0.0.0/24"
}

# ── Compute ───────────────────────────────────────────────────────────────────

variable "vm_image" {
  description = "Boot disk image for the VM."
  type        = string
  default     = "debian-cloud/debian-12"
}

variable "ssh_source_ranges" {
  description = "CIDR ranges allowed to SSH into the VM. Defaults to IAP forwarder range only — do not open to 0.0.0.0/0."
  type        = list(string)
  default     = ["35.235.240.0/20"]   # Google IAP TCP forwarding range
}

variable "iap_tunnel_users" {
  description = "List of Google identities granted IAP tunnel access to the VM (e.g. [\"user:you@example.com\"])."
  type        = list(string)
  default     = []
}

variable "allowed_http_ranges" {
  description = "CIDR ranges allowed to reach the FastAPI port."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ── API ───────────────────────────────────────────────────────────────────────

variable "api_machine_type" {
  description = "Machine type for the FastAPI VM."
  type        = string
  default     = "e2-small"   # cost-optimised for dev/staging
}

variable "api_disk_size_gb" {
  description = "Boot disk size in GB for the FastAPI VM."
  type        = number
  default     = 20
}

variable "api_port" {
  description = "Port that FastAPI/uvicorn listens on."
  type        = number
  default     = 8000
}

# ── MQTT broker ───────────────────────────────────────────────────────────────

variable "mqtt_machine_type" {
  description = "Machine type for the MQTT broker VM."
  type        = string
  default     = "e2-micro"
}

variable "mqtt_disk_size_gb" {
  description = "Boot disk size in GB for the MQTT broker VM."
  type        = number
  default     = 10
}

variable "mqtt_port" {
  description = "Port Mosquitto listens on."
  type        = number
  default     = 1883
}

# ── Cloud SQL ─────────────────────────────────────────────────────────────────

variable "db_version" {
  description = "PostgresSQL version."
  type        = string
  default     = "POSTGRES_16"
}

variable "db_tier" {
  description = "Cloud SQL machine tier."
  type        = string
  default     = "db-f1-micro"   # cost-optimised for dev/staging
}

variable "db_name" {
  description = "Name of the application database."
  type        = string
  default     = "appdb"
}

variable "db_app_user" {
  description = "PostgresSQL user for the application."
  type        = string
  default     = "appuser"
}

variable "db_app_user_password" {
  description = "Password for the application DB user. Supply via TF_VAR or Secret Manager."
  type        = string
  sensitive   = true
}

variable "db_data_user" {
  description = "PostgresSQL user for data ingestion."
  type        = string
  default     = "datauser"
}

variable "db_data_user_password" {
  description = "Password for the data-ingestion DB user. Supply via TF_VAR or Secret Manager."
  type        = string
  sensitive   = true
}