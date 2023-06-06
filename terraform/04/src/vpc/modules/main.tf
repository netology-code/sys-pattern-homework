terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}


#создаем облачную сеть
resource "yandex_vpc_network" "develop" {
  name = var.env_name
}

#создаем подсеть
resource "yandex_vpc_subnet" "develop" {
  name           =  var.env_name2
  zone           =  var.zone2
  network_id     =  yandex_vpc_network.develop.id
  v4_cidr_blocks =  var.cidr2
}


