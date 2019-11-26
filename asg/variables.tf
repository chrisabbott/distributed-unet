variable "aws-region" {
  default = "us-east-1"
}

variable "ubuntu-dl-ami" {
  # Deep Learning AMI (Ubuntu 18.04) Version 25.3
  default = "ami-0d21095cdfb1566c2"
}

variable "unet-training-cluster-az" {
  default = "us-east-1b, us-east-1c, us-east-1d, us-east-1e"
}

variable "instance-type" {
  default = "t2.nano"
}

variable "capacity-min" {
  default = 1
}

variable "capacity-max" {
  default = 1
}

variable "capacity-desired" {
  default = 1
}

variable "key_name" {
  description = ""
}
