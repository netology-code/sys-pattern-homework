
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2004-lts"
}

resource "yandex_compute_instance" "platform" {
  name        = "${local.name-prefix}-web"
  platform_id = var.vm_web_platform_id_instance
  resources {
    cores         = var.vm_web_hardware["cores"]
    memory        = var.vm_web_hardware["memory"]
    core_fraction = var.vm_web_hardware["fractions"]
  }
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.image_id
    }
  }
  scheduling_policy {
    preemptible = true
  }
  network_interface {
    subnet_id = yandex_vpc_subnet.develop.id
    nat       = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${var.vms_ssh_root_key}"
  }

}



data "yandex_compute_image" "ubuntu2" {
  family = var.vm_db_family1
}

resource "yandex_compute_instance" "platform2" {
  name        = "${local.name-prefix}-db"
  platform_id = var.vm_db_platform_id_instance
  resources {
    cores         = var.vm_db_hardware["cores"]
    memory        = var.vm_db_hardware["memory"]
    core_fraction = var.vm_db_hardware["fractions"]
  }
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.image_id
    }
  }
  scheduling_policy {
    preemptible = true
  }
  network_interface {
    subnet_id = yandex_vpc_subnet.develop.id
    nat       = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${var.vms_ssh_root_key}"
  }

}
