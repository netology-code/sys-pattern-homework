terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}


provider "yandex" {
  token     = var.token
  cloud_id  = "b1g1dt98fnh20q8l0229"
  folder_id = "b1gfbtk3726lm0j47c94"
  zone      = "ru-central1-a"
}


resource "yandex_vpc_network" "network-1" {
  name = "network1"
}

resource "yandex_vpc_subnet" "subnet" {
  count = 2

  name           = "subnet${count.index}"
  network_id     = yandex_vpc_network.network-1.id
  v4_cidr_blocks = ["192.168.1${count.index}.0/24"]
}

resource "yandex_compute_instance" "vm" {
  name = "terraform${count.index}"

  count = 2

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = "fd8tf1sepeiku6d37l4l"
    }
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.subnet[count.index].id
    nat       = true
  }

  metadata = {
    user-data = "${file("./meta.txt")}"
  }
}

resource "yandex_lb_target_group" "ya_tg" {
  name      = "ya-target-group"
  region_id = "ru-central1"

  target {
    subnet_id = "${yandex_vpc_subnet.subnet[0].id}"
    address   = "${yandex_compute_instance.vm[0].network_interface.0.ip_address}"
  }

  target {
    subnet_id = "${yandex_vpc_subnet.subnet[1].id}"
    address   = "${yandex_compute_instance.vm[1].network_interface.0.ip_address}"
  }
}

resource "yandex_lb_network_load_balancer" "ya_lb" {
  name = "ya-network-load-balancer"

  listener {
    name = "ya-listener"
    port = 80
    external_address_spec {
      ip_version = "ipv4"
    }
  }

  attached_target_group {
    target_group_id = "${yandex_lb_target_group.ya_tg.id}"

    healthcheck {
      name = "http"
      http_options {
        port = 80
        path = "/"
      }
    }
  }
}



output "internal_ip_address_vm_1" {
  value = yandex_compute_instance.vm[0].network_interface.0.ip_address
}
output "external_ip_address_vm_1" {
  value = yandex_compute_instance.vm[0].network_interface.0.nat_ip_address
}
output "internal_ip_address_vm_2" {
  value = yandex_compute_instance.vm[1].network_interface.0.ip_address
}
output "external_ip_address_vm_2" {
  value = yandex_compute_instance.vm[1].network_interface.0.nat_ip_address
}


resource "local_file" "write_hosts" {
  content  = <<EOT
[servers]
serv1 ansible_host=${yandex_compute_instance.vm[0].network_interface.0.nat_ip_address}
serv2 ansible_host=${yandex_compute_instance.vm[1].network_interface.0.nat_ip_address}
EOT
  filename = "${path.module}/hosts"
}

resource "null_resource" "ansible" {
  provisioner "local-exec" {
    command = "ansible-playbook playbook.yaml"
  }

  depends_on = [
    yandex_compute_instance.vm[0],
    yandex_compute_instance.vm[1]
  ]
}
