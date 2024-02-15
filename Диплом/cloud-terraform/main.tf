terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  service_account_key_file = "/home/mark/cloud-terraform/key1.json"
  cloud_id                 = "b1g4b96r348bedp6u3v2"
  folder_id                = "b1gbj91bhi2sl8024oha"
  zone                     = "ru-central1-a"
}

