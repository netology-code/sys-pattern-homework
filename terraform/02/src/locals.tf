variable "company" {
  type = string
  default = "netology"
}
variable "env" {
  type = string
  default = "develop"
}
variable "platf" {
  type = string
  default = "platform"
}

locals {
  name-prefix = "${var.company}-${var.env}-${var.platf}"
}


