
# create 2 VM
resource "yandex_compute_instance" "exercise_2" {
 depends_on = [yandex_compute_instance.exercise_1]
 for_each = {
   for res_vm in var.res_vm: res_vm.vm_name => res_vm
 }
 name        = each.value.vm_name
 platform_id = "standard-v1"
 resources {
   cores  = each.value.cpu
   memory = each.value.ram
   core_fraction = 20
 }
 boot_disk {
  initialize_params {
   image_id = data.yandex_compute_image.ubuntu-2004-lts.image_id
   type = "network-hdd"
   size = each.value.disk
  }   
 }
 metadata = {
   ssh-keys = "ubuntu:${local.public_key}"
 }
 scheduling_policy { preemptible = true }
 
 network_interface { 
  subnet_id = yandex_vpc_subnet.develop.id
  nat       = true
 }
allow_stopping_for_update = true
}
