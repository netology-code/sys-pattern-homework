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
  description = "VPC network&subnet name"
}


variable "res_vm" {
  description = "list of resourses"
  type = list(object({
    vm_name                 = string
    cpu                     = number
    ram                     = number
    disk                    = number
  }))
  default = [
    {
      vm_name                       = "vm1"
      cpu                           = 2 
      ram                           = 2
      disk                          = 5
    },
    {
      vm_name                       = "vm2"
      cpu                           = 4 
      ram                           = 4
      disk                          = 10
    }
  ]
}



###ssh vars

locals  {
  public_key = file ("~/.ssh/id_rsa.pub")
}

variable "public_key" {
  type    = string
  default = ""
}
