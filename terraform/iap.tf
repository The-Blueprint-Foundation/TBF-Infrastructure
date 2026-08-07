###############################################################################
# iap.tf – outputs that the tunnel helper script uses at runtime
###############################################################################

output "iap_tunnel_command_hint" {
  description = "Reminder of how to open the tunnels — see scripts/tunnel.sh for the full helper."
  value       = "Run: bash scripts/tunnel.sh ${var.project_id} ${var.zone} ${google_compute_instance.api_vm.name} ${google_compute_instance.mqtt_vm.name} ${google_compute_instance.proxy_vm.name} ${google_sql_database_instance.postgres.private_ip_address} ${var.api_port}"
}
