###############################################################################
# database.tf – Cloud SQL PostgreSQL instance, database, and user
###############################################################################

resource "google_sql_database_instance" "postgres" {
  name             = "${var.app_name}-pg-${random_id.suffix.hex}"
  database_version = var.db_version
  region           = var.region

  # Prevents accidental deletion via `terraform destroy`.
  deletion_protection = false   # set to true for production

  settings {
    tier              = var.db_tier
    availability_type = "ZONAL"   # REGIONAL for production HA

    disk_autoresize       = true
    disk_autoresize_limit = 50
    disk_size             = 10
    disk_type             = "PD_SSD"

    ip_configuration {
      ipv4_enabled    = false   # No public IP – private only
      private_network = google_compute_network.vpc.id

      # Require SSL for all client connections.
      ssl_mode = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled    = true
      start_time = "03:00"   # UTC
    }

    maintenance_window {
      day          = 7   # Sunday
      hour         = 4   # UTC
      update_track = "stable"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# The application database
resource "google_sql_database" "app_db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

# The user that will be used by the API. This user should only have read-only 
# privileges to the database, perhaps even limited access to certain tables/views
resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}