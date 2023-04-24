###cloud vars
variable "token" {
  type        = string
  description = "OAuth-token; https://cloud.yandex.ru/docs/iam/concepts/authorization/oauth-token"
}

variable "cloud_id" {
  type        = string
  description = "https://cloud.yandex.ru/docs/resource-manager/operations/cloud/get-id"
}

variable "folder_id" {
  type        = string
  description = "https://cloud.yandex.ru/docs/resource-manager/operations/folder/get-id"
}

variable "default_zone" {
  type        = string
  default     = "ru-central1-a"
  description = "https://cloud.yandex.ru/docs/overview/concepts/geo-scope"
}
variable "default_cidr" {
  type        = list(string)
  default     = ["10.0.1.0/24"]
  description = "https://cloud.yandex.ru/docs/vpc/operations/subnet-create"
}

variable "vpc_name" {
  type        = string
  default     = "develop"
  description = "VPC network & subnet name"
}


# variable "vm_web_name_instatce" {
#   type        = string
#   default     = "netology-develop-platform-web"
#   description = "name instance"
# }

variable "vm_web_platform_id_instance" {
  type        = string
  default     = "standard-v1"
  description = "platform id instance"
}


variable "vm_db_family1" {
  type        = string
  default     = "ubuntu-2004-lts"
  description = "VPC network & subnet name"
}

variable "vm_db_family" {
  type        = string
  default     = "ubuntu-2004-lts"
  description = "family"
}

# variable "vm_db_name_instatce" {
#   type        = string
#   default     = "netology-develop-platform-db"
#   description = "name instance"
# }

variable "vm_db_platform_id_instance" {
  type        = string
  default     = "standard-v1"
  description = "platform id instance"
}

variable "vm_web_hardware" {
  type = map (number)
  default = {
    "cores" = 2
    "memory" = 1
    "fractions" = 5
  }
}
variable "vm_db_hardware" {
  type = map (number)
  default = {
    "cores" = 2
    "memory" = 2
    "fractions" = 20
  }
}

###ssh vars

variable "vms_ssh_root_key" {
  type        = string
  default     = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGL1QHfLnVp1Jr3X0Mu+vIEYYiVWoVRXIzTb41rivhtZ ashubin@a-oit-k174"
  description = "ssh-keygen -t ed25519"
}
