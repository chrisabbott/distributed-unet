variable "aws-region" {
  default = "us-east-1"
}

variable "ubuntu-dl-base-ami" {
  default = "ami-063690c75d69a8f15"
}

variable "training-cluster-az" {
  default = "us-east-1b, us-east-1c, us-east-1d, us-east-1e"
}

variable "instance-type" {
  default = "p2.xlarge"
}

variable "capacity-min" {
  default = 1
}

variable "capacity-max" {
  default = 3
}

variable "capacity-desired" {
  default = 2
}

variable "key_name" {
  description = ""
}
