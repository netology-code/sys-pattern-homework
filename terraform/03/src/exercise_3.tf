# create 3 disks
resource "yandex_compute_disk" "volume" {
    count = 3
    name       = "netology-volume-${count.index}"
    type       = "network-hdd"
    size       = 1
}
# create VM
resource "yandex_compute_instance" "exercise_3" {
  name        = "netology-develop-platform-web-ex3"
  platform_id = "standard-v1"
  resources {
    cores  = 2
    memory = 1
    core_fraction = 20
  }
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu-2004-lts.image_id
      type = "network-hdd"
      size = 5
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

#  dynamic "secondary_disk" {
#     for_each = yandex_compute_disk.volume
#       content {
#       disk_id     = yandex_compute_disk.volume[1].id
#       auto_delete = true
#     }
# }
}

