###############################################################################
# outputs.tf
###############################################################################

output "vm_internal_ip" {
  description = "Internal IP of the FastAPI VM."
  value       = google_compute_instance.api_vm.network_interface[0].network_ip
}

output "vm_name" {
  description = "Name of the FastAPI VM instance."
  value       = google_compute_instance.api_vm.name
}

output "sql_instance_name" {
  description = "Cloud SQL instance name."
  value       = google_sql_database_instance.postgres.name
}

output "sql_private_ip" {
  description = "Private IP address of the Cloud SQL instance."
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "sql_connection_name" {
  description = "Cloud SQL connection name (useful for Auth Proxy if added later)."
  value       = google_sql_database_instance.postgres.connection_name
}

output "fastapi_url" {
  description = "Internal URL to reach FastAPI (use IAP tunnel or load balancer to expose publicly)."
  value       = "http://${google_compute_instance.api_vm.network_interface[0].network_ip}:8000"
}

output "proxy_public_ip" {
  description = "Static public IP address of the Nginx reverse proxy VM."
  value       = google_compute_address.proxy_static_ip.address
}

output "proxy_vm_name" {
  description = "Name of the proxy VM instance."
  value       = google_compute_instance.proxy_vm.name
}

output "api_url" {
  description = "Public URL for the FastAPI application via the reverse proxy."
  value       = "http://${google_compute_address.proxy_static_ip.address}/api"
}

output "mqtt_proxy_host" {
  description = "Public host for MQTT connections via the reverse proxy."
  value       = google_compute_address.proxy_static_ip.address
}
