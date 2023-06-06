output "vpc_id" {
  value = yandex_compute_instance.vm.*.network_interface.0.nat_ip_address
}

output "subnet_id" {
  value = yandex_compute_instance.vm.*.network_interface.0.ip_address
}


