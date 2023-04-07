output "instance_ip_addr_web" {
  value = yandex_compute_instance.platform.network_interface.0.nat_ip_address
}

output "instance_ip_addr_db" {
  value = yandex_compute_instance.platform2.network_interface.0.nat_ip_address
}
