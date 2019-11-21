provider "aws" {
  version = "~> 2.0"
  region = "${var.aws-region}"
}

resource "aws_autoscaling_group" "unet-training-cluster" {
  name                 = "unet-training-cluster"
  availability_zones   = "${split(", ", var.unet-training-cluster-az)}"
  max_size             = "${var.capacity-max}"
  min_size             = "${var.capacity-min}"
  desired_capacity     = "${var.capacity-desired}"
  launch_configuration = "${aws_launch_configuration.unet-training-cluster.name}"
}

resource "aws_launch_configuration" "unet-training-cluster" {
  name                 = "unet-training-cluster"
  iam_instance_profile = "${aws_iam_instance_profile.s3_rw_profile.name}"
  image_id             = "${var.ubuntu-dl-ami}"
  instance_type        = "${var.instance-type}"
  security_groups      = ["${aws_security_group.default.id}"]
  key_name             = "${var.key_name}"
  user_data            = "${filebase64("init")}"
}

resource "aws_autoscaling_lifecycle_hook" "await" {
  name                   = "await"
  autoscaling_group_name = "${aws_autoscaling_group.unet-training-cluster.name}"
  default_result         = "ABANDON"
  heartbeat_timeout      = 2000
  lifecycle_transition   = "autoscaling:EC2_INSTANCE_LAUNCHING"
}

resource "aws_autoscaling_lifecycle_hook" "failure" {
  name                   = "failure"
  autoscaling_group_name = "${aws_autoscaling_group.unet-training-cluster.name}"
  default_result         = "ABANDON"
  heartbeat_timeout      = 2000
  lifecycle_transition   = "autoscaling:EC2_INSTANCE_TERMINATING"
}

resource "aws_security_group" "default" {
  name        = "ssh-http-open-outbound"
  description = "Used by unet-training-cluster ASG"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
